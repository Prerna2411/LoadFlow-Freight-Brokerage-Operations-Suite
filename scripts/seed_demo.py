from backend.app.database.init_db import init_db


if __name__ == "__main__":
    init_db()
    print("Seeded demo data. Demo password: Password123")
