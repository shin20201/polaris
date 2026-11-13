from datetime import datetime, timedelta, timezone
from hashlib import sha256
from secrets import token_urlsafe

from fastapi import HTTPException
from sqlalchemy import delete, select, update
from sqlalchemy.orm import Session

from app.analysis.model import Analysis
from app.guest.model import GuestSession
from app.medication_record.model import MedicationRecord


def cleanup_expired(db: Session) -> int:
    result = db.execute(delete(GuestSession).where(GuestSession.expires_at <= datetime.now(timezone.utc)))
    db.commit()
    return result.rowcount


def create_session(db: Session) -> dict:
    cleanup_expired(db)
    token = token_urlsafe(32)
    guest = GuestSession(token_hash=sha256(token.encode()).hexdigest(),
                         expires_at=datetime.now(timezone.utc) + timedelta(hours=24))
    db.add(guest)
    db.commit()
    db.refresh(guest)
    return dict(guest_token=token, expires_at=guest.expires_at)


def require_guest(db: Session, token: str | None) -> GuestSession:
    if not token or len(token) > 256:
        raise HTTPException(401, "유효한 비회원 토큰이 필요합니다.")
    # 이전·종료·분석 저장이 같은 세션에서 동시에 진행되지 않도록 잠급니다.
    guest = db.scalar(select(GuestSession).where(
        GuestSession.token_hash == sha256(token.encode()).hexdigest(),
    ).with_for_update())
    if guest is None:
        raise HTTPException(401, "유효하지 않은 비회원 토큰입니다.")
    if guest.expires_at <= datetime.now(timezone.utc):
        db.delete(guest)
        db.commit()
        raise HTTPException(401, "비회원 이용 시간이 만료되었습니다.")
    return guest


def claim(db: Session, guest: GuestSession, user_id: int) -> dict:
    try:
        records = db.execute(update(MedicationRecord).where(
            MedicationRecord.guest_session_id == guest.guest_session_id,
        ).values(user_id=user_id, guest_session_id=None))
        analyses = db.execute(update(Analysis).where(
            Analysis.guest_session_id == guest.guest_session_id,
        ).values(user_id=user_id, guest_session_id=None))
        result = dict(medication_record_count=records.rowcount, analysis_count=analyses.rowcount)
        db.delete(guest)
        db.commit()
        return result
    except Exception:
        db.rollback()
        raise
