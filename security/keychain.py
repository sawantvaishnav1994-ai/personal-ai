from __future__ import annotations
import base64,secrets

SERVICE='PersonalAI.RootKey'
ACCOUNT='default'

class KeychainUnavailable(RuntimeError): pass

class RootKeyStore:
    def __init__(self,service:str=SERVICE,account:str=ACCOUNT): self.service=service; self.account=account
    def _kr(self):
        try: import keyring; return keyring
        except Exception as e: raise KeychainUnavailable('OS keychain backend unavailable') from e
    def get(self)->bytes|None:
        raw=self._kr().get_password(self.service,self.account)
        return base64.b64decode(raw) if raw else None
    def get_or_create(self)->bytes:
        key=self.get()
        if key:return key
        key=secrets.token_bytes(32); self._kr().set_password(self.service,self.account,base64.b64encode(key).decode()); return key
    def rotate(self)->bytes:
        key=secrets.token_bytes(32); self._kr().set_password(self.service,self.account,base64.b64encode(key).decode()); return key
    def delete(self):
        try:self._kr().delete_password(self.service,self.account)
        except Exception:pass
