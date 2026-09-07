from __future__ import annotations
import argparse,base64,hashlib,json,os
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

def sha256(path):
    h=hashlib.sha256()
    with open(path,'rb') as f:
        for chunk in iter(lambda:f.read(1024*1024),b''):h.update(chunk)
    return h.hexdigest()
def main():
    p=argparse.ArgumentParser();p.add_argument('--version',required=True);p.add_argument('--output',required=True);p.add_argument('artifacts',nargs='+');a=p.parse_args();key_b64=os.environ['PERSONAL_AI_RELEASE_PRIVATE_KEY_B64'];key=Ed25519PrivateKey.from_private_bytes(base64.b64decode(key_b64));manifest={'version':a.version,'artifacts':[{'name':Path(x).name,'sha256':sha256(x),'size':Path(x).stat().st_size} for x in a.artifacts]};raw=json.dumps(manifest,sort_keys=True,separators=(',',':')).encode();out=Path(a.output);out.write_bytes(raw);out.with_suffix(out.suffix+'.sig').write_text(base64.b64encode(key.sign(raw)).decode())
if __name__=='__main__':main()
