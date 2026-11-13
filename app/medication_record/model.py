from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Integer, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base


class MedicationRecord(Base):
    __tablename__ = "medication_record"
    __table_args__ = (CheckConstraint("(user_id IS NOT NULL) <> (guest_session_id IS NOT NULL)", name="ck_medication_record_owner"),)

    medication_record_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int | None] = mapped_column(
        ForeignKey("user.user_id", ondelete="CASCADE"), nullable=True, index=True,
    )
    guest_session_id: Mapped[int | None] = mapped_column(ForeignKey("guest_session.guest_session_id", ondelete="CASCADE"), nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(),
    )
    medications: Mapped[list[dict]] = mapped_column(JSONB, nullable=False)
