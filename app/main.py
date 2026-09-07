from __future__ import annotations
import sys, threading
from PyQt6.QtWidgets import QApplication
from core.config import settings
from core.events import EventBus
from memory.store import MemoryStore
from memory.second_brain import SecondBrain
from models.router import ModelRouter
from tools.registry import ToolRegistry
from tools.builtins import register_builtin_tools
from agent.executor import AgentExecutor
from automation.engine import AutomationEngine
from devices.registry import DeviceRegistry
from devices.gateway import DeviceGateway
from ui.main_window import MainWindow

def build_runtime():
    events=EventBus()
    memory=MemoryStore(settings.data_dir/"assistant.sqlite3")
    models=ModelRouter(settings)
    second_brain=SecondBrain(memory,models)
    device_registry=DeviceRegistry(settings.data_dir/"devices.sqlite3")
    device_gateway=DeviceGateway(device_registry,events)
    tools=ToolRegistry(settings)
    executor=AgentExecutor(models=models,tools=tools,memory=memory,events=events,second_brain=second_brain)
    automations=AutomationEngine(settings.data_dir/"automations.sqlite3",executor=executor,events=events)
    register_builtin_tools(tools,memory,settings,models=models,automation_engine=automations)
    return {"events":events,"memory":memory,"models":models,"second_brain":second_brain,
            "device_registry":device_registry,"device_gateway":device_gateway,
            "tools":tools,"executor":executor,"automations":automations}

def start_server(rt):
    if not settings.control_server_enabled:return
    from server.api import create_app
    import uvicorn
    app=create_app(rt["executor"],settings,device_registry=rt["device_registry"],
                   device_gateway=rt["device_gateway"],second_brain=rt["second_brain"],
                   automations=rt["automations"])
    uvicorn.run(app,host=settings.control_server_host,port=settings.control_server_port,log_level="warning")

def main():
    app=QApplication(sys.argv); app.setApplicationName("Personal AI")
    rt=build_runtime(); rt["automations"].start()
    if settings.control_server_enabled:
        threading.Thread(target=start_server,args=(rt,),daemon=True).start()
    win=MainWindow(events=rt["events"],executor=rt["executor"],memory=rt["memory"]); win.show()
    code=app.exec(); rt["automations"].stop(); return code

if __name__=="__main__": raise SystemExit(main())
