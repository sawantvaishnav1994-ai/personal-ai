from __future__ import annotations
import io,queue,tempfile,threading,time
from pathlib import Path
class FullDuplexVoiceSession:
    def __init__(self,models,executor,events=None,samplerate=16000,chunk_ms=80,voice_threshold=.012,utterance_end_ms=450):
        self.models=models; self.executor=executor; self.events=events; self.samplerate=samplerate; self.block=int(samplerate*chunk_ms/1000); self.threshold=voice_threshold; self.end_s=utterance_end_ms/1000; self._stop=threading.Event(); self._barge=threading.Event(); self._q=queue.Queue(); self.thread=None; self._play_thread=None
    def start(self):
        if self.thread and self.thread.is_alive():return
        self._stop.clear(); self.thread=threading.Thread(target=self._run,daemon=True); self.thread.start()
    def stop(self):self._stop.set(); self._barge.set()
    def _emit(self,name,**kw):
        if self.events:self.events.emit(name,**kw)
    def _play(self,wav:bytes):
        try:
            import sounddevice as sd,soundfile as sf,numpy as np
            audio,sr=sf.read(io.BytesIO(wav),dtype='float32'); self._barge.clear(); stream=sd.OutputStream(samplerate=sr,channels=1 if audio.ndim==1 else audio.shape[1],dtype='float32'); stream.start(); step=max(256,int(sr*.04))
            for i in range(0,len(audio),step):
                if self._barge.is_set() or self._stop.is_set():break
                stream.write(np.asarray(audio[i:i+step],dtype='float32'))
            stream.stop(); stream.close()
        except Exception as e:self._emit('voice.error',error=str(e))
    def _respond(self,text):
        self._emit('state',state='thinking'); answer=self.executor.chat(text); self._emit('voice.reply',text=answer); self._emit('state',state='speaking'); wav=self.models.synthesize(answer); self._play_thread=threading.Thread(target=self._play,args=(wav,),daemon=True); self._play_thread.start()
    def _run(self):
        try:import sounddevice as sd,numpy as np,soundfile as sf
        except Exception as e:self._emit('voice.error',error=str(e)); return
        speech=[]; last_voice=0.0; speaking=False
        def cb(indata,frames,time_info,status):self._q.put(indata.copy())
        with sd.InputStream(samplerate=self.samplerate,channels=1,dtype='float32',blocksize=self.block,callback=cb):
            self._emit('state',state='listening')
            while not self._stop.is_set():
                try:block=self._q.get(timeout=.15)
                except queue.Empty:continue
                rms=float(np.sqrt(np.mean(block**2))); now=time.monotonic()
                if rms>=self.threshold:
                    last_voice=now; speech.append(block); speaking=True
                    if self._play_thread and self._play_thread.is_alive():self._barge.set(); self._emit('voice.barge_in')
                elif speaking:speech.append(block)
                if speaking and now-last_voice>=self.end_s:
                    audio=np.concatenate(speech); speech=[]; speaking=False
                    if len(audio)<self.samplerate*.25:continue
                    with tempfile.NamedTemporaryFile(suffix='.wav',delete=False) as f:path=Path(f.name)
                    sf.write(path,audio,self.samplerate)
                    try:
                        text=self.models.transcribe(path)
                        if text.strip():self._emit('voice.transcript',text=text); threading.Thread(target=self._respond,args=(text,),daemon=True).start()
                    finally:path.unlink(missing_ok=True)
            self._emit('state',state='idle')
