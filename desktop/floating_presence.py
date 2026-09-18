from __future__ import annotations

import json
from pathlib import Path
from threading import RLock

from core.runtime_presentation import presentation_for
from core.runtime_state import RuntimeState


class PresenceController:
    """Sequence-aware projection controller for desktop Floating Presence."""

    def __init__(self, events, path: Path):
        self.events = events
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = RLock()
        snapshot = events.runtime_state.snapshot()
        self._state = snapshot.state
        self._sequence = snapshot.sequence
        self._position = self._load_position()
        self._unsubscribe = events.subscribe('runtime.state', self._on_runtime_state)

    @property
    def state(self) -> RuntimeState:
        with self._lock:
            return self._state

    @property
    def sequence(self) -> int:
        with self._lock:
            return self._sequence

    @property
    def position(self) -> tuple[int, int] | None:
        with self._lock:
            return self._position

    def _on_runtime_state(self, event):
        presentation = presentation_for(event.get('state'))
        try:
            sequence = int(event.get('sequence'))
        except (TypeError, ValueError):
            return
        if presentation is None:
            self.events.emit('presence.state.unknown_ignored', sequence=sequence)
            return
        with self._lock:
            if sequence <= self._sequence:
                return
            self._state = presentation.state
            self._sequence = sequence

    @staticmethod
    def clamp_position(x: int, y: int, *, left: int, top: int, right: int, bottom: int, width: int, height: int):
        max_x = max(left, right - max(1, width))
        max_y = max(top, bottom - max(1, height))
        return max(left, min(int(x), max_x)), max(top, min(int(y), max_y))

    def save_position(self, x: int, y: int):
        value = (int(x), int(y))
        temp = self.path.with_suffix(self.path.suffix + '.tmp')
        temp.write_text(json.dumps({'x': value[0], 'y': value[1]}), encoding='utf-8')
        temp.replace(self.path)
        with self._lock:
            self._position = value

    def _load_position(self):
        try:
            data = json.loads(self.path.read_text(encoding='utf-8'))
            return int(data['x']), int(data['y'])
        except (OSError, ValueError, TypeError, KeyError, json.JSONDecodeError):
            return None

    def close(self):
        self._unsubscribe()


try:
    from PyQt6.QtCore import QPoint, Qt
    from PyQt6.QtWidgets import QFrame, QHBoxLayout, QLabel, QLineEdit, QPushButton, QVBoxLayout, QWidget
    from ui.pulse import PulseWidget
except ImportError:  # package/static qualification can still import the controller
    QWidget = object


