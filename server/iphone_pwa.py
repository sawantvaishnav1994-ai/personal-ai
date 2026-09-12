from __future__ import annotations

import asyncio
import hmac
import threading
from pathlib import Path
from typing import Literal

from fastapi import APIRouter, Cookie, HTTPException, Request, Response
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel, Field

from agent.executor import ConfirmationRequired, ExecutionCancelled
from models.router import ModelError


class OwnerEnrollBody(BaseModel):
    code: str
    name: str = 'Owner iPhone'


class VoiceTurnBody(BaseModel):
    transcript: str = Field(min_length=1, max_length=8000)
    conversation_id: str | None = Field(default=None, max_length=80)


class BargeBody(BaseModel):
    speaking: bool = True


class VoiceClientEventBody(BaseModel):
    event: Literal['tts_started', 'tts_completed', 'tts_error']
    detail: str = Field(default='', max_length=160)


class QualificationStartBody(BaseModel):
    environment: dict = Field(default_factory=dict)
    notes: str = 'iPhone Safari physical voice qualification'


class QualificationTakeoverBody(QualificationStartBody):
    confirm: Literal[True]


class ConversationCreateBody(BaseModel):
    title: str = Field(default='New conversation', max_length=120)


class ConversationRenameBody(BaseModel):
    title: str = Field(min_length=1, max_length=120)


class IphonePwaState:
    def __init__(self):
        self._lock = threading.RLock()
        self._cancel: dict[str, threading.Event] = {}

    def begin_turn(self, device_id: str) -> threading.Event:
        with self._lock:
            previous = self._cancel.get(device_id)
            if previous:
                previous.set()
            current = threading.Event()
            self._cancel[device_id] = current
            return current

    def cancel(self, device_id: str) -> bool:
        with self._lock:
            current = self._cancel.get(device_id)
            if not current:
                return False
            current.set()
            return True

    def finish(self, device_id: str, event: threading.Event):
        with self._lock:
            if self._cancel.get(device_id) is event:
                self._cancel.pop(device_id, None)


