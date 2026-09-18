from pathlib import Path
from tools.registry import Tool, Risk


def register(reg, data_dir):
    root=(Path(data_dir)/"screenshots").expanduser().resolve()
    root.mkdir(parents=True,exist_ok=True)

    def safe_output(raw):
        value=str(raw or "latest.png").strip()
        candidate=Path(value).expanduser()
        if not candidate.is_absolute():
            candidate=root/candidate
        candidate=candidate.resolve()
        if candidate != root and root not in candidate.parents:
            raise PermissionError('screenshot output must remain inside the Personal AI screenshot directory')
        if candidate.suffix.lower() != '.png':
            raise ValueError('screenshot output must be a .png file')
        candidate.parent.mkdir(parents=True,exist_ok=True)
        return candidate

    def shot(p):
        import mss
        from PIL import Image
        path=safe_output(p.get("path"))
        with mss.mss() as sct:
            monitor=max(1,min(int(p.get("monitor",1)),len(sct.monitors)-1))
            mon=sct.monitors[monitor]
            raw=sct.grab(mon)
            Image.frombytes("RGB", raw.size, raw.rgb).save(path)
        return {"ok":True,"path":str(path)}
    reg.register(Tool("screenshot","Capture monitor screenshot into Personal AI internal screenshot storage; params: path, monitor",shot,Risk.READ_ONLY))
