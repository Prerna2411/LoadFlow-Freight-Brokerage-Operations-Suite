from collections.abc import Generator
from contextlib import contextmanager

from sqlalchemy import text
from sqlalchemy.orm import Session

from backend.app.main import DATABASE_URL, SessionLocal, engine, get_db


@contextmanager
def session_scope() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def database_url() -> str:
    return DATABASE_URL


def check_database_connection() -> bool:
    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))
    return True


__all__ = ["SessionLocal", "check_database_connection", "database_url", "get_db", "session_scope"]
