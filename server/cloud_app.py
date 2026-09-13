from __future__ import annotations
from contextlib import asynccontextmanager
import asyncio
import json
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
    evaluation_task = None
    if settings.model_evaluation_on_startup:
        async def evaluate_model():
            result = await asyncio.to_thread(runtime['model_evaluation'].run)
            safe = {key: value for key, value in result.items() if key != 'cases'}
            safe['case_results'] = [
                {'case': item['case'], 'passed': item['passed'], 'error_code': item['error_code']}
                for item in result['cases']
            ]
            print(json.dumps({'event': 'model.dialogue_evaluation', **safe}), flush=True)
        evaluation_task = asyncio.create_task(evaluate_model())
    try:
        yield
    finally:
        if evaluation_task and not evaluation_task.done():
            evaluation_task.cancel()
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
