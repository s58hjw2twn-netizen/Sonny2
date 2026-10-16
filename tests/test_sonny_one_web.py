"""Local demo contract: no external provider calls or server-side user state."""
import socket

import pytest
from fastapi.testclient import TestClient

from sonny_one.web_app import app


@pytest.fixture
def client(monkeypatch):
    def blocked(*args, **kwargs):
        raise AssertionError("Demo attempted network access")
    monkeypatch.setattr(socket.socket, 'connect', blocked)
    with TestClient(app) as browser:
        yield browser


def test_demo_assets_and_headers(client):
    page = client.get('/')
    assert page.status_code == 200
    assert 'Local demo' in page.text
    assert "frame-ancestors 'none'" in page.headers['content-security-policy']
    assert page.headers['cache-control'] == 'no-store'
    for path in ('/assets/app.js', '/assets/styles.css'):
        assert client.get(path).status_code == 200
    assert client.get('/api/status').json() == {
        'mode': 'deterministic-demo', 'model_connected': False,
        'api_cost': 0, 'server_persistence': False}


def test_plan_is_deterministic_and_uses_goal(client):
    body = {'message': 'Help me plan', 'goal': 'Ship my sample project'}
    first = client.post('/api/chat', json=body)
    assert first.status_code == 200
    assert first.json() == client.post('/api/chat', json=body).json()
    assert 'Ship my sample project' in first.json()['text']
    assert 'fixed demo plan' in first.json()['text']


def test_memory_only_comes_from_current_request(client):
    remembered = client.post('/api/chat', json={
        'message': 'What do you remember?', 'memories': ['Sample fact']}).json()
    assert 'Sample fact' in remembered['text']
    assert remembered['memory_count'] == 1
    fresh = client.post('/api/chat', json={'message': 'What do you remember?'}).json()
    assert fresh['memory_count'] == 0
    assert 'Sample fact' not in fresh['text']


@pytest.mark.parametrize('body', [
    {'message': ''}, {'message': '   '}, {'message': 'x' * 4001},
    {'message': 'hi', 'goal': 'x' * 501},
    {'message': 'hi', 'memories': ['x'] * 51},
    {'message': 'hi', 'memories': ['x' * 501]},
    {'message': 'hi', 'memories': [' ']},
])
def test_invalid_or_unbounded_input_rejected(client, body):
    assert client.post('/api/chat', json=body).status_code == 422


def test_unknown_request_does_not_claim_model_answer(client):
    response = client.post('/api/chat', json={'message': 'Calculate the orbit of Mars'}).json()
    assert 'not connected' in response['text']
