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

app = FastAPI()
app.include_router(auth_router)
app.include_router(user_router)


@app.get("/")
def root():
    with engine.connect() as conn:
        result = conn.execute(text("SELECT 1")).scalar()

    return {
        "message": "POLARIS Backend",
        "db": result
    }
