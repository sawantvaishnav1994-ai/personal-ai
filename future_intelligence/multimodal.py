from __future__ import annotations
from datetime import datetime,timezone
import uuid

def _now():return datetime.now(timezone.utc).isoformat()

class WorldUnderstanding:
    """P7 normalized multimodal observation ledger. No sensor is assumed present."""
    MODALITIES={'screen','camera','image','document','audio','location','device_sensor','wearable'}
    def __init__(self,*,gate,events=None):self.gate=gate;self.events=events;self._observations=[]
    def ingest(self,modality:str,payload:dict,*,source:str,device_id:str|None=None,confidence:float=1.0):
        modality=modality.strip().lower()
        if modality not in self.MODALITIES:raise ValueError('unsupported modality')
        if not source:raise ValueError('source attribution required')
        item={'id':str(uuid.uuid4()),'modality':modality,'payload':dict(payload or {}),'source':source,'device_id':device_id,'confidence':max(0,min(float(confidence),1)),'observed_at':_now()}
        self._observations.append(item)
        if self.events:self.events.emit('world.observed',observation_id=item['id'],modality=modality,device_id=device_id)
        return item
    def recent(self,limit=50):return list(reversed(self._observations[-max(1,min(int(limit),500)):]))
    def action_context(self):
        d=self.gate.decision('p7')
        return {'allowed_for_governed_action':d.allowed,'reason':d.reason,'observations':self.recent(20)}
