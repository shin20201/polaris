from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.analysis.service import get_owned
from app.guardian.model import Guardian
from app.notification.model import Notification
from app.notification.schema import NotificationCreate
from app.notification.payload import build_payload
from app.user.model import User


def visible_query(user_id: int):
    return select(Notification).join(Guardian, Notification.guardian_id == Guardian.guardian_id).where(
        (Notification.user_id == user_id) |
        ((Guardian.guardian_user_id == user_id) & (Notification.status == "sent")),
    )


def get_visible(db: Session, user_id: int, notification_id: int) -> Notification:
    notification = db.scalar(visible_query(user_id).where(Notification.notification_id == notification_id))
    if notification is None:
        raise HTTPException(404, "알림을 찾을 수 없습니다.")
    return notification


def send(db: Session, user: User, body: NotificationCreate):
    if user.guardian_notification is not True:
        raise HTTPException(403, "보호자 알림 전송에 동의해야 합니다.")
    guardian = db.scalar(select(Guardian).where(Guardian.guardian_id == body.guardian_id,
                                              Guardian.protected_user_id == user.user_id))
    if guardian is None:
        raise HTTPException(404, "연결된 보호자를 찾을 수 없습니다.")
    recipient = db.get(User, guardian.guardian_user_id)
    if recipient is None:
        raise HTTPException(409, "보호자 계정을 확인할 수 없습니다.")
    analysis = get_owned(db, user.user_id, body.analysis_id)
    payload = build_payload(analysis, body, user.name)
    notification = Notification(user_id=user.user_id, guardian_id=guardian.guardian_id,
                                analysis_id=analysis.analysis_id, payload=payload,
                                share_findings=body.share_findings, share_medications=body.share_medications,
                                share_map=False, status="sent", sent_at=datetime.now(timezone.utc))
    db.add(notification)
    db.commit()
    db.refresh(notification)
    return notification


def mark_read(db: Session, user_id: int, notification_id: int):
    notification = get_visible(db, user_id, notification_id)
    guardian = db.get(Guardian, notification.guardian_id)
    if guardian.guardian_user_id != user_id:
        raise HTTPException(403, "알림을 받은 보호자만 읽음 처리할 수 있습니다.")
    if notification.status != "sent":
        raise HTTPException(409, "전송 완료된 알림만 읽음 처리할 수 있습니다.")
    db.execute(update(Notification).where(Notification.notification_id == notification_id,
                                         Notification.read_at.is_(None)).values(read_at=datetime.now(timezone.utc)))
    db.commit()
    db.refresh(notification)
    return notification
