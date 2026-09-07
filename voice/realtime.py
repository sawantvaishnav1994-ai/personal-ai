from __future__ import annotations
import queue, tempfile, threading, time
from pathlib import Path
class RealtimeVoiceSession:
    def __init__(self,models,executor,events=None,samplerate=16000,chunk_seconds=.25,silence_seconds=1.0):
        self.models=models; self.executor=executor; self.events=events; self.samplerate=samplerate; self.chunk_seconds=chunk_seconds; self.silence_seconds=silence_seconds; self.q=queue.Queue(); self._stop=threading.Event(); self.thread=None
    def start(self):
        if self.thread and self.thread.is_alive(): return
        self._stop.clear(); self.thread=threading.Thread(target=self._run,daemon=True); self.thread.start()
    def stop(self): self._stop.set()
    def _run(self):
        try: import sounddevice as sd, numpy as np, soundfile as sf
        except Exception as e:
            if self.events:self.events.emit('voice.error',error=str(e))
            return
        frames=[]; last_voice=time.monotonic()
        def cb(indata,frames_count,time_info,status): self.q.put(indata.copy())
        with sd.InputStream(samplerate=self.samplerate,channels=1,dtype='float32',blocksize=int(self.samplerate*self.chunk_seconds),callback=cb):
            if self.events:self.events.emit('state',state='listening')
            while not self._stop.is_set():
                try:block=self.q.get(timeout=.2)
                except queue.Empty:continue
                rms=float(np.sqrt(np.mean(block**2))); frames.append(block)
                if rms>.012:last_voice=time.monotonic()
                if frames and time.monotonic()-last_voice>=self.silence_seconds:
                    audio=np.concatenate(frames); frames=[]; last_voice=time.monotonic()
                    if len(audio)<self.samplerate*.4:continue
                    with tempfile.NamedTemporaryFile(suffix='.wav',delete=False) as f:path=Path(f.name)
                    sf.write(path,audio,self.samplerate)
                    try:
                        text=self.models.transcribe(path)
                        if not text.strip():continue
                        if self.events:self.events.emit('voice.transcript',text=text); self.events.emit('state',state='thinking')
                        answer=self.executor.chat(text)
                        if self.events:self.events.emit('voice.reply',text=answer); self.events.emit('state',state='speaking')
                        self.models.speak(answer)
                    finally:path.unlink(missing_ok=True)
            if self.events:self.events.emit('state',state='idle')
