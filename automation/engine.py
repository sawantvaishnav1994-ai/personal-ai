from __future__ import annotations
import json,sqlite3,uuid,threading
from datetime import datetime,timezone
from pathlib import Path
from automation.conditions import evaluate_condition
def now(): return datetime.now(timezone.utc).isoformat()
class AutomationEngine:
    def __init__(self,path:Path,executor=None,events=None,poll_seconds:float=2.0,context_provider=None):
        self.path=Path(path); self.path.parent.mkdir(parents=True,exist_ok=True); self.executor=executor; self.events=events; self.poll_seconds=poll_seconds; self.context_provider=context_provider or (lambda:{}); self._stop=threading.Event(); self._thread=None
        with self._con() as c:
            c.execute('CREATE TABLE IF NOT EXISTS automations(id TEXT PRIMARY KEY,title TEXT,prompt TEXT,next_run_at TEXT,interval_seconds INTEGER,enabled INTEGER,last_run_at TEXT,created_at TEXT)')
            cols={r['name'] for r in c.execute('PRAGMA table_info(automations)')}
            if 'condition_json' not in cols:c.execute("ALTER TABLE automations ADD COLUMN condition_json TEXT DEFAULT '{}'")
            if 'last_result_json' not in cols:c.execute('ALTER TABLE automations ADD COLUMN last_result_json TEXT')
    def _con(self): c=sqlite3.connect(self.path); c.row_factory=sqlite3.Row; return c
    def create(self,title,prompt,next_run_at,interval_seconds=None,condition=None):
        i=str(uuid.uuid4())
        with self._con() as c:c.execute('INSERT INTO automations(id,title,prompt,next_run_at,interval_seconds,enabled,last_run_at,created_at,condition_json) VALUES(?,?,?,?,?,1,NULL,?,?)',(i,title,prompt,next_run_at,interval_seconds,now(),json.dumps(condition or {})))
        return i
    def list(self):
        with self._con() as c:return [dict(r) for r in c.execute('SELECT * FROM automations ORDER BY created_at DESC')]
    def enable(self,automation_id,enabled=True):
        with self._con() as c:c.execute('UPDATE automations SET enabled=? WHERE id=?',(int(enabled),automation_id))
    def start(self):
        if self._thread and self._thread.is_alive():return
        self._stop.clear(); self._thread=threading.Thread(target=self._loop,daemon=True); self._thread.start()
    def stop(self): self._stop.set()
    def _loop(self):
        while not self._stop.wait(self.poll_seconds):
            if not self.executor:continue
            with self._con() as c: due=c.execute('SELECT * FROM automations WHERE enabled=1 AND next_run_at<=? ORDER BY next_run_at',(now(),)).fetchall()
            for row in due:self._run_one(row)
    def _run_one(self,row):
        result={'executed':False}
        try:
            condition=json.loads(row['condition_json'] or '{}'); context=self.context_provider() or {}
            if condition and not evaluate_condition(condition,context):
                result={'executed':False,'reason':'condition_false'}
                if self.events:self.events.emit('automation.skipped',automation_id=row['id'])
            else:
                reply=self.executor.chat(row['prompt']); result={'executed':True,'reply':reply}
                if self.events:self.events.emit('automation.completed',automation_id=row['id'])
        except Exception as exc:
            result={'executed':False,'error':str(exc)}
            if self.events:self.events.emit('automation.failed',automation_id=row['id'],error=str(exc))
        finally:
            with self._con() as c:
                if row['interval_seconds']:
                    nxt=datetime.fromtimestamp(datetime.now(timezone.utc).timestamp()+row['interval_seconds'],timezone.utc).isoformat(); c.execute('UPDATE automations SET last_run_at=?,next_run_at=?,last_result_json=? WHERE id=?',(now(),nxt,json.dumps(result),row['id']))
                else:c.execute('UPDATE automations SET last_run_at=?,enabled=0,last_result_json=? WHERE id=?',(now(),json.dumps(result),row['id']))
