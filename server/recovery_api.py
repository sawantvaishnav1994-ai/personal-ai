from __future__ import annotations

import json
from typing import Callable

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel, Field

from desktop.operator_recovery import OperatorRecoveryStore, CONSEQUENTIAL_OWNER_DECISIONS
from desktop.operator_transactions import OperatorBinding


class RecoveryDecisionRequest(BaseModel):
    decision: str
    decision_id: str
    security_epoch: int = 0


class RecoveryVerifyRequest(BaseModel):
    dispatch_id: str


class RecoveryReportResponse(BaseModel):
    transaction_id: str
    goal: str
    state: str
    checkpoint_index: int
    resume_position: int
    recovery_reason: str
    owner_decision: str
    dispatches: list[dict] = Field(default_factory=list)
    verifications: list[dict] = Field(default_factory=list)
    compensations: list[dict] = Field(default_factory=list)
    rollback_limitations: str
    updated_at: float


def create_recovery_router(store: OperatorRecoveryStore, authenticate: Callable[[str,str], object], *,
                           current_security_epoch: Callable[[],int] | None=None,
                           consequential_authority: Callable[[OperatorBinding,str,str],bool] | None=None) -> APIRouter:
    """Owner-visible recovery API. Consequential decisions fail closed unless TAC-backed authority is supplied."""
    router=APIRouter(prefix='/activities/recovery',tags=['recovery'])
    authorize_consequential=consequential_authority or (lambda binding,decision,decision_id:False)

    def binding(authorization: str | None, device_id: str | None, session_id: str | None, security_epoch: int=0) -> OperatorBinding:
        if not authorization or not device_id or not session_id:raise HTTPException(status_code=401,detail='authentication_required')
        try:ctx=authenticate(str(authorization),str(device_id))
        except HTTPException:raise
        except Exception:raise HTTPException(status_code=401,detail='authentication_required')
        epoch=int(security_epoch)
        if current_security_epoch is not None and epoch!=int(current_security_epoch()):raise HTTPException(status_code=409,detail='security_epoch_changed')
        owner='owner' if not isinstance(ctx,dict) else str(ctx.get('owner_id') or ctx.get('user_id') or 'owner')
        return OperatorBinding(owner,str(device_id),str(session_id),epoch)

    @router.get('/{transaction_id}',response_model=RecoveryReportResponse)
    def report(transaction_id: str, authorization: str | None=Header(default=None), x_device_id: str | None=Header(default=None,alias='X-Device-ID'), x_session_id: str | None=Header(default=None,alias='X-Session-ID'), x_security_epoch: int=Header(default=0,alias='X-Security-Epoch')):
        bind=binding(authorization,x_device_id,x_session_id,x_security_epoch)
        try:store.transactions.assert_binding(transaction_id,bind);return store.recovery_report(transaction_id)
        except KeyError:raise HTTPException(status_code=404,detail='recovery_not_found')
        except PermissionError:raise HTTPException(status_code=403,detail='recovery_binding_mismatch')

    @router.post('/{transaction_id}/decision')
    def decide(transaction_id: str, request: RecoveryDecisionRequest, authorization: str | None=Header(default=None), x_device_id: str | None=Header(default=None,alias='X-Device-ID'), x_session_id: str | None=Header(default=None,alias='X-Session-ID')):
        bind=binding(authorization,x_device_id,x_session_id,request.security_epoch)
        reauthenticated=False
        if request.decision in CONSEQUENTIAL_OWNER_DECISIONS:
            if not authorize_consequential(bind,request.decision,request.decision_id):
                raise HTTPException(status_code=409,detail='reauthentication_required')
            reauthenticated=True
        try:
            result,created=store.owner_decision(transaction_id,bind,decision=request.decision,decision_id=request.decision_id,reauthenticated=reauthenticated)
            return {'ok':True,'created':created,'decision':result}
        except KeyError:raise HTTPException(status_code=404,detail='recovery_not_found')
        except PermissionError:raise HTTPException(status_code=409,detail='recovery_decision_rejected')
        except ValueError:raise HTTPException(status_code=400,detail='invalid_recovery_decision')

    @router.post('/{transaction_id}/verify-again')
    def verify_again(transaction_id: str, request: RecoveryVerifyRequest, authorization: str | None=Header(default=None), x_device_id: str | None=Header(default=None,alias='X-Device-ID'), x_session_id: str | None=Header(default=None,alias='X-Session-ID'), x_security_epoch: int=Header(default=0,alias='X-Security-Epoch')):
        bind=binding(authorization,x_device_id,x_session_id,x_security_epoch)
        try:
            store.transactions.assert_binding(transaction_id,bind);dispatch=store.dispatch(request.dispatch_id)
            if not dispatch or dispatch['transaction_id']!=transaction_id:raise HTTPException(status_code=404,detail='dispatch_not_found')
            return {'ok':True,'state':'verification_pending','dispatch_id':request.dispatch_id,'instruction':'perform_read_only_verification'}
        except PermissionError:raise HTTPException(status_code=403,detail='recovery_binding_mismatch')

    @router.get('/{transaction_id}/export')
    def export(transaction_id: str, authorization: str | None=Header(default=None), x_device_id: str | None=Header(default=None,alias='X-Device-ID'), x_session_id: str | None=Header(default=None,alias='X-Session-ID'), x_security_epoch: int=Header(default=0,alias='X-Security-Epoch')):
        bind=binding(authorization,x_device_id,x_session_id,x_security_epoch)
        try:store.transactions.assert_binding(transaction_id,bind);report=store.recovery_report(transaction_id)
        except KeyError:raise HTTPException(status_code=404,detail='recovery_not_found')
        except PermissionError:raise HTTPException(status_code=403,detail='recovery_binding_mismatch')
        return {'filename':f'recovery-{transaction_id}.json','media_type':'application/json','content':json.dumps(report,sort_keys=True,separators=(',',':'))}

    return router
