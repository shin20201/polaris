"""Run with python -m scripts.create_user_tables before starting the API."""
from app.auth.model import RevokedToken
from app.user.model import User
from app.db.database import engine


if __name__ == "__main__":
    with engine.begin() as connection:
        User.__table__.create(connection, checkfirst=True)
        RevokedToken.__table__.create(connection, checkfirst=True)
    print("User and auth tables are ready.")
