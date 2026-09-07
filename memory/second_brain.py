from __future__ import annotations
from dataclasses import dataclass

@dataclass
class MemoryCandidate:
    type: str
    subject: str
    content: str
    confidence: float
    source: str = "conversation"
    verified: bool = False
    tags: list[str] | None = None

class SecondBrain:
    def __init__(self, store, models=None):
        self.store = store
        self.models = models

    def remember(self, candidate: MemoryCandidate) -> str:
        existing = self.store.search(candidate.content[:120], limit=5)
        for row in existing:
            if row["content"].strip().lower() == candidate.content.strip().lower():
                return row["id"]
        return self.store.remember(type=candidate.type, subject=candidate.subject,
            content=candidate.content, source=candidate.source,
            confidence=candidate.confidence, verified=candidate.verified,
            tags=candidate.tags or [])

    def context(self, query: str, limit: int = 8) -> list[dict]:
        direct = self.store.search(query, limit=limit)
        if direct:
            return direct
        merged, seen = [], set()
        for word in [w for w in query.split() if len(w)>3][:6]:
            for row in self.store.search(word, limit=limit):
                if row["id"] not in seen:
                    seen.add(row["id"]); merged.append(row)
                if len(merged) >= limit:
                    return merged
        return merged

    def graph(self):
        return self.store.graph()

    def extract_candidates(self, user_text: str, assistant_text: str | None = None):
        if not self.models:
            return []
        prompt=f'''Extract only durable user facts/preferences/projects explicitly supported by USER TEXT.
Never treat assistant claims as user facts. Return JSON:
{{"memories":[{{"type":"fact|preference|project|person|note","subject":"...","content":"...","confidence":0.0,"tags":[]}}]}}
USER TEXT:\n{user_text}'''
        try:
            data=self.models.json(prompt,system="Return conservative memory candidates as JSON only.")
        except Exception:
            return []
        out=[]
        for m in data.get("memories",[]):
            try:
                c=MemoryCandidate(str(m.get("type","note")),str(m.get("subject","")),
                    str(m.get("content","")),max(0.0,min(1.0,float(m.get("confidence",.5)))),
                    "user-message",False,list(m.get("tags",[])))
                if c.subject and c.content: out.append(c)
            except Exception: pass
        return out
