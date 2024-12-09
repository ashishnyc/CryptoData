import pytest
from unittest.mock import Mock, patch


@pytest.fixture(autouse=True)
def mock_settings():
    """Mock settings before they're loaded"""
    mock_settings = Mock()
    mock_settings.bybit_api_key = "test_key"
    mock_settings.bybit_api_secret = "test_secret"
    mock_settings.bybit_testnet = True
    mock_settings.db_connection_string = (
        "postgresql://postgres:postgres@localhost:5432/test_db"
    )
    mock_settings.better_stack_source_token = "test_token"

    with patch("Config.Settings") as MockSettings:
        MockSettings.return_value = mock_settings
        with patch("Config.settings", mock_settings):
            yield mock_settings


@pytest.fixture(autouse=True)
def mock_db_operations():
    """Mock database operations for all tests"""
    with patch("database.Operations.get_session") as mock:
        mock.return_value = Mock()
        yield mock


@pytest.fixture(autouse=True)
def mock_redis():
    """Mock Redis for all tests"""
    with patch("redis.Redis") as mock:
        yield mock


@pytest.fixture
def mock_market_data():
    """Mock ByBit MarketData class"""
    with patch("xchanges.ByBit.MarketData") as mock:
        yield mock
