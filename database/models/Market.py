from datetime import datetime
from typing import Optional
from sqlmodel import SQLModel, Field, Numeric, UniqueConstraint
from decimal import Decimal


class ByBitLinearInstruments(SQLModel, table=True):
    __tablename__ = "bybit_linear_perp_instruments"

    # Primary key and tracking fields
    id: Optional[int] = Field(default=None, primary_key=True)

    # Basic instrument info
    symbol: str = Field(index=True)
    base_coin: str = Field(nullable=True)
    quote_coin: str = Field(nullable=True)
    launch_time: int = Field(nullable=True)
    price_scale: int
    funding_interval: Optional[int] = Field(default=None)

    # Leverage Filter fields
    min_leverage: Decimal
    max_leverage: Decimal
    leverage_step: Decimal

    # Lot Size Filter fields
    max_trading_qty: Decimal
    min_trading_qty: Decimal
    qty_step: Decimal

    # Price Filter fields
    min_price: Decimal
    max_price: Decimal
    tick_size: Decimal


class ByBitInstrumentsRaw(SQLModel, table=True):
    __tablename__ = "bybit_instruments_raw"

    # Primary key and tracking fields
    id: Optional[int] = Field(default=None, primary_key=True)
    downloaded_at: int = Field(nullable=False)

    # Basic instrument info
    symbol: str = Field(index=True)
    contract_type: str = Field(nullable=False)
    status: str = Field(nullable=True)
    base_coin: str = Field(nullable=True)
    quote_coin: str = Field(nullable=True)
    launch_time: int = Field(nullable=True)
    delivery_time: int = Field(nullable=True)
    delivery_fee_rate: Optional[Decimal] = Field(default=None)
    price_scale: int
    unified_margin_trade: bool = Field(default=False)
    funding_interval: Optional[int] = Field(default=None)
    settle_coin: Optional[str] = Field(default=None)

    # Leverage Filter fields
    min_leverage: Decimal
    max_leverage: Decimal
    leverage_step: Decimal

    # Lot Size Filter fields
    max_trading_qty: Decimal
    min_trading_qty: Decimal
    qty_step: Decimal

    # Price Filter fields
    min_price: Decimal
    max_price: Decimal
    tick_size: Decimal

    def set_downloaded_at(self, value: int):
        self.downloaded_at = value

    def set_symbol(self, value: str):
        self.symbol = value

    def set_contract_type(self, value: str):
        self.contract_type = value

    def set_status(self, value: str):
        self.status = value

    def set_base_coin(self, value: str):
        self.base_coin = value

    def set_quote_coin(self, value: str):
        self.quote_coin = value

    def set_launch_time(self, value: str):
        try:
            self.launch_time = int(value) / 1000
        except:
            print(f"Error converting launch time: {value}")
            self.launch_time = None

    def set_delivery_time(self, value: str):
        try:
            self.delivery_time = int(value) / 1000
        except:
            print(f"Error converting delivery time: {value}")
            self.delivery_time = None

    def set_delivery_fee_rate(self, value: str):
        if value == "":
            self.delivery_fee_rate = None
            return

        try:
            self.delivery_fee_rate = Decimal(value)
        except:
            print(f"Error converting delivery fee rate: {value}")
            self.delivery_fee_rate = None

    def set_price_scale(self, value: str):
        try:
            self.price_scale = int(value)
        except:
            print(f"Error converting price scale: {value}")
            self.price_scale = None

    def set_unified_margin_trade(self, value: str):
        self.unified_margin_trade = bool(value)

    def set_funding_interval(self, value: str):
        try:
            self.funding_interval = int(value)
        except:
            print(f"Error converting funding interval: {value}")
            self.funding_interval = None

    def set_settle_coin(self, value: str):
        self.settle_coin = value

    def set_min_leverage(self, value: str):
        try:
            self.min_leverage = Decimal(value)
        except:
            print(f"Error converting min leverage: {value}")
            self.min_leverage = None

    def set_max_leverage(self, value: str):
        try:
            self.max_leverage = Decimal(value)
        except:
            print(f"Error converting max leverage: {value}")
            self.max_leverage = None

    def set_leverage_step(self, value: str):
        try:
            self.leverage_step = Decimal(value)
        except:
            print(f"Error converting leverage step: {value}")
            self.leverage_step = None

    def set_max_trading_qty(self, value: str):
        try:
            self.max_trading_qty = Decimal(value)
        except:
            print(f"Error converting max trading qty: {value}")
            self.max_trading_qty = None

    def set_min_trading_qty(self, value: str):
        try:
            self.min_trading_qty = Decimal(value)
        except:
            print(f"Error converting min trading qty: {value}")
            self.min_trading_qty = None

    def set_qty_step(self, value: str):
        try:
            self.qty_step = Decimal(value)
        except:
            print(f"Error converting qty step: {value}")
            self.qty_step = None

    def set_min_price(self, value: str):
        try:
            self.min_price = Decimal(value)
        except:
            print(f"Error converting min price: {value}")
            self.min_price = None

    def set_max_price(self, value: str):
        try:
            self.max_price = Decimal(value)
        except:
            print(f"Error converting max price: {value}")
            self.max_price = None

    def set_tick_size(self, value: str):
        try:
            self.tick_size = Decimal(value)
        except:
            print(f"Error converting tick size: {value}")
            self.tick_size = None

    def process_xchange_info(self, xchange_data: dict):
        self.set_downloaded_at(xchange_data.get("downloaded_at"))
        self.set_symbol(xchange_data.get("symbol"))
        self.set_contract_type(xchange_data.get("contractType"))
        self.set_status(xchange_data.get("status"))
        self.set_base_coin(xchange_data.get("baseCoin"))
        self.set_quote_coin(xchange_data.get("quoteCoin"))

        # Time fields
        self.set_launch_time(xchange_data.get("launchTime"))
        self.set_delivery_time(xchange_data.get("deliveryTime"))
        self.set_delivery_fee_rate(xchange_data.get("deliveryFeeRate"))
        self.set_price_scale(xchange_data.get("priceScale"))
        self.set_unified_margin_trade(xchange_data.get("unifiedMarginTrade"))
        self.set_funding_interval(xchange_data.get("fundingInterval"))
        self.set_settle_coin(xchange_data.get("settleCoin"))

        # Leverage Filter fields\
        self.set_min_leverage(xchange_data.get("leverageFilter").get("minLeverage"))
        self.set_max_leverage(xchange_data.get("leverageFilter").get("maxLeverage"))
        self.set_leverage_step(xchange_data.get("leverageFilter").get("leverageStep"))

        # Lot Size Filter fields
        self.set_max_trading_qty(xchange_data.get("lotSizeFilter").get("maxOrderQty"))
        self.set_min_trading_qty(xchange_data.get("lotSizeFilter").get("minOrderQty"))
        self.set_qty_step(xchange_data.get("lotSizeFilter").get("qtyStep"))

        # Price Filter fields
        self.set_min_price(xchange_data.get("priceFilter").get("minPrice"))
        self.set_max_price(xchange_data.get("priceFilter").get("maxPrice"))
        self.set_tick_size(xchange_data.get("priceFilter").get("tickSize"))


