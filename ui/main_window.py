from __future__ import annotations
from PyQt6.QtCore import Qt,QThread,pyqtSignal
from PyQt6.QtWidgets import QMainWindow,QWidget,QVBoxLayout,QHBoxLayout,QLabel,QLineEdit,QPushButton,QTextBrowser,QMessageBox
from agent.executor import ConfirmationRequired
from ui.pulse import PulseWidget
from ui.memory_panel import MemoryPanel

class Worker(QThread):
    done=pyqtSignal(str); failed=pyqtSignal(object)
    def __init__(self,fn): super().__init__(); self.fn=fn
    def run(self):
        try:self.done.emit(self.fn())
        except Exception as e:self.failed.emit(e)

class MainWindow(QMainWindow):
    def __init__(self,*,events,executor,memory):
        super().__init__(); self.events=events; self.executor=executor; self.memory=memory; self.worker=None; self.pending_text=None
        self.setWindowTitle("Personal AI"); self.resize(1280,800)
        self.setStyleSheet("QMainWindow,QWidget{background:#050608;color:#eef4f8} QLineEdit{background:#0b0f14;border:1px solid #24313c;border-radius:14px;padding:12px 16px;font-size:15px} QPushButton{background:#101822;border:1px solid #263746;border-radius:12px;padding:10px 14px} QTextBrowser{background:#070a0e;border:1px solid #18242e;border-radius:12px;padding:12px}")
        root=QWidget(); self.setCentralWidget(root); lay=QVBoxLayout(root); lay.setContentsMargins(26,20,26,20)
        nav=QHBoxLayout(); brand=QLabel("PERSONAL AI"); brand.setStyleSheet("color:#9fb4c3;letter-spacing:1px")
        memory_btn=QPushButton("Memory"); memory_btn.clicked.connect(self.open_memory)
        nav.addWidget(brand); nav.addStretch(1); nav.addWidget(QLabel("Home   Workspace   Control   Dashboard")); nav.addWidget(memory_btn); lay.addLayout(nav)
        self.pulse=PulseWidget(); self.pulse.setMinimumHeight(330); lay.addWidget(self.pulse,1)
        self.state=QLabel("Idle"); self.state.setAlignment(Qt.AlignmentFlag.AlignCenter); lay.addWidget(self.state)
        self.chat=QTextBrowser(); self.chat.setMaximumHeight(210); lay.addWidget(self.chat)
        row=QHBoxLayout(); self.input=QLineEdit(); self.input.setPlaceholderText("Ask Personal AI anything…"); self.input.returnPressed.connect(self.submit)
        btn=QPushButton("Send"); btn.clicked.connect(self.submit); row.addWidget(self.input,1); row.addWidget(btn); lay.addLayout(row)
        events.subscribe("state",self.on_state)

    def open_memory(self):
        MemoryPanel(self.memory,self).exec()

    def on_state(self,e):
        state=e.get("state","idle"); self.state.setText(state.title()); self.pulse.set_state(state)

    def submit(self):
        text=self.input.text().strip()
        if not text:return
        self.input.clear(); self.pending_text=text; self.chat.append(f"<b>You:</b> {text}"); self.pulse.set_state("listening")
        self._run(lambda:self.executor.chat(text))

    def _run(self,fn):
        self.worker=Worker(fn); self.worker.done.connect(self.answer); self.worker.failed.connect(self.error); self.worker.start()

    def answer(self,text):
        self.chat.append(f"<b>AI:</b> {text}"); self.pulse.set_state("idle"); self.pending_text=None

    def error(self,e):
        if isinstance(e,ConfirmationRequired):
            choice=QMessageBox.question(self,"Confirm action",f"Personal AI wants to run:\n\n{e.tool_name}\n{e.description}\n{e.parameters}\n\nAllow this action once?",QMessageBox.StandardButton.Yes|QMessageBox.StandardButton.No)
            if choice==QMessageBox.StandardButton.Yes and self.pending_text:
                tool=e.tool_name; text=self.pending_text; self._run(lambda:self.executor.chat(text,confirmed_tools={tool})); return
            self.chat.append("<b>AI:</b> Action cancelled.")
        else:self.chat.append(f"<b>Error:</b> {e}")
        self.pulse.set_state("idle"); self.pending_text=None
