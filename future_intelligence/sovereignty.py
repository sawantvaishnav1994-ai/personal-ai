from __future__ import annotations
from dataclasses import dataclass,asdict

@dataclass(frozen=True)
class ModelTarget:
    id:str; locality:str; private:bool; capabilities:tuple[str,...]; available:bool=True; cost_rank:int=10

class HybridIntelligenceRouter:
    """P9 privacy-aware local/private/cloud policy independent of model vendor."""
    def __init__(self,*,gate):self.gate=gate;self._targets={}
    def register(self,target:ModelTarget):self._targets[target.id]=target
    def targets(self):return [asdict(v) for v in self._targets.values()]
    def route(self,*,capability:str,sensitivity:str='normal',offline:bool=False):
        d=self.gate.decision('p9')
        if not d.allowed:return {'routed':False,'blocked':True,'reason':d.reason}
        sensitivity=sensitivity.lower().strip();candidates=[]
        for t in self._targets.values():
            if not t.available or capability not in t.capabilities:continue
            if offline and t.locality!='local':continue
            if sensitivity in {'sensitive','secret'} and not (t.locality=='local' or t.private):continue
            candidates.append(t)
        if not candidates:return {'routed':False,'reason':'no eligible model target'}
        candidates.sort(key=lambda t:(0 if t.locality=='local' else 1,0 if t.private else 1,t.cost_rank,t.id))
        return {'routed':True,'target':asdict(candidates[0]),'policy':{'sensitivity':sensitivity,'offline':offline}}
