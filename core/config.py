from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import os
from dotenv import load_dotenv

load_dotenv()

def env_bool(name: str, default: bool=False) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.lower().strip() in {"1","true","yes","on"}

@dataclass(frozen=True)
class Settings:
    base_dir: Path = Path(__file__).resolve().parent.parent
    data_dir: Path = Path.home() / ".personal_ai"

    ai_provider: str = os.getenv("AI_PROVIDER","local").lower().strip()
    local_ai_url: str = os.getenv("LOCAL_AI_URL","http://127.0.0.1:11434/v1").rstrip("/")
    local_ai_model: str = os.getenv("LOCAL_AI_MODEL","llama3.2")
    openrouter_api_key: str = os.getenv("OPENROUTER_API_KEY","")
    openrouter_model: str = os.getenv("OPENROUTER_MODEL","meta-llama/llama-3.3-70b-instruct")

    autonomy_mode: str = os.getenv("AUTONOMY_MODE","ask").lower().strip()
    control_server_enabled: bool = env_bool("CONTROL_SERVER_ENABLED", False)
    control_server_host: str = os.getenv("CONTROL_SERVER_HOST","127.0.0.1")
    control_server_port: int = int(os.getenv("CONTROL_SERVER_PORT","8766"))
    pairing_ttl_seconds: int = int(os.getenv("PAIRING_TTL_SECONDS","300"))

settings = Settings()
settings.data_dir.mkdir(parents=True, exist_ok=True)
