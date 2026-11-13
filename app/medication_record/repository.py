from sqlalchemy import select
from sqlalchemy.orm import Session

from app.medication_record.model import MedicationRecord


def create(db: Session, user_id: int | None, medications: list[dict], guest_session_id: int | None = None) -> MedicationRecord:
    record = MedicationRecord(user_id=user_id, guest_session_id=guest_session_id, medications=medications)
    db.add(record)
    db.flush()
    return record


def list_for_user(db: Session, user_id: int) -> list[MedicationRecord]:
    return list(db.scalars(select(MedicationRecord).where(
        MedicationRecord.user_id == user_id,
    ).order_by(MedicationRecord.created_at.desc(), MedicationRecord.medication_record_id.desc())))
