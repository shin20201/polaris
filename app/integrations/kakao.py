from dataclasses import dataclass

import httpx
from fastapi import HTTPException

from app.core.security import unauthorized


@dataclass(frozen=True)
class KakaoUser:
    kakao_id: int
    name: str | None
    email: str | None = None


async def get_kakao_user(token: str, app_id: int) -> KakaoUser:
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            info = await client.get("https://kapi.kakao.com/v1/user/access_token_info", headers={"Authorization": f"Bearer {token}"})
            if info.status_code in (400, 401):
                raise unauthorized()
            info.raise_for_status()
            token_info = info.json()
            if token_info.get("app_id") != app_id:
                raise unauthorized()
            response = await client.get("https://kapi.kakao.com/v2/user/me", headers={"Authorization": f"Bearer {token}"})
            if response.status_code in (400, 401):
                raise unauthorized()
            response.raise_for_status()
            data = response.json()
            kakao_id = data["id"]
            if type(kakao_id) is not int or kakao_id <= 0 or token_info.get("id") != kakao_id:
                raise ValueError
            name = data.get("kakao_account", {}).get("profile", {}).get("nickname")
            if name is None:
                name = data.get("properties", {}).get("nickname")
            if name is not None and not isinstance(name, str):
                raise ValueError
            account = data.get("kakao_account", {})
            email = account.get("email")
            if email is not None and (not isinstance(email, str) or len(email) > 320):
                raise ValueError
            # 보호자 연결에는 카카오가 유효성과 소유자 인증을 확인한 이메일만 사용합니다.
            if account.get("is_email_valid") is not True or account.get("is_email_verified") is not True:
                email = None
            return KakaoUser(kakao_id, name, email)
    except httpx.RequestError:
        raise HTTPException(503, "카카오 인증 서버에 연결할 수 없습니다.") from None
    except (httpx.HTTPStatusError, ValueError, KeyError, TypeError, AttributeError):
        raise HTTPException(502, "카카오 인증 응답을 확인할 수 없습니다.") from None
