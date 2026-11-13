from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.db.database import get_db
from app.notification import service
from app.notification.model import Notification
from app.notification.schema import NotificationCreate, NotificationResponse
from app.user.model import User

router = APIRouter(prefix="/api/v1/notifications", tags=["notifications"])
Db = Annotated[Session, Depends(get_db)]
CurrentUser = Annotated[User, Depends(get_current_user)]


@router.post("", response_model=NotificationResponse)
def send_notification(body: NotificationCreate, user: CurrentUser, db: Db):
    return service.send(db, user, body)


@router.get("", response_model=list[NotificationResponse])
def list_notifications(user: CurrentUser, db: Db):
    return list(db.scalars(service.visible_query(user.user_id).order_by(Notification.notification_id.desc())))


@router.get("/{notification_id}", response_model=NotificationResponse)
def read_notification(notification_id: int, user: CurrentUser, db: Db):
    return service.get_visible(db, user.user_id, notification_id)


@router.patch("/{notification_id}/read", response_model=NotificationResponse)
def mark_notification_read(notification_id: int, user: CurrentUser, db: Db):
    return service.mark_read(db, user.user_id, notification_id)
