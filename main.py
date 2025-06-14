from flask import Flask, jsonify, request
import requests
from bs4 import BeautifulSoup
import re
import json
from datetime import datetime
import os
import threading
import time
from apscheduler.schedulers.background import BackgroundScheduler
import atexit

app = Flask(__name__)

# Global variable to store latest prices
latest_prices = {}
last_update = None

def get_gold_prices():
    """Scrapes current gold prices in EGP from iSagha website"""
    url = "https://market.isagha.com/prices"
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        page_text = soup.get_text()
        
        gold_prices = {}
        
        patterns = {
            '24_karat': r'عيار 24\s*([\d,\.]+)\s*ج\.م\s*بيع',
            '22_karat': r'عيار 22\s*([\d,\.]+)\s*ج\.م\s*بيع',
            '21_karat': r'عيار 21\s*([\d,\.]+)\s*ج\.م\s*بيع',
            '18_karat': r'عيار 18\s*([\d,\.]+)\s*ج\.م\s*بيع',
            '14_karat': r'عيار 14\s*([\d,\.]+)\s*ج\.م\s*بيع',
            'gold_pound': r'جنيه ذهب\s*([\d,\.]+)\s*ج\.م\s*بيع',
            'gold_ounce_usd': r'أوقية الذهب\s*([\d,\.]+)\s*\$\s*بيع'
        }
        
        for name, pattern in patterns.items():
            match = re.search(pattern, page_text)
            if match:
                price_str = match.group(1).replace(',', '')
                try:
                    price = float(price_str)
                    if 'usd' in name:
                        gold_prices[name] = {"price": price, "currency": "USD"}
                    else:
                        gold_prices[name] = {"price": price, "currency": "EGP"}
                except ValueError:
                    continue
        
        return gold_prices
        
    except Exception as e:
        print(f"Error fetching gold prices: {e}")
        return None

def update_prices():
    """Background task to update prices every 15 minutes"""
    global latest_prices, last_update
    
    print(f"[{datetime.now()}] Updating gold prices...")
    
    try:
        prices = get_gold_prices()
        if prices:
            latest_prices = prices
            last_update = datetime.now()
            print(f"[{datetime.now()}] Prices updated successfully. Found {len(prices)} prices.")
        else:
            print(f"[{datetime.now()}] Failed to fetch prices")
            
    except Exception as e:
        print(f"[{datetime.now()}] Error updating prices: {e}")

# Initialize scheduler for auto-updates every 15 minutes
scheduler = BackgroundScheduler()
scheduler.add_job(func=update_prices, trigger="interval", minutes=15)
scheduler.start()

# Shut down the scheduler when exiting the app
atexit.register(lambda: scheduler.shutdown())

@app.route('/')
def home():
    """API documentation endpoint"""
    return jsonify({
        "message": "Gold Price API - Auto Updates Every 15 Minutes",
        "version": "1.0",
        "last_update": last_update.strftime("%Y-%m-%d %H:%M:%S") if last_update else "Never",
        "endpoints": {
            "GET /": "API documentation",
            "GET /prices": "Get current gold prices",
            "GET /prices/<karat>": "Get specific karat price",
            "GET /prices/fresh": "Get fresh prices (fetch now)",
            "GET /health": "Health check"
        },
        "available_karats": [
            "24_karat", "22_karat", "21_karat", "18_karat", 
            "14_karat", "gold_pound", "gold_ounce_usd"
        ]
    })

@app.route('/health')
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "last_update": last_update.strftime("%Y-%m-%d %H:%M:%S") if last_update else "Never",
        "cached_prices_count": len(latest_prices)
    })

@app.route('/prices', methods=['GET'])
def get_cached_prices():
    """Get cached gold prices (updated every 15 minutes)"""
    if not latest_prices:
        # If no cached prices, fetch fresh ones
        update_prices()
        
        if not latest_prices:
            return jsonify({
                "success": False,
                "error": "No prices available",
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }), 503
    
    return jsonify({
        "success": True,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "last_update": last_update.strftime("%Y-%m-%d %H:%M:%S") if last_update else "Never",
        "source": "https://market.isagha.com/prices",
        "data": latest_prices,
        "auto_update": "Every 15 minutes"
    })

@app.route('/prices/fresh', methods=['GET'])
def get_fresh_prices():
    """Get fresh gold prices (fetch immediately)"""
    try:
        prices = get_gold_prices()
        
        if prices:
            global latest_prices, last_update
            latest_prices = prices
            last_update = datetime.now()
            
            return jsonify({
                "success": True,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "source": "https://market.isagha.com/prices",
                "data": prices,
                "note": "Fresh data fetched"
            })
        else:
            return jsonify({
                "success": False,
                "error": "Failed to fetch fresh prices",
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }), 500
    
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e),
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }), 500

@app.route('/prices/<karat>', methods=['GET'])
def get_specific_price(karat):
    """Get price for a specific karat"""
    if not latest_prices:
        update_prices()
    
    if karat not in latest_prices:
        return jsonify({
            "success": False,
            "error": f"Karat '{karat}' not found",
            "available_karats": list(latest_prices.keys())
        }), 404
    
    return jsonify({
        "success": True,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "last_update": last_update.strftime("%Y-%m-%d %H:%M:%S") if last_update else "Never",
        "karat": karat,
        "data": latest_prices[karat]
    })

if __name__ == '__main__':
    # Initial price fetch when starting
    print("🚀 Starting Gold Price API...")
    print("📊 Fetching initial gold prices...")
    update_prices()
    
    port = int(os.environ.get('PORT', 5000))
    
    print(f"✅ API running on port {port}")
    print("🔄 Auto-updates: Every 15 minutes")
    print("🌐 Ready to serve requests!")
    
    app.run(host='0.0.0.0', port=port, debug=False)