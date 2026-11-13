from typing import Annotated

from fastapi import Depends
from fastapi.security import APIKeyHeader
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.guest.model import GuestSession
from app.guest.service import require_guest

guest_key = APIKeyHeader(name="X-Guest-Token", scheme_name="GuestToken", auto_error=False)


def get_guest_session(
    db: Annotated[Session, Depends(get_db)],
    token: Annotated[str | None, Depends(guest_key)],
) -> GuestSession:
    return require_guest(db, token)
