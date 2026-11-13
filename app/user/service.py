from sqlalchemy.exc import IntegrityError
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.user import repository
from app.user.model import User
from app.analysis.model import Analysis
from app.guardian.model import Guardian


def get_profile(db: Session, user: User) -> dict:
    counts = db.execute(select(
        select(func.count()).select_from(Analysis).where(Analysis.user_id == user.user_id).scalar_subquery(),
        select(func.count()).select_from(Guardian).where(Guardian.protected_user_id == user.user_id).scalar_subquery(),
    )).one()
    return dict(name=user.name, email=user.email, guardian_notification=user.guardian_notification,
                analysis_count=counts[0], guardian_count=counts[1])


def get_or_create_kakao_user(
    db: Session, kakao_id: str, name: str | None, email: str | None = None,
) -> tuple[User, bool]:

    user = repository.get_by_kakao_id(db, kakao_id)
    if user is not None:
        changed = False
        if user.name == "사용자" and name:
            user.name = name
            changed = True
        if user.email != email:
            user.email = email
            changed = True
        if changed:
            db.commit()
            db.refresh(user)
        return user, False

    try:
        user = repository.create(db, kakao_id, name or "사용자", email)
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
