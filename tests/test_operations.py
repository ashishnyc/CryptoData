import pytest
from sqlmodel import create_engine, Session
from db.Operations import get_db_connection_str, get_engine, get_session
from Config import settings


def test_get_db_connection_str_with_custom_str():
    custom_str = "sqlite:///./test.db"
    assert get_db_connection_str(custom_str) == custom_str


def test_get_db_connection_str_with_default():
    assert get_db_connection_str() == settings.db_connection_string


def test_get_engine_with_custom_str():
    custom_str = "sqlite:///./test.db"
    engine = get_engine(custom_str)
    assert isinstance(engine, create_engine(custom_str).__class__)


def test_get_engine_with_default():
    engine = get_engine()
    assert isinstance(engine, create_engine(settings.db_connection_string).__class__)


def test_get_session_with_custom_str():
    custom_str = "sqlite:///./test.db"
    session = get_session(custom_str)
    assert isinstance(session, Session)
    session.close()


def test_get_session_with_default():
    session = get_session()
    assert isinstance(session, Session)
    session.close()
