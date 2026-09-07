from __future__ import annotations
import sys,threading
from PyQt6.QtWidgets import QApplication
from core.config import settings
from core.events import EventBus
from memory.store import MemoryStore
from memory.second_brain import SecondBrain
from memory.vector_store import VectorStore
from models.router import ModelRouter
from tools.registry import ToolRegistry
from tools.builtins import register_builtin_tools
from agent.executor import AgentExecutor
from automation.engine import AutomationEngine
from devices.registry import DeviceRegistry
from devices.gateway import DeviceGateway
from integrations.runtime import build_integrations
from integrations.plugins import PluginManifestRegistry
from security.vault import SecretVault
from notifications.apns import APNsProvider
from voice.realtime import RealtimeVoiceSession
from voice.wake_phrase import WakePhraseGate
from ui.main_window import MainWindow

def build_runtime():
    events=EventBus();memory=MemoryStore(settings.data_dir/'assistant.sqlite3');models=ModelRouter(settings);vector=VectorStore(settings.data_dir/'vectors.sqlite3',models.embed);second_brain=SecondBrain(memory,models,vector);device_registry=DeviceRegistry(settings.data_dir/'devices.sqlite3');device_gateway=DeviceGateway(device_registry,events);vault=SecretVault(settings.data_dir/'vault.json',settings.vault_password or None);integrations,adapters,oauth,oauth_providers=build_integrations(settings,vault);plugins=PluginManifestRegistry(settings.data_dir/'plugins');plugins.load();apns=APNsProvider(settings,device_registry,events);tools=ToolRegistry(settings);executor=AgentExecutor(models=models,tools=tools,memory=memory,events=events,second_brain=second_brain);context_provider=lambda:{'devices':device_registry.list(),'integrations':integrations.list(),'memory_count':len(second_brain.graph().get('nodes',[]))};automations=AutomationEngine(settings.data_dir/'automations.sqlite3',executor=executor,events=events,context_provider=context_provider);register_builtin_tools(tools,memory,settings,models=models,automation_engine=automations,apns=apns);voice=RealtimeVoiceSession(models,executor,events);wake_phrase=WakePhraseGate(events);events.subscribe('voice.transcript',lambda e:wake_phrase.accept(e.get('text','')));return {'events':events,'memory':memory,'models':models,'second_brain':second_brain,'vector_store':vector,'device_registry':device_registry,'device_gateway':device_gateway,'tools':tools,'executor':executor,'automations':automations,'integrations':integrations,'integration_adapters':adapters,'oauth':oauth,'oauth_providers':oauth_providers,'plugins':plugins,'vault':vault,'voice':voice,'wake_phrase':wake_phrase,'apns':apns}
def start_server(rt):
    if not settings.control_server_enabled:return
    from server.api import create_app
    import uvicorn
    app=create_app(rt['executor'],settings,device_registry=rt['device_registry'],device_gateway=rt['device_gateway'],second_brain=rt['second_brain'],automations=rt['automations'],runtime=rt);uvicorn.run(app,host=settings.control_server_host,port=settings.control_server_port,log_level='warning')
def main():
    app=QApplication(sys.argv);app.setApplicationName('Personal AI');rt=build_runtime();rt['automations'].start()
    if settings.control_server_enabled:threading.Thread(target=start_server,args=(rt,),daemon=True).start()
    win=MainWindow(events=rt['events'],executor=rt['executor'],memory=rt['memory'],runtime=rt);win.show();code=app.exec();rt['voice'].stop();rt['automations'].stop();rt['apns'].close();return code
if __name__=='__main__':raise SystemExit(main())
