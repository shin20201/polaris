"""Run: python -m scripts.check_medication_record_integration (test data rolls back)."""
from uuid import uuid4

from fastapi.testclient import TestClient
from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.core.security import create_access_token
from app.db.database import engine, get_db
from app.main import app
from app.medication_record.model import MedicationRecord
from app.medication_record.schema import MedicationRecordCreate
from app.medication_record.service import create_record
from app.user.model import User


def main():
    settings = Settings(_env_file=None, jwt_secret_key=uuid4().hex * 2, kakao_app_id=1)
    item = dict(line_no=1, source_index=1, raw_name="타이레놀정500밀리그람",
                ocr_confidence=0.94, dose_per_time=1.0, dose_unit="정",
                freq_per_day=3, duration_days=5)
    body = MedicationRecordCreate(medications=[dict(institution_name="내과의원", drugs=[item])])
    for drugs in ([item, item], [dict(item, dose_per_time=-1)]):
        try:
            MedicationRecordCreate(medications=[dict(drugs=drugs)])
        except ValidationError:
            pass
        else:
            raise AssertionError("Invalid medication payload accepted")
    missing_dose = MedicationRecordCreate(medications=[dict(drugs=[dict(line_no=1, source_index=2, raw_name="미판독약")])])
    assert missing_dose.medications[0].drugs[0].dose_per_time is None
    previous = app.dependency_overrides.copy()
    with engine.connect() as connection:
        transaction = connection.begin()
        db = Session(bind=connection, join_transaction_mode="create_savepoint")

        def override_db():
            yield db

        app.dependency_overrides[get_db] = override_db
        app.dependency_overrides[get_settings] = lambda: settings
        try:
            suffix = uuid4().hex
            owner = User(kakao_id=suffix + '1', name="회원")
            other = User(kakao_id=suffix + '2', name="다른회원")
            db.add_all([owner, other])
            db.commit()
            headers = {"Authorization": "Bearer " + create_access_token(owner.user_id, settings)}
            other_headers = {"Authorization": "Bearer " + create_access_token(other.user_id, settings)}
            path = '/api/v1/medication-records'
            with TestClient(app) as client:
                assert client.get(path).status_code == 401
                assert client.get(path, headers=headers).json() == []
                record = create_record(db, owner.user_id, body)
                db.commit()
                record_id = record.medication_record_id
                result = client.get(path, headers=headers)
                assert result.status_code == 200, result.text
                assert result.json()[0]['medications'] == body.model_dump()['medications']
                assert result.json()[0]['medication_record_id'] == record_id
                assert client.get(path, headers=other_headers).json() == []
                # 저장 함수가 commit하지 않아 분석 실패 시 함께 롤백할 수 있어야 합니다.
                rolled_back = create_record(db, owner.user_id, missing_dose)
                rolled_back_id = rolled_back.medication_record_id
                db.rollback()
                assert db.get(MedicationRecord, rolled_back_id) is None
                assert client.delete('/api/v1/users/me', headers=headers).status_code == 200
                assert db.scalar(select(MedicationRecord).where(MedicationRecord.medication_record_id == record_id)) is None
            print("PASS: payload validation, JSONB save/list, auth, isolation, rollback, withdrawal cascade.")
        finally:
            app.dependency_overrides.clear()
            app.dependency_overrides.update(previous)
            db.close()
            transaction.rollback()
            print("Test data rolled back.")


if __name__ == '__main__':
    main()
