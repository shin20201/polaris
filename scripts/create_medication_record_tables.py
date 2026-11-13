"""Run: python -m scripts.create_medication_record_tables"""
from app.db.database import engine
from app.user.model import User
from app.guest.model import GuestSession
from app.medication_record.model import MedicationRecord


if __name__ == "__main__":
    with engine.begin() as connection:
        GuestSession.__table__.create(connection, checkfirst=True)
        MedicationRecord.__table__.create(connection, checkfirst=True)
    print("MedicationRecord table is ready.")
