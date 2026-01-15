import streamlit as st
import pandas as pd
import time
import json
import websocket
import threading

# --- GLOBAL STORE FOR REAL-TIME DATA ---
# This dictionary will hold the latest prices from the websocket
if 'live_data' not in st.session_state:
    st.session_state.live_data = {
        'Polymarket': {'yes': 0.0, 'no': 0.0, 'last_update': 'Never'},
        'Kalshi': {'yes': 0.0, 'no': 0.0, 'last_update': 'Never'}
    }

# --- POLYMARKET WEBSOCKET WORKER ---
def run_poly_ws():
    def on_message(ws, message):
        data = json.loads(message)
        if data.get("event_type") == "book":
            payload = data.get("payload", {})
            bids = payload.get("bids", [])
            asks = payload.get("asks", [])
            if bids:
                st.session_state.live_data['Polymarket']['yes'] = float(bids[0]['price'])
            if asks:
                st.session_state.live_data['Polymarket']['no'] = 1.0 - float(asks[0]['price'])
            st.session_state.live_data['Polymarket']['last_update'] = time.strftime("%H:%M:%S")

    ws = websocket.WebSocketApp(
        "wss://clob.polymarket.com/ws/",
        on_message=on_message,
        on_open=lambda ws: ws.send(json.dumps({
            "type": "subscribe",
            "market_ids": ["0x218990e72288330752b0f498f3994326f2f012012046487e35b7e98a8767e98a"], # Example ID
            "channels": ["book"]
        }))
    )
    ws.run_forever()

# Start the websocket in a separate background thread so it doesn't freeze the website
if 'ws_thread' not in st.session_state:
    st.session_state.ws_thread = threading.Thread(target=run_poly_ws, daemon=True)
    st.session_state.ws_thread.start()

# --- STREAMLIT UI ---
st.set_page_config(page_title="Real-Time Arbitrage", layout="wide")
st.title("🚀 Real-Time Market Scanner")

# This creates an empty space that we will update in a loop
placeholder = st.empty()

st.sidebar.header("Connection Status")
st.sidebar.write(f"Poly Thread Alive: {st.session_state.ws_thread.is_alive()}")

# --- THE AUTO-UPDATE LOOP ---
while True:
    with placeholder.container():
        col1, col2 = st.columns(2)
        
        poly = st.session_state.live_data['Polymarket']
        kalshi = st.session_state.live_data['Kalshi']
        
        with col1:
            st.metric(label="Polymarket YES", value=f"${poly['yes']:.3f}", delta=None)
            st.caption(f"Last Update: {poly['last_update']}")
            
        with col2:
            # Note: You would add the Kalshi WS logic similar to Poly above
            st.metric(label="Kalshi YES", value=f"${kalshi['yes']:.3f}")
            st.caption("Waiting for Kalshi WS...")

        # Calculate Arbitrage live
        arb_cost = poly['yes'] + (1 - kalshi['yes']) # Simplistic example
        if arb_cost < 0.98 and arb_cost > 0.1:
            st.balloons()
            st.success(f"🔥 ARBITRAGE DETECTED! Total Cost: ${arb_cost:.3f}")
        
        # This is the "secret sauce" -> it tells the website to wait 1 second and then re-draw
        time.sleep(1) 
