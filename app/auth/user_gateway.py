from dataclasses import dataclass
from typing import Protocol

from fastapi import Depends
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.user import service


@dataclass(frozen=True)
class LoginUser:
    user_id: int
    name: str | None
    is_new_user: bool


class UserGateway(Protocol):
    def get_or_create_kakao_user(self, kakao_id: int, name: str | None, email: str | None = None) -> LoginUser:
        """Atomically find/create and commit a user; kakao_id must be unique."""
        ...


class DatabaseUserGateway:
    def __init__(self, db: Session):
        self.db = db

    def get_or_create_kakao_user(self, kakao_id: int, name: str | None, email: str | None = None) -> LoginUser:
        user, is_new = service.get_or_create_kakao_user(
            self.db, str(kakao_id), name, email,
        )
        return LoginUser(user.user_id, user.name, is_new)


def get_user_gateway(db: Session = Depends(get_db)) -> UserGateway:
    return DatabaseUserGateway(db)
