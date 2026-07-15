from backend.app.database.base import create_all_tables, database_tables
from backend.app.database.session import session_scope
from backend.app.main import seed_demo, seed_permissions


def init_db(seed: bool = True) -> dict[str, list[str]]:
    create_all_tables()
    if seed:
        with session_scope() as db:
            seed_permissions(db)
            seed_demo(db)
    return {"tables": database_tables()}


def init_permissions_only() -> None:
    with session_scope() as db:
        seed_permissions(db)


if __name__ == "__main__":
    result = init_db(seed=True)
    print(f"Initialized database with tables: {', '.join(result['tables'])}")
