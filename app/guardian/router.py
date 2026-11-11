from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.db.database import get_db
from app.guardian.model import Guardian
from app.guardian.schema import GuardianResponse
from app.user.model import User

router = APIRouter(prefix="/api/v1/guardians", tags=["guardians"])


@router.get("", response_model=list[GuardianResponse])
def list_guardians(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):

    return db.scalars(
        select(Guardian)
        .where(Guardian.protected_user_id == current_user.user_id)
        .order_by(Guardian.guardian_id)
    ).all()
