from __future__ import annotations
import argparse,gc,os,sys,time,psutil,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from memory.store import MemoryStore
from automation.conditions import evaluate_condition
def main():
 p=argparse.ArgumentParser();p.add_argument('--seconds',type=int,default=45);a=p.parse_args();proc=psutil.Process(os.getpid());start=proc.memory_info().rss;deadline=time.time()+a.seconds;i=0
 with tempfile.TemporaryDirectory() as d:
  store=MemoryStore(Path(d)/'soak.sqlite3')
  while time.time()<deadline:
   store.remember(type='note',subject=f's{i%100}',content=f'c{i}',source='soak',confidence=.5,verified=False,tags=['soak']);store.search('c',limit=10);assert evaluate_condition({'path':'n','op':'gte','value':1},{'n':1});i+=1
   if i%200==0:gc.collect()
 end=proc.memory_info().rss
 if end-start>256*1024*1024:raise SystemExit(f'memory growth too high: {end-start}')
 print({'iterations':i,'rss_growth':end-start})
if __name__=='__main__':main()
