import json
from typing import List, Optional
from fastapi import (
    FastAPI,
    Query,
    WebSocket,
    WebSocketDisconnect,
)
from sqlmodel import text
from dataManagers.ByBitMarketDataManager import ByBitDataService
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


@app.get("/api/symbols")
def read_instruments():
    bb = ByBitDataService()
    instruments = bb.get_linear_usdt_instruments(quote_coin="USDT", data_source="db")
    output = []
    for instrument in instruments:
        output.append((instrument.id, instrument.symbol, instrument.price_scale))
    return output


@app.get("/api/klines/{symbol}")
def read_klines(
    symbol: str,
    timeframe: str = Query(None, description="Timeframe for the klines"),
):
    bb = ByBitDataService()
    klines = bb.get_linear_instrument_klines(
        symbol=symbol, timeframe=timeframe, data_source="db"
    )
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


@app.get("/api/symbols/{symbol}")
def get_symbol_info(symbol: Optional[str] = None):
    if symbol is None:
        symbol = "_ALL__"
    bb = ByBitDataService()
    query = text(
        """
    WITH latest_time AS (
        SELECT MAX(period_start) as max_time 
        FROM bybit_linear_perp_kline_5m
        WHERE (
            symbol = '{symbol}'
            OR '{symbol}' = '_ALL__'
        )
    ),
    relevant_periods AS (
        SELECT 
            symbol, 
            period_start, 
            close_price,
            turnover,
            high_price,
            low_price
        FROM bybit_linear_perp_kline_5m k
        CROSS JOIN latest_time lt
        WHERE period_start >= lt.max_time - INTERVAL '1 day'
        AND (
            symbol = '{symbol}'
            OR '{symbol}' = '_ALL__'
        )
    ),
    price_and_turnover_points AS (
        SELECT 
            r.symbol,
            lt.max_time as period_start,
            -- Prices
            MAX(CASE WHEN r.period_start = lt.max_time THEN close_price END) as current_price,
            MAX(CASE WHEN r.period_start = lt.max_time - INTERVAL '5 minutes' THEN close_price END) as price_5m_ago,
            MAX(CASE WHEN r.period_start = lt.max_time - INTERVAL '15 minutes' THEN close_price END) as price_15m_ago,
            MAX(CASE WHEN r.period_start = lt.max_time - INTERVAL '1 hour' THEN close_price END) as price_1h_ago,
            MAX(CASE WHEN r.period_start = lt.max_time - INTERVAL '4 hours' THEN close_price END) as price_4h_ago,
            MAX(CASE WHEN r.period_start = lt.max_time - INTERVAL '1 day' THEN close_price END) as price_1d_ago,
            -- Turnovers
            SUM(CASE 
                WHEN r.period_start > lt.max_time - INTERVAL '5 minutes' 
                THEN turnover 
                END) as turnover_5m,
            SUM(CASE 
                WHEN r.period_start > lt.max_time - INTERVAL '15 minutes' 
                THEN turnover 
                END) as turnover_15m,
            SUM(CASE 
                WHEN r.period_start > lt.max_time - INTERVAL '1 hour' 
                THEN turnover 
                END) as turnover_1h,
            SUM(CASE 
                WHEN r.period_start > lt.max_time - INTERVAL '4 hours' 
                THEN turnover 
                END) as turnover_4h,
            SUM(CASE 
                WHEN r.period_start > lt.max_time - INTERVAL '1 day' 
                THEN turnover 
                END) as turnover_1d,
            -- Max Prices 
            MAX(CASE WHEN r.period_start = lt.max_time - INTERVAL '1 day' THEN high_price END) as max_price_24h,
            -- Low Prices
            MIN(CASE WHEN r.period_start = lt.max_time - INTERVAL '1 day' THEN low_price END) as min_price_24h
        FROM relevant_periods r
        CROSS JOIN latest_time lt
        GROUP BY r.symbol, lt.max_time
    ),
    instruments AS (
        SELECT symbol, price_scale
        FROM bybit_linear_perp_instruments
        where (
            symbol = '{symbol}'
            OR '{symbol}' = '_ALL__'
        )
    )
    SELECT 
        price_and_turnover_points.symbol,
        period_start,
        current_price,
        -- Price changes
        (current_price - price_5m_ago) / price_5m_ago as change_5m_pct,
        (current_price - price_15m_ago) / price_15m_ago as change_15m_pct,
        (current_price - price_1h_ago) / price_1h_ago as change_1h_pct,
        (current_price - price_4h_ago) / price_4h_ago as change_4h_pct,
        (current_price - price_1d_ago) / price_1d_ago as change_1d_pct,
        -- Turnovers
        turnover_5m,
        turnover_15m,
        turnover_1h,
        turnover_4h,
        turnover_1d,
        price_scale,
        max_price_24h,
        min_price_24h
    FROM price_and_turnover_points
    left join instruments
    on price_and_turnover_points.symbol = instruments.symbol
    WHERE current_price IS NOT NULL
    """.format(
            symbol=symbol
        )
    )
    instruments_info = bb.dbClient.exec(query).all()
    formatted_instruments = [
        {
            "symbol": instrument.symbol,
            "time": instrument.period_start.timestamp(),
            "current_price": instrument.current_price,
            "change_5m_pct": instrument.change_5m_pct,
            "change_15m_pct": instrument.change_15m_pct,
            "change_1h_pct": instrument.change_1h_pct,
            "change_4h_pct": instrument.change_4h_pct,
            "change_1d_pct": instrument.change_1d_pct,
            "turnover_5m": instrument.turnover_5m,
            "turnover_15m": instrument.turnover_15m,
            "turnover_1h": instrument.turnover_1h,
            "turnover_4h": instrument.turnover_4h,
            "turnover_1d": instrument.turnover_1d,
            "price_scale": instrument.price_scale,
            "max_price_24h": instrument.max_price_24h,
            "min_price_24h": instrument.min_price_24h,
        }
        for instrument in instruments_info
    ]
    return formatted_instruments
