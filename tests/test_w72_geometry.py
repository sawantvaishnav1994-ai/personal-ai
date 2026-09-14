import pytest

from desktop.evidence_geometry import CoordinateSpace, GeometryContext, GeometryError, Rect, clip_rect, document_rect_to_screenshot, viewport_rect_to_screenshot


def _ctx(**changes):
    values = dict(device_pixel_ratio=1.0, page_zoom=1.0, browser_window_x=100.0, browser_window_y=50.0, content_offset_x=8.0, content_offset_y=80.0, monitor_scale=1.0, screenshot_origin_x=0.0, screenshot_origin_y=0.0, screenshot_width=1920.0, screenshot_height=1080.0, scroll_x=0.0, scroll_y=0.0)
    values.update(changes)
    return GeometryContext(**values)


@pytest.mark.parametrize('scale', [1.0, 2.0, 3.0])
def test_device_pixel_ratio(scale):
    mapped = viewport_rect_to_screenshot(Rect(10, 20, 30, 40, CoordinateSpace.BROWSER_VIEWPORT), _ctx(device_pixel_ratio=scale))
    assert mapped.width == pytest.approx(30 * scale)


def test_scroll_and_clipping():
    mapped = document_rect_to_screenshot(Rect(100, 220, 20, 20, CoordinateSpace.BROWSER_DOCUMENT), _ctx(scroll_x=40, scroll_y=200))
    assert mapped == viewport_rect_to_screenshot(Rect(60, 20, 20, 20, CoordinateSpace.BROWSER_VIEWPORT), _ctx(scroll_x=40, scroll_y=200))
    clipped = clip_rect(Rect(-10, -5, 25, 20, CoordinateSpace.SCREENSHOT_IMAGE), 100, 100)
    assert clipped and (clipped.x, clipped.y, clipped.width, clipped.height) == (0, 0, 15, 15)


def test_missing_mapping_rejected():
    with pytest.raises(GeometryError):
        viewport_rect_to_screenshot(Rect(1, 1, 10, 10, CoordinateSpace.BROWSER_VIEWPORT), GeometryContext(screenshot_width=100, screenshot_height=100))
