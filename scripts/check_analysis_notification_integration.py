"""PostgreSQL integration tests with fake model; all test data rolls back.

Run: python -m scripts.check_analysis_notification_integration
"""
from copy import deepcopy
from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.analysis.model import Analysis
from app.analysis.model_gateway import get_analysis_model
from app.auth.model import RevokedToken
from app.core.config import Settings, get_settings
from app.core.security import create_access_token
from app.db.database import engine, get_db
from app.finding.model import Finding
from app.finding_medication.model import FindingMedication
from app.guardian.model import Guardian
from app.main import app
from app.medication_record.model import MedicationRecord
from app.notification.model import Notification
from app.user.model import User


class FakeModel:
    def __init__(self):
        self.output = {"rule_version": "test-1", "result": {
            "result_schema_version": "1.0", "n_items": 2,
            "is_lower_bound": True, "lower_bound_notice": "테스트 판독 한계 안내",
            "findings": [{"finding_id": "F01", "rule_type": "성분중복", "severity": 2,
                          "products": ["약A", "약B"], "ingredient": "테스트성분",
                          "medication_refs": [{"line_no": 1, "source_index": 1},
                                              {"line_no": 1, "source_index": 2}]}],
            "sentences": [{"finding_id": "F01", "text": "테스트 설명", "action_text": "테스트 행동 안내"},
                          {"finding_id": "UNKNOWN", "text": "연결되지 않은 문장"}],
        }}

    def analyze(self, request):
        return deepcopy(self.output)


