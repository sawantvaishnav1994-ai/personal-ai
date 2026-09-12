from __future__ import annotations
import json
from pathlib import Path
import sqlite3
import uuid

class AdvancedAutonomy:
    """P10 planning/reflection layer. It cannot bypass the existing executor permissions."""
    def __init__(self,*,gate,operations=None,events=None,path:Path|None=None):
        self.gate=gate;self.operations=operations;self.events=events;self._agents={};self._outcomes=[];self._db=None;self._emergency_stop=False
        if path is not None:
            path=Path(path);path.parent.mkdir(parents=True,exist_ok=True);self._db=sqlite3.connect(path,check_same_thread=False)
            self._db.executescript('''
                CREATE TABLE IF NOT EXISTS agents (id TEXT PRIMARY KEY, document TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS autonomy_outcomes (id INTEGER PRIMARY KEY AUTOINCREMENT, document TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS autonomy_state (key TEXT PRIMARY KEY, value TEXT NOT NULL);
            ''')
            self._agents={row[0]:json.loads(row[1]) for row in self._db.execute('SELECT id,document FROM agents')}
            self._outcomes=[json.loads(row[0]) for row in self._db.execute('SELECT document FROM autonomy_outcomes ORDER BY id')]
            row=self._db.execute("SELECT value FROM autonomy_state WHERE key='emergency_stop'").fetchone();self._emergency_stop=bool(row and row[0]=='1')
    def _save_agent(self,agent):
        if self._db is not None:
            self._db.execute('INSERT OR REPLACE INTO agents(id,document) VALUES(?,?)',(agent['id'],json.dumps(agent,sort_keys=True)));self._db.commit()
    def emergency_stop(self,reason:str='owner requested'):
        self._emergency_stop=True
        for agent in self._agents.values():agent['enabled']=False;self._save_agent(agent)
        if self._db is not None:self._db.execute("INSERT OR REPLACE INTO autonomy_state(key,value) VALUES('emergency_stop','1')");self._db.commit()
        if self.events:self.events.emit('future.autonomy.emergency_stop',reason=reason)
        return {'stopped':True,'reason':reason}
    def clear_emergency_stop(self):
        self._emergency_stop=False
        if self._db is not None:self._db.execute("INSERT OR REPLACE INTO autonomy_state(key,value) VALUES('emergency_stop','0')");self._db.commit()
        return {'stopped':False}
    def status(self):return {'emergency_stop':self._emergency_stop,'agents':list(self._agents.values())}
    def create_agent(self,name:str,mission:str,skills:list[str]):
        if not name.strip() or not mission.strip():raise ValueError('name and mission required')
        aid=str(uuid.uuid4());self._agents[aid]={'id':aid,'name':name.strip(),'mission':mission.strip(),'skills':list(dict.fromkeys(skills))[:20],'enabled':False,'tool_allowlist':[],'budget_limit':0};self._save_agent(self._agents[aid]);return self._agents[aid]
    def set_policy(self,agent_id:str,*,tool_allowlist:list[str],budget_limit:float):
        if agent_id not in self._agents:raise KeyError('agent not found')
        agent=self._agents[agent_id];agent['tool_allowlist']=list(dict.fromkeys(tool_allowlist))[:50];agent['budget_limit']=max(0,float(budget_limit));self._save_agent(agent);return agent
    def enable_agent(self,agent_id:str):
        if self._emergency_stop:return {'enabled':False,'blocked':True,'reason':'owner emergency stop is active'}
        d=self.gate.decision('p10')
        if not d.allowed:return {'enabled':False,'blocked':True,'reason':d.reason}
        if agent_id not in self._agents:raise KeyError('agent not found')
        self._agents[agent_id]['enabled']=True;self._save_agent(self._agents[agent_id]);return self._agents[agent_id]
    def long_horizon_plan(self,goal:str):
        d=self.gate.decision('p10')
        if not d.allowed:return {'blocked':True,'reason':d.reason,'goal':goal}
        return {'blocked':False,'goal':goal,'stages':['understand','gather_evidence','plan','seek_required_approvals','execute_governed_steps','verify','reflect','update_memory']}
    def record_outcome(self,objective:str,result:str,*,success:bool,evidence:dict|None=None):
        item={'objective':objective,'result':result,'success':bool(success),'evidence':dict(evidence or {})};self._outcomes.append(item)
        if self._db is not None:self._db.execute('INSERT INTO autonomy_outcomes(document) VALUES(?)',(json.dumps(item,sort_keys=True),));self._db.commit()
        return item
    def self_evaluation(self):
        total=len(self._outcomes);success=sum(1 for x in self._outcomes if x['success'])
        return {'samples':total,'success_rate':(success/total if total else None),'outcomes':self._outcomes[-50:]}
    def scenario(self,question:str,options:list[str]):
        return {'question':question,'options':options[:10],'warning':'Scenario analysis is advisory; it must not create authority or execute consequences.'}
