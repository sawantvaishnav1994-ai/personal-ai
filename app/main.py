from __future__ import annotations
import sys, threading
from PyQt6.QtWidgets import QApplication
from core.config import settings
from core.events import EventBus
from memory.store import MemoryStore
from models.router import ModelRouter
from tools.registry import ToolRegistry
from tools.builtins import register_builtin_tools
from agent.executor import AgentExecutor
from ui.main_window import MainWindow

def build_runtime():
    events=EventBus(); memory=MemoryStore(settings.data_dir/"assistant.sqlite3"); models=ModelRouter(settings); tools=ToolRegistry(settings); register_builtin_tools(tools,memory,settings); executor=AgentExecutor(models=models,tools=tools,memory=memory,events=events); return events,memory,models,tools,executor

def start_server(executor):
    if not settings.control_server_enabled:return
    from server.api import create_app
    import uvicorn
    app=create_app(executor,settings); uvicorn.run(app,host=settings.control_server_host,port=settings.control_server_port,log_level="warning")

def main():
    app=QApplication(sys.argv); app.setApplicationName("Personal AI"); events,memory,models,tools,executor=build_runtime()
    if settings.control_server_enabled: threading.Thread(target=start_server,args=(executor,),daemon=True).start()
    win=MainWindow(events=events,executor=executor,memory=memory); win.show(); return app.exec()

if __name__=="__main__": raise SystemExit(main())
