from __future__ import annotations
import base64, json, os, secrets
from pathlib import Path
from threading import RLock
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.scrypt import Scrypt

class SecretVault:
    VERSION=1
    def __init__(self,path:Path,password:str):
        self.path=Path(path); self.path.parent.mkdir(parents=True,exist_ok=True)
        self.password=password.encode(); self.lock=RLock(); self._data={}; self._salt=b''
        if self.path.exists(): self._load()
        else: self._salt=secrets.token_bytes(16); self._save()
    def _key(self): return Scrypt(salt=self._salt,length=32,n=2**14,r=8,p=1).derive(self.password)
    def _load(self):
        obj=json.loads(self.path.read_text())
        if obj.get('version')!=self.VERSION: raise ValueError('unsupported vault version')
        self._salt=base64.b64decode(obj['salt']); nonce=base64.b64decode(obj['nonce']); ct=base64.b64decode(obj['ciphertext'])
        self._data=json.loads(AESGCM(self._key()).decrypt(nonce,ct,b'personal-ai-vault-v1').decode())
    def _save(self):
        nonce=secrets.token_bytes(12); raw=json.dumps(self._data,sort_keys=True).encode(); ct=AESGCM(self._key()).encrypt(nonce,raw,b'personal-ai-vault-v1')
        tmp=self.path.with_suffix(self.path.suffix+'.tmp'); tmp.write_text(json.dumps({'version':self.VERSION,'salt':base64.b64encode(self._salt).decode(),'nonce':base64.b64encode(nonce).decode(),'ciphertext':base64.b64encode(ct).decode()})); os.replace(tmp,self.path)
    def set(self,name:str,value:str):
        with self.lock: self._data[name]=value; self._save()
    def get(self,name:str,default=None): return self._data.get(name,default)
    def delete(self,name:str):
        with self.lock: self._data.pop(name,None); self._save()
    def names(self): return sorted(self._data)
    def rotate_password(self,new_password:str):
        with self.lock: self.password=new_password.encode(); self._salt=secrets.token_bytes(16); self._save()
