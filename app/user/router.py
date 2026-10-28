from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.db.database import get_db
from app.user import service
from app.user.model import User
from app.user.schema import (
    GuardianNotificationResponse,
    GuardianNotificationUpdate,
    UserResponse,
)

router = APIRouter(prefix="/api/v1/users", tags=["users"])


@router.get("/me", response_model=UserResponse)
def read_me(current_user: User = Depends(get_current_user)):
    return current_user


@router.patch("/me", response_model=GuardianNotificationResponse)
def update_guardian_notification(
    body: GuardianNotificationUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):

    return service.update_guardian_notification(db, current_user, body.guardian_notification)


@router.delete("/me")
def withdraw(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):

    service.withdraw(db, current_user)
    return {"message": "회원 탈퇴가 완료되었습니다."}
