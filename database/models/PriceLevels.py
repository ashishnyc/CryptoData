from datetime import datetime
from typing import Optional
from sqlmodel import SQLModel, Field, Numeric, UniqueConstraint
from decimal import Decimal


class PriceLevel(SQLModel, table=True):
    __tablename__ = "crypto_symbols_price_pivot_levels"

    # Primary key and tracking fields
    id: Optional[int] = Field(default=None, primary_key=True)

    # Identifier fields
    exchange: str = Field(default="bybit", index=True)
    symbol: str = Field(index=True)
    instrument_type: str = Field(default="perp", index=True)
    timeframe: str = Field(index=True)
    period_start: datetime = Field(index=True)
    lookback_period: int = Field(default=0, index=True)

    # Price level
    price_level: Decimal = Field(sa_column=Numeric(38, 8))

    # Level characteristics
    is_support: bool = Field(default=False)
    is_resistance: bool = Field(default=False)

    __table_args__ = (
        UniqueConstraint(
            "exchange",
            "symbol",
            "instrument_type",
            "timeframe",
            "period_start",
            "lookback_period",
            name="uix_price_level_symbol_timeframe_period_price",
        ),
    )

    def to_dict(self):
        return {
            "exchange": self.exchange,
            "symbol": self.symbol,
            "instrument_type": self.instrument_type,
            "timeframe": self.timeframe,
            "period_start": self.period_start,
            "lookback_period": self.lookback_period,
            "price_level": self.price_level,
            "is_support": self.is_support,
            "is_resistance": self.is_resistance,
        }
