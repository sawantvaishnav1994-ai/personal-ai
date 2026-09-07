from tools.registry import Tool, Risk

def register(reg,engine):
    reg.register(Tool("automation_list","List scheduled automations",lambda p:engine.list(),Risk.READ_ONLY))
    reg.register(Tool("automation_create","Create scheduled automation; params: title,prompt,next_run_at,interval_seconds",
        lambda p:{"automation_id":engine.create(str(p["title"]),str(p["prompt"]),str(p["next_run_at"]),p.get("interval_seconds"))},
        Risk.REVERSIBLE))
