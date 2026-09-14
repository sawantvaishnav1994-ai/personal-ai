from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
import re
import time
from typing import Any

from browser.observation import observe_page, safe_browser_evidence
from security.policy_targets import TargetValidationError, canonical_path, normalize_origin, validate_file_metadata


class BrowserSafetyError(PermissionError):
    def __init__(self, reason_code: str, message: str | None = None):
        self.reason_code = str(reason_code)
        super().__init__(message or self.reason_code)


class BrowserRecoveryRequired(RuntimeError):
    reason_code = 'recovery_review_required'


@dataclass(frozen=True)
class TargetSnapshot:
    target_id: str
    geometry_digest: str
    path: str
    tag: str
    role: str
    field_type: str
    sensitive: bool
    actionable: bool


_SENSITIVE_FIELD = re.compile(r'password|passwd|secret|token|otp|one[-_ ]?time|passcode|pin|cvv|cvc|cc-number|payment|private[-_ ]?key', re.I)
_CAPTCHA_MFA = re.compile(r'captcha|recaptcha|hcaptcha|multi[- ]?factor|two[- ]?factor|2fa|security challenge|verification code', re.I)
_LEGAL = re.compile(r'accept|agree|terms|conditions|privacy policy|legal', re.I)
_UNSAFE_DOWNLOAD = re.compile(r'[<>:"|?*\x00-\x1f]')
_SIDE_EFFECT_ACTIONS = {'submit_form', 'upload_file', 'download_file'}


def _digest(value: Any) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False, default=str)
    return hashlib.sha256(raw.encode('utf-8')).hexdigest()


def _public_params(parameters: dict) -> dict:
    return {str(k): v for k, v in dict(parameters or {}).items() if not str(k).startswith('_')}


def _field_sensitive(element: dict) -> bool:
    if bool(element.get('sensitive')):
        return True
    text = ' '.join(str(element.get(key) or '') for key in ('type', 'name', 'label', 'placeholder', 'text'))
    return bool(_SENSITIVE_FIELD.search(text))


def _field_requires_owner(element: dict) -> str | None:
    text = ' '.join(str(element.get(key) or '') for key in ('type', 'name', 'label', 'placeholder', 'text'))
    if _CAPTCHA_MFA.search(text):
        return 'security_challenge_requires_owner'
    if _LEGAL.search(text) and str(element.get('tag') or '').lower() in {'button', 'input', 'a'}:
        return 'legal_acceptance_requires_owner'
    return None


class PlaywrightBrowserAdapter:
    """Thin adapter around the existing persistent browser session.

    No background monitoring is installed. Observations are captured only for an
    explicit operation/verification step.
    """
    def __init__(self, persistent_browser):
        self.browser = persistent_browser

    def start(self):
        self.browser.start(); return self

    @property
    def page(self):
        self.start(); return self.browser.page

    def observe(self) -> dict:
        return observe_page(self.page)

    def application_identity(self) -> dict:
        self.start()
        try:
            executable = str(self.browser._pw.chromium.executable_path)
            from security.policy_targets import application_identity
            return application_identity(executable, publisher='Playwright Chromium')
        except Exception as exc:
            raise BrowserSafetyError('application_not_allowed', 'Browser executable identity cannot be verified.') from exc

    def navigate(self, url: str, timeout_ms: int):
        response = self.page.goto(url, wait_until='domcontentloaded', timeout=timeout_ms)
        return {'url': self.page.url, 'status': getattr(response, 'status', None)}

    def go_back(self, timeout_ms: int):
        response = self.page.go_back(wait_until='domcontentloaded', timeout=timeout_ms)
        return {'url': self.page.url, 'status': getattr(response, 'status', None)}

    def go_forward(self, timeout_ms: int):
        response = self.page.go_forward(wait_until='domcontentloaded', timeout=timeout_ms)
        return {'url': self.page.url, 'status': getattr(response, 'status', None)}

    def refresh(self, timeout_ms: int):
        response = self.page.reload(wait_until='domcontentloaded', timeout=timeout_ms)
        return {'url': self.page.url, 'status': getattr(response, 'status', None)}

    def create_tab(self, url: str | None = None, timeout_ms: int = 10000):
        page = self.page.context.new_page(); self.browser.page = page
        if url:
            page.goto(url, wait_until='domcontentloaded', timeout=timeout_ms)
        return {'url': page.url}

    def select_tab(self, tab_id: str):
        for page in list(self.page.context.pages):
            obs = observe_page(page)
            if obs.get('tab_id') == tab_id:
                self.browser.page = page; page.bring_to_front(); return {'url': page.url}
        raise BrowserSafetyError('tab_changed', 'The requested browser tab is no longer available.')

    def close_tab(self):
        page = self.page; context = page.context; page.close()
        pages = list(context.pages)
        self.browser.page = pages[-1] if pages else context.new_page()
        return {'url': self.browser.page.url}

    def locator(self, path: str):
        return self.page.locator(path)

    def click(self, path: str):
        self.locator(path).click(timeout=10000)

    def fill(self, path: str, value: str):
        self.locator(path).fill(value, timeout=10000)

    def select_option(self, path: str, value: str):
        return self.locator(path).select_option(value, timeout=10000)

    def check(self, path: str, checked: bool):
        locator = self.locator(path)
        (locator.check if checked else locator.uncheck)(timeout=10000)

    def scroll(self, dx: int, dy: int):
        self.page.mouse.wheel(int(dx), int(dy))

    def wait_for(self, path: str, state: str, timeout_ms: int):
        self.locator(path).wait_for(state=state, timeout=timeout_ms)

    def set_input_files(self, path: str, file_path: str):
        self.locator(path).set_input_files(file_path, timeout=10000)


