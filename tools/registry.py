from __future__ import annotations
from dataclasses import dataclass
from enum import IntEnum
from pathlib import Path
import sqlite3
from typing import Callable, Any
from core.permissions import PermissionDecision, PermissionEngine

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
        self.settings=settings;self.permissions=PermissionEngine(settings.autonomy_mode);self._tools={};self.emergency_stop=False;self._control_path=None
        data_dir=getattr(settings,'data_dir',None)
        if data_dir is not None:
            self._control_path=Path(data_dir)/'runtime-controls.sqlite3';self._control_path.parent.mkdir(parents=True,exist_ok=True)
            with self._control_con() as con:
                con.execute('CREATE TABLE IF NOT EXISTS runtime_controls (key TEXT PRIMARY KEY,value TEXT NOT NULL)')
                row=con.execute("SELECT value FROM runtime_controls WHERE key='emergency_stop'").fetchone()
                self.emergency_stop=bool(row and row[0]=='1')
    def _control_con(self):return sqlite3.connect(self._control_path)
    def set_emergency_stop(self,enabled:bool):
        self.emergency_stop=bool(enabled)
        if self._control_path is not None:
            with self._control_con() as con:con.execute("INSERT OR REPLACE INTO runtime_controls(key,value) VALUES('emergency_stop',?)",('1' if enabled else '0',))
        return self.emergency_stop
    def register(self,t:Tool):
        if t.name in self._tools:raise ValueError(f'Duplicate tool {t.name}')
        self._tools[t.name]=t
    def get(self,name):return self._tools[name]
    def all(self):return list(self._tools.values())
    def schema_text(self):return '\n'.join(f'- {t.name}: {t.description}; risk={t.risk.name}' for t in self._tools.values())
    def set_autonomy_mode(self,mode:str):
        mode=str(mode).lower().strip()
        if mode not in {'observe','suggest','ask','act'}:raise ValueError('invalid autonomy mode')
        self.permissions.mode=mode;return mode
    @property
    def autonomy_mode(self):return self.permissions.mode
    def automatic(self,t:Tool):return self.authorize(t,confirmed=False).allowed
    def authorize(self,t:Tool,confirmed:bool=False):
        if self.emergency_stop:return PermissionDecision(False,False,'owner emergency stop is active')
        return self.permissions.decide(int(t.risk),confirmed=confirmed)
