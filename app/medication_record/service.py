from sqlalchemy.orm import Session

from app.medication_record import repository
from app.medication_record.model import MedicationRecord
from app.medication_record.schema import MedicationRecordCreate


def create_record(db: Session, user_id: int | None, body: MedicationRecordCreate, guest_session_id: int | None = None) -> MedicationRecord:
    """Analysis에서 호출하며 분석 결과와 함께 호출자가 commit/rollback합니다."""
    return repository.create(db, user_id, body.model_dump(mode="json")["medications"], guest_session_id)
