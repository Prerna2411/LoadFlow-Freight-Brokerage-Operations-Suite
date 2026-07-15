from sqlalchemy import inspect

from backend.app.main import Base, engine


def metadata_tables() -> list[str]:
    return sorted(Base.metadata.tables.keys())


def database_tables() -> list[str]:
    inspector = inspect(engine)
    return sorted(inspector.get_table_names())


def create_all_tables() -> None:
    Base.metadata.create_all(bind=engine)


__all__ = ["Base", "create_all_tables", "database_tables", "metadata_tables"]