class ByBitLinearInstrumentsKline5mRaw(SQLModel, table=True):
    __tablename__ = "bybit_linear_perp_kline_5m_raw"

    # Primary key and tracking fields
    id: Optional[int] = Field(default=None, primary_key=True)
    downloaded_at: int = Field(nullable=False)
    symbol: str
    startTime: str
    openPrice: str
    highPrice: str
    lowPrice: str
    closePrice: str
    volume: str
    turnover: str
    is_processed: bool = Field(default=False)


class ByBitLinearInstrumentsKline5m(SQLModel, table=True):
    __tablename__ = "bybit_linear_perp_kline_5m"

    # Primary key and tracking fields
    id: Optional[int] = Field(default=None, primary_key=True)
    symbol: str
    period_start: datetime
    open_price: Decimal = Field(sa_column=Numeric(38, 8))
    high_price: Decimal = Field(sa_column=Numeric(38, 8))
    low_price: Decimal = Field(sa_column=Numeric(38, 8))
    close_price: Decimal = Field(sa_column=Numeric(38, 8))
    volume: Decimal = Field(sa_column=Numeric(38, 8))
    turnover: Decimal = Field(sa_column=Numeric(38, 8))

    __table_args__ = (
        UniqueConstraint("symbol", "period_start", name="uix_symbol_period_start"),
    )