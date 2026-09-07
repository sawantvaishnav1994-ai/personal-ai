from __future__ import annotations
import base64, hashlib, json, shutil, tempfile, zipfile
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
class UpdateVerificationError(RuntimeError): pass
class SignedUpdater:
    def __init__(self,public_key_b64:str,install_dir:Path): self.public_key=Ed25519PublicKey.from_public_bytes(base64.b64decode(public_key_b64)); self.install_dir=Path(install_dir)
    def verify_manifest(self,manifest_bytes:bytes,signature_b64:str)->dict:
        try: self.public_key.verify(base64.b64decode(signature_b64),manifest_bytes)
        except Exception as e: raise UpdateVerificationError('manifest signature invalid') from e
        return json.loads(manifest_bytes)
    @staticmethod
    def verify_file(path:Path,expected_sha256:str):
        h=hashlib.sha256()
        with open(path,'rb') as f:
            for chunk in iter(lambda:f.read(1024*1024),b''): h.update(chunk)
        if h.hexdigest().lower()!=expected_sha256.lower(): raise UpdateVerificationError('package hash mismatch')
    def stage_zip(self,zip_path:Path,expected_sha256:str)->Path:
        self.verify_file(zip_path,expected_sha256); stage=Path(tempfile.mkdtemp(prefix='personal-ai-update-'))
        with zipfile.ZipFile(zip_path) as z:
            for info in z.infolist():
                dest=(stage/info.filename).resolve()
                if stage.resolve() not in dest.parents and dest!=stage.resolve(): raise UpdateVerificationError('unsafe zip path')
            z.extractall(stage)
        return stage
    def install_staged(self,stage:Path):
        backup=self.install_dir.with_name(self.install_dir.name+'.backup')
        if backup.exists(): shutil.rmtree(backup)
        if self.install_dir.exists(): shutil.copytree(self.install_dir,backup)
        try:
            self.install_dir.mkdir(parents=True,exist_ok=True)
            for src in Path(stage).rglob('*'):
                rel=src.relative_to(stage); dst=self.install_dir/rel
                if src.is_dir(): dst.mkdir(parents=True,exist_ok=True)
                else: dst.parent.mkdir(parents=True,exist_ok=True); shutil.copy2(src,dst)
        except Exception:
            if backup.exists(): shutil.rmtree(self.install_dir,ignore_errors=True); shutil.copytree(backup,self.install_dir)
            raise
        return backup
