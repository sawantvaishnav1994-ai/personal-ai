from __future__ import annotations

from dataclasses import dataclass, asdict
import json
from pathlib import Path
import sqlite3
import uuid


@dataclass(frozen=True)
class OperationStep:
    id:str; kind:str; instruction:str; consequential:bool=False; status:str='pending'


class PersonalOperations:
    """P6 long-horizon operation planner; external effects remain governed."""
    def __init__(self,*,gate,executor=None,automations=None,events=None,second_brain=None,path:Path|None=None):
        self.gate=gate;self.executor=executor;self.automations=automations;self.events=events;self.second_brain=second_brain;self._plans={};self._db=None
        if path is not None:
            path=Path(path);path.parent.mkdir(parents=True,exist_ok=True);self._db=sqlite3.connect(path,check_same_thread=False)
            self._db.execute('CREATE TABLE IF NOT EXISTS operation_plans (id TEXT PRIMARY KEY, document TEXT NOT NULL)')
            self._plans={row[0]:json.loads(row[1]) for row in self._db.execute('SELECT id,document FROM operation_plans')}
    def _save(self,plan):
        if self._db is not None:
            self._db.execute('INSERT OR REPLACE INTO operation_plans(id,document) VALUES(?,?)',(plan['id'],json.dumps(plan,sort_keys=True)))
            self._db.commit()
    def create_plan(self,title:str,steps:list[dict]):
        if not title.strip() or not steps: raise ValueError('title and steps required')
        pid=str(uuid.uuid4()); normalized=[]
        for item in steps[:50]:
            normalized.append(OperationStep(str(uuid.uuid4()),str(item.get('kind','reason')),str(item.get('instruction','')).strip(),bool(item.get('consequential',False))))
        self._plans[pid]={'id':pid,'title':title.strip(),'status':'planned','steps':[asdict(s) for s in normalized]}
        self._save(self._plans[pid])
        return self._plans[pid]
    def plan(self,plan_id): return self._plans.get(plan_id)
    def execute(self,plan_id:str):
        decision=self.gate.decision('p6')
        if not decision.allowed: return {'started':False,'blocked':True,'reason':decision.reason,'plan':self.plan(plan_id)}
        plan=self._plans.get(plan_id)
        if not plan: raise KeyError('plan not found')
        if any(step['consequential'] for step in plan['steps']):
            plan['status']='needs_approval'
            self._save(plan)
            if self.events:self.events.emit('future.operation.approval_required',plan_id=plan_id,title=plan['title'])
            return {'started':False,'approval_required':True,'plan':plan}
        plan['status']='ready'
        self._save(plan)
        return {'started':True,'delegated':False,'plan':plan,'note':'Execution must be delegated through the existing governed executor/automation engine.'}
