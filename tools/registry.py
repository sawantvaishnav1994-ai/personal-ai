from __future__ import annotations
from dataclasses import dataclass
from enum import IntEnum
from typing import Callable, Any

class Risk(IntEnum):
    READ_ONLY=0
    REVERSIBLE=1
    EXTERNAL_SIDE_EFFECT=2
    DESTRUCTIVE=3
    CRITICAL=4

@dataclass
class Tool:
    name:str
    description:str
    handler:Callable[[dict[str,Any]],Any]
    risk:Risk=Risk.READ_ONLY

class ToolRegistry:
    def __init__(self,settings):
        self.settings=settings; self._tools={}

    def register(self,t:Tool):
        if t.name in self._tools: raise ValueError(f"Duplicate tool {t.name}")
        self._tools[t.name]=t

    def get(self,name): return self._tools[name]
    def all(self): return list(self._tools.values())
    def schema_text(self):
        return "\n".join(f"- {t.name}: {t.description}; risk={t.risk.name}" for t in self._tools.values())

    def automatic(self,t:Tool):
        mode=self.settings.autonomy_mode
        if mode in {"observe","suggest"}: return False
        if mode=="ask": return t.risk==Risk.READ_ONLY
        if mode=="act": return t.risk<=Risk.REVERSIBLE
        return False
