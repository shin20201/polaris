from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.guardian.model import Guardian
from app.user.model import User


def find_users_by_email(db: Session, email: str) -> list[User]:
    return list(db.scalars(select(User).where(func.lower(User.email) == email.lower()).limit(2)))


def get_link(db: Session, protected_user_id: int, guardian_user_id: int) -> Guardian | None:
    return db.scalar(select(Guardian).where(
        Guardian.protected_user_id == protected_user_id,
        Guardian.guardian_user_id == guardian_user_id,
    ))


def list_for_user(db: Session, user_id: int):
    # 이름과 이메일은 연결된 회원의 최신 정보로 반환합니다.
    return db.execute(select(
        Guardian.guardian_id, User.name.label("nickname"),
        Guardian.profile_image_url, User.email.label("kakao_email"),
    ).join(User, User.user_id == Guardian.guardian_user_id).where(
        Guardian.protected_user_id == user_id,
    ).order_by(Guardian.guardian_id)).mappings().all()
