from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.db.database import get_db
from app.guardian import repository, service
from app.guardian.schema import GuardianCreate, GuardianResponse
from app.user.model import User

router = APIRouter(prefix="/api/v1/guardians", tags=["guardians"])


@router.get("", response_model=list[GuardianResponse])
def list_guardians(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):

    return repository.list_for_user(db, current_user.user_id)


@router.post("", response_model=GuardianResponse, status_code=201)
def add_guardian(
    body: GuardianCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    return service.add_guardian(db, current_user.user_id, str(body.email))
