from __future__ import annotations

import base64
import hashlib
import io
import os
from pathlib import Path
import re
import time
import uuid


class ScreenUnderstanding:
    def __init__(self, models=None, data_dir: Path | None = None, *, observation_ttl_seconds: int = 120, retention_seconds: int = 86400, max_evidence_files: int = 500):
        self.models = models
        self.data_dir = Path(data_dir or (Path.home() / '.personal_ai'))
        self.observation_ttl_seconds = max(5, min(int(observation_ttl_seconds), 600))
        self.retention_seconds = max(300, int(retention_seconds))
        self.max_evidence_files = max(20, int(max_evidence_files))

    def _evidence_dir(self) -> Path:
        root = self.data_dir
        root.mkdir(parents=True, exist_ok=True)
        if root.is_symlink():
            raise PermissionError('evidence data root cannot be a symlink')
        directory = root / 'screenshots'
        if directory.exists() and directory.is_symlink():
            raise PermissionError('evidence directory cannot be a symlink')
        directory.mkdir(parents=True, exist_ok=True, mode=0o700)
        try:
            os.chmod(directory, 0o700)
        except OSError:
            pass
        return directory

    @staticmethod
    def _clip_redaction(image, box):
        try:
            if bool(box.get('full_screen')):
                return (0, 0, image.width, image.height)
            x = max(0, int(box.get('x', 0))); y = max(0, int(box.get('y', 0)))
            w = max(0, int(box.get('width', 0))); h = max(0, int(box.get('height', 0)))
            right = min(image.width, x + w); bottom = min(image.height, y + h)
            return (x, y, right, bottom) if right > x and bottom > y else None
        except Exception:
            return None

    def _capture_png(self, monitor: int, redactions: list[dict] | None) -> tuple[bytes, int]:
        import mss
        from PIL import Image, ImageDraw
        with mss.mss() as sct:
            if int(monitor) < 0 or int(monitor) >= len(sct.monitors):
                raise ValueError('requested monitor is unavailable')
            mon = sct.monitors[int(monitor)]
            raw = sct.grab(mon)
            image = Image.frombytes('RGB', raw.size, raw.rgb)
        redaction_count = 0
        if redactions:
            draw = ImageDraw.Draw(image)
            for item in list(redactions)[:200]:
                clipped = self._clip_redaction(image, item)
                if clipped:
                    draw.rectangle(clipped, fill=(0, 0, 0)); redaction_count += 1
        buf = io.BytesIO(); image.save(buf, format='PNG')
        return buf.getvalue(), redaction_count

    def _secure_write(self, raw: bytes, observation_id: str) -> Path:
        if not re.fullmatch(r'[A-Za-z0-9_-]{1,96}', str(observation_id or '')):
            raise ValueError('invalid observation evidence identifier')
        directory = self._evidence_dir(); final_path = directory / f'observation-{observation_id}.png'
        if final_path.exists() or final_path.is_symlink():
            raise PermissionError('observation evidence destination collision')
        fd = os.open(final_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        try:
            with os.fdopen(fd, 'wb') as handle:
                handle.write(raw); handle.flush(); os.fsync(handle.fileno())
        except Exception:
            try:
                final_path.unlink(missing_ok=True)
            except OSError:
                pass
            raise
        return final_path

    def _prune(self, directory: Path):
        now = time.time()
        files = sorted((p for p in directory.glob('observation-*.png') if p.is_file() and not p.is_symlink()), key=lambda p: p.stat().st_mtime, reverse=True)
        for index, path in enumerate(files):
            try:
                if index >= self.max_evidence_files or now - path.stat().st_mtime > self.retention_seconds:
                    path.unlink(missing_ok=True)
            except OSError:
                pass

    def capture(self, monitor: int = 1, *, redactions=None, observation_id: str | None = None) -> Path:
        """Compatibility capture API; still on-demand, bounded, redacted-before-write and unique."""
        observation_id = str(observation_id or uuid.uuid4().hex)
        raw, _ = self._capture_png(monitor, redactions)
        path = self._secure_write(raw, observation_id); self._prune(path.parent); return path

    @staticmethod
    def fingerprint(path: Path) -> str:
        return hashlib.sha256(Path(path).read_bytes()).hexdigest()

    def observe_record(self, monitor: int = 1, *, redactions: list[dict] | None = None, application_context=None) -> dict:
        raw, redaction_count = self._capture_png(monitor, redactions)
        observation_id = uuid.uuid4().hex
        final_path = self._secure_write(raw, observation_id)
        captured_at = time.time(); fingerprint = hashlib.sha256(raw).hexdigest(); self._prune(final_path.parent)
        return {
            'observation_id': observation_id,
            'captured_at': captured_at,
            'expires_at': captured_at + self.observation_ttl_seconds,
            'screenshot_evidence_ref': f'screenshots/{final_path.name}',
            'screen_fingerprint': fingerprint,
            'screenshot_sha256': fingerprint,
            'redaction_count': redaction_count,
            'monitor': int(monitor),
            'application_context': dict(application_context or {}),
            '_image_data_url': 'data:image/png;base64,' + base64.b64encode(raw).decode('ascii'),
        }

    def prepare_payload(self, question: str = 'Describe the visible screen.', monitor: int = 1, *, redactions=None, application_context=None):
        """Compatibility transient payload. image_data_url is never part of durable evidence."""
        record = self.observe_record(monitor, redactions=redactions, application_context=application_context)
        return {**record, 'question': str(question), 'image_data_url': record.pop('_image_data_url')}

    def analyze(self, question: str = 'Describe the visible screen and identify actionable UI elements.', monitor: int = 1, *, redactions: list[dict] | None = None, application_context=None):
        record = self.observe_record(monitor, redactions=redactions, application_context=application_context)
        image_data = record.pop('_image_data_url', '')
        if self.models is None:
            return {**record, 'analysis': 'screen captured; no vision model configured'}
        prompt = f"{question}\nUse only visible evidence. If uncertain, say uncertain. Do not infer hidden credentials or secret values."
        response = self.models.vision(prompt, image_data)
        return {**record, 'analysis': response}
