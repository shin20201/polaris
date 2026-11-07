"""Run with python -m scripts.create_auth_tables before starting the API."""
from app.auth.model import RevokedToken
from app.db.database import engine

if __name__ == "__main__":
    RevokedToken.__table__.create(engine, checkfirst=True)
