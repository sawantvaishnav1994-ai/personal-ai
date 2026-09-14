from __future__ import annotations

from pathlib import Path

from browser.safe_operator import PlaywrightBrowserAdapter, SafeBrowserOperator
from browser.session import PersistentBrowser
from tools.registry import Tool, Risk


def register(reg):
    settings = reg.settings
    data_dir = Path(getattr(settings, 'data_dir', Path.home() / '.personal-ai'))
    browser = getattr(reg, '_persistent_browser', None)
    if browser is None:
        browser = PersistentBrowser(data_dir / 'browser-profile', headless=bool(getattr(settings, 'browser_headless', False)))
        reg._persistent_browser = browser
    operator = SafeBrowserOperator(reg, PlaywrightBrowserAdapter(browser), download_root=data_dir / 'downloads')
    reg._safe_browser_operator = operator

    def approved_roots(parameters, operation='read'):
        context = dict(parameters.get('_trusted_context') or {})
        owner = str(context.get('owner_id') or '')
        if not owner:
            return []
        roots = []
        for policy in reg.policy_snapshot(owner).get('policies', []):
            if not policy.get('active') or policy.get('target_type') != 'path':
                continue
            allowed = set(policy.get('allowed_operations') or [])
            if operation not in allowed and '*' not in allowed and 'read' not in allowed:
                continue
            root = str((policy.get('target_identity') or {}).get('root') or '')
            if root:
                roots.append(root)
        return roots

    def prep(action, tool_name, *, upload=False):
        def prepare(parameters):
            params = dict(parameters or {})
            if upload:
                params.pop('approved_roots', None)
            prepared = operator.prepare(action, params)
            prepared['_policy_tool_name'] = tool_name
            if upload:
                prepared['approved_roots'] = approved_roots(prepared, 'read')
                if not prepared['approved_roots']:
                    raise PermissionError('upload path is not covered by an owner-approved path policy')
            return prepared
        return prepare

    def handler(action):
        return lambda p: operator.execute(action, p)

    def add(name, description, action, risk, policy_operation, *, target_type='domain', reauth=False, upload=False, verification=True):
        reg.register(Tool(
            name, description, handler(action), risk,
            verification_required=verification,
            requires_reauth=reauth,
            minimum_risk=risk,
            prepare=prep(action, name, upload=upload),
            requires_trusted_context=True,
            policy_operation=policy_operation,
            policy_target_type=target_type,
        ))

    add('browser_navigate', 'Open one owner-approved URL through the safe browser operator; params: url,timeout_ms', 'navigate', Risk.EXTERNAL_SIDE_EFFECT, 'navigate')
    add('browser_back', 'Navigate back in the bound browser tab.', 'back', Risk.REVERSIBLE, 'navigate')
    add('browser_forward', 'Navigate forward in the bound browser tab.', 'forward', Risk.REVERSIBLE, 'navigate')
    add('browser_refresh', 'Refresh the bound browser tab.', 'refresh', Risk.REVERSIBLE, 'navigate')
    add('browser_create_tab', 'Create a browser tab; optional params: url.', 'create_tab', Risk.REVERSIBLE, 'navigate')
    add('browser_select_tab', 'Select an existing bound browser tab; params: tab_id.', 'select_tab', Risk.REVERSIBLE, 'navigate')
    add('browser_close_tab', 'Close the currently bound browser tab.', 'close_tab', Risk.REVERSIBLE, 'navigate')
    add('browser_click', 'Click one fresh stable target_id only; params: target_id.', 'click', Risk.EXTERNAL_SIDE_EFFECT, 'control')
    add('browser_type', 'Type non-secret text into one fresh stable field; params: target_id,text.', 'type', Risk.EXTERNAL_SIDE_EFFECT, 'application_input')
    add('browser_select_option', 'Select an option in one stable select field; params: target_id,value.', 'select_option', Risk.EXTERNAL_SIDE_EFFECT, 'application_input')
    add('browser_check', 'Check/uncheck one stable checkbox; params: target_id,checked.', 'check', Risk.EXTERNAL_SIDE_EFFECT, 'application_input')
    add('browser_scroll', 'Bounded scroll in current tab; params: dx,dy.', 'scroll', Risk.REVERSIBLE, 'read')
    add('browser_wait', 'Wait for one bounded stable target condition; params: target_id,state,timeout_ms.', 'wait', Risk.READ_ONLY, 'read')
    add('browser_extract_text', 'Extract bounded visible text/accessibility data from current approved page.', 'extract_visible', Risk.READ_ONLY, 'read')
    add('browser_submit_form', 'Explicitly submit an approved form through a stable submit target; params: target_id.', 'click', Risk.EXTERNAL_SIDE_EFFECT, 'form_submission')
    add('browser_upload_file', 'Upload one owner-approved local file to the approved page; params: target_id,file_path,claimed_mime,max_bytes.', 'upload_file', Risk.EXTERNAL_SIDE_EFFECT, 'external_upload', upload=True)

    # Retain the old tool name only as an explicit fail-closed compatibility marker.
    reg.register(Tool('browser_click_text', 'Legacy text-based browser clicking is disabled; use browser_click with a stable target_id.', lambda p: (_ for _ in ()).throw(PermissionError('text-based browser clicking is disabled; stable target_id required')), Risk.EXTERNAL_SIDE_EFFECT, prohibited=True))
    return operator
