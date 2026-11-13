from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base


class Analysis(Base):
    __tablename__ = "analysis"
    __table_args__ = (CheckConstraint("(user_id IS NOT NULL) <> (guest_session_id IS NOT NULL)", name="ck_analysis_owner"),)

    analysis_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("user.user_id", ondelete="CASCADE"), nullable=True, index=True)
    guest_session_id: Mapped[int | None] = mapped_column(ForeignKey("guest_session.guest_session_id", ondelete="CASCADE"), nullable=True, index=True)
    medication_record_id: Mapped[int] = mapped_column(ForeignKey("medication_record.medication_record_id", ondelete="CASCADE"), index=True)
    rule_version: Mapped[str] = mapped_column(String(255))
    analyzed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    input_snapshot: Mapped[dict] = mapped_column(JSONB)
    result: Mapped[dict] = mapped_column(JSONB)
