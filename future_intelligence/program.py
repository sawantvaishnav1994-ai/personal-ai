from __future__ import annotations
from pathlib import Path
from future_intelligence.gates import TrustGate
from future_intelligence.everyday import EverydayIntelligence
from future_intelligence.deep_brain import LifeGraph
from future_intelligence.operations import PersonalOperations
from future_intelligence.multimodal import WorldUnderstanding
from future_intelligence.everywhere import PersonalAIEverywhere
from future_intelligence.sovereignty import HybridIntelligenceRouter
from future_intelligence.autonomy import AdvancedAutonomy

class FutureIntelligenceProgram:
    """Integrated P4-P10 runtime foundation, deliberately gated by P3 evidence."""
    def __init__(self,data_dir:Path,*,runtime:dict):
        root=Path(data_dir);self.gate=TrustGate();self.runtime=runtime
        self.everyday=EverydayIntelligence(root/'everyday.sqlite3',memory=runtime.get('memory'),second_brain=runtime.get('second_brain'),proactive=runtime.get('proactive'),continuity=runtime.get('continuity'),integrations=runtime.get('integrations'),events=runtime.get('events'))
        self.life_graph=LifeGraph(root/'life-graph.sqlite3')
        self.operations=PersonalOperations(gate=self.gate,executor=runtime.get('executor'),automations=runtime.get('automations'),events=runtime.get('events'),second_brain=runtime.get('second_brain'))
        self.world=WorldUnderstanding(gate=self.gate,events=runtime.get('events'))
        self.everywhere=PersonalAIEverywhere(gate=self.gate,device_registry=runtime.get('device_registry'),continuity=runtime.get('continuity'))
        self.hybrid=HybridIntelligenceRouter(gate=self.gate)
        self.autonomy=AdvancedAutonomy(gate=self.gate,operations=self.operations,events=runtime.get('events'))
    def status(self):
        return {'p4':{'implemented':True,'activation':'safe-now'},'p5':{'implemented':True,'activation':'safe-now'},'p6':{'implemented':True,'activation':self.gate.decision('p6').reason},'p7':{'implemented':True,'activation':self.gate.decision('p7').reason},'p8':{'implemented':True,'activation':self.gate.decision('p8').reason},'p9':{'implemented':True,'activation':self.gate.decision('p9').reason},'p10':{'implemented':True,'activation':self.gate.decision('p10').reason}}
