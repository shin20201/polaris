from app.auth.schema import LoginResponse
from app.auth.user_gateway import UserGateway
from app.core.config import Settings
from app.core.security import create_access_token
from app.integrations.kakao import get_kakao_user


async def login_with_kakao(token: str, users: UserGateway, settings: Settings) -> LoginResponse:
    kakao_user = await get_kakao_user(token, settings.kakao_app_id)
    user = users.get_or_create_kakao_user(kakao_user.kakao_id, kakao_user.name)
    return LoginResponse(access_token=create_access_token(user.user_id, settings),
                         is_new_user=user.is_new_user, name=user.name)
