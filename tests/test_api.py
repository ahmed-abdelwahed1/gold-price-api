import pytest
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from main import app, get_gold_prices

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_get_gold_prices_logic():
    prices = get_gold_prices()
    assert isinstance(prices, dict)
    assert '24_karat' in prices or '21_karat' in prices

# Integration tests for API endpoints
def test_home(client):
    response = client.get('/')
    assert response.status_code == 200
    data = response.get_json()
    assert 'message' in data
    assert 'endpoints' in data

def test_health(client):
    response = client.get('/health')
    assert response.status_code == 200
    data = response.get_json()
    assert data['status'] == 'healthy'

def test_get_prices(client):
    response = client.get('/prices')
    assert response.status_code == 200
    data = response.get_json()
    assert 'data' in data
    assert data['success'] is True

def test_get_fresh_prices(client):
    response = client.get('/prices/fresh')
    assert response.status_code == 200
    data = response.get_json()
    assert 'data' in data
    assert data['success'] is True

def test_get_specific_karat(client):
    # First, get available karats
    response = client.get('/prices')
    data = response.get_json()
    karats = list(data['data'].keys())
    if karats:
        karat = karats[0]
        response = client.get(f'/prices/{karat}')
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert data['karat'] == karat
    else:
        pytest.skip('No karats available for testing')

def test_get_invalid_karat(client):
    response = client.get('/prices/invalid_karat')
    assert response.status_code == 404
    data = response.get_json()
    assert data['success'] is False
    assert 'error' in data 