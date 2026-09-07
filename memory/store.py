from __future__ import annotations
import sqlite3, json, uuid
from pathlib import Path
from datetime import datetime, timezone
from threading import RLock

def now(): return datetime.now(timezone.utc).isoformat()

class MemoryStore:
    def __init__(self,path:Path):
        self.path=Path(path); self.path.parent.mkdir(parents=True,exist_ok=True)
        self.lock=RLock(); self._init()

    def con(self):
        c=sqlite3.connect(self.path); c.row_factory=sqlite3.Row; return c

    def _init(self):
        with self.con() as c:
            c.executescript("""
            CREATE TABLE IF NOT EXISTS messages(
              id TEXT PRIMARY KEY, role TEXT, content TEXT, created_at TEXT);
            CREATE TABLE IF NOT EXISTS memories(
              id TEXT PRIMARY KEY, type TEXT, subject TEXT, content TEXT, source TEXT,
              confidence REAL, verified INTEGER, sensitivity TEXT, parent_id TEXT,
              tags_json TEXT, created_at TEXT, updated_at TEXT);
            CREATE TABLE IF NOT EXISTS relations(
              id TEXT PRIMARY KEY, source_id TEXT, relation TEXT, target_id TEXT, created_at TEXT);
            CREATE TABLE IF NOT EXISTS tasks(
              id TEXT PRIMARY KEY, title TEXT, status TEXT, due_at TEXT, payload_json TEXT, created_at TEXT);
            CREATE TABLE IF NOT EXISTS audit(
              id TEXT PRIMARY KEY, category TEXT, action TEXT, payload_json TEXT, created_at TEXT);
            """)

    def add_message(self,role,content):
        i=str(uuid.uuid4())
        with self.lock,self.con() as c:
            c.execute("INSERT INTO messages VALUES(?,?,?,?)",(i,role,content,now()))
        return i

    def recent_messages(self,limit=20):
        with self.con() as c:
            rows=c.execute("SELECT role,content FROM messages ORDER BY created_at DESC LIMIT ?",(limit,)).fetchall()
        return [dict(x) for x in reversed(rows)]

    def remember(self,*,type,subject,content,source="user",confidence=1.0,verified=False,
                 sensitivity="normal",parent_id=None,tags=None):
        i=str(uuid.uuid4()); ts=now()
        with self.lock,self.con() as c:
            c.execute("""INSERT INTO memories VALUES(?,?,?,?,?,?,?,?,?,?,?,?)""",
                (i,type,subject,content,source,float(confidence),int(verified),sensitivity,
                 parent_id,json.dumps(tags or []),ts,ts))
        return i

    def relate(self,source_id,relation,target_id):
        i=str(uuid.uuid4())
        with self.lock,self.con() as c:
            c.execute("INSERT INTO relations VALUES(?,?,?,?,?)",(i,source_id,relation,target_id,now()))
        return i

    def search(self,q,limit=20):
        term=f"%{q}%"
        with self.con() as c:
            rows=c.execute("""SELECT * FROM memories WHERE subject LIKE ? OR content LIKE ?
                              ORDER BY updated_at DESC LIMIT ?""",(term,term,limit)).fetchall()
        return [dict(r) for r in rows]

    def graph(self):
        with self.con() as c:
            return {
              "nodes":[dict(r) for r in c.execute("SELECT * FROM memories").fetchall()],
              "edges":[dict(r) for r in c.execute("SELECT * FROM relations").fetchall()]
            }

    def audit(self,category,action,payload=None):
        i=str(uuid.uuid4())
        with self.lock,self.con() as c:
            c.execute("INSERT INTO audit VALUES(?,?,?,?,?)",
                      (i,category,action,json.dumps(payload or {},default=str),now()))
        return i
