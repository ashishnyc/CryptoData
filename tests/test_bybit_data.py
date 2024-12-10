from dataManagers.ByBitMarketDataManager import ByBitDataIngestion, ByBitDataService
import pytest
from datetime import datetime
from decimal import Decimal
from unittest.mock import Mock, patch
from database.models import Market
from xchanges.ByBit import Category


class TestByBitDataIngestion:
    @pytest.fixture
    def data_ingestion(self, mock_market_data, mock_db_operations):
        instance = ByBitDataIngestion(testnet=True)
        instance.client = mock_market_data.return_value
        instance.dbClient = mock_db_operations.return_value
        instance.bb_data_service = Mock()
        return instance

    def test_download_linear_usdt_instruments(self, data_ingestion):
        """Test downloading new instruments when none exist"""
        # Mock the API response
        mock_instruments = [
            {
                "symbol": "BTCUSDT",
                "baseCoin": "BTC",
                "quoteCoin": "USDT",
                "launchTime": "1234567890",
                "priceScale": "2",
                "fundingInterval": "480",
                "leverageFilter": {
                    "minLeverage": "1",
                    "maxLeverage": "100",
                    "leverageStep": "1",
                },
                "lotSizeFilter": {
                    "maxOrderQty": "100",
                    "minOrderQty": "0.001",
                    "qtyStep": "0.001",
                },
                "priceFilter": {
                    "minPrice": "0.01",
                    "maxPrice": "100000",
                    "tickSize": "0.01",
                },
            }
        ]

        # Configure mocks
        data_ingestion.client.fetch_instruments.return_value = mock_instruments
        data_ingestion.bb_data_service.get_linear_usdt_instruments.return_value = []
        data_ingestion.dbClient.add = Mock()
        data_ingestion.dbClient.commit = Mock()

        # Execute the method
        inserts, updates, deletes = data_ingestion.download_linear_usdt_instruments()

        # Verify results
        assert inserts == 1, "Should have one insert"
        assert updates == 0, "Should have no updates"
        assert deletes == 0, "Should have no deletes"

        # Verify the mock was called correctly
        data_ingestion.client.fetch_instruments.assert_called_once()
        data_ingestion.bb_data_service.get_linear_usdt_instruments.assert_called_once_with(
            quote_coin=data_ingestion.quote_coin
        )

    def test_download_linear_usdt_instruments_with_updates(self, data_ingestion):
        """Test updating existing instruments"""
        # Mock API response
        mock_instruments = [
            {
                "symbol": "BTCUSDT",
                "baseCoin": "BTC",
                "quoteCoin": "USDT",
                "launchTime": "1234567890",
                "priceScale": "2",
                "fundingInterval": "480",
                "leverageFilter": {
                    "minLeverage": "1",
                    "maxLeverage": "100",
                    "leverageStep": "1",
                },
                "lotSizeFilter": {
                    "maxOrderQty": "100",
                    "minOrderQty": "0.001",
                    "qtyStep": "0.001",
                },
                "priceFilter": {
                    "minPrice": "0.01",
                    "maxPrice": "100000",
                    "tickSize": "0.01",
                },
            }
        ]

        # Mock existing instrument
        existing_instrument = Mock(spec=Market.ByBitLinearInstruments)
        existing_instrument.symbol = "BTCUSDT"
        existing_instrument.quote_coin = "USDT"
        existing_instrument.is_equal = Mock(return_value=False)  # Will trigger update

        # Configure mocks
        data_ingestion.client.fetch_instruments.return_value = mock_instruments
        data_ingestion.bb_data_service.get_linear_usdt_instruments.return_value = [
            existing_instrument
        ]
        data_ingestion.dbClient.add = Mock()
        data_ingestion.dbClient.commit = Mock()

        # Execute the method
        inserts, updates, deletes = data_ingestion.download_linear_usdt_instruments()

        # Verify results
        assert inserts == 0, "Should have no inserts"
        assert updates == 1, "Should have one update"
        assert deletes == 0, "Should have no deletes"

        # Verify mock calls
        data_ingestion.dbClient.add.assert_called_once()
        data_ingestion.dbClient.commit.assert_called_once()


class TestByBitDataService:
    @pytest.fixture
    def data_service(self, mock_db_operations, mock_redis):
        return ByBitDataService(dbClient=mock_db_operations.return_value)

    def test_get_linear_usdt_instruments(self, data_service):
        mock_instruments = [
            Mock(
                spec=Market.ByBitLinearInstruments,
                symbol="BTCUSDT",
                base_coin="BTC",
                quote_coin="USDT",
            )
        ]
        data_service.dbClient.exec.return_value.all.return_value = mock_instruments

        result = data_service.get_linear_usdt_instruments()

        assert len(result) == 1
        assert result[0].symbol == "BTCUSDT"
        assert result[0].base_coin == "BTC"
        assert result[0].quote_coin == "USDT"

    def test_deserialize_kline(self, data_service):
        test_data = {
            "symbol": "BTCUSDT",
            "period_start": 1633046400,
            "open_price": "50000.00",
            "high_price": "51000.00",
            "low_price": "49000.00",
            "close_price": "50500.00",
            "volume": "100.50",
            "turnover": "5025000.00",
        }

        result = data_service._deserialize_kline(test_data)

        assert result["symbol"] == "BTCUSDT"
        assert isinstance(result["period_start"], datetime)
        assert isinstance(result["open_price"], Decimal)
        assert isinstance(result["volume"], Decimal)
        assert result["open_price"] == Decimal("50000.00")

    def test_get_kline_table(self, data_service):
        assert (
            data_service._get_kline_table("5m") == Market.ByBitLinearInstrumentsKline5m
        )
        assert (
            data_service._get_kline_table("15m")
            == Market.ByBitLinearInstrumentsKline15m
        )
        assert (
            data_service._get_kline_table("1h") == Market.ByBitLinearInstrumentsKline1h
        )
        assert (
            data_service._get_kline_table("4h") == Market.ByBitLinearInstrumentsKline4h
        )
        assert (
            data_service._get_kline_table("1d") == Market.ByBitLinearInstrumentsKline1d
        )
