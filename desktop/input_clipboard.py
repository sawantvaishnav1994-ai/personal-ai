from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, Any

from security.policy_targets import classify_clipboard


class ClipboardAdapter(Protocol):
    def read_text(self) -> tuple[str,int]: ...
    def write_text(self,text:str) -> int: ...
    def clear(self) -> int: ...


class UnsupportedClipboardAdapter:
    def _unsupported(self,*args,**kwargs): raise RuntimeError('unsupported_platform')
    read_text=_unsupported; write_text=_unsupported; clear=_unsupported


class MemoryClipboardAdapter:
    def __init__(self,text=''): self._text=str(text); self._seq=1
    def read_text(self): return self._text,self._seq
    def write_text(self,text): self._text=str(text); self._seq+=1; return self._seq
    def clear(self): self._text=''; self._seq+=1; return self._seq


@dataclass(frozen=True)
class ClipboardSnapshot:
    sequence: int
    sha256: str
    classification: str
    size: int
    secret: bool
    @classmethod
    def from_value(cls,text:str,sequence:int,max_bytes:int=64*1024):
        meta=classify_clipboard(text,max_bytes=max_bytes)
        return cls(int(sequence),meta['sha256'],meta['classification'],int(meta['size']),bool(meta['secret']))
    def safe_dict(self)->dict[str,Any]:
        return {'sequence':self.sequence,'sha256':self.sha256,'classification':self.classification,'size':self.size,'secret':self.secret}


SAFE_HOTKEYS={('ctrl','a'),('ctrl','c'),('ctrl','v'),('ctrl','x'),('ctrl','z'),('ctrl','y'),('ctrl','f'),('ctrl','s'),('ctrl','p'),('alt','left'),('alt','right'),('esc',),('enter',),('tab',),('shift','tab')}

def validate_hotkey(keys:list[str]|tuple[str,...])->tuple[str,...]:
    normalized=tuple(str(k).strip().lower() for k in keys if str(k).strip())
    if normalized not in SAFE_HOTKEYS: raise PermissionError('keyboard_shortcut_not_allowed')
    return normalized