def main():
    settings = Settings(_env_file=None, jwt_secret_key=uuid4().hex * 2, kakao_app_id=1)
    previous = app.dependency_overrides.copy()
    with engine.connect() as connection:
        transaction = connection.begin()
        db = Session(bind=connection, join_transaction_mode="create_savepoint")

        def override_db():
            yield db

        app.dependency_overrides[get_db] = override_db
        app.dependency_overrides[get_settings] = lambda: settings
        model = FakeModel()
        try:
            suffix = uuid4().hex
            owner = User(kakao_id=suffix+'1', name="회원", guardian_notification=False)
            guardian_user = User(kakao_id=suffix+'2', name="보호자", email=f'{suffix}@example.com')
            outsider = User(kakao_id=suffix+'3', name="다른회원")
            db.add_all([owner, guardian_user, outsider])
            db.commit()
            owner_id = owner.user_id
            link = Guardian(protected_user_id=owner.user_id, guardian_user_id=guardian_user.user_id,
                            nickname=guardian_user.name, kakao_email=guardian_user.email)
            db.add(link)
            db.commit()
            def headers(user):
                return {"Authorization": "Bearer " + create_access_token(user.user_id, settings)}
            own, guard, other = headers(owner), headers(guardian_user), headers(outsider)
            request = {"patient": {"age": 78}, "medications": [{"institution_name": "내과의원", "drugs": [
                {"line_no": 1, "source_index": 1, "raw_name": "약A", "dose_per_time": 1, "dose_unit": "정"},
                {"line_no": 1, "source_index": 2, "raw_name": "약B"},
            ]}]}
            with TestClient(app) as client:
                assert client.get('/api/v1/analyses').status_code == 401
                unavailable = client.post('/api/v1/analyses', headers=own, json=request)
                assert unavailable.status_code == 503, unavailable.text
                app.dependency_overrides[get_analysis_model] = lambda: model
                base_count = db.scalar(select(func.count()).select_from(MedicationRecord))
                model.output['result']['findings'][0]['medication_refs'][0]['line_no'] = 999
                assert client.post('/api/v1/analyses', headers=own, json=request).status_code == 502
                assert db.scalar(select(func.count()).select_from(MedicationRecord)) == base_count
                model.output['result']['findings'][0]['medication_refs'][0]['line_no'] = 1
                created = client.post('/api/v1/analyses', headers=own, json=request)
                assert created.status_code == 200, created.text
                aid = created.json()['analysis_id']
                profile = client.get('/api/v1/users/me', headers=own).json()
                assert profile['analysis_count'] == 1 and profile['guardian_count'] == 1
                other_profile = client.get('/api/v1/users/me', headers=other).json()
                assert other_profile['analysis_count'] == 0 and other_profile['guardian_count'] == 0
                detail = client.get(f'/api/v1/analyses/{aid}', headers=own)
                assert detail.status_code == 200, detail.text
                assert detail.json()['result']['sentences'][0]['text'] == '테스트 설명'
                assert client.get(f'/api/v1/analyses/{aid}', headers=other).status_code == 404
                assert client.get('/api/v1/analyses', headers=other).json() == []
                finding = db.scalar(select(Finding).where(Finding.analysis_id == aid))
                finding_id = finding.finding_id
                assert finding.details['ingredient'] == '테스트성분'
                assert len(list(db.scalars(select(FindingMedication).where(FindingMedication.finding_id == finding.finding_id)))) == 2
                assert len(client.get('/api/v1/medication-records', headers=own).json()) == 1
                notify = dict(analysis_id=aid, guardian_id=link.guardian_id, share_findings=True,
                              share_medications=False, share_map=False)
                path = '/api/v1/notifications'
                assert client.post(path, headers=own, json=notify).status_code == 403
                owner.guardian_notification = True
                db.commit()
                assert client.post(path, headers=other, json=notify).status_code == 403
                assert client.post(path, headers=own, json=dict(notify, share_map=True)).status_code == 422
                sent = client.post(path, headers=own, json=notify)
                assert sent.status_code == 200, sent.text
                nid = sent.json()['notification_id']
                assert sent.json()['status'] == 'sent' and sent.json()['sent_at'] is not None
                shared = sent.json()['payload']
                assert 'medications' not in shared and 'medication_count' not in shared
                assert shared['findings'][0]['sentences'] == [{'text': '테스트 설명', 'action_text': '테스트 행동 안내'}]
                assert shared['findings'][0]['title'] == '성분중복'
                assert 'products' not in shared['findings'][0]
                assert shared['finding_count'] == 1
                assert shared['analysis_limitations']['lower_bound_notice'] == '테스트 판독 한계 안내'
                assert shared['sharing']['map'] is False and shared['sharing']['photos'] is False
                assert client.get(f'{path}/{nid}', headers=other).status_code == 404
                assert client.get(f'/api/v1/analyses/{aid}', headers=guard).status_code == 404
                assert client.patch(f'{path}/{nid}/read', headers=own).status_code == 403
                stored = db.get(Notification, nid)
                original_payload = deepcopy(stored.payload)
                assert client.patch('/api/v1/users/me', headers=own, json={'guardian_notification': False}).status_code == 200
                assert client.get(f'{path}/{nid}', headers=guard).json()['payload'] == original_payload
                assert client.patch('/api/v1/users/me', headers=own, json={'guardian_notification': True}).status_code == 200
                read = client.patch(f'{path}/{nid}/read', headers=guard)
                assert read.status_code == 200, read.text
                assert read.json()['read_at'] is not None
                assert client.patch(f'{path}/{nid}/read', headers=guard).json()['read_at'] == read.json()['read_at']
                assert len(client.get(path, headers=guard).json()) == 1
                meds = client.post(path, headers=own, json=dict(notify, share_findings=False, share_medications=True))
                assert meds.status_code == 200, meds.text
                shared_meds = meds.json()['payload']
                assert 'findings' not in shared_meds and 'analysis_limitations' not in shared_meds
                saved_analysis = db.get(Analysis, aid)
                assert shared_meds['medications'] == saved_analysis.input_snapshot['medications']
                assert shared_meds['medication_count'] == 2 and shared_meds['institution_count'] == 1
                combined = client.post(path, headers=own, json=dict(notify, share_medications=True))
                assert combined.status_code == 200, combined.text
                assert 'findings' in combined.json()['payload'] and 'medications' in combined.json()['payload']
                assert client.delete('/api/v1/analyses', headers=other).status_code == 200
                assert client.get(f'/api/v1/analyses/{aid}', headers=own).status_code == 200
                assert client.delete('/api/v1/analyses', headers=own).status_code == 200
                assert db.get(Analysis, aid) is None
                assert client.get('/api/v1/users/me', headers=own).json()['analysis_count'] == 0
                assert db.get(Finding, finding_id) is None
                assert client.get(path, headers=own).json() == []
                # 복용약 기록은 분석 기록 삭제와 별개로 보관하며, 회원 탈퇴 시 함께 삭제됩니다.
                assert len(client.get('/api/v1/medication-records', headers=own).json()) == 1
                assert client.delete('/api/v1/users/me', headers=own).status_code == 200
                assert db.scalar(select(MedicationRecord).where(MedicationRecord.user_id == owner_id)) is None
            print('PASS: analysis atomic save, JSON preservation, finding links, ownership, consent, sharing filters, account sharing/read, cascade deletion.')
        finally:
            app.dependency_overrides.clear()
            app.dependency_overrides.update(previous)
            db.close()
            transaction.rollback()
            print('Test data rolled back; no external messages sent.')


if __name__ == '__main__':
    main()
