from __future__ import annotations
import base64,json,queue,threading,time
from urllib.parse import quote

class OpenAIRealtimeVoiceSession:
    """Provider-native speech-to-speech session over the GA OpenAI Realtime WebSocket API."""
    def __init__(self,settings,events=None):
        self.settings=settings; self.events=events; self.thread=None; self._stop=threading.Event(); self._ws=None
        self._audio_q=queue.Queue(maxsize=128); self._play_q=queue.Queue(maxsize=256); self._response_active=False; self._connected=False
    @property
    def enabled(self): return bool(self.settings.openai_api_key and self.settings.realtime_provider in {'auto','openai'})
    @property
    def connected(self): return self._connected
    def _emit(self,name,**kw):
        if self.events:self.events.emit(name,**kw)
    def url(self): return f"wss://api.openai.com/v1/realtime?model={quote(self.settings.realtime_model)}"
    def headers(self):
        h=[f"Authorization: Bearer {self.settings.openai_api_key}"]
        if self.settings.realtime_safety_identifier:h.append(f"OpenAI-Safety-Identifier: {self.settings.realtime_safety_identifier}")
        return h
    def session_update(self):
        return {'type':'session.update','session':{'type':'realtime','model':self.settings.realtime_model,'instructions':self.settings.realtime_instructions,'output_modalities':['audio'],'reasoning':{'effort':self.settings.realtime_reasoning_effort},'audio':{'input':{'format':{'type':'audio/pcm','rate':self.settings.realtime_sample_rate},'turn_detection':{'type':'semantic_vad'}},'output':{'format':{'type':'audio/pcm'},'voice':self.settings.realtime_voice}}}}
    @staticmethod
    def append_event(pcm16:bytes): return {'type':'input_audio_buffer.append','audio':base64.b64encode(pcm16).decode('ascii')}
    def cancel_response(self):
        if self._ws and self._response_active:
            try:self._ws.send(json.dumps({'type':'response.cancel'}))
            except Exception:pass
        self._response_active=False; self._drain(self._play_q); self._emit('voice.barge_in')
    @staticmethod
    def _drain(q):
        try:
            while True:q.get_nowait()
        except queue.Empty:pass
    def handle_event(self,event:dict):
        t=event.get('type','')
        if t=='session.created':self._connected=True; self._emit('voice.realtime.connected',model=self.settings.realtime_model)
        elif t=='response.created':self._response_active=True; self._emit('state',state='speaking')
        elif t=='response.output_audio.delta':
            try:self._play_q.put_nowait(base64.b64decode(event.get('delta','')))
            except (ValueError,queue.Full):pass
        elif t=='response.output_audio_transcript.delta':
            if event.get('delta'):self._emit('voice.reply.delta',text=event['delta'])
        elif t=='response.done':self._response_active=False; self._emit('state',state='listening')
        elif t=='input_audio_buffer.speech_started':
            if self._response_active:self.cancel_response()
            self._emit('state',state='listening')
        elif t=='input_audio_buffer.speech_stopped':self._emit('state',state='thinking')
        elif t=='error':self._emit('voice.error',error=str(event.get('error',event)))
    def start(self):
        if not self.enabled:raise RuntimeError('OpenAI Realtime is not configured')
        if self.thread and self.thread.is_alive():return
        self._stop.clear(); self.thread=threading.Thread(target=self._run,daemon=True,name='personal-ai-realtime'); self.thread.start()
    def stop(self):
        self._stop.set(); self._connected=False
        try:
            if self._ws:self._ws.close()
        except Exception:pass
        self._drain(self._audio_q); self._drain(self._play_q); self._emit('state',state='idle')
    def _run(self):
        import websocket
        backoff=1.0
        while not self._stop.is_set():
            try:
                self._run_once(websocket); backoff=1.0
            except Exception as e:
                self._connected=False; self._emit('voice.realtime.disconnected',error=str(e))
                if self._stop.wait(backoff):break
                backoff=min(backoff*2,15.0)
    def _run_once(self,websocket):
        opened=threading.Event(); closed=threading.Event()
        def on_open(ws):
            self._ws=ws; ws.send(json.dumps(self.session_update())); opened.set()
        def on_message(ws,message):
            try:self.handle_event(json.loads(message))
            except Exception as e:self._emit('voice.error',error=f'realtime event: {e}')
        def on_error(ws,error):self._emit('voice.error',error=f'realtime transport: {error}')
        def on_close(ws,status,msg):self._connected=False; closed.set()
        app=websocket.WebSocketApp(self.url(),header=self.headers(),on_open=on_open,on_message=on_message,on_error=on_error,on_close=on_close); self._ws=app
        network=threading.Thread(target=lambda:app.run_forever(ping_interval=20,ping_timeout=10),daemon=True); network.start()
        if not opened.wait(15):raise RuntimeError('Realtime WebSocket connection timed out')
        self._emit('state',state='listening')
        io_thread=threading.Thread(target=self._audio_io,daemon=True); io_thread.start()
        while not self._stop.is_set() and network.is_alive():
            try:chunk=self._audio_q.get(timeout=.1)
            except queue.Empty:continue
            try:app.send(json.dumps(self.append_event(chunk)))
            except Exception:break
        try:app.close()
        except Exception:pass
        network.join(timeout=3)
    def _audio_io(self):
        import sounddevice as sd
        rate=self.settings.realtime_sample_rate
        def input_cb(indata,frames,time_info,status):
            if self._stop.is_set():return
            try:self._audio_q.put_nowait(bytes(indata))
            except queue.Full:pass
        with sd.RawInputStream(samplerate=rate,channels=1,dtype='int16',blocksize=max(240,int(rate*.02)),callback=input_cb) as inp, sd.RawOutputStream(samplerate=rate,channels=1,dtype='int16',blocksize=max(240,int(rate*.02))) as out:
            while not self._stop.is_set() and self._ws:
                try:chunk=self._play_q.get(timeout=.05)
                except queue.Empty:continue
                if chunk:out.write(chunk)
