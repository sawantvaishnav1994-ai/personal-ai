from __future__ import annotations

import hashlib
import json
import time
from urllib.parse import urlparse

MAX_VISIBLE_TEXT = 20000
MAX_DOM_CHARS = 30000
MAX_ELEMENTS = 200


def _hash_text(value: str) -> str:
    return hashlib.sha256(str(value or '').encode('utf-8')).hexdigest()


def _safe_url(url: str) -> dict:
    parsed = urlparse(str(url or ''))
    return {
        'url': str(url or '')[:4096],
        'scheme': parsed.scheme,
        'domain': (parsed.hostname or '').casefold(),
        'port': parsed.port,
        'path': parsed.path[:2048],
    }


def observe_page(page, *, max_text: int = MAX_VISIBLE_TEXT, max_elements: int = MAX_ELEMENTS) -> dict:
    """Capture bounded, value-redacted browser context from an already open page.

    Password/input values, cookies, storage and script contents are never
    collected. This is an on-demand snapshot only; no background observer is
    installed.
    """
    now = time.time()
    url_info = _safe_url(page.url)
    title = str(page.title() or '')[:1000]
    visible = str(page.locator('body').inner_text(timeout=5000) or '')[:max(0, min(int(max_text), MAX_VISIBLE_TEXT))]
    script = '''(limit) => {
      const nodes = Array.from(document.querySelectorAll('a,button,input,textarea,select,[role],[contenteditable="true"]')).slice(0, limit);
      return nodes.map((el, index) => {
        const rect = el.getBoundingClientRect();
        const type = (el.getAttribute('type') || '').toLowerCase();
        const sensitive = type === 'password' || /password|secret|token|otp|passcode/i.test(el.getAttribute('name') || '') || /password|secret|token|otp|passcode/i.test(el.getAttribute('autocomplete') || '');
        return {
          index,
          tag: el.tagName.toLowerCase(),
          role: el.getAttribute('role') || '',
          type,
          name: (el.getAttribute('name') || '').slice(0,120),
          label: (el.getAttribute('aria-label') || el.getAttribute('title') || '').slice(0,300),
          text: sensitive ? '[REDACTED]' : (el.innerText || el.textContent || '').trim().slice(0,500),
          placeholder: sensitive ? '[REDACTED]' : (el.getAttribute('placeholder') || '').slice(0,300),
          sensitive,
          visible: !!(rect.width && rect.height),
          box: {x: rect.x, y: rect.y, width: rect.width, height: rect.height}
        };
      });
    }'''
    try:
        elements = page.evaluate(script, max(1, min(int(max_elements), MAX_ELEMENTS))) or []
    except Exception:
        elements = []
    sensitive_regions = [
        item['box'] for item in elements
        if item.get('sensitive') and item.get('visible') and isinstance(item.get('box'), dict)
    ]
    try:
        sanitized_dom = page.evaluate('''() => {
          const root = document.documentElement.cloneNode(true);
          root.querySelectorAll('script,style,noscript').forEach(n => n.remove());
          root.querySelectorAll('input,textarea').forEach(n => {
            n.removeAttribute('value'); n.textContent = '';
            if ((n.getAttribute('type') || '').toLowerCase() === 'password') n.setAttribute('placeholder','[REDACTED]');
          });
          return root.outerHTML;
        }''') or ''
        sanitized_dom = str(sanitized_dom)[:MAX_DOM_CHARS]
    except Exception:
        sanitized_dom = ''
    try:
        pages = list(page.context.pages)
        tab_index = pages.index(page)
        tab_count = len(pages)
    except Exception:
        tab_index = 0; tab_count = 1
    try:
        accessibility = page.locator('body').aria_snapshot(timeout=5000)
        accessibility = str(accessibility or '')[:MAX_DOM_CHARS]
        accessibility_available = bool(accessibility)
    except Exception:
        accessibility = ''
        accessibility_available = False
    return {
        'captured_at': now,
        'browser': 'chromium',
        'tab_index': tab_index,
        'tab_count': tab_count,
        'title': title,
        **url_info,
        'visible_text': visible,
        'visible_text_sha256': _hash_text(visible),
        'elements': elements,
        'dom': sanitized_dom,
        'dom_sha256': _hash_text(sanitized_dom),
        'accessibility': accessibility,
        'accessibility_available': accessibility_available,
        'sensitive_regions': sensitive_regions,
    }


def safe_browser_evidence(snapshot: dict) -> dict:
    """Return identifiers/hashes only for durable transaction evidence."""
    return {
        'captured_at': snapshot.get('captured_at'),
        'browser': snapshot.get('browser'),
        'tab_index': snapshot.get('tab_index'),
        'tab_count': snapshot.get('tab_count'),
        'title': str(snapshot.get('title') or '')[:500],
        'domain': snapshot.get('domain'),
        'scheme': snapshot.get('scheme'),
        'path': str(snapshot.get('path') or '')[:1000],
        'visible_text_sha256': snapshot.get('visible_text_sha256'),
        'dom_sha256': snapshot.get('dom_sha256'),
        'accessibility_available': bool(snapshot.get('accessibility_available')),
        'element_count': len(snapshot.get('elements') or []),
        'sensitive_region_count': len(snapshot.get('sensitive_regions') or []),
    }
