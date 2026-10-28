from sqlalchemy import Boolean, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base


class User(Base):
    
    __tablename__ = "user"

    user_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    kakao_id: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)

    name: Mapped[str] = mapped_column(String(50), nullable=False)

    guardian_notification: Mapped[bool | None] = mapped_column(
        Boolean, nullable=True, default=False, server_default="false"
    )