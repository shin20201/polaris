from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.guardian import repository
from app.guardian.model import Guardian


def add_guardian(db: Session, user_id: int, email: str) -> Guardian:
    matches = repository.find_users_by_email(db, email)
    if not matches:
        raise HTTPException(404, "해당 이메일로 가입된 회원이 없습니다.")
    if len(matches) > 1:
        raise HTTPException(409, "동일한 이메일의 회원이 여러 명이라 연결할 수 없습니다.")
    target = matches[0]
    if target.user_id == user_id:
        raise HTTPException(400, "자기 자신을 보호자로 추가할 수 없습니다.")
    if repository.get_link(db, user_id, target.user_id) is not None:
        raise HTTPException(409, "이미 연결된 보호자입니다.")
    guardian = Guardian(
        guardian_user_id=target.user_id, protected_user_id=user_id,
        nickname=target.name, kakao_email=target.email,
    )
    db.add(guardian)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        if repository.get_link(db, user_id, target.user_id) is not None:
            raise HTTPException(409, "이미 연결된 보호자입니다.") from None
        raise
    db.refresh(guardian)
    return guardian
