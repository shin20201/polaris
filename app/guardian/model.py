from sqlalchemy import ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base


class Guardian(Base):

    __tablename__ = "guardian"
    __table_args__ = (UniqueConstraint("guardian_user_id", "protected_user_id", name="uq_guardian_pair"),)

    guardian_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    guardian_user_id: Mapped[int] = mapped_column(
        ForeignKey("user.user_id", ondelete="CASCADE"), nullable=False, index=True
    )

    protected_user_id: Mapped[int] = mapped_column(
        ForeignKey("user.user_id", ondelete="CASCADE"), nullable=False, index=True
    )

    nickname: Mapped[str] = mapped_column(String(50), nullable=False)
    profile_image_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    kakao_email: Mapped[str | None] = mapped_column(String(255), nullable=True)