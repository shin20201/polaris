from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.db.database import get_db
from app.medication_record import repository
from app.medication_record.schema import MedicationRecordResponse
from app.user.model import User

router = APIRouter(prefix="/api/v1/medication-records", tags=["medication-records"])


@router.get("", response_model=list[MedicationRecordResponse])
def list_medication_records(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    return repository.list_for_user(db, current_user.user_id)
