from __future__ import annotations
import sqlite3, uuid, threading
from datetime import datetime, timezone
from pathlib import Path

def now(): return datetime.now(timezone.utc).isoformat()

class AutomationEngine:
    def __init__(self,path:Path,executor=None,events=None,poll_seconds:float=2.0):
        self.path=Path(path); self.path.parent.mkdir(parents=True,exist_ok=True)
        self.executor=executor; self.events=events; self.poll_seconds=poll_seconds
        self._stop=threading.Event(); self._thread=None
        with self._con() as c:
            c.execute('''CREATE TABLE IF NOT EXISTS automations(
                id TEXT PRIMARY KEY,title TEXT,prompt TEXT,next_run_at TEXT,
                interval_seconds INTEGER,enabled INTEGER,last_run_at TEXT,created_at TEXT)''')

    def _con(self):
        c=sqlite3.connect(self.path); c.row_factory=sqlite3.Row; return c

    def create(self,title,prompt,next_run_at,interval_seconds=None):
        i=str(uuid.uuid4())
        with self._con() as c:
            c.execute("INSERT INTO automations VALUES(?,?,?,?,?,1,NULL,?)",
                      (i,title,prompt,next_run_at,interval_seconds,now()))
        return i

    def list(self):
        with self._con() as c:
            return [dict(r) for r in c.execute("SELECT * FROM automations ORDER BY created_at DESC")]

    def start(self):
        if self._thread and self._thread.is_alive(): return
        self._stop.clear(); self._thread=threading.Thread(target=self._loop,daemon=True); self._thread.start()

    def stop(self): self._stop.set()

    def _loop(self):
        while not self._stop.wait(self.poll_seconds):
            if not self.executor: continue
            current=now()
            with self._con() as c:
                due=c.execute("SELECT * FROM automations WHERE enabled=1 AND next_run_at<=? ORDER BY next_run_at",(current,)).fetchall()
            for row in due:
                try:
                    self.executor.chat(row["prompt"])
                    if self.events: self.events.emit("automation.completed",automation_id=row["id"])
                except Exception as exc:
                    if self.events: self.events.emit("automation.failed",automation_id=row["id"],error=str(exc))
                finally:
                    with self._con() as c:
                        if row["interval_seconds"]:
                            nxt=datetime.fromtimestamp(datetime.now(timezone.utc).timestamp()+row["interval_seconds"],timezone.utc).isoformat()
                            c.execute("UPDATE automations SET last_run_at=?,next_run_at=? WHERE id=?",(now(),nxt,row["id"]))
                        else:
                            c.execute("UPDATE automations SET last_run_at=?,enabled=0 WHERE id=?",(now(),row["id"]))
