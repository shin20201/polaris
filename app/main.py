'''from fastapi import FastAPI

app = FastAPI()


@app.get("/")
def root():
    return {"message": "POLARIS Backend"}'''
from fastapi import FastAPI
from sqlalchemy import text

from app.db.database import engine

app = FastAPI()


@app.get("/")
def root():
    with engine.connect() as conn:
        result = conn.execute(text("SELECT 1")).scalar()

    return {
        "message": "POLARIS Backend",
        "db": result
    }