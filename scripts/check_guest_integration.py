"""Run: python -m scripts.check_guest_integration. All test data is rolled back."""
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.analysis.model import Analysis
from app.analysis.model_gateway import get_analysis_model
from app.core.config import Settings, get_settings
from app.core.security import create_access_token
from app.db.database import engine, get_db
from app.finding.model import Finding
from app.finding_medication.model import FindingMedication
from app.guest.model import GuestSession
from app.guest.service import cleanup_expired
from app.main import app
from app.medication_record.model import MedicationRecord
from app.user.model import User
from scripts.check_analysis_notification_integration import FakeModel


def main():
    settings = Settings(_env_file=None, jwt_secret_key=uuid4().hex * 2, kakao_app_id=1)
    previous = app.dependency_overrides.copy()
    with engine.connect() as connection:
        transaction = connection.begin()
        db = Session(bind=connection, join_transaction_mode='create_savepoint')

        def override_db():
            yield db

        app.dependency_overrides[get_db] = override_db
        app.dependency_overrides[get_settings] = lambda: settings
        app.dependency_overrides[get_analysis_model] = lambda: FakeModel()
        try:
            user = User(kakao_id=uuid4().hex, name='Guest test member')
            db.add(user)
            db.commit()
            member_id = user.user_id
            member_headers = {'Authorization': 'Bearer ' + create_access_token(member_id, settings)}
            body = {'patient': {'age': 78}, 'medications': [{'drugs': [
                {'line_no': 1, 'source_index': 1, 'raw_name': 'A'},
                {'line_no': 1, 'source_index': 2, 'raw_name': 'B'},
            ]}]}
            root = '/api/v1/guest-sessions'
            with TestClient(app) as client:
                def start():
                    response = client.post(root)
                    assert response.status_code == 201, response.text
                    assert response.headers['cache-control'] == 'no-store'
                    return {'X-Guest-Token': response.json()['guest_token']}

                def analyze(headers):
                    response = client.post(root + '/me/analyses', headers=headers, json=body)
                    assert response.status_code == 200, response.text
                    return response.json()['analysis_id']

                guest, other = start(), start()
                aid = analyze(guest)
                record_id = db.get(Analysis, aid).medication_record_id
                finding_id = db.scalar(select(Finding.finding_id).where(Finding.analysis_id == aid))
                detail = root + f'/me/analyses/{aid}'
                assert client.get(detail, headers=guest).status_code == 200
                assert client.get(detail, headers=other).status_code == 404
                assert client.get(detail).status_code == 401
                assert client.get('/api/v1/users/me', headers=guest).status_code == 401
                assert client.get('/api/v1/analyses', headers=guest).status_code == 401
                assert client.get('/api/v1/guardians', headers=guest).status_code == 401
                assert client.get('/api/v1/notifications', headers=guest).status_code == 401
                assert client.get(f'/api/v1/analyses/{aid}', headers=member_headers).status_code == 404
                assert client.post(root + '/me/claim', headers=guest).status_code == 401
                claimed = client.post(root + '/me/claim', headers={**guest, **member_headers})
                assert claimed.status_code == 200, claimed.text
                assert claimed.json() == {'analysis_count': 1, 'medication_record_count': 1}
                assert client.get(detail, headers=guest).status_code == 401
                assert client.post(root + '/me/claim', headers={**guest, **member_headers}).status_code == 401
                assert client.get(f'/api/v1/analyses/{aid}', headers=member_headers).status_code == 200
                assert db.get(MedicationRecord, record_id).user_id == member_id
                assert db.get(MedicationRecord, record_id).guest_session_id is None
                assert db.get(Analysis, aid).guest_session_id is None
                assert db.get(Finding, finding_id) is not None
                assert len(list(db.scalars(select(FindingMedication).where(FindingMedication.finding_id == finding_id)))) == 2
                ended_id = analyze(other)
                assert client.delete(root + '/me', headers=other).status_code == 200
                assert db.get(Analysis, ended_id) is None
                assert client.delete(root + '/me', headers=other).status_code == 401
                expired = start()
                expired_id = analyze(expired)
                session_id = db.get(Analysis, expired_id).guest_session_id
                session = db.get(GuestSession, session_id)
                session.expires_at = datetime.now(timezone.utc) - timedelta(seconds=1)
                db.commit()
                assert client.get(root + f'/me/analyses/{expired_id}', headers=expired).status_code == 401
                assert db.get(Analysis, expired_id) is None
                timed = start()
                timed_id = analyze(timed)
                session = db.get(GuestSession, db.get(Analysis, timed_id).guest_session_id)
                session.expires_at = datetime.now(timezone.utc) - timedelta(seconds=1)
                db.commit()
                assert cleanup_expired(db) >= 1
                assert db.get(Analysis, timed_id) is None
                assert client.delete('/api/v1/users/me', headers=member_headers).status_code == 200
                assert db.get(Analysis, aid) is None
            print('PASS: guest create/analyze/view, isolation, member-only guards, claim/replay, end, expiry cleanup, deletion cascades.')
        finally:
            app.dependency_overrides.clear()
            app.dependency_overrides.update(previous)
            db.close()
            transaction.rollback()
            print('Test data rolled back.')


if __name__ == '__main__':
    main()
