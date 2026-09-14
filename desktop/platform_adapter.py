from __future__ import annotations

from dataclasses import dataclass
import hashlib
from pathlib import Path
import platform
import subprocess
from typing import Any, Protocol

from security.policy_targets import TargetValidationError, application_identity


@dataclass(frozen=True)
class WindowIdentity:
    process_id: int
    executable: str
    executable_sha256: str
    window_id: str
    title_digest: str
    foreground: bool
    visible: bool = True
    enabled: bool = True

    def safe_dict(self) -> dict[str, Any]:
        return {
            'process_id': int(self.process_id),
            'executable': Path(self.executable).name if self.executable else '',
            'executable_sha256': self.executable_sha256,
            'window_id': self.window_id,
            'title_digest': self.title_digest,
            'foreground': bool(self.foreground),
            'visible': bool(self.visible),
            'enabled': bool(self.enabled),
        }


class DesktopPlatformAdapter(Protocol):
    platform_name: str
    def application_identity(self, executable: str) -> dict[str, Any]: ...
    def launch(self, executable: str, args: list[str]) -> dict[str, Any]: ...
    def foreground_window(self) -> WindowIdentity | None: ...
    def focus_window(self, window_id: str) -> bool: ...
    def window_action(self, window_id: str, action: str, *, x: int | None = None, y: int | None = None, width: int | None = None, height: int | None = None) -> bool: ...
    def input_click(self, x: int, y: int, *, button: str = 'left') -> None: ...
    def input_type(self, text: str) -> None: ...
    def input_hotkey(self, keys: tuple[str, ...]) -> None: ...
    def input_scroll(self, amount: int) -> None: ...
    def release_input(self) -> None: ...
    def read_visible_text(self, window_id: str, *, max_chars: int = 12000) -> str: ...


class UnsupportedDesktopAdapter:
    platform_name = 'unsupported'
    def _unsupported(self, *args, **kwargs):
        raise RuntimeError('unsupported_platform')
    application_identity = _unsupported
    launch = _unsupported
    foreground_window = _unsupported
    focus_window = _unsupported
    window_action = _unsupported
    input_click = _unsupported
    input_type = _unsupported
    input_hotkey = _unsupported
    input_scroll = _unsupported
    release_input = _unsupported
    read_visible_text = _unsupported


class WindowsDesktopAdapter:
    """Minimal Win32 adapter. It never invokes a shell and never resolves executable names via PATH."""
    platform_name = 'windows'
    _WINDOW_ACTIONS = {'minimize','maximize','restore','close','move_resize'}

    def application_identity(self, executable: str) -> dict[str, Any]:
        raw = str(executable or '').strip()
        if not raw or not Path(raw).is_absolute():
            raise TargetValidationError('application_not_allowed', 'Executable must be an absolute canonical path.')
        return application_identity(raw)

    def launch(self, executable: str, args: list[str]) -> dict[str, Any]:
        identity = self.application_identity(executable)
        safe_args = self._validate_args(args)
        proc = subprocess.Popen([identity['canonical_path'], *safe_args], shell=False, close_fds=True)
        return {'process_id': int(proc.pid), 'application': identity}

    @staticmethod
    def _validate_args(args: list[str]) -> list[str]:
        if not isinstance(args, list): raise ValueError('application arguments must be a list')
        if len(args) > 32: raise ValueError('too many application arguments')
        out=[]
        for value in args:
            text=str(value)
            if len(text)>2048 or '\x00' in text or '\r' in text or '\n' in text:
                raise ValueError('invalid application argument')
            out.append(text)
        return out

    @staticmethod
    def _hwnd(value: str) -> int:
        text=str(value or '')
        if not text.startswith('hwnd:'): raise ValueError('invalid window identity')
        return int(text.split(':',1)[1],16)

    def foreground_window(self) -> WindowIdentity | None:
        try:
            import ctypes
            from ctypes import wintypes
            user32=ctypes.windll.user32; kernel32=ctypes.windll.kernel32
            hwnd=user32.GetForegroundWindow()
            if not hwnd: return None
            pid=wintypes.DWORD(); user32.GetWindowThreadProcessId(hwnd,ctypes.byref(pid))
            if not pid.value: return None
            PROCESS_QUERY_LIMITED_INFORMATION=0x1000
            handle=kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION,False,pid.value)
            if not handle: return None
            executable=''
            try:
                size=wintypes.DWORD(32768); buf=ctypes.create_unicode_buffer(size.value)
                if kernel32.QueryFullProcessImageNameW(handle,0,buf,ctypes.byref(size)): executable=buf.value
            finally: kernel32.CloseHandle(handle)
            if not executable: return None
            identity=application_identity(executable)
            length=user32.GetWindowTextLengthW(hwnd); title=ctypes.create_unicode_buffer(max(1,length+1)); user32.GetWindowTextW(hwnd,title,len(title))
            return WindowIdentity(int(pid.value),identity['canonical_path'],identity['sha256'],f'hwnd:{int(hwnd):x}',hashlib.sha256(title.value.encode()).hexdigest(),True,bool(user32.IsWindowVisible(hwnd)),bool(user32.IsWindowEnabled(hwnd)))
        except Exception:
            return None

    def focus_window(self, window_id: str) -> bool:
        import ctypes
        hwnd=self._hwnd(window_id)
        return bool(ctypes.windll.user32.SetForegroundWindow(hwnd))

    def window_action(self, window_id: str, action: str, *, x=None, y=None, width=None, height=None) -> bool:
        if action not in self._WINDOW_ACTIONS: raise ValueError('window action not allowed')
        import ctypes
        user32=ctypes.windll.user32; hwnd=self._hwnd(window_id)
        if action=='close': return bool(user32.PostMessageW(hwnd,0x0010,0,0))
        if action=='move_resize':
            if None in (x,y,width,height) or int(width)<=0 or int(height)<=0: raise ValueError('invalid window geometry')
            return bool(user32.MoveWindow(hwnd,int(x),int(y),int(width),int(height),True))
        cmd={'minimize':6,'maximize':3,'restore':9}[action]
        return bool(user32.ShowWindow(hwnd,cmd))

    @staticmethod
    def _pg():
        import pyautogui
        pyautogui.FAILSAFE=True
        return pyautogui

    def input_click(self,x:int,y:int,*,button='left')->None: self._pg().click(x=int(x),y=int(y),button=button)
    def input_type(self,text:str)->None: self._pg().write(str(text),interval=.01)
    def input_hotkey(self,keys:tuple[str,...])->None: self._pg().hotkey(*keys)
    def input_scroll(self,amount:int)->None: self._pg().scroll(int(amount))
    def release_input(self)->None:
        pg=self._pg()
        for key in ('ctrl','shift','alt','win'):
            try: pg.keyUp(key)
            except Exception: pass
        for button in ('left','middle','right'):
            try: pg.mouseUp(button=button)
            except Exception: pass

    def read_visible_text(self, window_id: str, *, max_chars: int = 12000) -> str:
        return ''


def default_desktop_adapter() -> DesktopPlatformAdapter:
    return WindowsDesktopAdapter() if platform.system().lower()=='windows' else UnsupportedDesktopAdapter()
