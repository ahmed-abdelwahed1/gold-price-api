import pytest
import sys
import os
from unittest.mock import patch, Mock
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

def test_get_gold_prices_with_mocked_html():
    """Test that the new flexible patterns work with various HTML formats"""
    # Mock HTML content without "بيع" (sell) text - simulating the new website format
    mock_html = '''
    <html>
    <body>
    عيار 24 3500 ج.م
    عيار 22 3200 ج.م
    عيار 21 3000 ج.م
    عيار 18 2500 ج.م
    جنيه ذهب 28000 ج.م
    أوقية الذهب 2700 $
    </body>
    </html>
    '''
    
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.content = mock_html.encode('utf-8')
    mock_response.raise_for_status = Mock()
    
    with patch('requests.get', return_value=mock_response):
        prices = get_gold_prices()
        
        # Should return a dict
        assert isinstance(prices, dict)
        # Should extract prices even without "بيع" text
        assert len(prices) >= 5
        # Verify structure
        assert '24_karat' in prices
        assert prices['24_karat']['price'] == 3500.0
        assert prices['24_karat']['currency'] == 'EGP'

def test_get_gold_prices_skips_carat_number():
    """Test that karat numbers are not mistakenly captured as prices.
    When the page text contains karat numbers adjacent to the karat label
    (e.g. 'عيار 24 عيار 22 3500'), the actual price must be returned,
    not the karat number itself."""
    mock_html = '''
    <html>
    <body>
    عيار 24 عيار 22 عيار 21
    3500 3200 3000
    </body>
    </html>
    '''

    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.content = mock_html.encode('utf-8')
    mock_response.raise_for_status = Mock()

    with patch('requests.get', return_value=mock_response):
        prices = get_gold_prices()

        assert isinstance(prices, dict)
        assert '24_karat' in prices
        # The price must not be a karat number (<=24); it must be the actual price
        assert prices['24_karat']['price'] > 100, (
            f"Expected a real price > 100, got {prices['24_karat']['price']} "
            "(looks like a karat number was captured instead of the price)"
        )
        assert prices['24_karat']['price'] == 3500.0
        assert prices['24_karat']['currency'] == 'EGP'


def test_get_gold_prices_backward_compatibility():
    """Test that old format with 'بيع' still works"""
    # Mock HTML content with old format
    mock_html = '''
    <html>
    <body>
    عيار 24 3500 ج.م بيع
    عيار 21 3000 ج.م بيع
    </body>
    </html>
    '''
    
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.content = mock_html.encode('utf-8')
    mock_response.raise_for_status = Mock()
    
    with patch('requests.get', return_value=mock_response):
        prices = get_gold_prices()
        
        assert isinstance(prices, dict)
        assert len(prices) >= 2
        assert '24_karat' in prices
        assert '21_karat' in prices

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