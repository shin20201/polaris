from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, Response
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_claims
from app.auth.model import RevokedToken
from app.auth.schema import KakaoLoginRequest, LoginResponse
from app.auth.service import login_with_kakao
from app.auth.user_gateway import UserGateway, get_user_gateway
from app.core.config import Settings, get_settings
from app.db.database import get_db

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


@router.post("/kakao", response_model=LoginResponse)
async def kakao_login(
    body: KakaoLoginRequest,
    users: Annotated[UserGateway, Depends(get_user_gateway)],
    settings: Annotated[Settings, Depends(get_settings)],
    response: Response,
) -> LoginResponse:
    result = await login_with_kakao(body.kakao_token.get_secret_value(), users, settings)
    response.headers["Cache-Control"] = "no-store"
    return result


@router.post("/logout", status_code=200)
def logout(
    claims: Annotated[dict, Depends(get_current_claims)],
    db: Annotated[Session, Depends(get_db)],
) -> dict:
    db.execute(insert(RevokedToken).values(
        jti=claims["jti"], expires_at=datetime.fromtimestamp(claims["exp"], timezone.utc),
    ).on_conflict_do_nothing(index_elements=["jti"]))
    db.commit()
    return {"message": "로그아웃되었습니다."}
