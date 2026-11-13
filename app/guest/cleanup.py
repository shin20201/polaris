import asyncio
import logging
from contextlib import asynccontextmanager, suppress

from fastapi.concurrency import run_in_threadpool

from app.db.database import SessionLocal
from app.guest.service import cleanup_expired

logger = logging.getLogger(__name__)


def cleanup_once():
    with SessionLocal() as db:
        return cleanup_expired(db)


async def cleanup_loop():
    while True:
        await asyncio.sleep(600)
        try:
            await run_in_threadpool(cleanup_once)
        except Exception:
            logger.exception("Expired guest session cleanup failed")


@asynccontextmanager
async def lifespan(app):
    task = asyncio.create_task(cleanup_loop())
    try:
        yield
    finally:
        task.cancel()
        with suppress(asyncio.CancelledError):
            await task
