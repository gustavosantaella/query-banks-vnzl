import threading
import asyncio

active_websocket = None
loop = None

# Dict for events: bank_code -> threading.Event
otp_events = {}

# Dict for code values: bank_code -> str
otp_values = {}

def send_ws_message(message: dict):
    global active_websocket, loop
    if active_websocket and loop:
        async def send():
            try:
                await active_websocket.send_json(message)
            except Exception as e:
                print(f"Error sending WS message: {e}")
        asyncio.run_coroutine_threadsafe(send(), loop)
    else:
        print("WebSocket not active or event loop not captured.")
