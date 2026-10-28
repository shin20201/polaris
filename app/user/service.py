from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.user import repository
from app.user.model import User


def get_or_create_kakao_user(db: Session, kakao_id: str, name: str) -> tuple[User, bool]:

    user = repository.get_by_kakao_id(db, kakao_id)
    if user is not None:
        return user, False

    try:
        user = repository.create(db, kakao_id, name)
        db.commit()
    except IntegrityError:
        db.rollback()
        return repository.get_by_kakao_id(db, kakao_id), False

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
