from __future__ import annotations

from dataclasses import dataclass
import hashlib
import os
from pathlib import Path
import shutil
import tempfile
from typing import Any

from security.policy_targets import TargetValidationError, canonical_path, validate_file_metadata


@dataclass(frozen=True)
class FileResult:
    status: str
    verified: bool
    rollback: str
    evidence: dict[str, Any]
    reason_code: str = 'allow'


class SafeFileAdapter:
    def __init__(self, *, max_bytes: int = 50 * 1024 * 1024):
        self.max_bytes=int(max_bytes)

    @staticmethod
    def checksum(path: str | os.PathLike) -> str:
        h=hashlib.sha256()
        with open(path,'rb') as fh:
            for chunk in iter(lambda:fh.read(1024*1024),b''): h.update(chunk)
        return h.hexdigest()

    @staticmethod
    def _safe(path: str, roots: list[str], *, must_exist=False) -> Path:
        canonical=canonical_path(path,roots)
        target=Path(canonical)
        if must_exist and not target.exists(): raise FileNotFoundError(canonical)
        for parent in [target,*target.parents]:
            if parent.exists() and parent.is_symlink(): raise TargetValidationError('path_changed','symlink traversal blocked')
        return target

    @staticmethod
    def _free_space(path: Path) -> int:
        probe=path if path.exists() else path.parent
        return shutil.disk_usage(probe).free

    def metadata(self,path:str,roots:list[str])->dict[str,Any]:
        p=self._safe(path,roots,must_exist=True); st=p.stat()
        return {'name':p.name,'size':st.st_size,'is_file':p.is_file(),'is_dir':p.is_dir(),'sha256':self.checksum(p) if p.is_file() else ''}

    def list_dir(self,path:str,roots:list[str],*,limit=500)->list[dict[str,Any]]:
        p=self._safe(path,roots,must_exist=True)
        if not p.is_dir(): raise NotADirectoryError(str(p))
        out=[]
        for child in sorted(p.iterdir(),key=lambda x:x.name.casefold())[:max(0,min(int(limit),500))]:
            if child.is_symlink(): continue
            out.append({'name':child.name,'is_file':child.is_file(),'is_dir':child.is_dir(),'size':child.stat().st_size if child.is_file() else 0})
        return out

    def read_text(self,path:str,roots:list[str],*,max_bytes=1024*1024)->str:
        p=self._safe(path,roots,must_exist=True)
        if not p.is_file(): raise IsADirectoryError(str(p))
        if p.stat().st_size>min(int(max_bytes),self.max_bytes): raise TargetValidationError('file_too_large','bounded file read exceeded')
        if p.suffix.lower() in {'.pdf','.doc','.docx','.ppt','.pptx','.xls','.xlsx','.zip','.exe','.dll','.png','.jpg','.jpeg'}:
            raise TargetValidationError('file_type_not_allowed','binary/structured documents must use Knowledge ingestion')
        return p.read_text(encoding='utf-8')

    def create_dir(self,path:str,roots:list[str])->FileResult:
        p=self._safe(path,roots)
        if p.exists(): raise FileExistsError('destination_exists')
        p.mkdir(parents=False)
        return FileResult('completed',p.is_dir(),'reversible',{'destination':str(p)})

    def create_file(self,path:str,roots:list[str],content:bytes|str=b'',*,claimed_mime='')->FileResult:
        p=self._safe(path,roots)
        if p.exists(): raise FileExistsError('destination_exists')
        data=content.encode('utf-8') if isinstance(content,str) else bytes(content)
        if len(data)>self.max_bytes: raise TargetValidationError('file_too_large','file exceeds configured limit')
        if self._free_space(p)<len(data)+1024*1024: raise OSError('insufficient_disk_space')
        fd,tmp=tempfile.mkstemp(prefix='.pai-',dir=str(p.parent)); os.close(fd); tmp_path=Path(tmp)
        try:
            tmp_path.write_bytes(data); os.replace(tmp_path,p)
            if claimed_mime: validate_file_metadata(str(p),claimed_mime=claimed_mime,max_bytes=self.max_bytes)
        except Exception:
            try: tmp_path.unlink(missing_ok=True)
            except Exception: pass
            try: p.unlink(missing_ok=True)
            except Exception: pass
            raise
        return FileResult('completed',p.exists(),'reversible',{'destination':str(p),'sha256':self.checksum(p),'size':p.stat().st_size})

    def copy(self,source:str,destination:str,roots:list[str],*,claimed_mime='')->FileResult:
        src=self._safe(source,roots,must_exist=True); dst=self._safe(destination,roots)
        if not src.is_file(): raise ValueError('source_not_regular_file')
        if dst.exists(): raise FileExistsError('destination_exists')
        validate_file_metadata(str(src),claimed_mime=claimed_mime,max_bytes=self.max_bytes)
        source_hash=self.checksum(src); size=src.stat().st_size
        if self._free_space(dst)<size+1024*1024: raise OSError('insufficient_disk_space')
        fd,tmp=tempfile.mkstemp(prefix='.pai-copy-',dir=str(dst.parent)); os.close(fd); tmp_path=Path(tmp)
        try:
            with src.open('rb') as r,tmp_path.open('wb') as w: shutil.copyfileobj(r,w,1024*1024)
            if self.checksum(src)!=source_hash: raise PermissionError('path_changed')
            if self.checksum(tmp_path)!=source_hash: raise IOError('checksum_mismatch')
            os.replace(tmp_path,dst)
        except Exception:
            try: tmp_path.unlink(missing_ok=True)
            except Exception: pass
            try: dst.unlink(missing_ok=True)
            except Exception: pass
            raise
        return FileResult('completed',dst.exists() and self.checksum(dst)==source_hash,'reversible',{'source_sha256':source_hash,'destination_sha256':self.checksum(dst),'destination':str(dst)})

    def move(self,source:str,destination:str,roots:list[str])->FileResult:
        src=self._safe(source,roots,must_exist=True); dst=self._safe(destination,roots)
        if dst.exists(): raise FileExistsError('destination_exists')
        source_hash=self.checksum(src) if src.is_file() else ''
        os.replace(src,dst)
        ok=dst.exists() and not src.exists() and (not source_hash or self.checksum(dst)==source_hash)
        return FileResult('completed',ok,'reversible',{'source_sha256':source_hash,'destination':str(dst)})

    def rename(self,source:str,destination:str,roots:list[str])->FileResult:
        return self.move(source,destination,roots)

    def trash(self,path:str,roots:list[str],trash_root:str)->FileResult:
        src=self._safe(path,roots,must_exist=True); tr=self._safe(trash_root,roots,must_exist=True)
        if not tr.is_dir(): raise NotADirectoryError(str(tr))
        candidate=tr/src.name; n=1
        while candidate.exists(): candidate=tr/f'{src.stem} ({n}){src.suffix}'; n+=1
        source_hash=self.checksum(src) if src.is_file() else ''
        os.replace(src,candidate)
        return FileResult('completed',candidate.exists() and not src.exists(),'compensating_action_available',{'trash_path':str(candidate),'source_sha256':source_hash})

    def permanent_delete(self,path:str,roots:list[str])->FileResult:
        target=self._safe(path,roots,must_exist=True)
        if target.is_dir():
            if any(target.iterdir()): raise OSError('non_empty_directory_delete_blocked')
            target.rmdir()
        else: target.unlink()
        return FileResult('completed',not target.exists(),'irreversible',{'target_absent':not target.exists(),'no_rollback':True})
