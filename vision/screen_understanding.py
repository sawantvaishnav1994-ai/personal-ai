from __future__ import annotations

import base64
import hashlib
import io
import os
from pathlib import Path
import time
import uuid


class ScreenUnderstanding:
    def __init__(self, models, data_dir, *, observation_ttl_seconds: int = 120, retention_seconds: int = 86400, max_evidence_files: int = 500):
        self.models = models
        self.data_dir = Path(data_dir)
        self.observation_ttl_seconds = max(5, min(int(observation_ttl_seconds), 600))
        self.retention_seconds = max(300, int(retention_seconds))
        self.max_evidence_files = max(20, int(max_evidence_files))

    def _evidence_dir(self) -> Path:
        root = self.data_dir
        root.mkdir(parents=True, exist_ok=True)
        if root.is_symlink(): raise PermissionError('evidence data root cannot be a symlink')
        directory = root / 'screenshots'
        if directory.exists() and directory.is_symlink(): raise PermissionError('evidence directory cannot be a symlink')
        directory.mkdir(parents=True, exist_ok=True, mode=0o700)
        try: os.chmod(directory, 0o700)
        except OSError: pass
        return directory

    @staticmethod
    def _clip_redaction(image, box):
        try:
            x=max(0,int(box.get('x',0))); y=max(0,int(box.get('y',0))); w=max(0,int(box.get('width',0))); h=max(0,int(box.get('height',0)))
            right=min(image.width,x+w); bottom=min(image.height,y+h)
            return (x,y,right,bottom) if right>x and bottom>y else None
        except Exception: return None

    def _prune(self, directory: Path):
        now=time.time(); files=sorted((p for p in directory.glob('observation-*.png') if p.is_file() and not p.is_symlink()), key=lambda p:p.stat().st_mtime, reverse=True)
        for index,path in enumerate(files):
            try:
                if index>=self.max_evidence_files or now-path.stat().st_mtime>self.retention_seconds: path.unlink(missing_ok=True)
            except OSError: pass

    def observe_record(self, *, monitor: int = 1, redactions: list[dict] | None = None) -> dict:
        import pyautogui
        image=pyautogui.screenshot(); redaction_count=0
        if redactions:
            from PIL import ImageDraw
            draw=ImageDraw.Draw(image)
            for item in redactions:
                clipped=self._clip_redaction(image,item)
                if clipped: draw.rectangle(clipped,fill=(0,0,0)); redaction_count+=1
        buf=io.BytesIO(); image.save(buf,format='PNG'); raw=buf.getvalue(); fingerprint=hashlib.sha256(raw).hexdigest(); observation_id=str(uuid.uuid4())
        directory=self._evidence_dir(); final_path=directory/f'observation-{observation_id}.png'
        if final_path.exists() or final_path.is_symlink(): raise PermissionError('observation evidence destination collision')
        fd=os.open(final_path,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
        try:
            with os.fdopen(fd,'wb') as handle: handle.write(raw); handle.flush(); os.fsync(handle.fileno())
        except Exception:
            try: final_path.unlink(missing_ok=True)
            except OSError: pass
            raise
        captured_at=time.time(); self._prune(directory)
        return {'observation_id':observation_id,'captured_at':captured_at,'expires_at':captured_at+self.observation_ttl_seconds,'screenshot_evidence_ref':f'screenshots/{final_path.name}','screen_fingerprint':fingerprint,'screenshot_sha256':fingerprint,'redaction_count':redaction_count,'monitor':int(monitor),'_image_data_url':'data:image/png;base64,'+base64.b64encode(raw).decode('ascii')}

    def analyze(self, question: str = 'Describe this screen and identify actionable UI elements.', monitor: int = 1, *, redactions: list[dict] | None = None):
        record=self.observe_record(monitor=monitor,redactions=redactions); image_data=record.pop('_image_data_url','')
        if self.models is None: return {**record,'analysis':'screen captured; no vision model configured'}
        prompt=f"{question}\nUse only visible evidence. If uncertain, say uncertain. Do not infer hidden credentials or secret values."
        response=self.models.vision(prompt,image_data)
        return {**record,'analysis':response}
