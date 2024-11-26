import json
from typing import List
from fastapi import (
    FastAPI,
    Query,
    WebSocket,
    WebSocketDisconnect,
)
from dataManagers.ByBitMarketDataManager import ByBitMarketDataManager
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="CryptoData API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://frontend:3000"],  # Your frontend URL
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)


class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)


manager = ConnectionManager()


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)

            if message["type"] == "ping":
                await websocket.send_text(json.dumps({"type": "pong"}))
            elif message["type"] == "subscribe":
                # Handle subscription
                pass
    except WebSocketDisconnect:
        manager.disconnect(websocket)


# Example endpoint
@app.get("/symbols/")
def read_instruments():
    bb = ByBitMarketDataManager()
    instruments = bb.get_current_linear_instruments(quote_coin="USDT")
    output = []
    for instrument in instruments:
        output.append(instrument.symbol)
    return output


@app.get("/klines/{symbol}")
def read_klines(
    symbol: str,
    timeframe: str = Query(None, description="Timeframe for the klines"),
):
    bb = ByBitMarketDataManager()
    klines = bb.get_linear_instruments_klines(symbol=symbol, timeframe=timeframe)
    formatted_klines = [
        {
            "time": kline.period_start.timestamp(),
            "open": kline.open_price,
            "high": kline.high_price,
            "low": kline.low_price,
            "close": kline.close_price,
            "volume": kline.turnover,
        }
        for kline in klines
    ]
    return formatted_klines
