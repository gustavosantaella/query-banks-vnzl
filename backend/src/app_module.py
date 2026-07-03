from sys import prefix
from nest.core import PyNestFactory, Module
from fastapi.middleware.cors import CORSMiddleware
from src.modules.query.query_module import QueryModule
        


@Module(imports=[
    QueryModule
], controllers=[], providers=[])
class AppModule:
    pass


app = PyNestFactory.create(
    AppModule,
    description="This is my PyNest app.",
    title="PyNest Application",
    version="1.0.0",
    debug=True,
)

http_server = app.get_server()

http_server.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

http_server.root_path = "/api"


import asyncio
from fastapi import WebSocket, WebSocketDisconnect
from src.config.app import ws_state

@http_server.websocket("/api/ws/query")
@http_server.websocket("/ws/query")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    print("WebSocket client connected.")
    ws_state.active_websocket = websocket
    ws_state.loop = asyncio.get_event_loop()
    try:
        while True:
            data = await websocket.receive_json()
            print(f"Received WS data: {data}")
            action = data.get("action")
            if action == "submit_otp":
                bank_code = data.get("bank_code")
                code = data.get("code")
                if bank_code:
                    ws_state.otp_values[bank_code] = code
                    if bank_code in ws_state.otp_events:
                        ws_state.otp_events[bank_code].set()
    except WebSocketDisconnect:
        print("WebSocket client disconnected.")
        ws_state.active_websocket = None


                