from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import ValidationError
import asyncio
from .planner import Goal, classify, make_plan, guard
from . import demo

app = FastAPI(title='Sahaj MVP')

@app.get('/health')
def health():
    return {'status': 'ok', 'mode': 'local-demo'}

@app.get('/', response_class=HTMLResponse)
def home():
    return demo.page('Sahaj demonstration', '<p>Open the Sahaj Chrome side panel to run a guided task.</p><p>Try “Book a bus ticket”, “Pay my electricity bill”, or “Compare bus fares”.</p>')

@app.get('/demo/{kind}', response_class=HTMLResponse)
def demo_page(kind: str):
    pages = {'bus': demo.bus, 'bill': demo.bill, 'scheme': demo.scheme}
    if kind not in pages:
        raise HTTPException(404)
    return pages[kind]()

@app.get('/demo/provider/{key}', response_class=HTMLResponse)
def provider(key: str):
    if key not in demo.OFFERS:
        raise HTTPException(404)
    return demo.provider(key)

@app.websocket('/ws')
async def agent(ws: WebSocket):
    origin = ws.headers.get('origin', '')
    # Local development only; not a production authentication mechanism.
    if not origin.startswith('chrome-extension://'):
        await ws.close(code=1008)
        return
    await ws.accept()
    async def emit(kind, **fields):
        await ws.send_json({'type': kind, **fields})
    try:
        data = Goal.model_validate(await asyncio.wait_for(ws.receive_json(), 15))
        intent = data.intent or classify(data.goal)
        if not intent:
            await emit('error', message='Please select a demo task: bus, bill, scheme, or comparison.')
            return
        plan = make_plan(intent)
        await emit('plan', intent=intent, steps=[s.model_dump() for s in plan])
        for index, step in enumerate(plan):
            if not guard(intent, index, step):
                await emit('error', message='Action blocked by server guard.')
                return
            await emit('step', index=index, intent=intent, step=step.model_dump())
            ack = await asyncio.wait_for(ws.receive_json(), 60)
            if not isinstance(ack, dict) or ack.get('index') != index or ack.get('ok') is not True:
                await emit('error', message='Execution stopped. No further action will be attempted.')
                return
        await emit('done', message='Demo complete. You remain in control.')
    except (ValidationError, ValueError, TypeError):
        await emit('error', message='Invalid request.')
    except asyncio.TimeoutError:
        await emit('error', message='Timed out; execution stopped.')
    except WebSocketDisconnect:
        pass
    finally:
        try:
            await ws.close()
        except RuntimeError:
            pass
