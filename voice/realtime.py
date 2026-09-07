from __future__ import annotations
from voice.full_duplex import FullDuplexVoiceSession
from voice.openai_realtime import OpenAIRealtimeVoiceSession

class RealtimeVoiceSession:
    """Select provider-native realtime when configured; preserve V5 turn pipeline as fallback."""
    def __init__(self,models,executor,events=None):
        native=OpenAIRealtimeVoiceSession(models.settings,events)
        self.backend=native if native.enabled else FullDuplexVoiceSession(models,executor,events)
        self.mode='openai-realtime' if native.enabled else 'stt-llm-tts-fallback'
    @property
    def thread(self):return getattr(self.backend,'thread',None)
    @property
    def connected(self):return getattr(self.backend,'connected',False)
    def start(self):return self.backend.start()
    def stop(self):return self.backend.stop()
    def __getattr__(self,name):return getattr(self.backend,name)