class FloatingPresence(QWidget):
    """Minimal always-on-top projection over the canonical Personal AI runtime."""

    CORE_SIZE = 118
    PANEL_WIDTH = 330

    def __init__(self, *, runtime, parent=None):
        if QWidget is object:
            raise RuntimeError('PyQt6 is required for Floating Presence')
        super().__init__(parent)
        self.runtime = runtime
        self.events = runtime['events']
        self.executor = runtime['executor']
        data_dir = Path(getattr(runtime.get('settings'), 'data_dir', Path.home() / '.personal-ai'))
        self.controller = PresenceController(self.events, data_dir / 'floating-presence.json')
        self._drag_offset = None
        self._expanded = False
        self._always_on_top = True
        self._rendered_sequence = -1
        self._active_request_id = None
        self._active_cancel_event = None
        self._submit_lock = RLock()
        self._build()
        self._unsubscribe = self.events.subscribe('runtime.state', self._render_state)
        self._render_snapshot()
        self._restore_position()

    def _build(self):
        self.setWindowTitle('Personal AI Floating Presence')
        self.setAccessibleName('Personal AI Floating Presence')
        self._apply_window_flags()
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.resize(self.CORE_SIZE, self.CORE_SIZE)
        self.shell = QFrame(self)
        self.shell.setObjectName('presenceShell')
        self.shell.setStyleSheet('QFrame#presenceShell{background:rgba(3,4,5,224);border:1px solid rgba(85,125,140,95);border-radius:22px;}QLineEdit{background:#070a0d;border:1px solid #17252d;border-radius:12px;padding:8px;color:#edf3f6;}QPushButton{background:#090d10;border:1px solid #17252d;border-radius:10px;padding:7px;color:#aab9c0;}QLabel{color:#dbe6ea;}')
        outer = QVBoxLayout(self); outer.setContentsMargins(0, 0, 0, 0); outer.addWidget(self.shell)
        layout = QVBoxLayout(self.shell); layout.setContentsMargins(8, 8, 8, 8); layout.setSpacing(6)
        self.core = PulseWidget(); self.core.setAccessibleName('Personal AI core state'); self.core.setFixedSize(self.CORE_SIZE - 16, self.CORE_SIZE - 16)
        self.core.mouseDoubleClickEvent = lambda event: self.toggle_panel(); layout.addWidget(self.core, alignment=Qt.AlignmentFlag.AlignCenter)
        self.panel = QWidget(); panel = QVBoxLayout(self.panel); panel.setContentsMargins(2, 2, 2, 2)
        self.status = QLabel('Connecting'); self.status.setAccessibleName('Current Personal AI state'); panel.addWidget(self.status)
        self.input = QLineEdit(); self.input.setAccessibleName('Quick message to Personal AI'); self.input.setPlaceholderText('Speak or type…'); self.input.returnPressed.connect(self.submit); panel.addWidget(self.input)
        actions = QHBoxLayout()
        self.voice = QPushButton('Voice'); self.voice.setAccessibleName('Toggle voice'); self.voice.clicked.connect(self.toggle_voice); actions.addWidget(self.voice)
        self.cancel = QPushButton('Cancel'); self.cancel.setAccessibleName('Cancel current work'); self.cancel.clicked.connect(self.cancel_work); actions.addWidget(self.cancel)
        self.pin = QPushButton('Unpin'); self.pin.setAccessibleName('Toggle always on top'); self.pin.clicked.connect(self.toggle_always_on_top); actions.addWidget(self.pin)
        self.collapse = QPushButton('Collapse'); self.collapse.clicked.connect(self.toggle_panel); actions.addWidget(self.collapse)
        panel.addLayout(actions); self.panel.setVisible(False); layout.addWidget(self.panel)

    def _render_snapshot(self):
        snapshot = self.events.runtime_state.snapshot()
        self._apply_projection(snapshot.state.value, snapshot.sequence)

    def _render_state(self, event):
        self._apply_projection(event.get('state'), event.get('sequence'))

    def _apply_projection(self, state_value, sequence):
        presentation = presentation_for(state_value)
        try:
            sequence = int(sequence)
        except (TypeError, ValueError):
            return
        if presentation is None or sequence <= self._rendered_sequence:
            return
        self._rendered_sequence = sequence
        self.core.set_state(presentation.visual)
        self.core.setAccessibleDescription(presentation.label)
        self.status.setText(presentation.label)

    def _apply_window_flags(self):
        flags = Qt.WindowType.FramelessWindowHint | Qt.WindowType.Tool
        if self._always_on_top:
            flags |= Qt.WindowType.WindowStaysOnTopHint
        self.setWindowFlags(flags)

    def toggle_always_on_top(self):
        self._always_on_top = not self._always_on_top
        position = self.pos()
        self._apply_window_flags()
        self.move(position)
        self.show()
        self.pin.setText('Unpin' if self._always_on_top else 'Pin')

    def toggle_panel(self):
        self._expanded = not self._expanded
        self.panel.setVisible(self._expanded)
        self.resize(self.PANEL_WIDTH if self._expanded else self.CORE_SIZE, 230 if self._expanded else self.CORE_SIZE)
        self._clamp_to_screen()
        if self._expanded:
            self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
            self.input.setFocus(Qt.FocusReason.ShortcutFocusReason)
        else:
            self.setFocusPolicy(Qt.FocusPolicy.NoFocus)

    def submit(self):
        text = self.input.text().strip()
        if not text:
            return
        self.input.clear()
        import threading
        import uuid
        request_id = 'floating-' + str(uuid.uuid4())
        cancel_event = threading.Event()
        with self._submit_lock:
            self._active_request_id = request_id
            self._active_cancel_event = cancel_event

        def run():
            try:
                self.executor.chat(text, request_id=request_id, surface='floating-presence', device_id='desktop', cancel_event=cancel_event)
            finally:
                with self._submit_lock:
                    if self._active_request_id == request_id:
                        self._active_request_id = None
                        self._active_cancel_event = None

        threading.Thread(target=run, daemon=True).start()
    def toggle_voice(self):
        voice = self.runtime.get('voice')
        if not voice: return
        voice.stop() if getattr(voice, 'running', False) else voice.start()

    def cancel_work(self):
        voice = self.runtime.get('voice')
        if voice and hasattr(voice, 'barge_in'):
            voice.barge_in()
        with self._submit_lock:
            request_id = self._active_request_id
            cancel_event = self._active_cancel_event
        if cancel_event is not None:
            cancel_event.set()
        if request_id and hasattr(self.executor, 'cancel_turn'):
            try:
                self.executor.cancel_turn(request_id, device_id='desktop')
            except (KeyError, PermissionError):
                return
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and not self._expanded:
            self._drag_offset = event.globalPosition().toPoint() - self.frameGeometry().topLeft(); event.accept()
        else: super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._drag_offset is not None and event.buttons() & Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self._drag_offset); event.accept()
        else: super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if self._drag_offset is not None:
            self._drag_offset = None; self._clamp_to_screen(); self.controller.save_position(self.x(), self.y())
        super().mouseReleaseEvent(event)

    def _screen_geometry(self):
        screen = self.screen(); return screen.availableGeometry() if screen else None

    def _clamp_to_screen(self):
        geometry = self._screen_geometry()
        if geometry is None: return
        x, y = self.controller.clamp_position(self.x(), self.y(), left=geometry.left(), top=geometry.top(), right=geometry.right() + 1, bottom=geometry.bottom() + 1, width=self.width(), height=self.height())
        self.move(x, y)

    def _restore_position(self):
        saved = self.controller.position
        if saved: self.move(QPoint(*saved))
        self._clamp_to_screen()

    def closeEvent(self, event):
        with self._submit_lock:
            cancel_event = self._active_cancel_event
            request_id = self._active_request_id
            self._active_cancel_event = None
            self._active_request_id = None
        if cancel_event is not None:
            cancel_event.set()
        if request_id and hasattr(self.executor, 'cancel_turn'):
            try:
                self.executor.cancel_turn(request_id, device_id='desktop')
            except (KeyError, PermissionError):
                pass
        self.controller.save_position(self.x(), self.y())
        self._unsubscribe()
        self.controller.close()
        super().closeEvent(event)
