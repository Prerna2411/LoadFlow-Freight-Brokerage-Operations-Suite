from backend.app.main import SessionLocal, seed_permissions


if __name__ == "__main__":
    with SessionLocal() as db:
        seed_permissions(db)
        db.commit()
    print("Seeded permission catalog.")
