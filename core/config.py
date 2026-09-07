from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import os
from dotenv import load_dotenv
load_dotenv()
def env_bool(name:str,default:bool=False)->bool:
    raw=os.getenv(name); return default if raw is None else raw.lower().strip() in {'1','true','yes','on'}
@dataclass(frozen=True)
class Settings:
    base_dir:Path=Path(__file__).resolve().parent.parent
    data_dir:Path=Path.home()/'.personal_ai'
    ai_provider:str=os.getenv('AI_PROVIDER','local').lower().strip()
    local_ai_url:str=os.getenv('LOCAL_AI_URL','http://127.0.0.1:11434/v1').rstrip('/')
    local_ai_model:str=os.getenv('LOCAL_AI_MODEL','llama3.2')
    openrouter_api_key:str=os.getenv('OPENROUTER_API_KEY','')
    openrouter_model:str=os.getenv('OPENROUTER_MODEL','meta-llama/llama-3.3-70b-instruct')
    openai_api_key:str=os.getenv('OPENAI_API_KEY','')
    realtime_provider:str=os.getenv('REALTIME_PROVIDER','auto').lower().strip()
    realtime_model:str=os.getenv('REALTIME_MODEL','gpt-realtime-2.1')
    realtime_voice:str=os.getenv('REALTIME_VOICE','marin')
    realtime_reasoning_effort:str=os.getenv('REALTIME_REASONING_EFFORT','low').lower().strip()
    realtime_safety_identifier:str=os.getenv('REALTIME_SAFETY_IDENTIFIER','')
    realtime_instructions:str=os.getenv('REALTIME_INSTRUCTIONS','You are Personal AI. Be concise, natural, context-aware, and ask before taking consequential actions.')
    realtime_sample_rate:int=int(os.getenv('REALTIME_SAMPLE_RATE','24000'))
    vision_model:str=os.getenv('VISION_MODEL','')
    embedding_model:str=os.getenv('EMBEDDING_MODEL','text-embedding-3-small')
    stt_model:str=os.getenv('STT_MODEL','whisper-1')
    tts_model:str=os.getenv('TTS_MODEL','tts-1')
    tts_voice:str=os.getenv('TTS_VOICE','alloy')
    autonomy_mode:str=os.getenv('AUTONOMY_MODE','ask').lower().strip()
    control_server_enabled:bool=env_bool('CONTROL_SERVER_ENABLED',False)
    control_server_host:str=os.getenv('CONTROL_SERVER_HOST','127.0.0.1')
    control_server_port:int=int(os.getenv('CONTROL_SERVER_PORT','8766'))
    pairing_ttl_seconds:int=int(os.getenv('PAIRING_TTL_SECONDS','300'))
    browser_headless:bool=env_bool('BROWSER_HEADLESS',False)
    vault_password:str=os.getenv('PERSONAL_AI_VAULT_PASSWORD','')
    google_client_id:str=os.getenv('GOOGLE_CLIENT_ID','')
    google_client_secret:str=os.getenv('GOOGLE_CLIENT_SECRET','')
    slack_client_id:str=os.getenv('SLACK_CLIENT_ID','')
    slack_client_secret:str=os.getenv('SLACK_CLIENT_SECRET','')
    gmail_token:str=os.getenv('GMAIL_ACCESS_TOKEN','')
    calendar_token:str=os.getenv('GOOGLE_CALENDAR_ACCESS_TOKEN','')
    slack_token:str=os.getenv('SLACK_BOT_TOKEN','')
    home_assistant_url:str=os.getenv('HOME_ASSISTANT_URL','')
    home_assistant_token:str=os.getenv('HOME_ASSISTANT_TOKEN','')
    release_public_key_b64:str=os.getenv('RELEASE_PUBLIC_KEY_B64','')
settings=Settings(); settings.data_dir.mkdir(parents=True,exist_ok=True)
