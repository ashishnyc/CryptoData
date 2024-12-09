import pytest
from unittest.mock import Mock, patch


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
