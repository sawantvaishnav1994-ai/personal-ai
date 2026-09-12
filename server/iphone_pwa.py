from __future__ import annotations

import asyncio
import hmac
import threading
from pathlib import Path
from typing import Literal

from fastapi import APIRouter, Cookie, HTTPException, Request, Response
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field

from agent.executor import ExecutionCancelled
from models.router import ModelError


class OwnerEnrollBody(BaseModel):
    code: str
    name: str = 'Owner iPhone'


class VoiceTurnBody(BaseModel):
    transcript: str = Field(min_length=1, max_length=8000)


class BargeBody(BaseModel):
    speaking: bool = True


class VoiceClientEventBody(BaseModel):
    event: Literal['tts_started', 'tts_completed', 'tts_error']
    detail: str = Field(default='', max_length=160)


class QualificationStartBody(BaseModel):
    environment: dict = Field(default_factory=dict)
    notes: str = 'iPhone Safari physical voice qualification'


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
        return device_id

    def emit(name: str, **payload):
        if events:
            events.emit(name, **payload)

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
        pa_device: str | None = Cookie(default=None),
        pa_token: str | None = Cookie(default=None),
    ):
        device_id = auth_device(pa_device, pa_token)
        active_qualification = None
        if recorder is not None:
            active = recorder.active_session()
            if active and active.get('environment', {}).get('device_id') == device_id:
                active_qualification = {
                    'session_id': active['id'],
                    'evidence_class': active['evidence_class'],
                    'started_at': active.get('started_at'),
                }
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
        if continuity:
            continuity.resume(device['id'])
        cookie_kwargs = dict(httponly=True, secure=True, samesite='strict', path='/iphone', max_age=60 * 60 * 24 * 30)
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
        cancel_event = state.begin_turn(device_id)
        emit('state', state='understanding', device_id=device_id, source='iphone-pwa')
        emit('voice.transcript', text=transcript, device_id=device_id, source='iphone-pwa')
        try:
            reply = await asyncio.to_thread(executor.chat, transcript, cancel_event=cancel_event, device_id=device_id)
            if cancel_event.is_set():
                emit('voice.turn.cancelled', device_id=device_id, source='iphone-pwa')
                emit('state', state='listening', device_id=device_id, source='iphone-pwa')
                raise HTTPException(409, 'turn_cancelled')
            emit('voice.reply', text=reply, device_id=device_id, source='iphone-pwa')
            emit('state', state='speaking', device_id=device_id, source='iphone-pwa')
            return {'reply': reply, 'device_id': device_id}
        except ExecutionCancelled:
            emit('voice.turn.cancelled', device_id=device_id, source='iphone-pwa')
            emit('state', state='listening', device_id=device_id, source='iphone-pwa')
            raise HTTPException(409, 'turn_cancelled')
        except ModelError as exc:
            emit('voice.error', error=exc.code, device_id=device_id, source='iphone-pwa')
            emit('state', state='error', error=exc.code, device_id=device_id, source='iphone-pwa')
            raise HTTPException(exc.status_code, {'code': exc.code, 'message': exc.user_message})
        finally:
            state.finish(device_id, cancel_event)

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
        auth_device(pa_device, pa_token)
        if recorder is None:
            raise HTTPException(503, 'Voice qualification recorder unavailable')
        try:
            return recorder.stop_session()
        except RuntimeError as exc:
            if str(exc) != 'no active voice qualification session':
                raise
            return {'ok': True, 'status': 'already_stopped', 'message': 'Session already stopped'}

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
