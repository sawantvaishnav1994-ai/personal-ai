from __future__ import annotations

import base64
import binascii
from pathlib import Path
from typing import Literal

from fastapi import APIRouter, Cookie, HTTPException
from pydantic import BaseModel, Field

from knowledge.store import KnowledgeError
from memory.second_brain import MemoryCandidate


class MemoryCreateBody(BaseModel):
    type: str = Field(default='note', min_length=1, max_length=60)
    subject: str = Field(min_length=1, max_length=240)
    content: str = Field(min_length=1, max_length=20000)
    source: str = Field(default='explicit-owner', max_length=240)
    confidence: float = Field(default=1.0, ge=0, le=1)
    verified: bool = True
    sensitivity: Literal['normal', 'sensitive', 'secret'] = 'normal'
    tags: list[str] = Field(default_factory=list, max_length=50)
    importance: float = Field(default=.7, ge=0, le=1)
    occurred_at: str | None = None
    parent_id: str | None = None


class MemoryUpdateBody(BaseModel):
    type: str | None = Field(default=None, max_length=60)
    subject: str | None = Field(default=None, max_length=240)
    content: str | None = Field(default=None, max_length=20000)
    confidence: float | None = Field(default=None, ge=0, le=1)
    verified: bool | None = None
    sensitivity: Literal['normal', 'sensitive', 'secret'] | None = None
    tags: list[str] | None = Field(default=None, max_length=50)
    importance: float | None = Field(default=None, ge=0, le=1)
    occurred_at: str | None = None
    parent_id: str | None = None


class RetentionBody(BaseModel):
    older_than_days: int = Field(ge=1, le=36500)
    sensitivity: Literal['normal', 'sensitive', 'secret'] | None = None
    confirm_delete: bool = False


class KnowledgeUploadBody(BaseModel):
    filename: str = Field(min_length=1, max_length=180)
    title: str | None = Field(default=None, max_length=240)
    media_type: str = Field(default='application/octet-stream', max_length=160)
    source: str = Field(default='owner-upload', max_length=500)
    access_class: Literal['owner', 'trusted-devices', 'private'] = 'owner'
    content_base64: str | None = Field(default=None, max_length=14_000_000)
    text: str | None = Field(default=None, max_length=10_000_000)
    metadata: dict = Field(default_factory=dict)


class KnowledgeUpdateBody(BaseModel):
    title: str | None = Field(default=None, max_length=240)
    source: str | None = Field(default=None, max_length=500)
    access_class: Literal['owner', 'trusted-devices', 'private'] | None = None
    metadata: dict | None = None


class DevicePermissionsBody(BaseModel):
    scopes: list[str] = Field(max_length=30)


class ConfirmBody(BaseModel):
    confirm: Literal[True]


class QualificationSessionBody(BaseModel):
    stage: Literal['P3.2', 'P3.3', 'P3.4', 'P3.5', 'P3.6', 'P3.7', 'P3.8']
    evidence_class: Literal['real_device', 'production_like', 'competitive']
    environment: dict = Field(default_factory=dict)


class QualificationTrialBody(BaseModel):
    task: str = Field(min_length=1, max_length=240)
    passed: bool
    latency_ms: float | None = Field(default=None, ge=0)
    metrics: dict = Field(default_factory=dict)
    evidence: dict = Field(default_factory=dict)


class QualificationFinishBody(BaseModel):
    duration_seconds: float | None = Field(default=None, ge=0)


class WorkflowCreateBody(BaseModel):
    title: str = Field(min_length=1, max_length=240)
    trigger: dict = Field(default_factory=lambda: {'type': 'manual'})
    steps: list[dict] = Field(min_length=1, max_length=50)
    next_run_at: str | None = None
    interval_seconds: int | None = Field(default=None, ge=1)


class WorkflowRunBody(BaseModel):
    context: dict = Field(default_factory=dict)


class EmergencyStopBody(BaseModel):
    enabled: bool


