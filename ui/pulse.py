from __future__ import annotations
import math
from PyQt6.QtCore import QTimer
from PyQt6.QtGui import QPainter,QPen,QColor
from PyQt6.QtWidgets import QWidget

class PulseWidget(QWidget):
    def __init__(self,parent=None):
        super().__init__(parent); self.t=0.; self.state="idle"; self.timer=QTimer(self); self.timer.timeout.connect(self.tick); self.timer.start(16)
    def set_state(self,state): self.state=state; self.update()
    def tick(self): self.t+={"idle":.018,"listening":.04,"thinking":.06,"acting":.08,"speaking":.05}.get(self.state,.02); self.update()
    def paintEvent(self,_):
        p=QPainter(self); p.setRenderHint(QPainter.RenderHint.Antialiasing); w,h=self.width(),self.height(); cx,cy=w/2,h/2; amp={"idle":18,"listening":40,"thinking":56,"acting":70,"speaking":46}.get(self.state,20)
        for layer in range(8):
            p.setPen(QPen(QColor(115,225,255,max(18,125-layer*13)),max(.6,2.1-layer*.16))); pts=[]
            for i in range(220):
                q=i/219; x=cx-w*.33+i*(w*.66/219); env=math.sin(math.pi*q)**1.45; y=cy+math.sin(i*.16+self.t*(1+layer*.04))*amp*env+math.sin(i*.049+self.t*.72+layer)*17*env+(q-.5)*30; pts.append((int(x),int(y)))
            for a,b in zip(pts,pts[1:]): p.drawLine(a[0],a[1],b[0],b[1])
