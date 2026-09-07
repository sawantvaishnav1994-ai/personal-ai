from __future__ import annotations
class DesktopController:
    def __init__(self,pause=.15): self.pause=pause
    def _pg(self): import pyautogui; pyautogui.PAUSE=self.pause; return pyautogui
    def position(self): p=self._pg().position(); return {'x':p.x,'y':p.y}
    def move(self,x,y,duration=.2): self._pg().moveTo(int(x),int(y),duration=float(duration)); return self.position()
    def click(self,x=None,y=None,button='left'): self._pg().click(x=x,y=y,button=button); return {'ok':True}
    def type_text(self,text,interval=.01): self._pg().write(str(text),interval=float(interval)); return {'ok':True}
    def hotkey(self,*keys): self._pg().hotkey(*keys); return {'ok':True}
    def screenshot(self,path): self._pg().screenshot(path); return {'path':str(path)}
