import websocket
import json
import requests
import threading

# --- STEP 1: HELPER TO GET ACTIVE MARKET IDs ---
def get_active_market_ids():
    """Fetches the first 2 active market IDs from the Gamma API to track."""
    url = "https://gamma-api.polymarket.com/markets?active=true&closed=false&limit=2"
    try:
        resp = requests.get(url)
        data = resp.json()
        # We need the 'conditionId' for the WebSocket
        return [m['conditionId'] for m in data if 'conditionId' in m]
    except Exception as e:
        print(f"Error fetching IDs: {e}")
        return []

# --- STEP 2: WEBSOCKET LOGIC ---

def on_message(ws, message):
    """Triggered every time a price change occurs."""
    data = json.loads(message)
    
    # Polymarket sends 'book' events when prices change
    if data.get("event_type") == "book":
        market_id = data.get("market_id")
        payload = data.get("payload", {})
        
        # Bids = People wanting to buy YES (Price they pay)
        # Asks = People wanting to buy NO (1 - AskPrice)
        bids = payload.get("bids", [])
        asks = payload.get("asks", [])

        print(f"\n🔔 REAL-TIME UPDATE | Market: {market_id[:10]}...")
        if bids:
            print(f"   🟢 Best YES Price (Bid): ${bids[0]['price']}")
        if asks:
            print(f"   🔴 Best NO Price (Ask):  ${asks[0]['price']}")

def on_error(ws, error):
    print(f"❌ WebSocket Error: {error}")

def on_close(ws, close_status_code, close_msg):
    print("🔌 Connection Closed")

def on_open(ws):
    print("🚀 Connected to Polymarket CLOB WebSocket")
    
    # Get real IDs to subscribe to
    target_ids = get_active_market_ids()
    
    if not target_ids:
        print("⚠️ No active markets found to track.")
        return

    # Subscription Message
    subscribe_msg = {
        "type": "subscribe",
        "market_ids": target_ids,
        "channels": ["book"] # 'book' is the real-time orderbook channel
    }
    
    ws.send(json.dumps(subscribe_msg))
    print(f"📡 Subscribed to markets: {target_ids}")

def start_poly_realtime():
    ws_url = "wss://clob.polymarket.com/ws/"
    
    ws = websocket.WebSocketApp(
        ws_url,
        on_open=on_open,
        on_message=on_message,
        on_error=on_error,
        on_close=on_close
    )
    
    # Run the websocket in the background
    ws.run_forever()

if __name__ == "__main__":
    start_poly_realtime()