def owner_product_router(runtime):
    router = APIRouter(prefix='/iphone/api', tags=['owner-product'])
    registry = runtime['device_registry']
    memory = runtime['memory']
    second_brain = runtime['second_brain']
    knowledge = runtime['knowledge']

    def authenticate(device_id: str | None, token: str | None, scope: str):
        if not device_id or not token or not registry.authenticate(device_id, token):
            raise HTTPException(401, 'This browser is not trusted or its session was revoked')
        if hasattr(registry, 'authorize') and not registry.authorize(device_id, scope):
            raise HTTPException(403, f'This device is not permitted to use {scope}')
        return device_id

    def audit(action: str, *, device_id: str, **payload):
        memory.audit('owner-product', action, {'device_id': device_id, **payload})

    def knowledge_access(device_id: str):
        classes = {'owner', 'trusted-devices'}
        if not hasattr(registry, 'authorize') or registry.authorize(device_id, 'knowledge:private'):
            classes.add('private')
        return classes

    def can_read_sensitive_memory(device_id: str):
        return not hasattr(registry, 'authorize') or registry.authorize(device_id, 'memory:sensitive')

    def filter_memories(rows, device_id: str):
        if can_read_sensitive_memory(device_id):
            return rows
        return [row for row in rows if str(row.get('sensitivity', 'normal')) not in {'sensitive', 'secret'}]

    def filter_tree(rows, device_id: str):
        output = []
        for row in rows:
            children = filter_tree(row.get('children', []), device_id)
            if can_read_sensitive_memory(device_id) or str(row.get('sensitivity', 'normal')) not in {'sensitive', 'secret'}:
                output.append({**row, 'children': children})
            else:
                output.extend(children)
        return output

    @router.get('/memory')
    def memory_list(
        q: str = '',
        limit: int = 100,
        pa_device: str | None = Cookie(default=None),
        pa_token: str | None = Cookie(default=None),
    ):
        device_id = authenticate(pa_device, pa_token, 'memory:read')
        rows = second_brain.context(q, min(limit, 100)) if q.strip() else memory.temporal_search(limit=min(limit, 100))
        return {'memories': filter_memories(rows, device_id)}

    @router.get('/memory/graph')
    def memory_graph(pa_device: str | None = Cookie(default=None), pa_token: str | None = Cookie(default=None)):
        device_id = authenticate(pa_device, pa_token, 'memory:read')
        graph = second_brain.graph()
        nodes = filter_memories(graph.get('nodes', []), device_id)
        ids = {row['id'] for row in nodes}
        return {'nodes': nodes, 'edges': [edge for edge in graph.get('edges', []) if edge['source_id'] in ids and edge['target_id'] in ids]}

    @router.get('/memory/tree')
    def memory_tree(pa_device: str | None = Cookie(default=None), pa_token: str | None = Cookie(default=None)):
        device_id = authenticate(pa_device, pa_token, 'memory:read')
        return {'roots': filter_tree(memory.tree(), device_id)}

    @router.get('/memory/export')
    def memory_export(
        include_sensitive: bool = True,
        pa_device: str | None = Cookie(default=None),
        pa_token: str | None = Cookie(default=None),
    ):
        device_id = authenticate(pa_device, pa_token, 'memory:read')
        if include_sensitive and not can_read_sensitive_memory(device_id):
            raise HTTPException(403, 'This device cannot export sensitive memory')
        audit('memory.exported', device_id=device_id, include_sensitive=include_sensitive)
        return memory.export(include_sensitive=include_sensitive)

    @router.post('/memory/retention')
    def memory_retention(
        body: RetentionBody,
        pa_device: str | None = Cookie(default=None),
        pa_token: str | None = Cookie(default=None),
    ):
        device_id = authenticate(pa_device, pa_token, 'memory:write')
        if body.sensitivity in {'sensitive', 'secret'} and not can_read_sensitive_memory(device_id):
            raise HTTPException(403, 'This device cannot create sensitive memory')
        result = second_brain.apply_retention(
            older_than_days=body.older_than_days,
            sensitivity=body.sensitivity,
            dry_run=not body.confirm_delete,
        )
        audit('memory.retention', device_id=device_id, matched=result['matched'], deleted=body.confirm_delete)
        return result

    @router.post('/memory')
    def memory_create(
        body: MemoryCreateBody,
        pa_device: str | None = Cookie(default=None),
        pa_token: str | None = Cookie(default=None),
    ):
        device_id = authenticate(pa_device, pa_token, 'memory:write')
        if body.sensitivity in {'sensitive', 'secret'} and not can_read_sensitive_memory(device_id):
            raise HTTPException(403, 'This device cannot create sensitive memory')
        memory_id = second_brain.remember(MemoryCandidate(
            type=body.type,
            subject=body.subject,
            content=body.content,
            confidence=body.confidence,
            source=body.source,
            verified=body.verified,
            tags=body.tags,
            importance=body.importance,
            sensitivity=body.sensitivity,
            occurred_at=body.occurred_at,
        ))
        if body.parent_id:
            memory.update_memory(memory_id, parent_id=body.parent_id)
        audit('memory.created', device_id=device_id, memory_id=memory_id)
        return second_brain.memory_detail(memory_id)

    @router.get('/memory/{memory_id}')
    def memory_detail(memory_id: str, pa_device: str | None = Cookie(default=None), pa_token: str | None = Cookie(default=None)):
        device_id = authenticate(pa_device, pa_token, 'memory:read')
        detail = second_brain.memory_detail(memory_id)
        if not detail or not filter_memories([detail], device_id):
            raise HTTPException(404, 'Memory not found')
        return detail

    @router.patch('/memory/{memory_id}')
    def memory_update(
        memory_id: str,
        body: MemoryUpdateBody,
        pa_device: str | None = Cookie(default=None),
        pa_token: str | None = Cookie(default=None),
    ):
        device_id = authenticate(pa_device, pa_token, 'memory:write')
        existing = memory.get(memory_id)
        if not existing or not filter_memories([existing], device_id):
            raise HTTPException(404, 'Memory not found')
        if body.sensitivity in {'sensitive', 'secret'} and not can_read_sensitive_memory(device_id):
            raise HTTPException(403, 'This device cannot mark memory sensitive')
        changes = body.model_dump(exclude_none=True)
        if not memory.update_memory(memory_id, **changes):
            raise HTTPException(404, 'Memory not found or no supported changes supplied')
        audit('memory.corrected', device_id=device_id, memory_id=memory_id, fields=sorted(changes))
        return second_brain.memory_detail(memory_id)

    @router.delete('/memory/{memory_id}')
    def memory_delete(
        memory_id: str,
        confirm: bool = False,
        pa_device: str | None = Cookie(default=None),
        pa_token: str | None = Cookie(default=None),
    ):
        device_id = authenticate(pa_device, pa_token, 'memory:write')
        if not confirm:
            raise HTTPException(409, 'Memory deletion requires confirm=true')
        existing = memory.get(memory_id)
        if not existing or not filter_memories([existing], device_id):
            raise HTTPException(404, 'Memory not found')
        if not second_brain.delete(memory_id):
            raise HTTPException(404, 'Memory not found')
        audit('memory.deleted', device_id=device_id, memory_id=memory_id)
        return {'ok': True, 'memory_id': memory_id}

    @router.get('/knowledge')
    def knowledge_list(
        q: str = '',
        limit: int = 100,
        pa_device: str | None = Cookie(default=None),
        pa_token: str | None = Cookie(default=None),
    ):
        device_id = authenticate(pa_device, pa_token, 'knowledge:read')
        return {'documents': knowledge.list(q, limit=min(limit, 100), access_classes=knowledge_access(device_id))}

    @router.get('/knowledge/search')
    def knowledge_search(
        q: str,
        limit: int = 12,
        pa_device: str | None = Cookie(default=None),
        pa_token: str | None = Cookie(default=None),
    ):
        device_id = authenticate(pa_device, pa_token, 'knowledge:read')
        return {'results': knowledge.search(q, limit=min(limit, 50), access_classes=knowledge_access(device_id))}

    @router.get('/knowledge/export')
    def knowledge_export(pa_device: str | None = Cookie(default=None), pa_token: str | None = Cookie(default=None)):
        device_id = authenticate(pa_device, pa_token, 'knowledge:read')
        audit('knowledge.exported', device_id=device_id)
        return knowledge.export(access_classes=knowledge_access(device_id))

    @router.post('/knowledge')
    def knowledge_upload(
        body: KnowledgeUploadBody,
        pa_device: str | None = Cookie(default=None),
        pa_token: str | None = Cookie(default=None),
    ):
        device_id = authenticate(pa_device, pa_token, 'knowledge:write')
        if body.access_class == 'private' and 'private' not in knowledge_access(device_id):
            raise HTTPException(403, 'This device cannot create private knowledge')
        try:
            if body.content_base64 is not None:
                data = base64.b64decode(body.content_base64, validate=True)
            elif body.text is not None:
                data = body.text.encode('utf-8')
            else:
                raise KnowledgeError('File content is required')
            document = knowledge.ingest(
                filename=body.filename,
                data=data,
                title=body.title,
                media_type=body.media_type,
                source=body.source,
                access_class=body.access_class,
                metadata=body.metadata,
            )
        except (KnowledgeError, binascii.Error) as exc:
            raise HTTPException(400, str(exc)) from exc
        audit('knowledge.ingested', device_id=device_id, document_id=document['id'], checksum=document['checksum'])
        return document

    @router.get('/knowledge/{document_id}')
    def knowledge_detail(document_id: str, pa_device: str | None = Cookie(default=None), pa_token: str | None = Cookie(default=None)):
        device_id = authenticate(pa_device, pa_token, 'knowledge:read')
        document = knowledge.detail(document_id)
        if not document or document['access_class'] not in knowledge_access(device_id):
            raise HTTPException(404, 'Knowledge document not found')
        return document

    @router.patch('/knowledge/{document_id}')
    def knowledge_update(
        document_id: str,
        body: KnowledgeUpdateBody,
        pa_device: str | None = Cookie(default=None),
        pa_token: str | None = Cookie(default=None),
    ):
        device_id = authenticate(pa_device, pa_token, 'knowledge:write')
        existing = knowledge.detail(document_id)
        if not existing or existing['access_class'] not in knowledge_access(device_id):
            raise HTTPException(404, 'Knowledge document not found')
        if body.access_class == 'private' and 'private' not in knowledge_access(device_id):
            raise HTTPException(403, 'This device cannot mark knowledge private')
        try:
            document = knowledge.update(document_id, **body.model_dump(exclude_none=True))
        except KeyError as exc:
            raise HTTPException(404, str(exc)) from exc
        except KnowledgeError as exc:
            raise HTTPException(400, str(exc)) from exc
        audit('knowledge.updated', device_id=device_id, document_id=document_id)
        return document

    @router.delete('/knowledge/{document_id}')
    def knowledge_delete(
        document_id: str,
        confirm: bool = False,
        pa_device: str | None = Cookie(default=None),
        pa_token: str | None = Cookie(default=None),
    ):
        device_id = authenticate(pa_device, pa_token, 'knowledge:write')
        if not confirm:
            raise HTTPException(409, 'Knowledge deletion requires confirm=true')
        existing = knowledge.detail(document_id)
        if not existing or existing['access_class'] not in knowledge_access(device_id):
            raise HTTPException(404, 'Knowledge document not found')
        if not knowledge.delete(document_id):
            raise HTTPException(404, 'Knowledge document not found')
        audit('knowledge.deleted', device_id=device_id, document_id=document_id)
        return {'ok': True, 'document_id': document_id}

    @router.get('/activities')
    def activities(
        category: str | None = None,
        limit: int = 200,
        pa_device: str | None = Cookie(default=None),
        pa_token: str | None = Cookie(default=None),
    ):
        authenticate(pa_device, pa_token, 'activities:read')
        return {'activities': memory.audit_entries(category, min(limit, 500))}

    @router.get('/devices')
    def devices(pa_device: str | None = Cookie(default=None), pa_token: str | None = Cookie(default=None)):
        device_id = authenticate(pa_device, pa_token, 'device:read')
        return {'current_device_id': device_id, 'devices': registry.list()}

    @router.patch('/devices/{target_device_id}/permissions')
    def device_permissions(
        target_device_id: str,
        body: DevicePermissionsBody,
        pa_device: str | None = Cookie(default=None),
        pa_token: str | None = Cookie(default=None),
    ):
        device_id = authenticate(pa_device, pa_token, 'device:admin')
        try:
            result = registry.set_permissions(target_device_id, body.scopes)
        except KeyError as exc:
            raise HTTPException(404, str(exc)) from exc
        except ValueError as exc:
            raise HTTPException(400, str(exc)) from exc
        audit('device.permissions.updated', device_id=device_id, target_device_id=target_device_id, scopes=result['scopes'])
        return result

    @router.post('/devices/{target_device_id}/revoke')
    def device_revoke(
        target_device_id: str,
        body: ConfirmBody,
        pa_device: str | None = Cookie(default=None),
        pa_token: str | None = Cookie(default=None),
    ):
        device_id = authenticate(pa_device, pa_token, 'device:admin')
        if not registry.revoke(target_device_id):
            raise HTTPException(404, 'Device not found')
        audit('device.revoked', device_id=device_id, target_device_id=target_device_id)
        return {'ok': True, 'revoked_device_id': target_device_id, 'current_device_revoked': target_device_id == device_id}

    @router.get('/workflows')
    def workflows(pa_device: str | None = Cookie(default=None), pa_token: str | None = Cookie(default=None)):
        authenticate(pa_device, pa_token, 'workflow:read')
        engine = runtime['automations']
        return {'workflows': engine.workflows(), 'runs': engine.runs(limit=100)}

    @router.post('/workflows')
    def workflow_create(body: WorkflowCreateBody, pa_device: str | None = Cookie(default=None), pa_token: str | None = Cookie(default=None)):
        device_id = authenticate(pa_device, pa_token, 'workflow:write')
        try:
            workflow_id = runtime['automations'].create_workflow(
                body.title, body.trigger, body.steps,
                next_run_at=body.next_run_at, interval_seconds=body.interval_seconds,
            )
        except (TypeError, ValueError) as exc:
            raise HTTPException(400, str(exc)) from exc
        audit('workflow.created', device_id=device_id, workflow_id=workflow_id)
        return runtime['automations'].workflow(workflow_id)

    @router.post('/workflows/{workflow_id}/run')
    def workflow_run(workflow_id: str, body: WorkflowRunBody, pa_device: str | None = Cookie(default=None), pa_token: str | None = Cookie(default=None)):
        device_id = authenticate(pa_device, pa_token, 'workflow:write')
        try:
            run_id = runtime['automations'].run_workflow(workflow_id, context=body.context, background=True)
        except (KeyError, RuntimeError) as exc:
            raise HTTPException(409, str(exc)) from exc
        audit('workflow.started', device_id=device_id, workflow_id=workflow_id, run_id=run_id)
        return {'workflow_id': workflow_id, 'run_id': run_id, 'status': 'queued'}

    @router.post('/workflows/runs/{run_id}/cancel')
    def workflow_cancel(run_id: str, pa_device: str | None = Cookie(default=None), pa_token: str | None = Cookie(default=None)):
        device_id = authenticate(pa_device, pa_token, 'workflow:write')
        try:
            result = runtime['automations'].cancel_run(run_id)
        except KeyError as exc:
            raise HTTPException(404, str(exc)) from exc
        audit('workflow.cancelled', device_id=device_id, run_id=run_id)
        return result

    @router.post('/workflows/runs/{run_id}/resume')
    def workflow_resume(run_id: str, pa_device: str | None = Cookie(default=None), pa_token: str | None = Cookie(default=None)):
        device_id = authenticate(pa_device, pa_token, 'workflow:write')
        try:
            result = runtime['automations'].resume_run(run_id)
        except (KeyError, RuntimeError) as exc:
            raise HTTPException(409, str(exc)) from exc
        audit('workflow.resumed', device_id=device_id, run_id=run_id)
        return result

    @router.post('/workflows/runs/{run_id}/approve')
    def workflow_approve(run_id: str, pa_device: str | None = Cookie(default=None), pa_token: str | None = Cookie(default=None)):
        device_id = authenticate(pa_device, pa_token, 'workflow:approve')
        run = runtime['automations']._run(run_id)
        approval_id = run.get('pending_approval_id')
        if not approval_id:
            raise HTTPException(409, 'Workflow is not waiting for approval')
        try:
            result = runtime['automations'].approve_run(run_id, approval_id)
        except (KeyError, PermissionError, RuntimeError) as exc:
            raise HTTPException(409, str(exc)) from exc
        audit('workflow.approved', device_id=device_id, run_id=run_id, approval_id=approval_id)
        return result

    @router.post('/workflows/runs/{run_id}/reject')
    def workflow_reject(run_id: str, pa_device: str | None = Cookie(default=None), pa_token: str | None = Cookie(default=None)):
        device_id = authenticate(pa_device, pa_token, 'workflow:approve')
        run = runtime['automations']._run(run_id)
        approval_id = run.get('pending_approval_id')
        if not approval_id:
            raise HTTPException(409, 'Workflow is not waiting for approval')
        try:
            result = runtime['automations'].reject_run(run_id, approval_id)
        except (KeyError, PermissionError, RuntimeError) as exc:
            raise HTTPException(409, str(exc)) from exc
        audit('workflow.rejected', device_id=device_id, run_id=run_id, approval_id=approval_id)
        return result

    @router.post('/system/emergency-stop')
    def emergency_stop(body: EmergencyStopBody, pa_device: str | None = Cookie(default=None), pa_token: str | None = Cookie(default=None)):
        device_id = authenticate(pa_device, pa_token, 'device:admin')
        runtime['tools'].set_emergency_stop(body.enabled)
        autonomy = runtime.get('advanced_autonomy')
        if autonomy is not None:
            autonomy.emergency_stop('owner requested from trusted device') if body.enabled else autonomy.clear_emergency_stop()
        audit('system.emergency_stop', device_id=device_id, enabled=body.enabled)
        return {'enabled': body.enabled, 'message': 'All tool actions stopped' if body.enabled else 'Tool actions enabled'}

    @router.get('/qualification')
    def qualification_status(pa_device: str | None = Cookie(default=None), pa_token: str | None = Cookie(default=None)):
        authenticate(pa_device, pa_token, 'qualification:read')
        return runtime['p3_qualification'].status()

    @router.post('/qualification/stages')
    def qualification_start(
        body: QualificationSessionBody,
        pa_device: str | None = Cookie(default=None),
        pa_token: str | None = Cookie(default=None),
    ):
        device_id = authenticate(pa_device, pa_token, 'qualification:record')
        environment = {**body.environment, 'device_id': device_id, 'surface': 'ios-pwa'}
        try:
            session_id = runtime['p3_qualification'].start_session(
                body.stage,
                evidence_class=body.evidence_class,
                environment=environment,
            )
        except ValueError as exc:
            raise HTTPException(400, str(exc)) from exc
        audit('qualification.session.started', device_id=device_id, session_id=session_id, stage=body.stage)
        return {'session_id': session_id, 'stage': body.stage, 'evidence_class': body.evidence_class}

    @router.post('/qualification/sessions/{session_id}/trials')
    def qualification_trial(
        session_id: str,
        body: QualificationTrialBody,
        pa_device: str | None = Cookie(default=None),
        pa_token: str | None = Cookie(default=None),
    ):
        device_id = authenticate(pa_device, pa_token, 'qualification:record')
        evidence = {**body.evidence, 'device_id': device_id}
        try:
            trial = runtime['p3_qualification'].record_trial(
                session_id,
                body.task,
                passed=body.passed,
                latency_ms=body.latency_ms,
                metrics=body.metrics,
                evidence=evidence,
            )
        except (KeyError, ValueError) as exc:
            raise HTTPException(400, str(exc)) from exc
        return {'trial': trial, 'session_id': session_id}

    @router.post('/qualification/sessions/{session_id}/finish')
    def qualification_finish(
        session_id: str,
        body: QualificationFinishBody,
        pa_device: str | None = Cookie(default=None),
        pa_token: str | None = Cookie(default=None),
    ):
        device_id = authenticate(pa_device, pa_token, 'qualification:record')
        try:
            result = runtime['p3_qualification'].finish_session(session_id, duration_seconds=body.duration_seconds)
        except (KeyError, ValueError) as exc:
            raise HTTPException(400, str(exc)) from exc
        audit('qualification.session.finished', device_id=device_id, session_id=session_id)
        return result

    @router.get('/system/status')
    def system_status(pa_device: str | None = Cookie(default=None), pa_token: str | None = Cookie(default=None)):
        authenticate(pa_device, pa_token, 'activities:read')
        return {
            'model': runtime['models'].status(),
            'tools': [
                {'name': tool.name, 'description': tool.description, 'risk': tool.risk.name}
                for tool in runtime['tools'].all()
            ],
            'integrations': runtime['integrations'].list(),
            'future_intelligence': runtime['future_intelligence'].status(),
            'emergency_stop': bool(getattr(runtime['tools'], 'emergency_stop', False)),
        }

    return router
