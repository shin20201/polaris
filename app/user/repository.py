from sqlalchemy import select
from sqlalchemy.orm import Session

from app.user.model import User


def get_by_id(db: Session, user_id: int) -> User | None:
    return db.get(User, user_id)


def get_by_kakao_id(db: Session, kakao_id: str) -> User | None:
    return db.scalar(select(User).where(User.kakao_id == kakao_id))


def create(db: Session, kakao_id: str, name: str) -> User:
    user = User(kakao_id=kakao_id, name=name, guardian_notification=False)
    db.add(user)
    db.flush()
    return user


def delete(db: Session, user: User) -> None:
    db.delete(user)