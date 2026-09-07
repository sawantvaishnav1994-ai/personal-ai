from __future__ import annotations
import json, requests

class ModelRouter:
    def __init__(self, settings): self.settings=settings

    def chat(self, prompt:str, *, system:str="You are a helpful personal AI assistant.",
             history:list[dict]|None=None, temperature:float=.3)->str:
        history = history or []
        if self.settings.ai_provider == "openrouter":
            return self._call(
                "https://openrouter.ai/api/v1",
                self.settings.openrouter_model, prompt, system, history, temperature,
                self.settings.openrouter_api_key
            )
        return self._call(
            self.settings.local_ai_url,
            self.settings.local_ai_model, prompt, system, history, temperature, None
        )

    def json(self, prompt:str, *, system:str="Return valid JSON only.")->dict:
        raw=self.chat(prompt, system=system, temperature=.1).strip()
        if raw.startswith("```"):
            raw=raw.replace("```json","").replace("```","").strip()
        return json.loads(raw)

    @staticmethod
    def _call(base_url, model, prompt, system, history, temperature, key):
        headers={"Content-Type":"application/json"}
        if key: headers["Authorization"]=f"Bearer {key}"
        messages=[{"role":"system","content":system}, *history, {"role":"user","content":prompt}]
        r=requests.post(f"{base_url}/chat/completions",headers=headers,
                        json={"model":model,"messages":messages,"temperature":temperature},
                        timeout=120)
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"].strip()
