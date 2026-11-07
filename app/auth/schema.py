from pydantic import BaseModel, Field, SecretStr


class KakaoLoginRequest(BaseModel):
    kakao_token: SecretStr = Field(min_length=1, max_length=4096)


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    is_new_user: bool
    name: str | None
