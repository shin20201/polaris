"""Exercise user/auth against PostgreSQL; all test data is rolled back.

Run: python -m scripts.check_user_integration
Kakao's remote response is mocked; the database and API dependencies are real.
"""
from unittest.mock import AsyncMock, patch
from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.db.database import engine, get_db
from app.integrations.kakao import KakaoUser
from app.main import app


def main():
    settings = Settings(
        _env_file=None, jwt_secret_key=uuid4().hex + uuid4().hex, kakao_app_id=1,
    )
    with engine.connect() as connection:
        transaction = connection.begin()
        db = Session(bind=connection, join_transaction_mode="create_savepoint")

        def override_db():
            yield db

        app.dependency_overrides[get_db] = override_db
        app.dependency_overrides[get_settings] = lambda: settings
        try:
            kakao_user = KakaoUser(uuid4().int % (2**60), None)
            with patch("app.auth.service.get_kakao_user", new=AsyncMock(return_value=kakao_user)) as kakao:
                with TestClient(app) as client:
                    first = client.post("/api/v1/auth/kakao", json={"kakao_token": "test"})
                    assert first.status_code == 200, first.text
                    assert first.json()["is_new_user"] is True
                    assert first.json()["name"] == "사용자"
                    kakao.return_value = KakaoUser(kakao_user.kakao_id, "테스트닉네임")
                    again = client.post("/api/v1/auth/kakao", json={"kakao_token": "test"})
                    assert again.status_code == 200, again.text
                    assert again.json()["is_new_user"] is False
                    assert again.json()["name"] == "테스트닉네임"
                    kakao.return_value = kakao_user
                    missing_name = client.post("/api/v1/auth/kakao", json={"kakao_token": "test"})
                    assert missing_name.status_code == 200, missing_name.text
                    assert missing_name.json()["name"] == "테스트닉네임"
                    headers = {"Authorization": "Bearer " + first.json()["access_token"]}
                    assert client.get("/api/v1/users/me").status_code == 401
                    me = client.get("/api/v1/users/me", headers=headers)
                    assert me.status_code == 200, me.text
                    assert me.json()["guardian_notification"] is False
                    updated = client.patch("/api/v1/users/me", headers=headers,
                                           json={"guardian_notification": True})
                    assert updated.status_code == 200, updated.text
                    assert updated.json()["guardian_notification"] is True
                    assert client.get("/api/v1/users/me", headers=headers).json()["guardian_notification"] is True
                    logged_out = client.post("/api/v1/auth/logout", headers=headers)
                    assert logged_out.status_code == 200, logged_out.text
                    assert client.get("/api/v1/users/me", headers=headers).status_code == 401
                    second_headers = {"Authorization": "Bearer " + again.json()["access_token"]}
                    deleted = client.delete("/api/v1/users/me", headers=second_headers)
                    assert deleted.status_code == 200, deleted.text
                    assert client.get("/api/v1/users/me", headers=second_headers).status_code == 401
            print("PASS: create/reuse user, profile, notification update, logout, withdrawal.")
        finally:
            app.dependency_overrides.clear()
            db.close()
            transaction.rollback()
            print("Test data rolled back.")


if __name__ == "__main__":
    main()
