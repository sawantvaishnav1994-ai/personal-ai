from __future__ import annotations
from dataclasses import dataclass
from memory.knowledge_graph import KnowledgeGraph
@dataclass
class MemoryCandidate:
    type:str; subject:str; content:str; confidence:float; source:str='conversation'; verified:bool=False; tags:list[str]|None=None
class SecondBrain:
    def __init__(self,store,models=None,vector_store=None): self.store=store; self.models=models; self.vector_store=vector_store; self.kg=KnowledgeGraph(store)
    def remember(self,candidate:MemoryCandidate)->str:
        existing=self.store.search(candidate.content[:120],limit=5)
        for row in existing:
            if row['content'].strip().lower()==candidate.content.strip().lower(): return row['id']
        mid=self.store.remember(type=candidate.type,subject=candidate.subject,content=candidate.content,source=candidate.source,confidence=candidate.confidence,verified=candidate.verified,tags=candidate.tags or [])
        if self.vector_store:
            try:self.vector_store.upsert(mid,f'{candidate.subject}\n{candidate.content}')
            except Exception:pass
        return mid
    def context(self,query:str,limit:int=8)->list[dict]:
        combined={}
        if self.vector_store:
            try:
                graph_nodes={n['id']:n for n in self.store.graph().get('nodes',[])}
                for hit in self.vector_store.search(query,limit=limit):
                    if hit['memory_id'] in graph_nodes: combined[hit['memory_id']]={**graph_nodes[hit['memory_id']],'semantic_score':hit['score']}
            except Exception:pass
        for row in self.store.search(query,limit=limit): combined.setdefault(row['id'],row)
        if not combined:
            for word in [w for w in query.split() if len(w)>3][:6]:
                for row in self.store.search(word,limit=limit): combined.setdefault(row['id'],row)
        return list(combined.values())[:limit]
    def graph(self): return self.store.graph()
    def related(self,memory_id,depth=2): return self.kg.subgraph([memory_id],depth)
    def extract_candidates(self,user_text:str,assistant_text:str|None=None):
        if not self.models:return []
        prompt=f'''Extract only durable user facts/preferences/projects explicitly supported by USER TEXT. Never treat assistant claims as user facts. Return JSON: {{"memories":[{{"type":"fact|preference|project|person|note","subject":"...","content":"...","confidence":0.0,"tags":[]}}]}} USER TEXT:\n{user_text}'''
        try:data=self.models.json(prompt,system='Return conservative memory candidates as JSON only.')
        except Exception:return []
        out=[]
        for m in data.get('memories',[]):
            try:
                c=MemoryCandidate(str(m.get('type','note')),str(m.get('subject','')),str(m.get('content','')),max(0.0,min(1.0,float(m.get('confidence',.5)))),'user-message',False,list(m.get('tags',[])))
                if c.subject and c.content: out.append(c)
            except Exception: pass
        return out
