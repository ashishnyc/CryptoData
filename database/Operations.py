from sqlmodel import create_engine, Session
import logging
from Config import settings

logger = logging.getLogger(__name__)


def get_db_connection_str(connnection_str: str = None):
    if connnection_str:
        return connnection_str
    return settings.db_connection_string


def get_engine(connnection_str: str = None):
    return create_engine(get_db_connection_str(connnection_str), future=True)


def get_session(connection_str: str = None):
    db = Session(get_engine(connection_str))
    return db
