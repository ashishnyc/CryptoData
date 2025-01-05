from datetime import datetime
from enum import Enum
from typing import Optional
from sqlmodel import SQLModel, Field, Numeric, UniqueConstraint
from decimal import Decimal


class ByBitTradesHistoryRaw(SQLModel, table=True):
    __tablename__ = "bybit_trades_history_raw"

    id: Optional[int] = Field(default=None, primary_key=True)
    symbol: str
    category: str
    order_type: str
    underlying_price: str
    order_link_id: str
    side: str
    index_price: str
    order_id: str
    stop_order_type: str
    leaves_qty: str
    exec_time: str
    fee_currency: str
    is_maker: str
    exec_fee: str
    fee_rate: str
    exec_id: str
    trade_iv: str
    block_trade_id: str
    mark_price: str
    exec_price: str
    mark_iv: str
    order_qty: str
    order_price: str
    exec_value: str
    exec_type: str
    exec_qty: str
    closed_size: str
    seq: str
