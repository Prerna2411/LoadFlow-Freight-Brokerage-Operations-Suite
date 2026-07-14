from backend.app.main import init_app_database


def init_db() -> None:
    init_app_database()


if __name__ == "__main__":
    init_db()
