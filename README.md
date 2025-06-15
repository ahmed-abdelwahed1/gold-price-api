# Gold Price API

A real-time gold price tracking API that provides current gold prices in EGP and USD, with automatic updates every 15 minutes.

## Features

- Real-time gold prices
- Multiple karat options (24K, 22K, 21K, 18K, 14K)
- Gold pound and ounce prices
- Automatic price updates every 15 minutes
- Cached and fresh price endpoints

## API Endpoints

- `GET /` - API documentation
- `GET /prices` - Get all current gold prices
- `GET /prices/<karat>` - Get specific karat price
- `GET /prices/fresh` - Get fresh prices (fetch now)
- `GET /health` - Health check

## Installation

```bash
pip install -r requirements.txt
python main.py
```

## Environment

- Python 3.9+
- Flask
- BeautifulSoup4
- APScheduler

## License

MIT
