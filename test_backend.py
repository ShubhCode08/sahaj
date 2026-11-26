from fastapi.testclient import TestClient
from backend.main import app
from backend.planner import classify, make_plan, guard, Step
import pytest

client = TestClient(app)
ORIGIN = {'origin':'chrome-extension://test-extension'}

@pytest.mark.parametrize('goal,intent', [('Book a bus ticket','bus'),('Pay electricity bill','bill'),('Find government scheme','scheme'),('Compare bus fares','compare'),('बिजली बिल','bill'),('ಬಸ್ ಟಿಕೆಟ್','bus'),('तुलना बस','compare')])
def test_classification(goal,intent):
    assert classify(goal)==intent

@pytest.mark.parametrize('intent',['bus','bill','scheme','compare'])
def test_protocol(intent):
    with client.websocket_connect('/ws',headers=ORIGIN) as ws:
        ws.send_json({'goal':'sample task','intent':intent})
        msg=ws.receive_json(); assert msg['type']=='plan'; assert msg['intent']==intent
        for i, expected in enumerate(make_plan(intent)):
            msg=ws.receive_json(); assert msg['type']=='step' and msg['index']==i
            assert Step.model_validate(msg['step'])==expected
            ws.send_json({'index':i,'ok':True})
        assert ws.receive_json()['type']=='done'

@pytest.mark.parametrize('intent',['bus','bill','scheme','compare'])
def test_guard_rejects_sensitive_steps(intent):
    for target in ['password','otp','payment','submit','checkout']:
        assert not guard(intent,0,Step(action='click',target=target,narration='unsafe'))
    assert not guard(intent,0,Step(action='navigate',target='https://example.com',narration='unsafe'))

def test_ack_failure_stops():
    with client.websocket_connect('/ws',headers=ORIGIN) as ws:
        ws.send_json({'goal':'bus'}); ws.receive_json(); ws.receive_json()
        ws.send_json({'index':0,'ok':False}); assert ws.receive_json()['type']=='error'

def test_unknown_goal():
    with client.websocket_connect('/ws',headers=ORIGIN) as ws:
        ws.send_json({'goal':'unrecognized'}); assert ws.receive_json()['type']=='error'

def test_invalid_origin():
    from starlette.websockets import WebSocketDisconnect
    with pytest.raises(WebSocketDisconnect):
        with client.websocket_connect('/ws',headers={'origin':'https://example.com'}): pass

def test_demo_pages():
    assert client.get('/health').json()['status']=='ok'
    for path in ['/demo/bus','/demo/bill','/demo/scheme','/demo/provider/a','/demo/provider/b']:
        r=client.get(path); assert r.status_code==200; assert 'Fictional demonstration' in r.text; assert 'disabled' in r.text
    assert client.get('/demo/provider/nope').status_code==404
