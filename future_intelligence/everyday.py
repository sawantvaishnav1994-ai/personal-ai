from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import datetime, timezone
import sqlite3
from pathlib import Path
import uuid


def _now():
    return datetime.now(timezone.utc).isoformat()


@dataclass(frozen=True)
class Goal:
    id: str
    title: str
    status: str
    priority: float
    due_at: str | None
    context: str


class EverydayIntelligence:
    """P4 daily operating layer over memory, proactive, continuity and integrations."""

    def __init__(self, path: Path, *, memory=None, second_brain=None, proactive=None, continuity=None, integrations=None, events=None):
        self.path = Path(path); self.path.parent.mkdir(parents=True, exist_ok=True)
        self.memory = memory; self.second_brain = second_brain; self.proactive = proactive
        self.continuity = continuity; self.integrations = integrations; self.events = events
        with sqlite3.connect(self.path) as c:
            c.executescript('''
            CREATE TABLE IF NOT EXISTS everyday_items(
              id TEXT PRIMARY KEY,kind TEXT NOT NULL,title TEXT NOT NULL,status TEXT NOT NULL,
              priority REAL NOT NULL,due_at TEXT,context TEXT NOT NULL,source TEXT NOT NULL,
              created_at TEXT NOT NULL,updated_at TEXT NOT NULL);
            CREATE INDEX IF NOT EXISTS idx_everyday_kind_status ON everyday_items(kind,status);
            ''')

    def add(self, kind: str, title: str, *, priority: float = .5, due_at: str | None = None, context: str = '', source: str = 'user'):
        kind = kind.strip().lower()
        if kind not in {'goal','reminder','followup','task','commitment'}: raise ValueError('unsupported everyday item')
        item_id = str(uuid.uuid4()); stamp = _now()
        with sqlite3.connect(self.path) as c:
            c.execute('INSERT INTO everyday_items VALUES(?,?,?,?,?,?,?,?,?,?)',(item_id,kind,title.strip(),'open',max(0,min(float(priority),1)),due_at,context,source,stamp,stamp))
        if self.events: self.events.emit('everyday.item.created', item_id=item_id, kind=kind)
        return item_id

    def complete(self, item_id: str):
        with sqlite3.connect(self.path) as c:
            changed=c.execute("UPDATE everyday_items SET status='completed',updated_at=? WHERE id=?",(_now(),item_id)).rowcount
        return bool(changed)

    def items(self, *, status='open', limit=100):
        with sqlite3.connect(self.path) as c:
            c.row_factory=sqlite3.Row
            rows=c.execute('SELECT * FROM everyday_items WHERE status=? ORDER BY priority DESC,COALESCE(due_at,\'9999\') ASC LIMIT ?',(status,max(1,min(int(limit),500)))).fetchall()
        return [dict(r) for r in rows]

    def attention(self):
        rows=self.items(limit=50)
        return [r for r in rows if r['priority'] >= .7 or r['due_at']]

    def forgotten(self):
        """Return commitments/followups still open; never invent forgotten obligations."""
        return [r for r in self.items(limit=200) if r['kind'] in {'commitment','followup'}]

    def context_switch(self, device_id: str, *, topic: str, surface: str = 'personal-ai'):
        if not self.continuity: return {'device_id':device_id,'topic':topic,'surface':surface}
        bundle=self.continuity.resume(device_id)
        thread=bundle['thread']
        context=self.continuity.update_context(thread['id'], {'topic':topic,'surface':surface,'switched_at':_now()})
        if self.events: self.events.emit('context.switched',device_id=device_id,thread_id=thread['id'],topic=topic)
        return {'thread_id':thread['id'],'context':context}

    def briefing(self):
        open_items=self.items(limit=100); attention=self.attention(); forgotten=self.forgotten()
        memories=[]
        if self.second_brain:
            try: memories=self.second_brain.search('important current goals commitments decisions', limit=8)
            except Exception: memories=[]
        integration_state=[]
        if self.integrations:
            try: integration_state=self.integrations.list()
            except Exception: integration_state=[]
        return {
            'generated_at':_now(),
            'top_priorities':open_items[:5],
            'needs_attention':attention[:10],
            'possible_forgotten_commitments':forgotten[:10],
            'relevant_memory':memories,
            'connected_services':integration_state,
            'counts':{'open':len(open_items),'attention':len(attention),'followups':len(forgotten)},
        }
