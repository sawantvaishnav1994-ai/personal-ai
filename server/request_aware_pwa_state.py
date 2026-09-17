from __future__ import annotations

import threading

from server.logical_request_middleware import current_logical_request_id


class RequestAwareIphonePwaState:
    """Process-local cooperative cancellation only; never request authority.

    CanonicalTurnRuntime/SQLite owns logical request identity. This helper merely
    prevents a duplicate transport of the same request from cancelling its first
    in-flight execution while preserving explicit cancellation of that request.
    """

    def __init__(self, cancel_turn=None):
        self._lock = threading.RLock()
        self._active: dict[str, dict] = {}
        self._cancel_turn = cancel_turn

    def begin_turn(self, device_id: str) -> threading.Event:
        request_id = current_logical_request_id()
        with self._lock:
            previous = self._active.get(device_id)
            if previous and request_id and previous.get('request_id') == request_id:
                previous['leases'] += 1
                return previous['event']
            if previous:
                previous['event'].set()
            current = threading.Event()
            self._active[device_id] = {
                'request_id': request_id,
                'event': current,
                'leases': 1,
            }
            return current

    def cancel(self, device_id: str) -> bool:
        with self._lock:
            active = self._active.get(device_id)
            if not active:
                return False
            event = active['event']
            request_id = active.get('request_id')
            event.set()
        if request_id and callable(self._cancel_turn):
            try:
                self._cancel_turn(request_id)
            except Exception:
                pass
        return True

    def finish(self, device_id: str, event: threading.Event):
        with self._lock:
            active = self._active.get(device_id)
            if not active or active.get('event') is not event:
                return
            active['leases'] = max(0, int(active.get('leases', 1)) - 1)
            if active['leases'] == 0:
                self._active.pop(device_id, None)
