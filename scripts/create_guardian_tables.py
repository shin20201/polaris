"""Run: python -m scripts.create_guardian_tables"""
from sqlalchemy import text

from app.db.database import engine
from app.user.model import User
from app.guardian.model import Guardian


if __name__ == "__main__":
    with engine.begin() as connection:
        Guardian.__table__.create(connection, checkfirst=True)
        connection.execute(text('ALTER TABLE guardian ALTER COLUMN kakao_email TYPE VARCHAR(320)'))
    print("Guardian table is ready.")
