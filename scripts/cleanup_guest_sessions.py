"""Run periodically: python -m scripts.cleanup_guest_sessions.

Expired records are also removed on guest creation and expired-token access.
"""
from app.db.database import SessionLocal
from app.guest.service import cleanup_expired


if __name__ == '__main__':
    with SessionLocal() as db:
        print('Deleted expired guest sessions:', cleanup_expired(db))
