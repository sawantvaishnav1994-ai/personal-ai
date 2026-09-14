from tools.registry import Tool, Risk
from desktop.controller import DesktopController


def register(reg, settings):
    # Browser authority is owned exclusively by tools.browser / W7.4.
    # Do not re-register raw selector/goto/fill/snapshot methods here; doing so
    # would create a weaker parallel path around W7.2 observations + W7.3 policy.
    desktop = DesktopController()
    reg.register(Tool('desktop_position','Read mouse position',lambda p:desktop.position(),Risk.READ_ONLY))
    reg.register(Tool('desktop_move','Move pointer; params:x,y,duration',lambda p:desktop.move(p['x'],p['y'],p.get('duration',.2)),Risk.REVERSIBLE))
    reg.register(Tool('desktop_click','Click desktop; params:x,y,button',lambda p:desktop.click(p.get('x'),p.get('y'),p.get('button','left')),Risk.EXTERNAL_SIDE_EFFECT))
    reg.register(Tool('desktop_type','Type text; params:text',lambda p:desktop.type_text(p['text'],p.get('interval',.01)),Risk.EXTERNAL_SIDE_EFFECT))
    reg.register(Tool('desktop_hotkey','Press hotkey; params:keys',lambda p:desktop.hotkey(*p['keys']),Risk.EXTERNAL_SIDE_EFFECT))
