from __future__ import annotations
import json
from agent.planner import Planner

class ConfirmationRequired(RuntimeError):
    def __init__(self,tool_name,parameters,description=""):
        super().__init__(f"Confirmation required for {tool_name}")
        self.tool_name=tool_name; self.parameters=parameters; self.description=description

class AgentExecutor:
    def __init__(self,*,models,tools,memory,events):
        self.models=models; self.tools=tools; self.memory=memory; self.events=events
        self.planner=Planner(models,tools)

    def chat(self,text):
        self.memory.add_message("user",text)
        history=self.memory.recent_messages(16)
        self.events.emit("state",state="thinking")
        try:
            plan=self.planner.plan(text)
        except Exception:
            answer=self.models.chat(text,history=history[:-1])
            self.memory.add_message("assistant",answer)
            self.events.emit("state",state="speaking")
            return answer

        results={}
        for n,step in enumerate(plan.get("steps",[]),1):
            tool=self.tools.get(step["tool"]); params=step.get("parameters",{})
            if not self.tools.automatic(tool):
                raise ConfirmationRequired(tool.name,params,step.get("description",""))
            self.events.emit("state",state="acting",tool=tool.name)
            try:
                result=tool.handler(params)
                results[f"step{n}"]={"ok":True,"result":result}
                self.memory.audit("tool","execute",{"tool":tool.name,"params":params,"ok":True})
            except Exception as exc:
                self.memory.audit("tool","execute",{"tool":tool.name,"params":params,"ok":False,"error":str(exc)})
                raise

        if results:
            answer=self.models.chat(
                f"User request: {text}\nTool results: {json.dumps(results,default=str)[:12000]}\n"
                "Summarize what was completed and mention any limitations.",
                system="You are a concise personal AI assistant."
            )
        else:
            answer=self.models.chat(text,history=history[:-1])

        self.memory.add_message("assistant",answer)
        self.events.emit("state",state="speaking")
        return answer
