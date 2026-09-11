from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.main import build_runtime
from core.config import settings
from server.api import create_app

runtime = build_runtime()


@asynccontextmanager
async def lifespan(app):
    runtime['automations'].start()
    try:
        yield
    finally:
        runtime['voice'].stop()
        runtime['automations'].stop()
        runtime['telemetry'].persist()
        runtime['apns'].close()


app = create_app(
    runtime['executor'],
    settings,
    device_registry=runtime['device_registry'],
    device_gateway=runtime['device_gateway'],
    second_brain=runtime['second_brain'],
    automations=runtime['automations'],
    runtime=runtime,
)
app.router.lifespan_context = lifespan

# Serve the real Personal AI responsive web companion from the same Railway
# service as the API. This keeps one production URL and avoids detached UI
# previews. API routes above remain authoritative; the static app is mounted
# only after those routes are registered.
WEB_COMPANION = Path(__file__).resolve().parent.parent / 'web-companion'

if WEB_COMPANION.exists():
    @app.get('/', include_in_schema=False)
    async def personal_ai_home():
        return FileResponse(WEB_COMPANION / 'index.html')

    @app.get('/styles.css', include_in_schema=False)
    async def personal_ai_styles():
        return FileResponse(WEB_COMPANION / 'styles.css', media_type='text/css')

    @app.get('/app.js', include_in_schema=False)
    async def personal_ai_app_js():
        return FileResponse(WEB_COMPANION / 'app.js', media_type='application/javascript')

    @app.get('/manifest.webmanifest', include_in_schema=False)
    async def personal_ai_manifest():
        return FileResponse(
            WEB_COMPANION / 'manifest.webmanifest',
            media_type='application/manifest+json',
        )

    @app.get('/sw.js', include_in_schema=False)
    async def personal_ai_service_worker():
        return FileResponse(WEB_COMPANION / 'sw.js', media_type='application/javascript')

    assets = WEB_COMPANION / 'assets'
    if assets.exists():
        app.mount('/assets', StaticFiles(directory=assets), name='personal-ai-assets')
