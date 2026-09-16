from __future__ import annotations

import sqlite3
import time
import uuid
from pathlib import Path
from threading import RLock

from agent.executor import ConfirmationRequired, ExecutionCancelled, ReauthenticationRequired
from core.turn_context import current_turn_context, new_turn_context, reset_turn_context, set_turn_context
from desktop.operator_context import OperatorRequestContext, reset_operator_request, set_operator_request


class TurnReplayBlocked(RuntimeError):
    """A request ID already exists in a state that must not be blindly replayed."""


class CanonicalTurnRuntime:
    """One conversation/turn orchestration path for Personal AI V1.

    This layer owns no intelligence or action authority. It binds one owner turn to
    the canonical Continuity ledger, bounded working history, request-scoped context
    and the existing AgentExecutor. P6/W7/security/model/Memory/Knowledge/P10 remain
    authoritative in their existing components.
    """

    HISTORY_LIMIT = 16
    CANONICAL_OWNER = 'owner'

    def __init__(self, executor, continuity, path: Path, *, events=None):
        self._executor = executor
        self.continuity = continuity
        self.events = events
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.lock = RLock()
        with self._con() as con:
            con.executescript(
                '''
                CREATE TABLE IF NOT EXISTS canonical_turns(
                    request_id TEXT PRIMARY KEY,
                    owner_id TEXT NOT NULL,
                    conversation_id TEXT,
                    device_id TEXT,
                    session_id TEXT,
                    surface TEXT NOT NULL,
                    input_modality TEXT NOT NULL,
                    privacy_level TEXT NOT NULL,
                    risk_level TEXT NOT NULL,
                    user_text TEXT NOT NULL,
                    status TEXT NOT NULL,
                    assistant_text TEXT,
                    approval_id TEXT,
                    error_code TEXT,
                    created_at REAL NOT NULL,
                    updated_at REAL NOT NULL
                );
                CREATE UNIQUE INDEX IF NOT EXISTS idx_canonical_turn_approval
                    ON canonical_turns(approval_id) WHERE approval_id IS NOT NULL;
                CREATE INDEX IF NOT EXISTS idx_canonical_turn_conversation
                    ON canonical_turns(conversation_id,created_at);
                '''
            )

    def _con(self):
        con = sqlite3.connect(self.path, timeout=30)
        con.row_factory = sqlite3.Row
        return con

    def __getattr__(self, name):
        return getattr(self._executor, name)

    def _emit(self, event: str, **payload):
        if self.events:
            self.events.emit(event, **payload)

    @staticmethod
    def _clean_text(text) -> str:
        value = str(text or '').strip()
        if not value:
            raise ValueError('turn text is required')
        return value

    def _security_epoch(self) -> int:
        approvals = getattr(self._executor, 'approvals', None)
        provider = getattr(approvals, 'current_security_epoch', None)
        try:
            return int(provider()) if callable(provider) else 0
        except Exception:
            return 0

    @classmethod
    def _owner(cls, owner_id) -> str:
        owner = str(owner_id or cls.CANONICAL_OWNER)
        if owner != cls.CANONICAL_OWNER:
            raise PermissionError('Personal AI V1 is single-owner; alternate owner identity is forbidden')
        return owner

    def _existing(self, request_id: str):
        with self._con() as con:
            row = con.execute('SELECT * FROM canonical_turns WHERE request_id=?', (request_id,)).fetchone()
        return dict(row) if row else None

    def _turn_by_approval(self, approval_id: str):
        with self._con() as con:
            row = con.execute('SELECT * FROM canonical_turns WHERE approval_id=?', (approval_id,)).fetchone()
        return dict(row) if row else None

    def _resolve_conversation(self, *, device_id: str | None, conversation_id: str | None, surface: str):
        if self.continuity is None:
            return str(conversation_id or '')
        if conversation_id:
            thread = self.continuity.thread(str(conversation_id))
            if not thread or thread.get('closed_at'):
                raise KeyError('active conversation is unavailable')
            if device_id:
                self.continuity.set_active(device_id, thread['id'])
            return str(thread['id'])
        continuity_device = str(device_id or f'local:{surface or "runtime"}')
        bundle = self.continuity.resume(continuity_device, event_limit=self.HISTORY_LIMIT * 2)
        thread = bundle.get('thread') or {}
        resolved = str(thread.get('id') or '')
        if not resolved:
            raise RuntimeError('continuity failed to establish a conversation')
        return resolved

    def _history(self, conversation_id: str, explicit_history):
        if explicit_history is not None:
            return [
                {'role': str(item.get('role')), 'content': str(item.get('content'))}
                for item in list(explicit_history)[-self.HISTORY_LIMIT:]
                if isinstance(item, dict)
                and item.get('role') in {'user', 'assistant'}
                and str(item.get('content') or '').strip()
            ]
        if self.continuity is None or not conversation_id:
            return None
        return self.continuity.conversation_history(conversation_id, limit=self.HISTORY_LIMIT)

    def _append(self, conversation_id: str, *, device_id, kind: str, text: str, event_id: str):
        if self.continuity is None or not conversation_id:
            return None
        return self.continuity.append(
            conversation_id,
            device_id=device_id,
            kind=kind,
            payload={'text': str(text)},
            event_id=event_id,
        )

    def _insert_started(self, *, request_id, owner_id, conversation_id, device_id, session_id,
                        surface, input_modality, privacy_level, risk_level, user_text):
        stamp = time.time()
        with self.lock, self._con() as con:
            con.execute(
                '''INSERT INTO canonical_turns(
                    request_id,owner_id,conversation_id,device_id,session_id,surface,input_modality,
                    privacy_level,risk_level,user_text,status,assistant_text,approval_id,error_code,
                    created_at,updated_at
                ) VALUES(?,?,?,?,?,?,?,?,?,?, 'started',NULL,NULL,NULL,?,?)''',
                (
                    request_id, owner_id, conversation_id or None, device_id, session_id, surface,
                    input_modality, privacy_level, risk_level, user_text, stamp, stamp,
                ),
            )

    def _update(self, request_id: str, status: str, *, assistant_text=None, approval_id=None, error_code=None):
        with self.lock, self._con() as con:
            con.execute(
                '''UPDATE canonical_turns SET status=?,assistant_text=?,approval_id=?,error_code=?,updated_at=?
                   WHERE request_id=?''',
                (status, assistant_text, approval_id, error_code, time.time(), request_id),
            )

    def _validate_replay(self, existing: dict, *, text: str, owner_id: str, device_id: str | None):
        if existing['owner_id'] != owner_id or existing['user_text'] != text:
            raise PermissionError('request_id is already bound to different turn content or authority')
        if (existing.get('device_id') or None) != (device_id or None):
            raise PermissionError('request_id is already bound to a different device')
        if existing['status'] == 'completed':
            answer = str(existing.get('assistant_text') or '')
            self._append(
                str(existing.get('conversation_id') or ''),
                device_id=existing.get('device_id'),
                kind='assistant_message',
                text=answer,
                event_id=f"{existing['request_id']}:assistant",
            )
            self._emit('turn.replayed', request_id=existing['request_id'], status='completed')
            return answer
        raise TurnReplayBlocked(
            f"request {existing['request_id']} is {existing['status']}; use approval/recovery or a new owner turn instead of replaying it"
        )

    def _bind_context(self, *, request_id, conversation_id, owner_id, device_id, session_id,
                      surface, input_modality, privacy_level, risk_level, refs):
        existing_context = current_turn_context()
        if existing_context is not None and existing_context.request_id == request_id:
            return None, None
        turn = new_turn_context(
            request_id=request_id,
            conversation_id=conversation_id,
            owner_id=owner_id,
            device_id=device_id or '',
            session_id=session_id or '',
            security_epoch=self._security_epoch(),
            surface=surface,
            input_modality=input_modality,
            privacy_level=privacy_level,
            risk_level=risk_level,
            memory_refs=refs.get('memory_refs') or (),
            knowledge_refs=refs.get('knowledge_refs') or (),
            p7_observation_refs=refs.get('p7_observation_refs') or (),
            p8_continuity_refs=(conversation_id,) if conversation_id else (),
            model_routing_refs=refs.get('model_routing_refs') or (),
            p10_goal_refs=refs.get('p10_goal_refs') or (),
            tool_refs=refs.get('tool_refs') or (),
            approval_refs=refs.get('approval_refs') or (),
            verification_refs=refs.get('verification_refs') or (),
            recovery_refs=refs.get('recovery_refs') or (),
        )
        turn_token = set_turn_context(turn)
        operator_token = set_operator_request(OperatorRequestContext(
            owner_id=owner_id,
            device_id=str(device_id or ''),
            session_id=str(session_id or ''),
            security_epoch=self._security_epoch(),
            conversation_id=conversation_id,
            workflow_id=str(refs.get('workflow_id') or ''),
            reauthenticated_at=refs.get('reauthenticated_at'),
        ))
        return turn_token, operator_token

    @staticmethod
    def _reset_context(tokens):
        turn_token, operator_token = tokens
        if operator_token is not None:
            reset_operator_request(operator_token)
        if turn_token is not None:
            reset_turn_context(turn_token)

    def chat(self, text, **kwargs):
        user_text = self._clean_text(text)
        owner_id = self._owner(kwargs.pop('owner_id', self.CANONICAL_OWNER))
        request_id = str(kwargs.pop('request_id', None) or uuid.uuid4())
        device_id = kwargs.get('device_id')
        session_id = kwargs.get('session_id')
        surface = str(kwargs.pop('surface', None) or ('desktop' if not device_id else 'device'))
        input_modality = str(kwargs.pop('input_modality', None) or 'text')
        privacy_level = str(kwargs.pop('privacy_level', None) or 'normal')
        risk_level = str(kwargs.pop('risk_level', None) or 'low')
        refs = {
            key: kwargs.pop(key, ())
            for key in (
                'memory_refs', 'knowledge_refs', 'p7_observation_refs', 'model_routing_refs',
                'p10_goal_refs', 'tool_refs', 'approval_refs', 'verification_refs', 'recovery_refs',
            )
        }
        refs['workflow_id'] = kwargs.pop('workflow_id', '')
        refs['reauthenticated_at'] = kwargs.get('reauthenticated_at')

        existing = self._existing(request_id)
        if existing is not None:
            return self._validate_replay(existing, text=user_text, owner_id=owner_id, device_id=device_id)

        conversation_id = self._resolve_conversation(
            device_id=device_id,
            conversation_id=kwargs.get('conversation_id'),
            surface=surface,
        )
        history = self._history(conversation_id, kwargs.pop('conversation_history', None))
        kwargs['conversation_id'] = conversation_id or None
        if history is not None:
            kwargs['conversation_history'] = history
        kwargs['owner_id'] = owner_id

        self._append(
            conversation_id,
            device_id=device_id,
            kind='user_message',
            text=user_text,
            event_id=f'{request_id}:user',
        )
        self._insert_started(
            request_id=request_id,
            owner_id=owner_id,
            conversation_id=conversation_id,
            device_id=device_id,
            session_id=session_id,
            surface=surface,
            input_modality=input_modality,
            privacy_level=privacy_level,
            risk_level=risk_level,
            user_text=user_text,
        )
        self._emit(
            'turn.started', request_id=request_id, conversation_id=conversation_id,
            device_id=device_id, surface=surface, input_modality=input_modality,
        )

        tokens = self._bind_context(
            request_id=request_id,
            conversation_id=conversation_id,
            owner_id=owner_id,
            device_id=device_id,
            session_id=session_id,
            surface=surface,
            input_modality=input_modality,
            privacy_level=privacy_level,
            risk_level=risk_level,
            refs=refs,
        )
        try:
            answer = self._executor.chat(user_text, **kwargs)
        except ConfirmationRequired as exc:
            self._update(request_id, 'needs_approval', approval_id=exc.approval_id)
            self._emit(
                'turn.needs_approval', request_id=request_id, conversation_id=conversation_id,
                approval_id=exc.approval_id,
            )
            raise
        except ReauthenticationRequired as exc:
            self._update(request_id, 'needs_reauthentication', error_code='reauthentication_required')
            self._emit('turn.needs_reauthentication', request_id=request_id, conversation_id=conversation_id)
            raise
        except ExecutionCancelled:
            self._update(request_id, 'cancelled', error_code='cancelled')
            self._emit('turn.cancelled', request_id=request_id, conversation_id=conversation_id)
            raise
        except Exception as exc:
            self._update(request_id, 'failed', error_code=type(exc).__name__)
            self._emit(
                'turn.failed', request_id=request_id, conversation_id=conversation_id,
                error_type=type(exc).__name__,
            )
            raise
        finally:
            self._reset_context(tokens)

        answer = str(answer)
        self._update(request_id, 'completed', assistant_text=answer)
        self._append(
            conversation_id,
            device_id=device_id,
            kind='assistant_message',
            text=answer,
            event_id=f'{request_id}:assistant',
        )
        self._emit('turn.completed', request_id=request_id, conversation_id=conversation_id)
        return answer

    def _approval_call(self, approval_id: str, callback, **kwargs):
        owner_id = self._owner(kwargs.get('owner_id', self.CANONICAL_OWNER))
        turn = self._turn_by_approval(approval_id)
        if turn is None:
            return callback(**kwargs)
        if turn['owner_id'] != owner_id:
            raise PermissionError('approval is not bound to this owner')
        if kwargs.get('device_id') and kwargs['device_id'] != turn.get('device_id'):
            raise PermissionError('approval is not bound to this device')
        refs = {'approval_refs': (approval_id,), 'reauthenticated_at': kwargs.get('reauthenticated_at')}
        tokens = self._bind_context(
            request_id=turn['request_id'],
            conversation_id=str(turn.get('conversation_id') or ''),
            owner_id=owner_id,
            device_id=turn.get('device_id'),
            session_id=turn.get('session_id'),
            surface=str(turn.get('surface') or 'device'),
            input_modality='approval',
            privacy_level=str(turn.get('privacy_level') or 'normal'),
            risk_level=str(turn.get('risk_level') or 'low'),
            refs=refs,
        )
        try:
            reply = callback(**kwargs)
        except ConfirmationRequired as exc:
            self._update(turn['request_id'], 'needs_approval', approval_id=exc.approval_id)
            raise
        except ReauthenticationRequired:
            self._update(turn['request_id'], 'needs_reauthentication', error_code='reauthentication_required')
            raise
        except Exception as exc:
            self._update(turn['request_id'], 'failed', error_code=type(exc).__name__)
            raise
        finally:
            self._reset_context(tokens)
        answer = str(reply)
        self._update(turn['request_id'], 'completed', assistant_text=answer)
        self._append(
            str(turn.get('conversation_id') or ''),
            device_id=turn.get('device_id'),
            kind='assistant_message',
            text=answer,
            event_id=f"{turn['request_id']}:assistant",
        )
        self._emit(
            'turn.completed', request_id=turn['request_id'],
            conversation_id=turn.get('conversation_id'), approval_id=approval_id,
        )
        return reply

    def approve(self, approval_id: str, **kwargs):
        kwargs['owner_id'] = self._owner(kwargs.get('owner_id', self.CANONICAL_OWNER))
        return self._approval_call(approval_id, lambda **call_kwargs: self._executor.approve(approval_id, **call_kwargs), **kwargs)

    def reject(self, approval_id: str, **kwargs):
        turn = self._turn_by_approval(approval_id)
        reply = self._executor.reject(approval_id, **kwargs)
        if turn is not None:
            answer = str(reply)
            self._update(turn['request_id'], 'rejected', assistant_text=answer)
            self._append(
                str(turn.get('conversation_id') or ''),
                device_id=turn.get('device_id'),
                kind='assistant_message',
                text=answer,
                event_id=f"{turn['request_id']}:assistant",
            )
            self._emit('turn.rejected', request_id=turn['request_id'], approval_id=approval_id)
        return reply

    def turn(self, request_id: str):
        row = self._existing(str(request_id))
        if row is None:
            return None
        return {key: value for key, value in row.items() if key not in {'user_text', 'assistant_text'}}

    def recent_turns(self, *, conversation_id: str | None = None, limit: int = 100):
        bounded = max(1, min(int(limit), 500))
        with self._con() as con:
            if conversation_id:
                rows = con.execute(
                    '''SELECT request_id,owner_id,conversation_id,device_id,surface,input_modality,status,
                       approval_id,error_code,created_at,updated_at FROM canonical_turns
                       WHERE conversation_id=? ORDER BY created_at DESC LIMIT ?''',
                    (conversation_id, bounded),
                ).fetchall()
            else:
                rows = con.execute(
                    '''SELECT request_id,owner_id,conversation_id,device_id,surface,input_modality,status,
                       approval_id,error_code,created_at,updated_at FROM canonical_turns
                       ORDER BY created_at DESC LIMIT ?''',
                    (bounded,),
                ).fetchall()
        return [dict(row) for row in rows]
