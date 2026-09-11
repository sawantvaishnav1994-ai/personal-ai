from __future__ import annotations

import html
from datetime import datetime

from PyQt6.QtCore import QEasingCurve, QPropertyAnimation, QThread, QTimer, Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QStackedWidget,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
)

from agent.executor import ConfirmationRequired
from ui.control_panel import ControlPanel
from ui.memory_panel import MemoryPanel
from ui.pulse import PulseWidget
from ui.settings_panel import SettingsPanel


class Worker(QThread):
    done = pyqtSignal(str)
    failed = pyqtSignal(object)

    def __init__(self, fn):
        super().__init__()
        self.fn = fn

    def run(self):
        try:
            self.done.emit(self.fn())
        except Exception as exc:
            self.failed.emit(exc)


class MainWindow(QMainWindow):
    """Personal AI — cinematic Home V1.

    The Home screen is the primary environment: one living AI presence, direct
    speech/text interaction, and lightweight paths to memory, activity, devices
    and knowledge. Detailed operational pages remain separate from Home.
    """

    NAV = (
        "Home",
        "Conversation",
        "Memory",
        "Knowledge",
        "Activities",
        "World",
        "Dashboard",
        "Apps & Tools",
        "Settings",
    )
    TOP_NAV = ("Home", "Memory", "Knowledge", "Activities", "World")
    STATE_COPY = {
        "idle": ("PERSONAL AI", "Ready"),
        "active": ("PERSONAL AI", "Listening..."),
        "listening": ("PERSONAL AI", "Listening..."),
        "understanding": ("PERSONAL AI", "Understanding..."),
        "thinking": ("PERSONAL AI", "Thinking..."),
        "memory": ("PERSONAL AI", "Remembering..."),
        "knowledge": ("PERSONAL AI", "Retrieving knowledge..."),
        "acting": ("PERSONAL AI", "Working..."),
        "speaking": ("PERSONAL AI", "Responding..."),
        "approval": ("PERSONAL AI", "Needs approval"),
        "error": ("PERSONAL AI", "Interrupted"),
        "background": ("PERSONAL AI", "Always available"),
    }

    def __init__(self, *, events, executor, memory, runtime=None):
        super().__init__()
        self.events = events
        self.executor = executor
        self.memory = memory
        self.runtime = runtime or {}
        self.worker = None
        self.pending_text = None
        self.voice_running = False
        self.current_page = "Home"

        self.setWindowTitle("Personal AI")
        self.resize(1600, 920)
        self.setMinimumSize(1120, 720)

        self._install_theme()

        root = QWidget()
        self.setCentralWidget(root)
        outer = QVBoxLayout(root)
        outer.setContentsMargins(28, 18, 28, 18)
        outer.setSpacing(8)
        outer.addLayout(self._build_top_nav())

        shell = QHBoxLayout()
        shell.setContentsMargins(0, 0, 0, 0)
        shell.setSpacing(10)

        self.stack = QStackedWidget()
        self.pages = {}
        for name in self.NAV:
            page = self._build_page(name)
            self.pages[name] = page
            self.stack.addWidget(page)
        shell.addWidget(self.stack, 1)

        self.menu_drawer = self._build_main_menu()
        self.menu_drawer.setMinimumWidth(0)
        self.menu_drawer.setMaximumWidth(0)
        shell.addWidget(self.menu_drawer)
        outer.addLayout(shell, 1)

        self.menu_anim = QPropertyAnimation(self.menu_drawer, b"maximumWidth", self)
        self.menu_anim.setDuration(240)
        self.menu_anim.setEasingCurve(QEasingCurve.Type.OutCubic)

        self._show_page("Home", close_menu=False)

        events.subscribe("state", self.on_state)
        events.subscribe("voice.transcript", self._on_voice_transcript)
        events.subscribe("voice.reply", self._on_voice_reply)
        events.subscribe("voice.wake", self._on_voice_wake)

        self.clock_timer = QTimer(self)
        self.clock_timer.timeout.connect(self._update_clock)
        self.clock_timer.start(1000)
        self._update_clock()

        # Continuous voice is the default Personal AI experience. The microphone
        # button remains available as a manual privacy override, but the user does
        # not need to click it on every launch.
        QTimer.singleShot(650, self._ensure_voice_active)

    def _install_theme(self):
        prefs = self.runtime.get("preferences")
        high = bool(prefs.get("high_contrast")) if prefs else False
        muted = "#aeb9ca" if high else "#8290a5"
        self.setStyleSheet(
            f"""
            QMainWindow, QWidget {{
                background:#02050a;
                color:#f3f7ff;
                font-family:Inter, "Segoe UI", Arial;
            }}
            QLabel#brand {{font-size:16px;font-weight:650;letter-spacing:5px;color:#f5f8ff;}}
            QLabel#brandSub {{font-size:10px;color:#66758b;}}
            QLabel#muted {{color:{muted};}}
            QLabel#heroTitle {{font-size:28px;font-weight:500;letter-spacing:8px;color:#f4f7ff;}}
            QLabel#heroState {{font-size:14px;letter-spacing:3px;color:#a8b9d4;}}
            QLabel#sideTitle {{font-size:26px;font-weight:350;letter-spacing:3px;color:#edf3ff;}}
            QLabel#sideKicker {{font-size:10px;font-weight:650;letter-spacing:4px;color:#7e8ca4;}}
            QLabel#quote {{font-size:15px;color:#8e9ab0;}}
            QLabel#attention {{font-size:12px;color:#e3cc93;}}
            QLineEdit {{
                background:transparent;border:0;padding:13px 8px;color:#eef5ff;
                font-size:15px;selection-background-color:#274a75;
            }}
            QPushButton {{
                background:transparent;border:1px solid transparent;border-radius:15px;
                padding:9px 14px;color:#9aa9be;
            }}
            QPushButton:hover {{background:#07111d;color:#f5f8ff;border-color:#18304a;}}
            QPushButton:checked {{background:#0a1726;color:#f7fbff;border-color:#315c8d;}}
            QPushButton#topNav {{font-size:13px;padding:10px 18px;border-radius:18px;}}
            QPushButton#topNav:checked {{background:#0b1828;border:1px solid #2d5f94;color:#f5f9ff;}}
            QPushButton#iconButton {{font-size:17px;min-width:30px;max-width:30px;padding:6px;}}
            QPushButton#mic {{
                background:#101b2b;border:1px solid #2a4567;border-radius:22px;
                min-width:44px;max-width:44px;min-height:44px;max-height:44px;
                color:#d9eaff;font-size:18px;padding:0;
            }}
            QPushButton#mic:checked {{background:#102a42;border-color:#58a9ff;color:#ffffff;}}
            QFrame#composer {{
                background:rgba(8,15,25,222);border:1px solid #293d5a;border-radius:28px;
            }}
            QFrame#feature {{background:transparent;border:0;border-radius:16px;}}
            QFrame#feature:hover {{background:#060d17;}}
            QFrame#card {{background:#060b12;border:1px solid #17263a;border-radius:16px;}}
            QFrame#menuDrawer {{background:#040911;border-left:1px solid #15263a;border-radius:18px;}}
            QTextBrowser {{background:#050a12;border:1px solid #17263a;border-radius:16px;padding:14px;}}
            QTextBrowser#homeConversation {{
                background:rgba(4,9,16,215);border:1px solid #172942;border-radius:16px;
                padding:10px 14px;color:#d6e0ed;
            }}
            """
        )

    def _build_top_nav(self):
        nav = QHBoxLayout()
        nav.setSpacing(7)

        brand_box = QVBoxLayout()
        brand_box.setSpacing(0)
        brand = QLabel("PERSONAL AI")
        brand.setObjectName("brand")
        sub = QLabel("A Personal AI Operating System")
        sub.setObjectName("brandSub")
        brand_box.addWidget(brand)
        brand_box.addWidget(sub)
        nav.addLayout(brand_box)
        nav.addStretch(1)

        self.top_buttons = {}
        icons = {"Home": "⌂", "Memory": "◉", "Knowledge": "▱", "Activities": "⌁", "World": "◎"}
        for name in self.TOP_NAV:
            button = QPushButton(f"{icons[name]}  {name}")
            button.setObjectName("topNav")
            button.setCheckable(True)
            button.clicked.connect(lambda _checked=False, target=name: self._show_page(target))
            self.top_buttons[name] = button
            nav.addWidget(button)

        nav.addStretch(1)
        search = QPushButton("⌕")
        search.setObjectName("iconButton")
        search.setToolTip("Search")
        search.clicked.connect(lambda: self.input.setFocus() if hasattr(self, "input") else None)
        nav.addWidget(search)

        settings = QPushButton("⚙")
        settings.setObjectName("iconButton")
        settings.setToolTip("Settings")
        settings.clicked.connect(lambda: self._show_page("Settings"))
        nav.addWidget(settings)

        self.menu_btn = QPushButton("☰")
        self.menu_btn.setObjectName("iconButton")
        self.menu_btn.setCheckable(True)
        self.menu_btn.clicked.connect(self._toggle_main_menu)
        nav.addWidget(self.menu_btn)

        orb = QLabel("✦")
        orb.setStyleSheet("font-size:22px;color:#7dc5ff;padding:0 8px")
        nav.addWidget(orb)
        greeting = QLabel("Good morning,\nLet’s build a better today.")
        greeting.setObjectName("muted")
        nav.addWidget(greeting)
        return nav

    def _build_main_menu(self):
        drawer = QFrame()
        drawer.setObjectName("menuDrawer")
        layout = QVBoxLayout(drawer)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(6)
        title = QLabel("PERSONAL AI")
        title.setObjectName("sideKicker")
        layout.addWidget(title)
        self.menu_buttons = {}
        for name in self.NAV:
            button = QPushButton(name)
            button.setCheckable(True)
            button.setMinimumWidth(220)
            button.clicked.connect(lambda _checked=False, target=name: self._show_page(target))
            self.menu_buttons[name] = button
            layout.addWidget(button)
        layout.addStretch(1)
        footer = QLabel("One intelligence · one continuous environment")
        footer.setObjectName("muted")
        footer.setWordWrap(True)
        layout.addWidget(footer)
        return drawer

    def _toggle_main_menu(self, checked):
        self.menu_anim.stop()
        self.menu_anim.setStartValue(self.menu_drawer.maximumWidth())
        self.menu_anim.setEndValue(270 if checked else 0)
        self.menu_anim.start()

    def _close_main_menu(self):
        if not self.menu_btn.isChecked() and self.menu_drawer.maximumWidth() == 0:
            return
        self.menu_btn.setChecked(False)
        self._toggle_main_menu(False)

    def _build_page(self, name):
        if name == "Home":
            return self._home_page()
        if name == "Conversation":
            return self._conversation_page()

        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(18, 22, 18, 18)
        title = QLabel(name)
        title.setStyleSheet("font-size:30px;font-weight:600")
        layout.addWidget(title)
        subtitle = QLabel(self._subtitle(name))
        subtitle.setObjectName("muted")
        subtitle.setWordWrap(True)
        layout.addWidget(subtitle)
        layout.addSpacing(14)

        if name == "Memory":
            self._memory_content(layout)
        elif name == "Knowledge":
            self._knowledge_content(layout)
        elif name == "Activities":
            self._activities_content(layout)
        elif name == "World":
            self._world_content(layout)
        elif name == "Dashboard":
            self._dashboard_content(layout)
        elif name == "Apps & Tools":
            self._apps_tools_content(layout)
        elif name == "Settings":
            self._settings_content(layout)
        layout.addStretch(1)
        return page

    def _home_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        self.needs_label = QLabel("")
        self.needs_label.setObjectName("attention")
        self.needs_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.needs_label.setVisible(False)
        layout.addWidget(self.needs_label)

        hero = QGridLayout()
        hero.setContentsMargins(10, 0, 10, 0)
        hero.setHorizontalSpacing(14)

        left = QWidget()
        left_layout = QVBoxLayout(left)
        left_layout.setContentsMargins(16, 78, 6, 18)
        left_layout.addWidget(self._label("A more\ncapable you.", "sideTitle"))
        left_layout.addSpacing(18)
        for word in ("UNDERSTAND", "REMEMBER", "REASON", "PLAN", "ACT", "WITH YOU"):
            left_layout.addWidget(self._label(word, "sideKicker"))
        left_layout.addStretch(1)
        hero.addWidget(left, 0, 0)

        self.pulse = PulseWidget()
        prefs = self.runtime.get("preferences")
        if prefs and hasattr(self.pulse, "set_reduce_motion"):
            self.pulse.set_reduce_motion(bool(prefs.get("reduce_motion")))
        hero.addWidget(self.pulse, 0, 1)

        right = QWidget()
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(10, 150, 12, 18)
        right_layout.addStretch(1)
        quote = QLabel('“Intelligence\nin service of\na meaningful life.”')
        quote.setObjectName("quote")
        quote.setAlignment(Qt.AlignmentFlag.AlignRight)
        right_layout.addWidget(quote)
        right_layout.addStretch(1)
        hero.addWidget(right, 0, 2)
        hero.setColumnStretch(0, 2)
        hero.setColumnStretch(1, 8)
        hero.setColumnStretch(2, 2)
        layout.addLayout(hero, 1)

        self.state = QLabel("PERSONAL AI")
        self.state.setObjectName("heroTitle")
        self.state.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.state)

        self.state_hint = QLabel("Ready")
        self.state_hint.setObjectName("heroState")
        self.state_hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.state_hint)

        waveform = QLabel("·  ▁▂▃▅▇▅▃▂▁  ·  ▁▃▆█▆▃▁  ·")
        waveform.setAlignment(Qt.AlignmentFlag.AlignCenter)
        waveform.setStyleSheet("color:#67b7ff;font-size:15px;letter-spacing:2px;")
        layout.addWidget(waveform)

        self.chat = QTextBrowser()
        self.chat.setObjectName("homeConversation")
        self.chat.setMaximumHeight(104)
        self.chat.setVisible(False)
        layout.addWidget(self.chat)

        composer_wrap = QHBoxLayout()
        composer_wrap.addStretch(2)
        composer = QFrame()
        composer.setObjectName("composer")
        composer.setMinimumWidth(620)
        composer.setMaximumWidth(900)
        row = QHBoxLayout(composer)
        row.setContentsMargins(16, 6, 8, 6)
        row.setSpacing(6)
        wave_icon = QLabel("≋")
        wave_icon.setStyleSheet("color:#6ebdff;font-size:23px;padding:0 8px")
        row.addWidget(wave_icon)
        self.input = QLineEdit()
        self.input.setPlaceholderText("Ask Personal AI anything...")
        self.input.setAccessibleName("Ask Personal AI")
        self.input.returnPressed.connect(lambda: self.submit(self.input))
        row.addWidget(self.input, 1)
        self.mic_btn = QPushButton("◉")
        self.mic_btn.setObjectName("mic")
        self.mic_btn.setCheckable(True)
        self.mic_btn.setAccessibleName("Pause continuous voice")
        self.mic_btn.clicked.connect(self.toggle_voice)
        row.addWidget(self.mic_btn)
        composer_wrap.addWidget(composer, 6)
        composer_wrap.addStretch(2)
        layout.addLayout(composer_wrap)

        helper = QLabel("Speak naturally   •   Type a message   •   Or give a command")
        helper.setObjectName("muted")
        helper.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(helper)
        layout.addSpacing(8)

        features = QHBoxLayout()
        features.setSpacing(10)
        feature_specs = (
            ("◉", "Memory", "Your history. Your context.\nAlways with you.", "Memory"),
            ("⌁", "Activities", "What Personal AI is doing\nfor you right now.", "Activities"),
            ("▣", "Devices", "Your connected world.\nIn sync.", "World"),
            ("▱", "Knowledge", "Information when you need it.\nFrom anywhere.", "Knowledge"),
        )
        for icon, title, text, target in feature_specs:
            features.addWidget(self._feature(icon, title, text, target), 1)
        layout.addLayout(features)

        footer = QHBoxLayout()
        self.clock_label = QLabel("")
        self.clock_label.setObjectName("muted")
        footer.addWidget(self.clock_label)
        footer.addStretch(1)
        motto = QLabel("T H I N K   ·   P L A N   ·   C R E A T E   ·   T O G E T H E R")
        motto.setStyleSheet("color:#48566c;font-size:9px;letter-spacing:2px")
        footer.addWidget(motto)
        footer.addStretch(1)
        self.system_status = QLabel("All systems operational  ●")
        self.system_status.setStyleSheet("color:#8290a5;font-size:11px")
        footer.addWidget(self.system_status)
        layout.addLayout(footer)
        return page

    def _feature(self, icon, title, text, target):
        frame = QFrame()
        frame.setObjectName("feature")
        row = QHBoxLayout(frame)
        row.setContentsMargins(14, 10, 14, 10)
        icon_label = QLabel(icon)
        icon_label.setStyleSheet("font-size:25px;color:#71bdff")
        row.addWidget(icon_label)
        copy = QVBoxLayout()
        name = QPushButton(title)
        name.setStyleSheet("text-align:left;color:#edf4ff;font-size:14px;padding:0;border:0;")
        name.clicked.connect(lambda _checked=False: self._show_page(target))
        detail = QLabel(text)
        detail.setObjectName("muted")
        detail.setStyleSheet("font-size:10px")
        copy.addWidget(name)
        copy.addWidget(detail)
        row.addLayout(copy, 1)
        arrow = QPushButton("›")
        arrow.setObjectName("iconButton")
        arrow.clicked.connect(lambda _checked=False: self._show_page(target))
        row.addWidget(arrow)
        return frame

    def _label(self, text, object_name):
        label = QLabel(text)
        label.setObjectName(object_name)
        return label

    def _conversation_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        title = QLabel("Conversation")
        title.setStyleSheet("font-size:30px;font-weight:600")
        layout.addWidget(title)
        self.conversation_chat = QTextBrowser()
        layout.addWidget(self.conversation_chat, 1)
        composer = QFrame()
        composer.setObjectName("composer")
        row = QHBoxLayout(composer)
        self.conversation_input = QLineEdit()
        self.conversation_input.setPlaceholderText("Continue the conversation...")
        self.conversation_input.returnPressed.connect(lambda: self.submit(self.conversation_input))
        row.addWidget(self.conversation_input, 1)
        self.conversation_mic_btn = QPushButton("◉")
        self.conversation_mic_btn.setObjectName("mic")
        self.conversation_mic_btn.setCheckable(True)
        self.conversation_mic_btn.clicked.connect(self.toggle_voice)
        row.addWidget(self.conversation_mic_btn)
        layout.addWidget(composer)
        return page

    def _card(self, title, value, detail=""):
        frame = QFrame()
        frame.setObjectName("card")
        box = QVBoxLayout(frame)
        label = QLabel(title)
        label.setObjectName("muted")
        value_label = QLabel(str(value))
        value_label.setStyleSheet("font-size:25px;font-weight:650")
        box.addWidget(label)
        box.addWidget(value_label)
        if detail:
            d = QLabel(detail)
            d.setObjectName("muted")
            d.setWordWrap(True)
            box.addWidget(d)
        return frame

    def _memory_content(self, layout):
        graph = self._graph()
        grid = QGridLayout()
        grid.addWidget(self._card("Memory", len(graph.get("nodes", [])), "Second Brain objects"), 0, 0)
        grid.addWidget(self._card("Relationships", len(graph.get("edges", [])), "Graph connections"), 0, 1)
        layout.addLayout(grid)
        button = QPushButton("Open Memory — Ambient / Graph / Tree / Detail")
        button.clicked.connect(self.open_memory)
        layout.addWidget(button)

    def _knowledge_content(self, layout):
        integrations = self.runtime.get("integrations")
        linked = integrations.list() if integrations and hasattr(integrations, "list") else []
        layout.addWidget(self._card("Connected sources", len(linked), "External knowledge sources"))

    def _activities_content(self, layout):
        automations = self.runtime.get("automations")
        rows = automations.list() if automations and hasattr(automations, "list") else []
        grid = QGridLayout()
        grid.addWidget(self._card("Running", sum(1 for x in rows if x.get("enabled")), "Active automated work"), 0, 0)
        grid.addWidget(self._card("Completed", sum(1 for x in rows if x.get("last_run_at")), "Work handled for you"), 0, 1)
        layout.addLayout(grid)

    def _world_content(self, layout):
        grid = QGridLayout()
        grid.addWidget(self._card("Devices", self._device_count(), "Trusted connected devices"), 0, 0)
        integrations = self.runtime.get("integrations")
        linked = integrations.list() if integrations and hasattr(integrations, "list") else []
        grid.addWidget(self._card("Connected apps", len(linked), "Permission-scoped services"), 0, 1)
        layout.addLayout(grid)

    def _dashboard_content(self, layout):
        grid = QGridLayout()
        grid.addWidget(self._card("Second Brain", self._memory_count(), "memory nodes"), 0, 0)
        grid.addWidget(self._card("Devices", self._device_count(), "registered identities"), 0, 1)
        grid.addWidget(self._card("Voice", "Active" if self.voice_running else "Ready", "continuous voice runtime"), 1, 0)
        grid.addWidget(self._card("Security", "Enforced", "permissions · approvals · audit"), 1, 1)
        layout.addLayout(grid)
        button = QPushButton("Open Detailed Control Dashboard")
        button.clicked.connect(self.open_control)
        layout.addWidget(button)

    def _apps_tools_content(self, layout):
        integrations = self.runtime.get("integrations")
        linked = integrations.list() if integrations and hasattr(integrations, "list") else []
        plugins = self.runtime.get("plugins")
        plugin_rows = plugins.list() if plugins and hasattr(plugins, "list") else []
        grid = QGridLayout()
        grid.addWidget(self._card("Connected apps", len(linked), "Accounts and services"), 0, 0)
        grid.addWidget(self._card("Extensions", len(plugin_rows), "Declarative tool manifests"), 0, 1)
        layout.addLayout(grid)

    def _settings_content(self, layout):
        text = QLabel("Personal AI · Identity · Voice · Appearance · Memory · Privacy · Permissions · Connected Apps · Notifications · Automation · Data · Security · Devices · Models · Advanced")
        text.setObjectName("muted")
        text.setWordWrap(True)
        layout.addWidget(text)
        button = QPushButton("Open Settings")
        button.clicked.connect(self.open_settings)
        layout.addWidget(button)

    def _subtitle(self, name):
        return {
            "Memory": "Your personal context, relationships and recall surfaces.",
            "Knowledge": "Documents, research, files and connected information.",
            "Activities": "What Personal AI has done, is doing, or needs from you.",
            "World": "Your devices, apps and connected environment.",
            "Dashboard": "System overview without cluttering Home.",
            "Apps & Tools": "Capabilities behind Personal AI.",
            "Settings": "Identity, privacy, permissions, voice, models and devices.",
        }[name]

    def _show_page(self, name, close_menu=True):
        if name not in self.pages:
            return
        self.current_page = name
        self.stack.setCurrentWidget(self.pages[name])
        for target, button in self.top_buttons.items():
            button.setChecked(target == name)
        for target, button in self.menu_buttons.items():
            button.setChecked(target == name)
        if close_menu:
            self._close_main_menu()

    def _graph(self):
        try:
            return self.memory.graph()
        except Exception:
            second_brain = self.runtime.get("second_brain")
            if second_brain and hasattr(second_brain, "graph"):
                try:
                    return second_brain.graph()
                except Exception:
                    pass
        return {"nodes": [], "edges": []}

    def _memory_count(self):
        return len(self._graph().get("nodes", []))

    def _device_count(self):
        registry = self.runtime.get("device_registry")
        try:
            return len(registry.list()) if registry and hasattr(registry, "list") else 0
        except Exception:
            return 0

    def _context_count(self):
        return self._device_count() + (1 if self.pending_text else 0)

    def _activity_count(self):
        automations = self.runtime.get("automations")
        if not automations or not hasattr(automations, "list"):
            return 0
        try:
            return sum(1 for item in automations.list() if item.get("last_run_at"))
        except Exception:
            return 0

    def _refresh_home_indicators(self):
        pass

    def _update_clock(self):
        if hasattr(self, "clock_label"):
            now = datetime.now()
            self.clock_label.setText(now.strftime("%H:%M\n%a, %d %b %Y"))

    def open_memory(self):
        MemoryPanel(self.memory, self).exec()

    def open_control(self):
        if self.runtime:
            ControlPanel(self.runtime, self).exec()

    def open_settings(self):
        if self.runtime:
            SettingsPanel(self.runtime, self).exec()

    def _ensure_voice_active(self):
        voice = self.runtime.get("voice")
        if not voice or self.voice_running:
            if not voice and hasattr(self, "system_status"):
                self.system_status.setText("Voice unavailable  ●")
            return
        try:
            voice.start()
            self.voice_running = True
            self._set_state("active")
            self._update_voice_buttons()
        except Exception as exc:
            self.voice_running = False
            if hasattr(self, "system_status"):
                self.system_status.setText("Voice needs attention  ●")
            self._append_chat("System", f"Voice could not start: {exc}")

    def _update_voice_buttons(self):
        label = "◉" if self.voice_running else "○"
        accessible = "Pause continuous voice" if self.voice_running else "Start continuous voice"
        for attr in ("mic_btn", "conversation_mic_btn"):
            button = getattr(self, attr, None)
            if button:
                button.setText(label)
                button.setAccessibleName(accessible)
                button.setChecked(self.voice_running)

    def toggle_voice(self):
        voice = self.runtime.get("voice")
        if not voice:
            return
        try:
            if self.voice_running:
                voice.stop()
                self.voice_running = False
                self._set_state("idle")
            else:
                voice.start()
                self.voice_running = True
                self._set_state("active")
        finally:
            self._update_voice_buttons()

    def _set_state(self, state):
        normalized = PulseWidget.normalize_state(state)
        title, hint = self.STATE_COPY.get(normalized, self.STATE_COPY["idle"])
        if hasattr(self, "state"):
            self.state.setText(title)
        if hasattr(self, "state_hint"):
            self.state_hint.setText(hint)
        if hasattr(self, "pulse"):
            self.pulse.set_state(normalized)
        if hasattr(self, "needs_label"):
            if normalized == "approval":
                self.needs_label.setText("Your approval is required")
                self.needs_label.setVisible(True)
            elif normalized != "error":
                self.needs_label.setVisible(False)

    def on_state(self, event):
        self._set_state(event.get("state", "idle"))

    def _on_voice_wake(self, event):
        self._set_state("listening")

    def _on_voice_transcript(self, event):
        text = event.get("text", "")
        if text:
            self._set_state("listening")
            self._append_chat("You", text)

    def _on_voice_reply(self, event):
        text = event.get("text", "")
        if text:
            self._append_chat("AI", text)
            self._set_state("speaking")
            QTimer.singleShot(950, lambda: self._set_state("active" if self.voice_running else "idle"))

    def _append_chat(self, who, text):
        if not text:
            return
        safe_who = html.escape(str(who))
        safe_text = html.escape(str(text)).replace("\n", "<br>")
        block = f'<div style="margin:4px 0 8px 0;"><span style="color:#7189a7;font-size:11px;">{safe_who}</span><br><span style="color:#dce8f6;">{safe_text}</span></div>'
        if hasattr(self, "chat"):
            self.chat.append(block)
            self.chat.setVisible(True)
        if hasattr(self, "conversation_chat"):
            self.conversation_chat.append(block)

    def submit(self, source=None):
        field = source if isinstance(source, QLineEdit) else self.input
        text = field.text().strip()
        if not text:
            return
        field.clear()
        self.pending_text = text
        self._append_chat("You", text)
        self._set_state("understanding")
        QTimer.singleShot(170, lambda: self._set_state("thinking") if self.worker and self.worker.isRunning() else None)
        self._run(lambda: self.executor.chat(text))

    def _run(self, fn):
        self.worker = Worker(fn)
        self.worker.done.connect(self.answer)
        self.worker.failed.connect(self.error)
        self.worker.start()

    def answer(self, text):
        self._append_chat("AI", text)
        self.pending_text = None
        self._set_state("speaking")
        voice = self.runtime.get("voice")
        if voice and hasattr(voice, "speak"):
            try:
                voice.speak(text)
            except Exception:
                pass
        QTimer.singleShot(1100, lambda: self._set_state("active" if self.voice_running else "idle"))

    def error(self, exc):
        if isinstance(exc, ConfirmationRequired):
            self._set_state("approval")
            choice = QMessageBox.question(
                self,
                "Approve once",
                f"Personal AI wants to run:\n\n{exc.tool_name}\n{exc.description}\n{exc.parameters}\n\nAllow this one action?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            if choice == QMessageBox.StandardButton.Yes:
                approval_id = exc.approval_id
                self.pending_text = None
                self._set_state("acting")
                self._run(lambda: self.executor.approve(approval_id))
                return
            self.executor.reject(exc.approval_id)
            self._append_chat("AI", "Action cancelled.")
            self.pending_text = None
            self._set_state("active" if self.voice_running else "idle")
            return

        self._append_chat("Error", str(exc))
        self.pending_text = None
        if hasattr(self, "needs_label"):
            self.needs_label.setText("Something interrupted the request")
            self.needs_label.setVisible(True)
        self._set_state("error")
        QTimer.singleShot(1800, lambda: self._set_state("active" if self.voice_running else "idle"))
