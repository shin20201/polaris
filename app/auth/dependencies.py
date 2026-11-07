from typing import Annotated

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.auth.model import RevokedToken
from app.core.config import Settings, get_settings
from app.core.security import decode_access_token, unauthorized
from app.db.database import get_db
from app.user.model import User
from app.user.repository import get_by_id

bearer = HTTPBearer(auto_error=False)


def get_current_claims(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
    db: Annotated[Session, Depends(get_db)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> dict:
    if credentials is None:
        raise unauthorized()
    claims = decode_access_token(credentials.credentials, settings)
    if db.get(RevokedToken, claims["jti"]) is not None:
        raise unauthorized()
    return claims


def get_current_user_id(claims: Annotated[dict, Depends(get_current_claims)]) -> int:
    return int(claims["sub"])


def get_current_user(
    user_id: Annotated[int, Depends(get_current_user_id)],
    db: Annotated[Session, Depends(get_db)],
) -> User:
    user = get_by_id(db, user_id)
    if user is None:
        raise unauthorized()
    return user
