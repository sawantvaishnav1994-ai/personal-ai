from types import SimpleNamespace
from tools.registry import ToolRegistry,Tool,Risk

def test_ask_mode():
    r=ToolRegistry(SimpleNamespace(autonomy_mode="ask")); assert r.automatic(Tool("r","",lambda p:None,Risk.READ_ONLY)); assert not r.automatic(Tool("w","",lambda p:None,Risk.REVERSIBLE))

def test_emergency_stop_persists_and_blocks_all_tools(tmp_path):
    settings=SimpleNamespace(autonomy_mode='act',data_dir=tmp_path);tool=Tool('read','',lambda p:True,Risk.READ_ONLY)
    first=ToolRegistry(settings);assert first.authorize(tool).allowed
    first.set_emergency_stop(True);assert not first.authorize(tool,confirmed=True).allowed
    restarted=ToolRegistry(settings);assert restarted.emergency_stop is True
    restarted.set_emergency_stop(False);assert ToolRegistry(settings).authorize(tool).allowed
