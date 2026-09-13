from __future__ import annotations
from contextlib import asynccontextmanager
from app.main import build_runtime
from core.config import settings
from server.api import create_app
from server.iphone_pwa import iphone_pwa_router
from server.owner_product import owner_product_router
from server.capability_console import capability_console_router

runtime=build_runtime()

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

app=create_app(
    runtime['executor'],
    settings,
    device_registry=runtime['device_registry'],
    device_gateway=runtime['device_gateway'],
    second_brain=runtime['second_brain'],
    automations=runtime['automations'],
    runtime=runtime,
)
app.include_router(iphone_pwa_router(runtime, settings))
app.include_router(owner_product_router(runtime))
app.include_router(capability_console_router(runtime))
app.router.lifespan_context=lifespan