def iphone_pwa_router(runtime, settings):
    router = APIRouter(prefix='/iphone', tags=['iphone-pwa'])
    state = IphonePwaState()
    web_dir = Path(settings.base_dir) / 'pwa'
    registry = runtime['device_registry']
    executor = runtime['executor']
    events = runtime.get('events')
    continuity = runtime.get('continuity')
    recorder = runtime.get('voice_qualification')
    pending_approvals: dict[str, dict] = {}
    pending_approvals_lock = threading.RLock()

    def device_cookie_kwargs():
        cookie_days = max(1, min(int(getattr(settings, 'iphone_device_cookie_days', 365)), 3650))
        return dict(
            httponly=True,
            secure=True,
            samesite='strict',
            path='/iphone',
            max_age=60 * 60 * 24 * cookie_days,
        )

    def require_https(request: Request):
        forwarded = request.headers.get('x-forwarded-proto', '').split(',')[0].strip().lower()
        scheme = forwarded or request.url.scheme.lower()
        if scheme != 'https' and not getattr(settings, 'iphone_pwa_allow_insecure', False):
            raise HTTPException(400, 'iPhone owner enrollment requires HTTPS')

    def auth_device(device_id: str | None, device_token: str | None):
        if not device_id or not device_token or not registry.authenticate(device_id, device_token):
            raise HTTPException(401, 'iPhone session is not enrolled or has been revoked')
        if not registry.is_active(device_id):
            raise HTTPException(401, 'iPhone device is revoked')
        if hasattr(registry, 'authorize') and not registry.authorize(device_id, 'ai:chat'):
            raise HTTPException(403, 'This device is not permitted to use conversation or voice')
        return device_id

    def emit(name: str, **payload):
        if events:
            events.emit(name, **payload)

    def resolve_conversation(device_id: str, conversation_id: str | None = None):
        if continuity is None:
            return None
        if conversation_id:
            thread = continuity.thread(conversation_id)
            if not thread or thread.get('closed_at'):
                raise HTTPException(404, 'Conversation not found')
            continuity.set_active(device_id, thread['id'])
            return thread
        bundle = continuity.resume(device_id, event_limit=100)
        return bundle.get('thread')

    def append_conversation(thread, device_id: str, kind: str, text: str, **payload):
        if not thread or continuity is None:
            return
        continuity.append(
            thread['id'],
            device_id=device_id,
            kind=kind,
            payload={'text': text, **payload},
        )

    def model_history(thread):
        if not thread or continuity is None:
            return None
        roles = {'user_message': 'user', 'assistant_message': 'assistant'}
        history = []
        for event in continuity.events_for_thread(thread['id'], limit=1000):
            role = roles.get(event.get('kind'))
            text = str(event.get('payload', {}).get('text') or '').strip()
            if role and text:
                history.append({'role': role, 'content': text})
        return history[-16:]

    @router.get('', response_class=HTMLResponse, include_in_schema=False)
    @router.get('/', response_class=HTMLResponse, include_in_schema=False)
    def iphone_home():
        return HTMLResponse((web_dir / 'index.html').read_text(encoding='utf-8'), headers={'Cache-Control': 'no-store'})

    @router.get('/manifest.webmanifest', include_in_schema=False)
    def manifest():
        return Response((web_dir / 'manifest.webmanifest').read_text(encoding='utf-8'), media_type='application/manifest+json')

    @router.get('/sw.js', include_in_schema=False)
    def service_worker():
        return Response((web_dir / 'sw.js').read_text(encoding='utf-8'), media_type='application/javascript', headers={'Cache-Control': 'no-cache'})

    @router.get('/api/status')
    def status(
        response: Response,
        pa_device: str | None = Cookie(default=None),
        pa_token: str | None = Cookie(default=None),
    ):
        device_id = auth_device(pa_device, pa_token)
        # Successful use renews this browser's durable trust without changing
        # its scoped credential or weakening revocation checks.
        response.set_cookie('pa_device', device_id, **device_cookie_kwargs())
        response.set_cookie('pa_token', pa_token, **device_cookie_kwargs())
        active_qualification = None
        if recorder is not None:
            active = recorder.active_session()
            if active and active.get('environment', {}).get('device_id') == device_id:
                active_qualification = {
                    'session_id': active['id'],
                    'evidence_class': active['evidence_class'],
                    'started_at': active.get('started_at'),
                }
        conversation = None
        conversations = []
        if continuity is not None:
            bundle = continuity.resume(device_id, event_limit=100)
            conversation = bundle
            conversations = continuity.list_threads(limit=50)
        memory_count = 0
        second_brain = runtime.get('second_brain')
        if second_brain is not None:
            try:
                memory_count = len(second_brain.graph().get('nodes', []))
            except Exception:
                memory_count = 0
        return {
            'ok': True,
            'device_id': device_id,
            'voice_qualification_available': recorder is not None,
            'active_qualification': active_qualification,
            'continuity_available': continuity is not None,
            'conversation': conversation,
            'conversations': conversations,
            'memory_count': memory_count,
            'model': runtime['models'].status() if runtime.get('models') else {'state': 'unavailable'},
        }

    @router.post('/api/enroll')
    def enroll(body: OwnerEnrollBody, request: Request, response: Response):
        require_https(request)
        expected = getattr(settings, 'iphone_owner_enrollment_code', '').strip()
        if len(expected) < 12:
            raise HTTPException(503, 'iPhone owner enrollment is not configured')
        if not hmac.compare_digest(body.code.strip(), expected):
            raise HTTPException(401, 'Invalid owner enrollment code')
        device, token = registry.enroll(body.name.strip() or 'Owner iPhone', 'ios-pwa')
        if hasattr(registry, 'set_permissions') and hasattr(registry, 'OWNER_SCOPES'):
            registry.set_permissions(device['id'], registry.OWNER_SCOPES)
        if continuity:
            continuity.resume(device['id'])
        cookie_kwargs = device_cookie_kwargs()
        response.set_cookie('pa_device', device['id'], **cookie_kwargs)
        response.set_cookie('pa_token', token, **cookie_kwargs)
        emit('iphone.enrolled', device_id=device['id'], platform='ios-pwa')
        return {'ok': True, 'device_id': device['id']}

    @router.post('/api/logout')
    def logout(response: Response):
        response.delete_cookie('pa_device', path='/iphone')
        response.delete_cookie('pa_token', path='/iphone')
        return {'ok': True}

    @router.post('/api/voice/turn')
    async def voice_turn(
        body: VoiceTurnBody,
        pa_device: str | None = Cookie(default=None),
        pa_token: str | None = Cookie(default=None),
    ):
        device_id = auth_device(pa_device, pa_token)
        transcript = body.transcript.strip()
        conversation = resolve_conversation(device_id, body.conversation_id)
        conversation_history = model_history(conversation)
        append_conversation(conversation, device_id, 'user_message', transcript)
        if conversation and conversation['title'] in {'New conversation', 'Current context', 'Primary Personal AI Context'}:
            continuity.rename_thread(conversation['id'], transcript[:72])
            conversation = continuity.thread(conversation['id'])
        cancel_event = state.begin_turn(device_id)
        emit('state', state='understanding', device_id=device_id, source='iphone-pwa')
        emit('voice.transcript', text=transcript, device_id=device_id, source='iphone-pwa')
        try:
            reply = await asyncio.to_thread(
                executor.chat,
                transcript,
                cancel_event=cancel_event,
                device_id=device_id,
                conversation_id=conversation['id'] if conversation else None,
                conversation_history=conversation_history,
            )
            if cancel_event.is_set():
                emit('voice.turn.cancelled', device_id=device_id, source='iphone-pwa')
                emit('state', state='listening', device_id=device_id, source='iphone-pwa')
                raise HTTPException(409, 'turn_cancelled')
            emit('voice.reply', text=reply, device_id=device_id, source='iphone-pwa')
            append_conversation(conversation, device_id, 'assistant_message', reply)
            emit('state', state='speaking', device_id=device_id, source='iphone-pwa')
            return {
                'reply': reply,
                'device_id': device_id,
                'conversation_id': conversation['id'] if conversation else None,
                'conversation_title': conversation['title'] if conversation else None,
            }
        except ExecutionCancelled:
            emit('voice.turn.cancelled', device_id=device_id, source='iphone-pwa')
            emit('state', state='listening', device_id=device_id, source='iphone-pwa')
            raise HTTPException(409, 'turn_cancelled')
        except ConfirmationRequired as exc:
            with pending_approvals_lock:
                pending_approvals[exc.approval_id] = {
                    'device_id': device_id,
                    'tool': exc.tool_name,
                    'conversation_id': conversation['id'] if conversation else None,
                }
            emit(
                'state',
                state='approval',
                approval_id=exc.approval_id,
                tool=exc.tool_name,
                device_id=device_id,
                source='iphone-pwa',
            )
            return JSONResponse(status_code=202, content={
                'status': 'approval_required',
                'reply': f'This action needs your approval before I can use {exc.tool_name}.',
                'approval': {
                    'id': exc.approval_id,
                    'tool': exc.tool_name,
                    'description': exc.description or f'Use {exc.tool_name}',
                    'expires_at': exc.expires_at,
                },
                'device_id': device_id,
                'conversation_id': conversation['id'] if conversation else None,
            })
        except ModelError as exc:
            emit('voice.error', error=exc.code, device_id=device_id, source='iphone-pwa')
            emit('state', state='error', error=exc.code, device_id=device_id, source='iphone-pwa')
            raise HTTPException(exc.status_code, {'code': exc.code, 'message': exc.user_message})
        finally:
            state.finish(device_id, cancel_event)

    def claim_pending_approval(approval_id: str, device_id: str):
        with pending_approvals_lock:
            pending = pending_approvals.get(approval_id)
        if not pending or pending['device_id'] != device_id:
            raise HTTPException(404, {
                'code': 'approval_not_found',
                'message': 'This approval is missing, expired, or belongs to another device.',
            })
        return pending

    @router.post('/api/approval/{approval_id}/approve')
    async def approval_approve(
        approval_id: str,
        pa_device: str | None = Cookie(default=None),
        pa_token: str | None = Cookie(default=None),
    ):
        device_id = auth_device(pa_device, pa_token)
        pending = claim_pending_approval(approval_id, device_id)
        emit('state', state='acting', device_id=device_id, source='iphone-pwa')
        try:
            reply = await asyncio.to_thread(executor.approve, approval_id)
        except PermissionError:
            raise HTTPException(409, {
                'code': 'approval_expired',
                'message': 'This approval has expired or was already used.',
            })
        except ModelError as exc:
            raise HTTPException(exc.status_code, {'code': exc.code, 'message': exc.user_message})
        except Exception:
            emit('voice.error', error='tool_error', device_id=device_id, source='iphone-pwa')
            raise HTTPException(502, {
                'code': 'tool_error',
                'message': 'The approved action could not be completed safely.',
            })
        finally:
            with pending_approvals_lock:
                pending_approvals.pop(approval_id, None)
        emit('voice.reply', text=reply, device_id=device_id, source='iphone-pwa')
        conversation_id = pending.get('conversation_id')
        if conversation_id and continuity is not None:
            append_conversation(continuity.thread(conversation_id), device_id, 'assistant_message', reply)
        emit('state', state='speaking', device_id=device_id, source='iphone-pwa')
        return {'status': 'approved', 'reply': reply, 'device_id': device_id}

    @router.post('/api/approval/{approval_id}/reject')
    def approval_reject(
        approval_id: str,
        pa_device: str | None = Cookie(default=None),
        pa_token: str | None = Cookie(default=None),
    ):
        device_id = auth_device(pa_device, pa_token)
        pending = claim_pending_approval(approval_id, device_id)
        try:
            reply = executor.reject(approval_id)
        finally:
            with pending_approvals_lock:
                pending_approvals.pop(approval_id, None)
        emit('state', state='listening', device_id=device_id, source='iphone-pwa')
        conversation_id = pending.get('conversation_id')
        if conversation_id and continuity is not None:
            continuity.append(
                conversation_id,
                device_id=device_id,
                kind='approval_rejected',
                payload={'text': reply, 'approval_id': approval_id},
            )
        return {'status': 'rejected', 'reply': reply, 'device_id': device_id}

    @router.get('/api/conversations')
    def conversation_list(
        q: str = '',
        limit: int = 50,
        pa_device: str | None = Cookie(default=None),
        pa_token: str | None = Cookie(default=None),
    ):
        device_id = auth_device(pa_device, pa_token)
        if continuity is None:
            raise HTTPException(503, 'Conversation continuity is unavailable')
        active = continuity.active_for_device(device_id)
        return {
            'active_conversation_id': active['id'] if active else None,
            'conversations': continuity.list_threads(q, limit=max(1, min(limit, 100))),
        }

    @router.post('/api/conversations')
    def conversation_create(
        body: ConversationCreateBody,
        pa_device: str | None = Cookie(default=None),
        pa_token: str | None = Cookie(default=None),
    ):
        device_id = auth_device(pa_device, pa_token)
        if continuity is None:
            raise HTTPException(503, 'Conversation continuity is unavailable')
        thread_id = continuity.create_thread(body.title.strip() or 'New conversation', device_id=device_id)
        return {'conversation': continuity.thread(thread_id), 'events': []}

    @router.get('/api/conversations/{conversation_id}')
    def conversation_get(
        conversation_id: str,
        pa_device: str | None = Cookie(default=None),
        pa_token: str | None = Cookie(default=None),
    ):
        device_id = auth_device(pa_device, pa_token)
        thread = resolve_conversation(device_id, conversation_id)
        return {
            'conversation': thread,
            'events': continuity.events_for_thread(thread['id'], limit=500),
        }

    @router.post('/api/conversations/{conversation_id}/activate')
    def conversation_activate(
        conversation_id: str,
        pa_device: str | None = Cookie(default=None),
        pa_token: str | None = Cookie(default=None),
    ):
        device_id = auth_device(pa_device, pa_token)
        thread = resolve_conversation(device_id, conversation_id)
        return {
            'conversation': thread,
            'events': continuity.events_for_thread(thread['id'], limit=500),
        }

    @router.patch('/api/conversations/{conversation_id}')
    def conversation_rename(
        conversation_id: str,
        body: ConversationRenameBody,
        pa_device: str | None = Cookie(default=None),
        pa_token: str | None = Cookie(default=None),
    ):
        device_id = auth_device(pa_device, pa_token)
        resolve_conversation(device_id, conversation_id)
        return {'conversation': continuity.rename_thread(conversation_id, body.title)}

    @router.post('/api/voice/barge')
    def voice_barge(
        body: BargeBody,
        pa_device: str | None = Cookie(default=None),
        pa_token: str | None = Cookie(default=None),
    ):
        device_id = auth_device(pa_device, pa_token)
        cancelled = state.cancel(device_id)
        if body.speaking or cancelled:
            emit('voice.barge_in', device_id=device_id, source='iphone-pwa')
            emit('voice.turn.cancelled', device_id=device_id, source='iphone-pwa')
            emit('state', state='listening', device_id=device_id, source='iphone-pwa')
        return {'ok': True, 'cancelled_server_turn': cancelled}

    @router.post('/api/voice/client-event')
    def voice_client_event(
        body: VoiceClientEventBody,
        pa_device: str | None = Cookie(default=None),
        pa_token: str | None = Cookie(default=None),
    ):
        device_id = auth_device(pa_device, pa_token)
        emit(f'voice.client.{body.event}', device_id=device_id, source='iphone-pwa', detail=body.detail)
        if body.event == 'tts_error':
            emit('voice.error', error='tts_error', detail=body.detail, device_id=device_id, source='iphone-pwa')
        return {'ok': True}

    @router.post('/api/qualification/start')
    def qualification_start(
        body: QualificationStartBody,
        request: Request,
        pa_device: str | None = Cookie(default=None),
        pa_token: str | None = Cookie(default=None),
    ):
        device_id = auth_device(pa_device, pa_token)
        if recorder is None:
            raise HTTPException(503, 'Voice qualification recorder unavailable')
        environment = {
            **body.environment,
            'device_id': device_id,
            'platform': 'ios-pwa',
            'user_agent': request.headers.get('user-agent', ''),
            'transport': 'https-pwa',
        }

        def resume_active_session():
            active = recorder.active_session()
            if not active:
                return None
            if active.get('environment', {}).get('device_id') != device_id:
                raise HTTPException(409, {
                    'code': 'qualification_session_active',
                    'message': 'Another trusted device already has an active qualification session',
                })
            emit('state', state='listening', device_id=device_id, source='iphone-pwa')
            return {
                'session_id': active['id'],
                'evidence_class': active['evidence_class'],
                'status': 'already_active',
                'message': 'Existing session resumed',
            }

        resumed = resume_active_session()
        if resumed:
            return resumed
        try:
            session_id = recorder.start_session(evidence_class='real_device', environment=environment, notes=body.notes)
        except RuntimeError as exc:
            if str(exc) != 'voice qualification session already active':
                raise
            resumed = resume_active_session()
            if resumed:
                return resumed
            raise HTTPException(409, {
                'code': 'qualification_session_active',
                'message': 'A qualification session is already active',
            })
        emit('state', state='listening', device_id=device_id, source='iphone-pwa')
        return {'session_id': session_id, 'evidence_class': 'real_device', 'status': 'started'}

    @router.post('/api/qualification/stop')
    def qualification_stop(
        pa_device: str | None = Cookie(default=None),
        pa_token: str | None = Cookie(default=None),
    ):
        device_id = auth_device(pa_device, pa_token)
        if recorder is None:
            raise HTTPException(503, 'Voice qualification recorder unavailable')
        active = recorder.active_session()
        if active and active.get('environment', {}).get('device_id') != device_id:
            raise HTTPException(409, {
                'code': 'qualification_session_owned_by_other_device',
                'message': 'This evidence session belongs to another trusted browser and was left running.',
            })
        try:
            return recorder.stop_session()
        except RuntimeError as exc:
            if str(exc) != 'no active voice qualification session':
                raise
            return {'ok': True, 'status': 'already_stopped', 'message': 'Session already stopped'}

    @router.post('/api/qualification/takeover')
    def qualification_takeover(
        body: QualificationTakeoverBody,
        request: Request,
        pa_device: str | None = Cookie(default=None),
        pa_token: str | None = Cookie(default=None),
    ):
        device_id = auth_device(pa_device, pa_token)
        if recorder is None:
            raise HTTPException(503, 'Voice qualification recorder unavailable')
        close_sessions = getattr(recorder, 'close_active_sessions', None)
        if not callable(close_sessions):
            raise HTTPException(503, 'Qualification session recovery is unavailable')
        closed_session_ids = close_sessions(
            reason=f'Owner-confirmed takeover by trusted device {device_id}'
        )
        environment = {
            **body.environment,
            'device_id': device_id,
            'platform': 'ios-pwa',
            'user_agent': request.headers.get('user-agent', ''),
            'transport': 'https-pwa',
        }
        session_id = recorder.start_session(
            evidence_class='real_device',
            environment=environment,
            notes=body.notes,
        )
        emit(
            'qualification.session_takeover',
            device_id=device_id,
            closed_session_ids=closed_session_ids,
            session_id=session_id,
            source='iphone-pwa',
        )
        emit('state', state='listening', device_id=device_id, source='iphone-pwa')
        return {
            'status': 'started',
            'session_id': session_id,
            'evidence_class': 'real_device',
            'closed_session_ids': closed_session_ids,
        }

    @router.get('/api/qualification/sessions')
    def qualification_sessions(
        pa_device: str | None = Cookie(default=None),
        pa_token: str | None = Cookie(default=None),
    ):
        auth_device(pa_device, pa_token)
        if recorder is None:
            raise HTTPException(503, 'Voice qualification recorder unavailable')
        return {'sessions': recorder.sessions()}

    return router
