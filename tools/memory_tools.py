from tools.registry import Tool, Risk

def register(reg,store):
    def remember(p):
        i=store.remember(type=str(p.get("type","note")),subject=str(p.get("subject","note")),content=str(p["content"]),source="user-command",verified=True,tags=list(p.get("tags",[])))
        return {"memory_id":i}
    reg.register(Tool("remember","Save verified memory; params: type,subject,content,tags",remember,Risk.REVERSIBLE))
    reg.register(Tool("search_memory","Search memory; params: query",lambda p:store.search(str(p["query"]),int(p.get("limit",20))),Risk.READ_ONLY))
