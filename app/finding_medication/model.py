from sqlalchemy import ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base


class FindingMedication(Base):
    __tablename__ = "finding_medication"

    finding_id: Mapped[int] = mapped_column(ForeignKey("finding.finding_id", ondelete="CASCADE"), primary_key=True)
    medication_record_id: Mapped[int] = mapped_column(ForeignKey("medication_record.medication_record_id", ondelete="CASCADE"), primary_key=True)
    line_no: Mapped[int] = mapped_column(Integer, primary_key=True)
    source_index: Mapped[int] = mapped_column(Integer, primary_key=True)
