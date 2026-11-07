from datetime import datetime, timedelta, timezone
from uuid import uuid4

import jwt
from fastapi import HTTPException

from app.core.config import Settings


def unauthorized() -> HTTPException:
    return HTTPException(401, "유효하지 않거나 만료된 인증 정보입니다.", headers={"WWW-Authenticate": "Bearer"})


def create_access_token(user_id: int, settings: Settings) -> str:
    now = datetime.now(timezone.utc)
    return jwt.encode(
        {"sub": str(user_id), "iat": now, "exp": now + timedelta(minutes=settings.jwt_access_token_expire_minutes),
         "jti": str(uuid4()), "iss": settings.jwt_issuer, "type": "access"},
        settings.jwt_secret_key.get_secret_value(), algorithm="HS256",
    )


def decode_access_token(token: str, settings: Settings) -> dict:
    try:
        claims = jwt.decode(
            token, settings.jwt_secret_key.get_secret_value(), algorithms=["HS256"],
            issuer=settings.jwt_issuer, options={"require": ["sub", "exp", "iat", "jti", "iss", "type"]},
        )
        if claims["type"] != "access" or not claims["sub"].isdigit() or int(claims["sub"]) <= 0:
            raise ValueError
        if not isinstance(claims["jti"], str) or not claims["jti"]:
            raise ValueError
        return claims
    except (jwt.InvalidTokenError, ValueError, TypeError, AttributeError):
        raise unauthorized() from None
