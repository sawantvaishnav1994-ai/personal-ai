from __future__ import annotations
import argparse,asyncio,base64,gc,os,sqlite3,sys,time,psutil,tempfile
from pathlib import Path
from types import SimpleNamespace
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from memory.store import MemoryStore
from automation.conditions import evaluate_condition
from devices.gateway import DeviceGateway,DeviceCommand
from future_intelligence.multimodal import SimulatedObservationAdapter,WorldUnderstanding
from security.vault import SecretVault
from voice.openai_realtime import OpenAIRealtimeVoiceSession

class Events:
 def emit(self,*args,**kwargs):pass
class Registry:pass
class P7Gate:
 def decision(self,phase):
  assert phase=='p7';return SimpleNamespace(allowed=True,reason='ok')

def realtime_settings():
 return SimpleNamespace(openai_api_key='test',realtime_provider='openai',realtime_model='gpt-realtime-2.1',realtime_voice='marin',realtime_reasoning_effort='low',realtime_safety_identifier='',realtime_instructions='test',realtime_sample_rate=24000)

async def verify_device_pending_cleanup(gateway,i):
 try:await gateway.request('offline',DeviceCommand('device_info',{},f'soak-{i}'),timeout=.01)
 except RuntimeError:pass
 assert not gateway._pending

def main():
 p=argparse.ArgumentParser();p.add_argument('--seconds',type=int,default=45);a=p.parse_args();proc=psutil.Process(os.getpid());start=proc.memory_info().rss;peak=start;deadline=time.time()+a.seconds;i=0;p7_events=0
 with tempfile.TemporaryDirectory() as d:
  root=Path(d);db=root/'soak.sqlite3';world_db=root/'world.sqlite3';store=MemoryStore(db);current_password='soak-password';vault=SecretVault(root/'vault.json',current_password);events=Events();gateway=DeviceGateway(Registry(),events);realtime=OpenAIRealtimeVoiceSession(realtime_settings(),events);world=WorldUnderstanding(gate=P7Gate(),path=world_db,events=events);screen=SimulatedObservationAdapter('p7-soak-screen','screen')
  while time.time()<deadline:
   store.remember(type='note',subject=f's{i%100}',content=f'c{i}',source='soak',confidence=.5,verified=False,tags=['soak']);store.search('c',limit=10);assert evaluate_condition({'path':'n','op':'gte','value':1},{'n':1})
   if i%20==0:
    item=screen.ingest(world,{'title':f'soak-{i}'},source_event_id=f'p7-screen-{i}');dup=screen.ingest(world,{'title':f'soak-{i}'},source_event_id=f'p7-screen-{i}');assert dup['id']==item['id'] and dup['duplicate'] is True;assert len(world.recent(limit=5))<=5;assert world.capability('p7-soak-screen')['state']=='simulation_only';p7_events+=1
   if i%100==0:
    raw=world.ingest('image',{'fixture':i},source='p7-soak',source_event_id=f'p7-raw-{i}');child=world.ingest('image',{'fact':i},source='p7-soak-derived',source_event_id=f'p7-child-{i}',lineage_stage='derived',parent_observation_ids=[raw['id']],derivation_type='soak');assert len(world.lineage(child['id']))==2;assert world.delete(raw['id']) is True;assert world.get(child['id']) is None
    try:screen.ingest(world,{'api_key':'must-never-persist'},source_event_id=f'p7-reject-{i}')
    except ValueError:pass
    else:raise AssertionError('P7 secret-bearing soak payload was accepted')
   if i%50==0:
    vault.set('rotation-probe',str(i));assert vault.get('rotation-probe')==str(i)
    encoded=base64.b64encode(f'audio-{i}'.encode()).decode();realtime.handle_event({'type':'response.output_audio.delta','delta':encoded});assert realtime._play_q.get_nowait()==f'audio-{i}'.encode()
   if i%250==0:asyncio.run(verify_device_pending_cleanup(gateway,i))
   if i%500==0:
    current_password=f'soak-password-{i}';vault.rotate_password(current_password);assert vault.get('rotation-probe')==str(i)
    gc.collect();peak=max(peak,proc.memory_info().rss)
   i+=1
  integrity=sqlite3.connect(db).execute('PRAGMA integrity_check').fetchone()[0];assert integrity=='ok';p7_integrity=sqlite3.connect(world_db).execute('PRAGMA integrity_check').fetchone()[0];assert p7_integrity=='ok'
  vault_reloaded=SecretVault(root/'vault.json',current_password);assert vault_reloaded.get('rotation-probe') is not None
  restarted=WorldUnderstanding(gate=P7Gate(),path=world_db);p7_status=restarted.storage_status();assert p7_status['loaded_observations_in_memory']==0;assert p7_status['observation_count']>=p7_events
 end=proc.memory_info().rss;growth=end-start
 if growth>256*1024*1024:raise SystemExit(f'memory growth too high: {growth}')
 print({'iterations':i,'rss_start':start,'rss_peak':peak,'rss_end':end,'rss_growth':growth,'sqlite_integrity':integrity,'pending_device_requests':len(gateway._pending),'p7_events':p7_events,'p7_sqlite_integrity':p7_integrity,'p7_observations':p7_status['observation_count'],'p7_database_bytes':p7_status['database_bytes'],'p7_loaded_observations_in_memory':p7_status['loaded_observations_in_memory']})
if __name__=='__main__':main()
