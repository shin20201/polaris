"""Run: python -m scripts.create_analysis_tables (existing tables/data are preserved)."""
from app.db.database import engine
from app.user.model import User
from app.guest.model import GuestSession
from app.guardian.model import Guardian
from app.medication_record.model import MedicationRecord
from app.analysis.model import Analysis
from app.finding.model import Finding
from app.finding_medication.model import FindingMedication
from app.notification.model import Notification


if __name__ == "__main__":
    with engine.begin() as connection:
        for model in (User, GuestSession, Guardian, MedicationRecord, Analysis, Finding, FindingMedication, Notification):
            model.__table__.create(connection, checkfirst=True)
    print("Analysis, Finding, FindingMedication and Notification tables are ready.")