class SafeBrowserOperator:
    """W7.4 bounded browser operator.

    Execution authority remains W7.1 Trusted Action + W7.3 PolicyGateway. This
    class performs fresh W7.2 observations, stable-target verification, dispatch,
    postcondition verification and redacted evidence only.
    """
    def __init__(self, registry, adapter, *, download_root: Path | None = None, observation_ttl_seconds: int = 30):
        self.registry = registry
        self.adapter = adapter
        self.download_root = Path(download_root) if download_root else None
        self.observation_ttl_seconds = max(5, min(int(observation_ttl_seconds), 120))

    def _observe(self) -> dict:
        observation = self.adapter.observe()
        observation['observation_digest'] = _digest(safe_browser_evidence(observation))
        return observation

    @staticmethod
    def _element(observation: dict, target_id: str) -> dict:
        matches = [e for e in observation.get('elements', []) if e.get('target_id') == target_id]
        if len(matches) != 1:
            raise BrowserSafetyError('element_changed', 'The approved page element is missing or no longer unique.')
        return dict(matches[0])

    @staticmethod
    def _target_snapshot(element: dict) -> TargetSnapshot:
        return TargetSnapshot(
            str(element.get('target_id') or ''), str(element.get('geometry_digest') or ''), str(element.get('path') or ''),
            str(element.get('tag') or ''), str(element.get('role') or ''), str(element.get('type') or ''),
            _field_sensitive(element), bool(element.get('actionable')),
        )

    def _assert_observation_fresh(self, prepared: dict, fresh: dict, *, require_origin: bool = True):
        captured = float(prepared.get('_observation_captured_at') or 0)
        if captured and time.time() - captured > self.observation_ttl_seconds:
            raise BrowserSafetyError('observation_expired', 'The browser observation expired before dispatch.')
        for key, code in (('_browser_context_id', 'browser_session_changed'), ('_tab_id', 'tab_changed')):
            if prepared.get(key) and prepared.get(key) != fresh.get(key[1:] if key.startswith('_') else key):
                actual_key = 'browser_context_id' if key == '_browser_context_id' else 'tab_id'
                if prepared.get(key) != fresh.get(actual_key):
                    raise BrowserSafetyError(code)
        if require_origin and prepared.get('_origin') and prepared.get('_origin') != fresh.get('origin'):
            raise BrowserSafetyError('origin_changed', 'Browser origin changed after authorization.')

    def prepare(self, action: str, parameters: dict) -> dict:
        params = _public_params(parameters)
        action = str(action)
        if action == 'navigate':
            target = str(params.get('url') or '').strip()
            origin = normalize_origin(target)
            before = self._observe()
            params['destination'] = origin.value
            prepared = before
        else:
            prepared = self._observe()
            params['destination'] = str(prepared.get('origin') or '')
        params['_browser_context_id'] = prepared.get('browser_context_id') or ''
        params['_tab_id'] = prepared.get('tab_id') or ''
        params['_origin'] = prepared.get('origin') or ''
        params['_observation_digest'] = prepared.get('observation_digest') or ''
        params['_observation_captured_at'] = float(prepared.get('captured_at') or time.time())
        params['_application'] = self.adapter.application_identity()

        target_id = str(params.get('target_id') or '')
        if target_id:
            element = self._element(prepared, target_id)
            target = self._target_snapshot(element)
            if not target.actionable:
                raise BrowserSafetyError('element_not_actionable', 'The element is hidden, covered, disabled, sensitive, or otherwise unsafe.')
            owner_reason = _field_requires_owner(element)
            if owner_reason:
                raise BrowserSafetyError(owner_reason)
            params['_target_path'] = target.path
            params['_target_geometry_digest'] = target.geometry_digest
            params['_target_tag'] = target.tag
            params['_target_role'] = target.role
            params['_target_type'] = target.field_type
            params['_target_sensitive'] = target.sensitive
        params['_prepared_action'] = action
        return params

    def _fresh_target(self, params: dict) -> tuple[dict, dict | None]:
        fresh = self._observe()
        self._assert_observation_fresh(params, fresh, require_origin=params.get('_prepared_action') != 'navigate')
        target_id = str(params.get('target_id') or '')
        if not target_id:
            return fresh, None
        element = self._element(fresh, target_id)
        target = self._target_snapshot(element)
        if not target.actionable:
            raise BrowserSafetyError('element_not_actionable')
        if target.geometry_digest != params.get('_target_geometry_digest') or target.path != params.get('_target_path'):
            raise BrowserSafetyError('element_changed', 'Element identity or geometry changed after approval.')
        if target.sensitive:
            raise BrowserSafetyError('sensitive_field_blocked')
        owner_reason = _field_requires_owner(element)
        if owner_reason:
            raise BrowserSafetyError(owner_reason)
        return fresh, element

    def _consume_permit(self, params: dict):
        self.registry.consume_tool_policy_permit(params)

    def execute(self, action: str, parameters: dict) -> dict:
        params = dict(parameters or {})
        if params.get('_prepared_action') != action:
            raise BrowserSafetyError('stale_page', 'Browser action was not prepared from a trusted fresh observation.')
        if getattr(self.registry, 'emergency_stop', False):
            raise BrowserSafetyError('emergency_stop_active')
        timeout_ms = max(100, min(int(params.get('timeout_ms') or 10000), 30000))
        fresh, element = self._fresh_target(params)
        self._consume_permit(params)
        before = safe_browser_evidence(fresh)
        dispatched = False
        try:
            if action == 'navigate':
                initial = str(fresh.get('origin') or '')
                target = str(params.get('url') or '')
                if initial.startswith('https://') and target.startswith('http://'):
                    raise BrowserSafetyError('https_downgrade_blocked')
                dispatched = True; raw = self.adapter.navigate(target, timeout_ms)
            elif action == 'back': dispatched = True; raw = self.adapter.go_back(timeout_ms)
            elif action == 'forward': dispatched = True; raw = self.adapter.go_forward(timeout_ms)
            elif action == 'refresh': dispatched = True; raw = self.adapter.refresh(timeout_ms)
            elif action == 'create_tab': dispatched = True; raw = self.adapter.create_tab(params.get('url'), timeout_ms)
            elif action == 'select_tab': dispatched = True; raw = self.adapter.select_tab(str(params.get('tab_id') or ''))
            elif action == 'close_tab': dispatched = True; raw = self.adapter.close_tab()
            elif action == 'click': dispatched = True; self.adapter.click(str(params['_target_path'])); raw = {}
            elif action == 'type':
                if element is None: raise BrowserSafetyError('element_not_actionable')
                if _field_sensitive(element): raise BrowserSafetyError('sensitive_field_blocked')
                dispatched = True; self.adapter.fill(str(params['_target_path']), str(params.get('text') or '')); raw = {}
            elif action == 'select_option': dispatched = True; raw = {'selected': self.adapter.select_option(str(params['_target_path']), str(params.get('value') or ''))}
            elif action == 'check': dispatched = True; self.adapter.check(str(params['_target_path']), bool(params.get('checked', True))); raw = {}
            elif action == 'scroll': dispatched = True; self.adapter.scroll(int(params.get('dx') or 0), int(params.get('dy') or 0)); raw = {}
            elif action == 'wait': self.adapter.wait_for(str(params['_target_path']), str(params.get('state') or 'visible'), timeout_ms); raw = {}
            elif action == 'extract_visible':
                raw = {'visible_text': str(fresh.get('visible_text') or '')[:20000], 'accessibility': str(fresh.get('accessibility') or '')[:30000]}
            elif action == 'upload_file':
                if element is None or str(element.get('tag')) != 'input': raise BrowserSafetyError('upload_not_allowed')
                file_path = str(params.get('file_path') or '')
                roots = list(params.get('approved_roots') or [])
                canonical = canonical_path(file_path, roots, allow_network=False)
                validate_file_metadata(canonical, claimed_mime=str(params.get('claimed_mime') or ''), max_bytes=int(params.get('max_bytes') or 50*1024*1024))
                dispatched = True; self.adapter.set_input_files(str(params['_target_path']), canonical); raw = {'file_sha256': self._file_hash(canonical)}
            else:
                raise BrowserSafetyError('operation_not_allowed', f'Unsupported browser operation: {action}')
        except TimeoutError as exc:
            if dispatched and action in _SIDE_EFFECT_ACTIONS:
                raise BrowserRecoveryRequired('Consequential browser outcome is uncertain after timeout.') from exc
            raise
        after = self._observe()
        verification = self._verify(action, params, fresh, after)
        return {'verified': verification['verified'], 'reason': verification['reason'], 'evidence': {'before': before, 'after': safe_browser_evidence(after), **verification.get('evidence', {})}, **raw}

    @staticmethod
    def _file_hash(path: str) -> str:
        h = hashlib.sha256()
        with open(path, 'rb') as fh:
            for chunk in iter(lambda: fh.read(1024 * 1024), b''): h.update(chunk)
        return h.hexdigest()

    def _verify(self, action: str, params: dict, before: dict, after: dict) -> dict:
        if action == 'navigate':
            requested = normalize_origin(str(params.get('url') or ''))
            actual = normalize_origin(str(after.get('normalized_url') or after.get('origin') or ''))
            if actual.scheme == 'http' and requested.scheme == 'https':
                raise BrowserSafetyError('https_downgrade_blocked')
            if actual.value != requested.value:
                raise BrowserSafetyError('redirect_not_allowed', 'Navigation ended on an unapproved origin.')
            return {'verified': True, 'reason': 'navigation origin verified'}
        if action in {'back', 'forward', 'refresh', 'create_tab', 'select_tab', 'close_tab'}:
            return {'verified': bool(after.get('browser_context_id') and after.get('tab_id')), 'reason': 'browser context read back'}
        if action == 'type':
            return {'verified': bool(after.get('active_target_id') == params.get('target_id') or self._has_target(after, str(params.get('target_id') or ''))), 'reason': 'field remains bound after input'}
        if action in {'click', 'select_option', 'check', 'scroll', 'wait', 'upload_file'}:
            return {'verified': bool(after.get('browser_context_id') == before.get('browser_context_id')), 'reason': 'fresh browser postcondition observed'}
        return {'verified': True, 'reason': 'read-only fresh observation'}

    @staticmethod
    def _has_target(observation: dict, target_id: str) -> bool:
        return any(e.get('target_id') == target_id for e in observation.get('elements', []))

    @staticmethod
    def sanitize_download_name(name: str) -> str:
        value = os.path.basename(str(name or '')).strip().replace('..', '_')
        value = _UNSAFE_DOWNLOAD.sub('_', value).strip(' .')
        if not value or value in {'.', '..'}: value = 'download.bin'
        return value[:180]

    def confined_download_path(self, filename: str) -> Path:
        if self.download_root is None:
            raise BrowserSafetyError('download_not_allowed', 'No owner-approved download root is configured.')
        root = self.download_root.resolve(); root.mkdir(parents=True, exist_ok=True)
        name = self.sanitize_download_name(filename); candidate = root / name
        stem, suffix = candidate.stem, candidate.suffix; index = 1
        while candidate.exists():
            candidate = root / f'{stem} ({index}){suffix}'; index += 1
        canonical_path(str(candidate), [str(root)])
        return candidate
