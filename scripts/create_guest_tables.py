"""Run: python -m scripts.create_guest_tables. Existing member records are preserved."""
from sqlalchemy import inspect, text

from app.db.database import engine
from app.user.model import User
from app.guest.model import GuestSession
from app.medication_record.model import MedicationRecord
from app.analysis.model import Analysis


if __name__ == "__main__":
    with engine.begin() as connection:
        GuestSession.__table__.create(connection, checkfirst=True)
        for model in (MedicationRecord, Analysis):
            table = model.__tablename__
            model.__table__.create(connection, checkfirst=True)
            connection.execute(text(f'ALTER TABLE {table} ADD COLUMN IF NOT EXISTS guest_session_id INTEGER REFERENCES guest_session(guest_session_id) ON DELETE CASCADE'))
            connection.execute(text(f'ALTER TABLE {table} ALTER COLUMN user_id DROP NOT NULL'))
            connection.execute(text(f'CREATE INDEX IF NOT EXISTS ix_{table}_guest_session_id ON {table} (guest_session_id)'))
            name = f'ck_{table}_owner'
            if name not in {item['name'] for item in inspect(connection).get_check_constraints(table)}:
                connection.execute(text(f'ALTER TABLE {table} ADD CONSTRAINT {name} CHECK ((user_id IS NOT NULL) <> (guest_session_id IS NOT NULL))'))
    print('Guest session table and ownership columns are ready.')
