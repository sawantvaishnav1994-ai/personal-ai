from __future__ import annotations

from types import SimpleNamespace

import pytest

from agent.durable_executor import DurableAgentExecutor
from agent.executor import AgentExecutor, ConfirmationRequired
from core.events import EventBus
from memory.store import MemoryStore
from tools.registry import Risk, Tool, ToolRegistry


class Models:
    def chat(self, *args, **kwargs):
        return 'completed'


class Planner:
    def __init__(self):
        self.calls = 0

    def plan(self, *args, **kwargs):
        self.calls += 1
        return {
            'steps': [
                {
                    'tool': 'dangerous',
                    'parameters': {'destination': 'example.com', 'value': 7},
                    'description': 'perform exact external action',
                }
            ]
        }


def build_executor(tmp_path, calls, executor_cls=AgentExecutor):
    settings = SimpleNamespace(autonomy_mode='ask', data_dir=tmp_path)
    tools = ToolRegistry(settings)
    tools.register(Tool(
        'dangerous',
        'external action',
        lambda params: calls.append(dict(params)) or {'verified': True},
        Risk.EXTERNAL_SIDE_EFFECT,
    ))
    executor = executor_cls(
        models=Models(),
        tools=tools,
        memory=MemoryStore(tmp_path / 'assistant.sqlite3'),
        events=EventBus(),
    )
    executor.planner = Planner()
    return executor


def test_pending_approval_resumes_after_executor_restart_without_replanning(tmp_path):
    calls = []
    first = build_executor(tmp_path, calls)

    with pytest.raises(ConfirmationRequired) as proposed:
        first.chat(
            'perform it',
            device_id='device-1',
            session_id='session-1',
            owner_id='owner',
        )

    approval_id = proposed.value.approval_id
    assert calls == []
    assert first.planner.calls == 1

    restarted = build_executor(tmp_path, calls)
    assert restarted.planner.calls == 0
    context = restarted.approval_context(approval_id)
    assert context['device_id'] == 'device-1'
    assert context['session_id'] == 'session-1'

    reply = restarted.approve(
        approval_id,
        device_id='device-1',
        session_id='session-1',
        owner_id='owner',
    )

    assert reply == 'completed'
    assert calls == [{'destination': 'example.com', 'value': 7}]
    assert restarted.planner.calls == 0
    with pytest.raises(PermissionError):
        restarted.approve(
            approval_id,
            device_id='device-1',
            session_id='session-1',
        )


def test_restarted_executor_rejects_wrong_device_or_session(tmp_path):
    calls = []
    first = build_executor(tmp_path, calls)
    with pytest.raises(ConfirmationRequired) as proposed:
        first.chat('perform it', device_id='device-1', session_id='session-1')
    approval_id = proposed.value.approval_id

    restarted = build_executor(tmp_path, calls)
    with pytest.raises(PermissionError, match='device'):
        restarted.approve(approval_id, device_id='device-2', session_id='session-1')
    with pytest.raises(PermissionError, match='session'):
        restarted.approve(approval_id, device_id='device-1', session_id='session-2')

    assert calls == []
    assert restarted.approval_context(approval_id) is not None


def test_security_epoch_invalidation_prevents_stale_execution(tmp_path):
    calls = []
    first = build_executor(tmp_path, calls)
    with pytest.raises(ConfirmationRequired) as proposed:
        first.chat('perform it', device_id='device-1', session_id='session-1')
    approval_id = proposed.value.approval_id

    restarted = build_executor(tmp_path, calls)
    assert restarted.invalidate_pending_approvals() == 1
    with pytest.raises(PermissionError):
        restarted.approve(approval_id, device_id='device-1', session_id='session-1')
    assert calls == []


def test_emergency_stop_invalidates_approval_even_after_stop_is_cleared(tmp_path):
    calls = []
    executor = build_executor(tmp_path, calls)
    with pytest.raises(ConfirmationRequired) as proposed:
        executor.chat('perform it', device_id='device-1', session_id='session-1')
    approval_id = proposed.value.approval_id
    epoch_before = executor.approvals.current_security_epoch()

    executor.tools.set_emergency_stop(True)
    assert executor.approvals.current_security_epoch() == epoch_before + 1
    assert executor.approval_context(approval_id) is None

    executor.tools.set_emergency_stop(False)
    with pytest.raises(PermissionError):
        executor.approve(approval_id, device_id='device-1', session_id='session-1')
    assert calls == []


def test_stage8_post_dispatch_security_audit_failure_requires_recovery(tmp_path):
    calls = []
    executor = build_executor(tmp_path, calls, executor_cls=DurableAgentExecutor)

    with pytest.raises(ConfirmationRequired) as proposed:
        executor.chat('perform it', device_id='device-1', session_id='session-1')
    approval_id = proposed.value.approval_id

    original_append = executor.action_audit.append

    def fail_tool_execution_audit(category, action, payload=None):
        if category == 'tool' and action == 'execute':
            raise OSError('isolated audit storage failure')
        return original_append(category, action, payload)

    executor.action_audit.append = fail_tool_execution_audit

    with pytest.raises(OSError, match='audit storage failure'):
        executor.approve(
            approval_id,
            device_id='device-1',
            session_id='session-1',
            owner_id='owner',
        )

    assert calls == [{'destination': 'example.com', 'value': 7}]
    record = executor.approvals.record(approval_id)
    assert record['status'] == 'recovery_required'
    assert record['failure_code'] == 'OSError_after_dispatch'
