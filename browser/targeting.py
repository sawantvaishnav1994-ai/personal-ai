from __future__ import annotations

from dataclasses import dataclass
from typing import Any


class TargetResolutionError(PermissionError):
    def __init__(self, reason_code: str, message: str | None = None):
        self.reason_code = reason_code
        super().__init__(message or reason_code)


@dataclass(frozen=True)
class ResolvedTarget:
    target_id: str
    method: str
    evidence: dict[str, Any]


def _actionable(observation: dict) -> list[dict]:
    return [dict(e) for e in observation.get('elements', []) if e.get('actionable') and e.get('target_id')]


def _by_id(observation: dict, target_id: str) -> ResolvedTarget:
    rows = [e for e in _actionable(observation) if e.get('target_id') == target_id]
    if len(rows) != 1:
        raise TargetResolutionError('element_not_actionable', 'Stable target is missing, ambiguous, hidden, covered or disabled.')
    return ResolvedTarget(target_id, 'dom', {'geometry_digest': rows[0].get('geometry_digest')})


def _accessibility(observation: dict, query: dict) -> ResolvedTarget:
    role = str(query.get('role') or '').strip().casefold()
    name = str(query.get('name') or '').strip().casefold()
    if not role and not name:
        raise TargetResolutionError('accessibility_target_invalid')
    rows = []
    for element in _actionable(observation):
        erole = str(element.get('role') or element.get('tag') or '').casefold()
        ename = ' '.join(str(element.get(k) or '') for k in ('label', 'text', 'placeholder')).strip().casefold()
        if role and role != erole:
            continue
        if name and name not in ename:
            continue
        rows.append(element)
    if len(rows) != 1:
        raise TargetResolutionError('accessibility_target_ambiguous', 'Accessibility target must resolve to exactly one actionable element.')
    return ResolvedTarget(str(rows[0]['target_id']), 'accessibility', {'geometry_digest': rows[0].get('geometry_digest')})


def _visual(observation: dict, visual: dict) -> ResolvedTarget:
    if str(visual.get('redaction_status') or '') != 'sanitized':
        raise TargetResolutionError('visual_evidence_not_sanitized')
    if str(visual.get('observation_digest') or '') != str(observation.get('observation_digest') or ''):
        raise TargetResolutionError('visual_evidence_stale')
    target_id = str(visual.get('target_id') or '')
    box = visual.get('box') if isinstance(visual.get('box'), dict) else None
    resolved = _by_id(observation, target_id)
    row = next(e for e in _actionable(observation) if e.get('target_id') == target_id)
    if box is not None and dict(row.get('box') or {}) != dict(box):
        raise TargetResolutionError('visual_target_changed')
    return ResolvedTarget(target_id, 'verified_visual', {'geometry_digest': row.get('geometry_digest')})


def _coordinate(observation: dict, coordinate: dict) -> ResolvedTarget:
    if str(coordinate.get('observation_digest') or '') != str(observation.get('observation_digest') or ''):
        raise TargetResolutionError('coordinate_evidence_stale')
    try:
        x = float(coordinate['x']); y = float(coordinate['y'])
    except Exception as exc:
        raise TargetResolutionError('coordinate_target_invalid') from exc
    matches = []
    for element in _actionable(observation):
        box = dict(element.get('box') or {})
        try:
            left=float(box['x']); top=float(box['y']); width=float(box['width']); height=float(box['height'])
        except Exception:
            continue
        if width > 0 and height > 0 and left <= x <= left+width and top <= y <= top+height:
            matches.append(element)
    if len(matches) != 1:
        raise TargetResolutionError('coordinate_target_ambiguous', 'Coordinate fallback must map to exactly one actionable element.')
    return ResolvedTarget(str(matches[0]['target_id']), 'restricted_coordinate', {'geometry_digest': matches[0].get('geometry_digest')})


def resolve_target(observation: dict, request: dict) -> ResolvedTarget:
    """DOM → accessibility → verified visual → restricted coordinate.

    Visual and coordinate fallbacks never authorize arbitrary pixels. They must
    map back to exactly one actionable W7.2 element in the same observation.
    """
    target_id = str(request.get('target_id') or '')
    if target_id:
        return _by_id(observation, target_id)
    accessibility = request.get('accessibility_target')
    if isinstance(accessibility, dict):
        return _accessibility(observation, accessibility)
    visual = request.get('visual_target')
    if isinstance(visual, dict):
        return _visual(observation, visual)
    coordinate = request.get('coordinate_target')
    if isinstance(coordinate, dict):
        return _coordinate(observation, coordinate)
    raise TargetResolutionError('target_required', 'A stable DOM/accessibility/verified-visual target is required.')
