import websocket
import json
import time
import base64
import requests
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.backends import default_backend

# --- CONFIGURATION ---
KALSHI_KEY_ID = "YOUR_KALSHI_KEY_ID"
KALSHI_KEY_FILE = "kalshi_key.pem"
# Example Ticker: 'KXAU-24DEC31-B2750' (Gold price market)
# You get these tickers from the standard Kalshi API
TARGET_TICKER = "KXAU-24DEC31-B2750" 

# --- AUTHENTICATION (Same as before to get Token) ---
def get_kalshi_token():
    with open(KALSHI_KEY_FILE, "rb") as f:
        private_key = serialization.load_pem_private_key(
            f.read(), password=None, backend=default_backend()
        )
    timestamp = str(int(time.time() * 1000))
    signature = private_key.sign(
        timestamp.encode('utf-8'),
        padding.PKCS1v15(),
        hashes.SHA256()
    )
    sig_b64 = base64.b64encode(signature).decode('utf-8')
    
    response = requests.post("https://api.kalshi.com/trade-api/v2/login", json={
        "keyId": KALSHI_KEY_ID,
        "signature": sig_b64,
        "timestamp": timestamp
    })
    return response.json().get("token")

# --- WEBSOCKET LOGIC ---
def on_message(ws, message):
    data = json.loads(message)
    
    # Check for orderbook updates
    if data.get("type") == "orderbook_delta":
        msg = data.get("msg", {})
        print(f"⚡ LIVE UPDATE [{msg.get('ticker')}]:")
        if "yes" in msg:
            # Price is in cents (e.g. 55 = $0.55)
            print(f"   YES Price: {msg['yes'][0][0]} cents")
        if "no" in msg:
            print(f"   NO Price: {msg['no'][0][0]} cents")

def on_open(ws):
    print("✅ Connected to Kalshi Real-Time Feed")
    # Subscribe to the orderbook for your target ticker
    subscribe_msg = {
        "id": 1,
        "type": "subscribe",
        "channels": ["orderbook_delta"],
        "market_tickers": [TARGET_TICKER]
    }
    ws.send(json.dumps(subscribe_msg))

def start_websocket():
    token = get_kalshi_token()
    # Kalshi requires the token in the URL or as a Header
    ws_url = f"wss://api.kalshi.com/trade-api/v2/ws?token={token}"
    
    ws = websocket.WebSocketApp(
        ws_url,
        on_open=on_open,
        on_message=on_message
    )
    ws.run_forever()

if __name__ == "__main__":
    start_websocket()
