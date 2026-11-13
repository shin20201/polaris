'''from fastapi import FastAPI

app = FastAPI()


@app.get("/")
def root():
    return {"message": "POLARIS Backend"}'''
from fastapi import FastAPI
from sqlalchemy import text

from app.db.database import engine
from app.auth.router import router as auth_router
from app.user.router import router as user_router
from app.guardian.router import router as guardian_router
from app.medication_record.router import router as medication_record_router
from app.analysis.router import router as analysis_router
from app.notification.router import router as notification_router
from app.guest.router import router as guest_router
from app.guest.cleanup import lifespan

app = FastAPI(lifespan=lifespan)
app.include_router(auth_router)
app.include_router(user_router)
app.include_router(guardian_router)
app.include_router(medication_record_router)
app.include_router(analysis_router)
app.include_router(notification_router)
app.include_router(guest_router)


@app.get("/")
def root():
    with engine.connect() as conn:
        result = conn.execute(text("SELECT 1")).scalar()

    return {
        "message": "POLARIS Backend",
        "db": result
    }
