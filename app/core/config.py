from functools import lru_cache

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    jwt_secret_key: SecretStr = Field(min_length=32)
    jwt_access_token_expire_minutes: int = Field(default=60, ge=1)
    jwt_issuer: str = "polaris"
    kakao_app_id: int = Field(gt=0)


@lru_cache
def get_settings() -> Settings:
    return Settings()
