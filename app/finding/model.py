from sqlalchemy import ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base


class Finding(Base):
    __tablename__ = "finding"
    __table_args__ = (UniqueConstraint("analysis_id", "result_finding_id"),)

    finding_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    analysis_id: Mapped[int] = mapped_column(ForeignKey("analysis.analysis_id", ondelete="CASCADE"), index=True)
    result_finding_id: Mapped[str] = mapped_column(String(100))
    rule_type: Mapped[str] = mapped_column(String(100))
    severity: Mapped[int] = mapped_column(Integer)
    details: Mapped[dict] = mapped_column(JSONB)
