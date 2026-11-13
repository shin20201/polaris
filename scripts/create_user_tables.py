"""Run with python -m scripts.create_user_tables before starting the API."""
from sqlalchemy import text

from app.auth.model import RevokedToken
from app.user.model import User
from app.db.database import engine


if __name__ == "__main__":
    with engine.begin() as connection:
        User.__table__.create(connection, checkfirst=True)
        connection.execute(text('ALTER TABLE public."user" ADD COLUMN IF NOT EXISTS email VARCHAR(320)'))
        connection.execute(text('CREATE INDEX IF NOT EXISTS ix_user_email ON public."user" (email)'))
        RevokedToken.__table__.create(connection, checkfirst=True)
    print("User and auth tables are ready.")
