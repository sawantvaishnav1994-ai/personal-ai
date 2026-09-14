from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Iterable

COORDINATE_SPACE_VERSION = 1


class CoordinateSpace(str, Enum):
    BROWSER_VIEWPORT = 'browser_viewport'
    BROWSER_DOCUMENT = 'browser_document'
    BROWSER_WINDOW = 'browser_window'
    PHYSICAL_MONITOR = 'physical_monitor'
    VIRTUAL_DESKTOP = 'virtual_desktop'
    SCREENSHOT_IMAGE = 'screenshot_image'


@dataclass(frozen=True)
class Rect:
    x: float
    y: float
    width: float
    height: float
    space: CoordinateSpace

    def valid(self) -> bool:
        return all(isinstance(v, (int, float)) for v in (self.x, self.y, self.width, self.height)) and self.width > 0 and self.height > 0


@dataclass(frozen=True)
class GeometryContext:
    device_pixel_ratio: float | None = None
    page_zoom: float | None = None
    viewport_width: float | None = None
    viewport_height: float | None = None
    scroll_x: float | None = None
    scroll_y: float | None = None
    browser_window_x: float | None = None
    browser_window_y: float | None = None
    browser_window_width: float | None = None
    browser_window_height: float | None = None
    content_offset_x: float | None = None
    content_offset_y: float | None = None
    monitor_x: float | None = None
    monitor_y: float | None = None
    monitor_width: float | None = None
    monitor_height: float | None = None
    monitor_scale: float | None = None
    virtual_origin_x: float | None = None
    virtual_origin_y: float | None = None
    screenshot_origin_x: float | None = None
    screenshot_origin_y: float | None = None
    screenshot_width: float | None = None
    screenshot_height: float | None = None
    capture_source: str = ''

    def complete_for_viewport_to_screenshot(self) -> bool:
        values = (
            self.device_pixel_ratio, self.page_zoom,
            self.browser_window_x, self.browser_window_y,
            self.content_offset_x, self.content_offset_y,
            self.monitor_scale, self.screenshot_origin_x, self.screenshot_origin_y,
            self.screenshot_width, self.screenshot_height,
        )
        return all(v is not None for v in values) and all(float(v) > 0 for v in (self.device_pixel_ratio, self.page_zoom, self.monitor_scale, self.screenshot_width, self.screenshot_height))

    def as_dict(self) -> dict:
        return {key: getattr(self, key) for key in self.__dataclass_fields__}


class GeometryError(ValueError):
    pass


def _finite(value: float) -> bool:
    try:
        return float('-inf') < float(value) < float('inf')
    except Exception:
        return False


def clip_rect(rect: Rect, width: float, height: float) -> Rect | None:
    if rect.space is not CoordinateSpace.SCREENSHOT_IMAGE or not rect.valid() or not all(_finite(v) for v in (rect.x, rect.y, rect.width, rect.height, width, height)):
        return None
    left = max(0.0, float(rect.x)); top = max(0.0, float(rect.y))
    right = min(float(width), float(rect.x) + float(rect.width)); bottom = min(float(height), float(rect.y) + float(rect.height))
    if right <= left or bottom <= top:
        return None
    return Rect(left, top, right-left, bottom-top, CoordinateSpace.SCREENSHOT_IMAGE)


def viewport_rect_to_screenshot(rect: Rect, context: GeometryContext) -> Rect:
    if rect.space is not CoordinateSpace.BROWSER_VIEWPORT:
        raise GeometryError('rectangle is not in browser viewport coordinates')
    if not rect.valid() or not context.complete_for_viewport_to_screenshot():
        raise GeometryError('coordinate mapping inputs are incomplete')
    # Browser viewport CSS pixels -> virtual/physical screenshot pixels. Page scroll does not
    # translate viewport-relative element boxes; it is recorded for provenance and document mapping.
    browser_scale = float(context.device_pixel_ratio) * float(context.page_zoom)
    os_scale = float(context.monitor_scale)
    x = (float(context.browser_window_x) + float(context.content_offset_x) + float(rect.x)) * browser_scale * os_scale
    y = (float(context.browser_window_y) + float(context.content_offset_y) + float(rect.y)) * browser_scale * os_scale
    x -= float(context.screenshot_origin_x)
    y -= float(context.screenshot_origin_y)
    return Rect(x, y, float(rect.width) * browser_scale * os_scale, float(rect.height) * browser_scale * os_scale, CoordinateSpace.SCREENSHOT_IMAGE)


def document_rect_to_screenshot(rect: Rect, context: GeometryContext) -> Rect:
    if rect.space is not CoordinateSpace.BROWSER_DOCUMENT:
        raise GeometryError('rectangle is not in browser document coordinates')
    if context.scroll_x is None or context.scroll_y is None:
        raise GeometryError('document scroll offsets are unavailable')
    viewport = Rect(float(rect.x)-float(context.scroll_x), float(rect.y)-float(context.scroll_y), rect.width, rect.height, CoordinateSpace.BROWSER_VIEWPORT)
    return viewport_rect_to_screenshot(viewport, context)


def transform_sensitive_rectangles(rectangles: Iterable[Rect], context: GeometryContext) -> list[Rect]:
    transformed: list[Rect] = []
    for rect in rectangles:
        if rect.space is CoordinateSpace.BROWSER_VIEWPORT:
            mapped = viewport_rect_to_screenshot(rect, context)
        elif rect.space is CoordinateSpace.BROWSER_DOCUMENT:
            mapped = document_rect_to_screenshot(rect, context)
        elif rect.space is CoordinateSpace.SCREENSHOT_IMAGE:
            mapped = rect
        else:
            raise GeometryError(f'unsupported redaction coordinate space: {rect.space.value}')
        clipped = clip_rect(mapped, float(context.screenshot_width or 0), float(context.screenshot_height or 0))
        if clipped is not None:
            transformed.append(clipped)
    return transformed
