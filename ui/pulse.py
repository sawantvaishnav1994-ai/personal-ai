from __future__ import annotations
import math,random
from PyQt6.QtCore import QTimer,QPointF,Qt
from PyQt6.QtGui import QPainter,QPen,QColor,QPainterPath,QRadialGradient
from PyQt6.QtWidgets import QWidget

class PulseWidget(QWidget):
    """Asymmetrical living Neural Pulse Core with an accessibility-safe reduced-motion mode."""
    def __init__(self,parent=None):
        super().__init__(parent);self.t=0.;self.state='idle';self.reduce_motion=False;self.timer=QTimer(self);self.timer.timeout.connect(self.tick);self.timer.start(16);self.seed=[random.Random(i).uniform(-1,1) for i in range(16)]
    def set_state(self,state):self.state=state;self.update()
    def set_reduce_motion(self,value:bool):self.reduce_motion=bool(value);self.timer.setInterval(120 if self.reduce_motion else 16);self.update()
    def tick(self):
        speed={'idle':.015,'listening':.045,'thinking':.065,'acting':.085,'speaking':.052}.get(self.state,.02);self.t+=speed*(.18 if self.reduce_motion else 1.0);self.update()
    def paintEvent(self,_):
        p=QPainter(self);p.setRenderHint(QPainter.RenderHint.Antialiasing);w,h=self.width(),self.height();cx,cy=w*.50,h*.49;amp={'idle':15,'listening':34,'thinking':48,'acting':61,'speaking':40}.get(self.state,18);amp*=.42 if self.reduce_motion else 1
        glow=QRadialGradient(QPointF(cx,cy),min(w,h)*.42);glow.setColorAt(0,QColor(69,151,182,34));glow.setColorAt(.42,QColor(56,115,139,18));glow.setColorAt(1,QColor(0,0,0,0));p.setPen(Qt.PenStyle.NoPen);p.setBrush(glow);p.drawEllipse(QPointF(cx,cy),min(w,h)*.42,min(w,h)*.31)
        for layer in range(12):
            alpha=max(12,112-layer*7);pen=QPen(QColor(121,222,249,alpha),max(.45,1.7-layer*.08));p.setPen(pen);path=QPainterPath();steps=260
            for i in range(steps):
                q=i/(steps-1);x=cx-w*.36+q*w*.72;env=(math.sin(math.pi*q)**1.6);phase=self.t*(1+layer*.023);base=math.sin(i*.12+phase)*amp*env;detail=math.sin(i*.037+phase*.61+layer*.73)*13*env*(.45 if self.reduce_motion else 1);asym=(q-.5)*26+math.sin(q*8.2+layer)*8;drift=self.seed[layer%len(self.seed)]*7*env;y=cy+base+detail+asym+drift
                if i==0:path.moveTo(x,y)
                else:path.lineTo(x,y)
            p.drawPath(path)
        for n in range(15):
            a=n*.73+self.t*.14;radius=min(w,h)*(.08+.013*n);x=cx+math.cos(a*1.19)*radius*1.65;y=cy+math.sin(a*.91)*radius*.64;p.setBrush(QColor(150,232,255,max(15,105-n*5)));p.setPen(Qt.PenStyle.NoPen);p.drawEllipse(QPointF(x,y),1.4+(n%3)*.45,1.4+(n%3)*.45)
