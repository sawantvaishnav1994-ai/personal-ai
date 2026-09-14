from __future__ import annotations

from dataclasses import dataclass, asdict
import os
import platform
from pathlib import Path
import time


@dataclass(frozen=True)
class ApplicationContext:
    captured_at: float
    platform: str
    available: bool
    application: str = ''
    executable: str = ''
    process_id: int | None = None
    window_title: str = ''
    source: str = 'unavailable'

    def safe_dict(self):
        data = asdict(self)
        # Executable is retained as basename only; never persist a user path here.
        data['executable'] = Path(self.executable).name if self.executable else ''
        return data


class ApplicationContextObserver:
    """On-demand foreground application/window identity.

    No thread, timer, hook or background polling is created. Unsupported
    platforms return an explicit unavailable result instead of guessing.
    """

    def capture(self) -> dict:
        if platform.system().lower() == 'windows':
            value = self._windows()
            if value is not None:
                return value.safe_dict()
        value = self._pygetwindow()
        if value is not None:
            return value.safe_dict()
        return ApplicationContext(
            captured_at=time.time(),
            platform=platform.system().lower() or 'unknown',
            available=False,
        ).safe_dict()

    def _windows(self):
        try:
            import ctypes
            from ctypes import wintypes

            user32 = ctypes.windll.user32
            kernel32 = ctypes.windll.kernel32
            hwnd = user32.GetForegroundWindow()
            if not hwnd:
                return None
            length = user32.GetWindowTextLengthW(hwnd)
            buf = ctypes.create_unicode_buffer(max(1, length + 1))
            user32.GetWindowTextW(hwnd, buf, len(buf))
            pid = wintypes.DWORD()
            user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
            executable = ''
            PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
            handle = kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, pid.value)
            if handle:
                try:
                    size = wintypes.DWORD(32768)
                    path = ctypes.create_unicode_buffer(size.value)
                    if kernel32.QueryFullProcessImageNameW(handle, 0, path, ctypes.byref(size)):
                        executable = path.value
                finally:
                    kernel32.CloseHandle(handle)
            app = Path(executable).stem if executable else ''
            return ApplicationContext(
                captured_at=time.time(), platform='windows', available=True,
                application=app, executable=executable, process_id=int(pid.value),
                window_title=buf.value[:1000], source='win32_foreground_window',
            )
        except Exception:
            return None

    def _pygetwindow(self):
        try:
            import pygetwindow
            window = pygetwindow.getActiveWindow()
            if window is None:
                return None
            title = str(getattr(window, 'title', '') or '')[:1000]
            if not title:
                return None
            return ApplicationContext(
                captured_at=time.time(), platform=platform.system().lower() or 'unknown',
                available=True, window_title=title, source='pygetwindow',
            )
        except Exception:
            return None
