from types import SimpleNamespace
import pytest

from core.permissions import ActionRisk
from tools import desktop_file
from tools.registry import ToolRegistry


def registry(tmp_path):
    settings=SimpleNamespace(data_dir=tmp_path,autonomy_mode='ask')
    reg=ToolRegistry(settings)
    desktop_file.register(reg,settings)
    return reg


def test_w75_tools_register_with_strict_risks(tmp_path):
    reg=registry(tmp_path)
    read=reg.get('desktop_file_read');act=reg.get('desktop_file_act')
    assert read.risk==ActionRisk.READ_ONLY and read.requires_trusted_context
    assert act.risk==ActionRisk.EXTERNAL_SIDE_EFFECT and act.requires_reauth and act.requires_trusted_context


def test_side_effect_handler_cannot_run_without_trusted_context(tmp_path):
    reg=registry(tmp_path)
    with pytest.raises(PermissionError,match='trusted_context_required'):
        reg.get('desktop_file_act').handler({'kind':'mkdir','transaction_id':'x','path':str(tmp_path/'x'),'roots':[str(tmp_path)]})


def test_read_tool_rejects_side_effect_kind_with_injected_context(tmp_path):
    reg=registry(tmp_path);tool=reg.get('desktop_file_read')
    params={'kind':'mkdir','transaction_id':'x','path':str(tmp_path/'x'),'roots':[str(tmp_path)],'_trusted_context':{'owner_id':'owner','device_id':'device','session_id':'session','security_epoch':0}}
    with pytest.raises(PermissionError,match='side_effect_requires_approved_tool'):
        tool.handler(params)
