from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.user import repository
from app.user.model import User


def get_or_create_kakao_user(db: Session, kakao_id: str, name: str | None) -> tuple[User, bool]:

    user = repository.get_by_kakao_id(db, kakao_id)
    if user is not None:
        if user.name == "사용자" and name:
            user.name = name
            db.commit()
            db.refresh(user)
        return user, False

    try:
        user = repository.create(db, kakao_id, name or "사용자")
        db.commit()
    except IntegrityError:
        db.rollback()
        existing = repository.get_by_kakao_id(db, kakao_id)
        if existing is None:
            raise
        return existing, False

    db.refresh(user)
    return user, True


def update_guardian_notification(db: Session, user: User, guardian_notification: bool) -> User:
    user.guardian_notification = guardian_notification
    db.commit()
    db.refresh(user)
    return user


def withdraw(db: Session, user: User) -> None:
    repository.delete(db, user)
    db.commit()
