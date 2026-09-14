from __future__ import annotations
from pathlib import Path
import base64,hashlib,time,uuid


class ScreenUnderstanding:
    def __init__(self,models=None,data_dir:Path|None=None,observation_ttl_seconds:int=120):
        self.models=models; self.data_dir=Path(data_dir or Path.home()/'.personal_ai'); self.observation_ttl_seconds=max(5,min(int(observation_ttl_seconds),600))
    def capture(self,monitor:int=1,*,redactions=None,observation_id:str|None=None)->Path:
        import mss
        from PIL import Image,ImageDraw
        observation_id=observation_id or uuid.uuid4().hex
        path=self.data_dir/'screenshots'/f'observation-{observation_id}.png'; path.parent.mkdir(parents=True,exist_ok=True)
        with mss.mss() as sct:
            mon=sct.monitors[monitor]; raw=sct.grab(mon); image=Image.frombytes('RGB',raw.size,raw.rgb)
            if redactions:
                draw=ImageDraw.Draw(image)
                for item in list(redactions)[:200]:
                    try:
                        x=float(item.get('x',0)); y=float(item.get('y',0)); w=float(item.get('width',0)); h=float(item.get('height',0))
                        if w>0 and h>0:draw.rectangle((x,y,x+w,y+h),fill='black')
                    except Exception:continue
            image.save(path)
        return path
    @staticmethod
    def fingerprint(path:Path)->str:return hashlib.sha256(Path(path).read_bytes()).hexdigest()
    def observe_record(self,monitor:int=1,*,redactions=None,application_context=None)->dict:
        now=time.time(); observation_id=uuid.uuid4().hex; path=self.capture(monitor,redactions=redactions,observation_id=observation_id)
        return {'observation_id':observation_id,'captured_at':now,'expires_at':now+self.observation_ttl_seconds,'screenshot':str(path),'screen_sha256':self.fingerprint(path),'monitor':int(monitor),'application_context':dict(application_context or {})}
    def prepare_payload(self,question:str='Describe the visible screen.',monitor:int=1,*,redactions=None,application_context=None):
        record=self.observe_record(monitor,redactions=redactions,application_context=application_context); encoded=base64.b64encode(Path(record['screenshot']).read_bytes()).decode('ascii'); return {**record,'question':question,'image_data_url':f'data:image/png;base64,{encoded}'}
    def analyze(self,question:str='Describe the visible screen.',monitor:int=1,*,redactions=None,application_context=None):
        payload=self.prepare_payload(question,monitor,redactions=redactions,application_context=application_context)
        if not self.models:return payload
        return {key:value for key,value in payload.items() if key!='image_data_url'}|{'analysis':self.models.vision(question,payload['image_data_url'])}
