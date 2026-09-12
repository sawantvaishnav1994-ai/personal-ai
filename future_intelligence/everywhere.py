from __future__ import annotations

class PersonalAIEverywhere:
    """P8 device-independent surface registry over one identity/continuity model."""
    SURFACES={'iphone','ipad','desktop','web','watch','wearable','earbuds','car','home','ar'}
    def __init__(self,*,gate,device_registry=None,continuity=None):self.gate=gate;self.device_registry=device_registry;self.continuity=continuity
    def capabilities(self):return sorted(self.SURFACES)
    def resume(self,device_id:str,surface:str):
        surface=surface.strip().lower()
        if surface not in self.SURFACES:raise ValueError('unknown surface')
        d=self.gate.decision('p8')
        if not d.allowed:return {'resumed':False,'blocked':True,'reason':d.reason,'surface':surface}
        if not self.continuity:return {'resumed':False,'blocked':True,'reason':'continuity service unavailable','surface':surface}
        bundle=self.continuity.resume(device_id)
        thread=bundle['thread'];context=self.continuity.update_context(thread['id'],{'surface':surface})
        return {'resumed':True,'surface':surface,'thread':thread,'context':context}
