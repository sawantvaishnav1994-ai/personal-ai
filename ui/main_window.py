from __future__ import annotations
from PyQt6.QtCore import Qt,QThread,pyqtSignal
from PyQt6.QtWidgets import QMainWindow,QWidget,QVBoxLayout,QHBoxLayout,QLabel,QLineEdit,QPushButton,QTextBrowser,QMessageBox,QStackedWidget,QFrame,QGridLayout
from agent.executor import ConfirmationRequired
from ui.pulse import PulseWidget
from ui.memory_panel import MemoryPanel
from ui.control_panel import ControlPanel
from ui.settings_panel import SettingsPanel

class Worker(QThread):
    done=pyqtSignal(str);failed=pyqtSignal(object)
    def __init__(self,fn):super().__init__();self.fn=fn
    def run(self):
        try:self.done.emit(self.fn())
        except Exception as e:self.failed.emit(e)

class MainWindow(QMainWindow):
    NAV=('Home','Workspace','Memory','Control','Dashboard','More')
    def __init__(self,*,events,executor,memory,runtime=None):
        super().__init__();self.events=events;self.executor=executor;self.memory=memory;self.runtime=runtime or {};self.worker=None;self.pending_text=None;self.voice_running=False
        self.setWindowTitle('Personal AI');self.resize(1380,860);self.setMinimumSize(1040,700)
        prefs=self.runtime.get('preferences');high=bool(prefs.get('high_contrast')) if prefs else False
        muted='#9badb7' if high else '#72838e';border='#2b4350' if high else '#14212a'
        self.setStyleSheet(f'''QMainWindow,QWidget{{background:#040506;color:#eef4f8;font-family:Inter,Segoe UI,Arial}} QLabel#brand{{color:#c9d8e1;font-size:15px;font-weight:700;letter-spacing:3px}} QLabel#muted{{color:{muted}}} QLabel#heroState{{font-size:21px;font-weight:650;color:#edf7fb}} QLineEdit{{background:#090d11;border:1px solid #1c2a34;border-radius:18px;padding:13px 17px;font-size:15px;selection-background-color:#244656}} QPushButton{{background:transparent;border:1px solid transparent;border-radius:12px;padding:9px 13px;color:#9aabb5}} QPushButton:hover{{background:#0b1116;color:#eef7fb;border-color:#16242d}} QPushButton:checked{{background:#0d151b;color:#eef7fb;border-color:#233641}} QPushButton#primary{{background:#101c24;border:1px solid #29404d;color:#eaf7fb}} QTextBrowser{{background:#06090c;border:1px solid #131f27;border-radius:16px;padding:14px}} QFrame#card{{background:#070b0f;border:1px solid {border};border-radius:16px}}''')
        root=QWidget();self.setCentralWidget(root);outer=QVBoxLayout(root);outer.setContentsMargins(26,18,26,20);outer.setSpacing(12);outer.addLayout(self._build_nav());self.stack=QStackedWidget();outer.addWidget(self.stack,1);self.pages={}
        for name in self.NAV:
            page=self._build_page(name);self.pages[name]=page;self.stack.addWidget(page)
        self._show_page('Home');events.subscribe('state',self.on_state);events.subscribe('voice.transcript',lambda e:self._append_chat('You (voice)',e.get('text','')));events.subscribe('voice.reply',lambda e:self._append_chat('AI',e.get('text','')));events.subscribe('voice.wake',lambda e:self._append_chat('System',f"Wake phrase detected: {e.get('phrase','Hey Personal')}"))
    def _build_nav(self):
        nav=QHBoxLayout();brand=QLabel('PERSONAL AI');brand.setObjectName('brand');nav.addWidget(brand);nav.addStretch(1);self.nav_buttons={}
        for name in self.NAV:
            b=QPushButton(name);b.setCheckable(True);b.clicked.connect(lambda checked,n=name:self._show_page(n));self.nav_buttons[name]=b;nav.addWidget(b)
        self.voice_btn=QPushButton('●  Voice');self.voice_btn.setObjectName('primary');self.voice_btn.clicked.connect(self.toggle_voice);nav.addSpacing(8);nav.addWidget(self.voice_btn);return nav
    def _build_page(self,name):
        if name=='Home':return self._home_page()
        page=QWidget();lay=QVBoxLayout(page);lay.setContentsMargins(12,18,12,12);title=QLabel(name);title.setStyleSheet('font-size:28px;font-weight:650');lay.addWidget(title);subtitle=QLabel(self._subtitle(name));subtitle.setObjectName('muted');subtitle.setWordWrap(True);lay.addWidget(subtitle)
        if name=='Workspace':self._workspace_content(lay)
        elif name=='Memory':self._memory_content(lay)
        elif name=='Control':self._control_content(lay)
        elif name=='Dashboard':self._dashboard_content(lay)
        else:self._more_content(lay)
        lay.addStretch(1);return page
    def _home_page(self):
        page=QWidget();lay=QVBoxLayout(page);lay.setContentsMargins(6,8,6,0);lay.setSpacing(8);summary=QHBoxLayout();self.needs_label=QLabel('0 things need you');self.needs_label.setObjectName('muted');self.handled_label=QLabel(self._handled_text());self.handled_label.setObjectName('muted');summary.addStretch(1);summary.addWidget(self.needs_label);summary.addSpacing(20);summary.addWidget(self.handled_label);summary.addStretch(1);lay.addLayout(summary);self.pulse=PulseWidget();self.pulse.setMinimumHeight(330)
        prefs=self.runtime.get('preferences');
        if prefs and hasattr(self.pulse,'set_reduce_motion'):self.pulse.set_reduce_motion(bool(prefs.get('reduce_motion')))
        lay.addWidget(self.pulse,1);self.state=QLabel('Idle');self.state.setObjectName('heroState');self.state.setAlignment(Qt.AlignmentFlag.AlignCenter);lay.addWidget(self.state);autonomy=QHBoxLayout();autonomy.addStretch(1);autonomy_label=QLabel('Observe   ·   Suggest   ·   Ask   ·   Act');autonomy_label.setObjectName('muted');autonomy.addWidget(autonomy_label);autonomy.addStretch(1);lay.addLayout(autonomy);self.chat=QTextBrowser();self.chat.setMaximumHeight(190);lay.addWidget(self.chat);row=QHBoxLayout();self.input=QLineEdit();self.input.setAccessibleName('Ask Personal AI');self.input.setPlaceholderText('Ask Personal AI anything…');self.input.returnPressed.connect(self.submit);btn=QPushButton('Send');btn.setObjectName('primary');btn.clicked.connect(self.submit);row.addWidget(self.input,1);row.addWidget(btn);lay.addLayout(row);status=QHBoxLayout();mic=QLabel('Mic ●');memory=QLabel('Memory ●');devices=QLabel(f'Devices {self._device_count()} ●');policy=QLabel('Ask before acting')
        for w in (mic,memory,devices,policy):w.setObjectName('muted');status.addWidget(w)
        status.addStretch(1);lay.addLayout(status);return page
    def _card(self,title,value,detail=''):
        f=QFrame();f.setObjectName('card');l=QVBoxLayout(f);t=QLabel(title);t.setObjectName('muted');v=QLabel(str(value));v.setStyleSheet('font-size:25px;font-weight:650');l.addWidget(t);l.addWidget(v)
        if detail:d=QLabel(detail);d.setObjectName('muted');d.setWordWrap(True);l.addWidget(d)
        return f
    def _workspace_content(self,lay):
        grid=QGridLayout();autos=self.runtime.get('automations');auto_rows=autos.list() if autos and hasattr(autos,'list') else [];integrations=self.runtime.get('integrations');linked=integrations.list() if integrations and hasattr(integrations,'list') else [];plugins=self.runtime.get('plugins');plugin_rows=plugins.list() if plugins and hasattr(plugins,'list') else []
        grid.addWidget(self._card('Active automations',sum(1 for x in auto_rows if x.get('enabled')),'Scheduled and conditional work'),0,0);grid.addWidget(self._card('Linked integrations',len(linked),'Permission-scoped accounts and services'),0,1);grid.addWidget(self._card('Trusted devices',self._device_count(),'Desktop and companion-device control plane'),1,0);grid.addWidget(self._card('Extensions',len(plugin_rows),'Declarative manifests; no arbitrary Python execution'),1,1);lay.addLayout(grid)
    def _memory_content(self,lay):
        graph=self.memory.graph();grid=QGridLayout();grid.addWidget(self._card('Memory nodes',len(graph.get('nodes',[])),'Second Brain objects'),0,0);grid.addWidget(self._card('Relationships',len(graph.get('edges',[])),'Knowledge graph edges'),0,1);lay.addLayout(grid);b=QPushButton('Open Second Brain — Overview / Graph / Tree / Timeline');b.setObjectName('primary');b.clicked.connect(self.open_memory);lay.addWidget(b)
    def _control_content(self,lay):
        mode=getattr(getattr(self.runtime.get('tools'),'settings',None),'autonomy_mode','ask');grid=QGridLayout();grid.addWidget(self._card('Autonomy',str(mode).title(),'Central policy enforced below model output'),0,0);grid.addWidget(self._card('Device trust',self._device_count(),'Bearer-authenticated and revocable'),0,1);lay.addLayout(grid);b=QPushButton('Open Control Center');b.setObjectName('primary');b.clicked.connect(self.open_control);lay.addWidget(b)
    def _dashboard_content(self,lay):
        graph=self.memory.graph();telemetry=self.runtime.get('telemetry');snap=telemetry.snapshot() if telemetry else {'metrics':{},'counters':{}};grid=QGridLayout();grid.addWidget(self._card('Second Brain',len(graph.get('nodes',[])),'memory nodes'),0,0);grid.addWidget(self._card('Devices',self._device_count(),'registered identities'),0,1);grid.addWidget(self._card('Voice','Ready' if self.runtime.get('voice') else 'Unavailable','Realtime + fallback runtime'),1,0);grid.addWidget(self._card('Security','Enforced','permissions · one-use approvals · vault · audit · device trust'),1,1);grid.addWidget(self._card('Local telemetry',len(snap.get('metrics',{})),'timed operations; never uploaded'),2,0);grid.addWidget(self._card('Recovery','Ready' if self.runtime.get('backups') else 'Unavailable','integrity-checked backup/restore'),2,1);lay.addLayout(grid);b=QPushButton('Open Detailed Control Dashboard');b.setObjectName('primary');b.clicked.connect(self.open_control);lay.addWidget(b)
    def _more_content(self,lay):
        text=QTextBrowser();text.setHtml('<h3>Capabilities</h3><p>Voice-first interaction · Hey Personal wake phrase · browser and desktop control · Word/Excel/PowerPoint/PDF productivity · automations · account integrations · companion devices · secure notifications · Second Brain memory.</p><h3>Safety boundary</h3><p>External side effects require one-use execution-scoped approval. Device identity is revocable. Secrets stay in the vault or OS credential store.</p><h3>Recovery & privacy</h3><p>Backups are integrity checked and exclude the Personal AI vault and common secret files. Performance telemetry stays local.</p>');text.setMaximumHeight(330);lay.addWidget(text);settings_btn=QPushButton('Settings · Onboarding · Accessibility · Backup & Recovery');settings_btn.setObjectName('primary');settings_btn.clicked.connect(self.open_settings);lay.addWidget(settings_btn)
    def _subtitle(self,name):return {'Workspace':'Active work, automations, integrations and execution context.','Memory':'Your Second Brain: structured memories, graph relationships and timeline.','Control':'Autonomy, approvals, permissions, devices and security controls.','Dashboard':'On-demand operational health and system evidence.','More':'Capabilities, settings, recovery and extension surfaces.'}[name]
    def _show_page(self,name):
        self.stack.setCurrentWidget(self.pages[name])
        for n,b in self.nav_buttons.items():b.setChecked(n==name)
    def _device_count(self):
        r=self.runtime.get('device_registry');return len(r.list()) if r and hasattr(r,'list') else 0
    def _handled_text(self):
        a=self.runtime.get('automations');rows=a.list() if a and hasattr(a,'list') else [];return f"{sum(1 for x in rows if x.get('last_run_at'))} handled for you"
    def open_memory(self):MemoryPanel(self.memory,self).exec()
    def open_control(self):
        if self.runtime:ControlPanel(self.runtime,self).exec()
    def open_settings(self):
        if self.runtime:SettingsPanel(self.runtime,self).exec()
    def toggle_voice(self):
        voice=self.runtime.get('voice')
        if not voice:return
        if self.voice_running:voice.stop();self.voice_running=False;self.voice_btn.setText('●  Voice')
        else:voice.start();self.voice_running=True;self.voice_btn.setText('■  Stop Voice')
    def on_state(self,e):state=e.get('state','idle');self.state.setText(state.title());self.pulse.set_state(state)
    def _append_chat(self,who,text):
        if hasattr(self,'chat') and text:self.chat.append(f'<b>{who}:</b> {text}')
    def submit(self):
        text=self.input.text().strip()
        if not text:return
        self.input.clear();self.pending_text=text;self._append_chat('You',text);self.pulse.set_state('listening');self._run(lambda:self.executor.chat(text))
    def _run(self,fn):self.worker=Worker(fn);self.worker.done.connect(self.answer);self.worker.failed.connect(self.error);self.worker.start()
    def answer(self,text):self._append_chat('AI',text);self.pulse.set_state('idle');self.pending_text=None;self.needs_label.setText('0 things need you');self.handled_label.setText(self._handled_text())
    def error(self,e):
        if isinstance(e,ConfirmationRequired):
            self.needs_label.setText('1 thing needs you');choice=QMessageBox.question(self,'Approve once',f'Personal AI wants to run:\n\n{e.tool_name}\n{e.description}\n{e.parameters}\n\nThis approval is one-use and bound to these exact parameters. Allow it?',QMessageBox.StandardButton.Yes|QMessageBox.StandardButton.No)
            if choice==QMessageBox.StandardButton.Yes:
                approval_id=e.approval_id;self.pending_text=None;self._run(lambda:self.executor.approve(approval_id));return
            self.executor.reject(e.approval_id);self._append_chat('AI','Action cancelled.');self.needs_label.setText('0 things need you')
        else:self._append_chat('Error',str(e))
        self.pulse.set_state('idle');self.pending_text=None
