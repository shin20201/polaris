"""Run: python -m scripts.check_guardian_integration

Uses PostgreSQL and rolls back all test data.
"""
from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.core.security import create_access_token
from app.db.database import engine, get_db
from app.guardian.model import Guardian
from app.main import app
from app.user.model import User


def main():
    settings = Settings(_env_file=None, jwt_secret_key=uuid4().hex * 2, kakao_app_id=1)
    previous_overrides = app.dependency_overrides.copy()
    with engine.connect() as connection:
        transaction = connection.begin()
        db = Session(bind=connection, join_transaction_mode="create_savepoint")

        def override_db():
            yield db

        app.dependency_overrides[get_db] = override_db
        app.dependency_overrides[get_settings] = lambda: settings
        try:
            suffix = uuid4().hex
            owner = User(kakao_id=suffix + '1', name="회원", email=f"owner-{suffix}@example.com")
            target = User(kakao_id=suffix + '2', name="보호자", email=f"guardian-{suffix}@example.com")
            other = User(kakao_id=suffix + '3', name="다른회원", email=f"other-{suffix}@example.com")
            db.add_all([owner, target, other])
            db.commit()
            owner_id, target_id = owner.user_id, target.user_id
            headers = {"Authorization": "Bearer " + create_access_token(owner_id, settings)}
            other_headers = {"Authorization": "Bearer " + create_access_token(other.user_id, settings)}
            path = '/api/v1/guardians'
            with TestClient(app) as client:
                assert client.get(path).status_code == 401
                assert client.post(path, json={"email": target.email}).status_code == 401
                assert client.get(path, headers=headers).json() == []
                assert client.post(path, headers=headers, json={"email": "invalid"}).status_code == 422
                assert client.post(path, headers=headers, json={"email": f"missing-{suffix}@example.com"}).status_code == 404
                assert client.post(path, headers=headers, json={"email": owner.email}).status_code == 400
                added = client.post(path, headers=headers, json={"email": target.email.upper()})
                assert added.status_code == 201, added.text
                assert added.json()['name'] == "보호자"
                assert added.json()['kakao_email'] == target.email
                assert client.post(path, headers=headers, json={"email": target.email}).status_code == 409
                assert len(client.get(path, headers=headers).json()) == 1
                assert client.get(path, headers=other_headers).json() == []
                target.name = "새닉네임"
                db.commit()
                assert client.get(path, headers=headers).json()[0]['name'] == "새닉네임"
                duplicate = User(kakao_id=suffix + '4', name="중복이메일", email=target.email)
                db.add(duplicate)
                db.commit()
                assert client.post(path, headers=other_headers, json={"email": target.email}).status_code == 409
                db.delete(duplicate)
                db.delete(target)
                db.commit()
                assert client.get(path, headers=headers).json() == []
                assert db.scalar(select(Guardian).where(Guardian.guardian_user_id == target_id)) is None
                assert client.delete('/api/v1/users/me', headers=headers).status_code == 200
            print("PASS: auth, add/list, invalid/missing/self/duplicate email, isolation, current profile, cascade deletion.")
        finally:
            app.dependency_overrides.clear()
            app.dependency_overrides.update(previous_overrides)
            db.close()
            transaction.rollback()
            print("Test data rolled back.")


if __name__ == '__main__':
    main()
