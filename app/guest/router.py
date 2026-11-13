from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.analysis import service as analysis_service
from app.analysis.model import Analysis
from app.analysis.model_gateway import AnalysisModel, get_analysis_model
from app.analysis.schema import AnalysisCreated, AnalysisRequest, AnalysisResponse
from app.auth.dependencies import get_current_user
from app.db.database import get_db
from app.guest import service
from app.guest.dependencies import get_guest_session
from app.guest.model import GuestSession
from app.guest.schema import GuestClaimResponse, GuestSessionCreated
from app.user.model import User

router = APIRouter(prefix="/api/v1/guest-sessions", tags=["guest-sessions"])
Db = Annotated[Session, Depends(get_db)]
Guest = Annotated[GuestSession, Depends(get_guest_session)]


@router.post("", response_model=GuestSessionCreated, status_code=201)
def create_guest(db: Db, response: Response):
    response.headers["Cache-Control"] = "no-store"
    return service.create_session(db)


@router.delete("/me")
def end_guest(guest: Guest, db: Db):
    db.delete(guest)
    db.commit()
    return {"message": "비회원 임시 기록을 삭제했습니다."}


@router.post("/me/claim", response_model=GuestClaimResponse)
def claim_guest(guest: Guest, db: Db, user: Annotated[User, Depends(get_current_user)]):
    return service.claim(db, guest, user.user_id)


@router.post("/me/analyses", response_model=AnalysisCreated)
def create_guest_analysis(body: AnalysisRequest, guest: Guest, db: Db,
                          model: Annotated[AnalysisModel, Depends(get_analysis_model)]):
    analysis = analysis_service.analyze(db, None, body, model, guest_session_id=guest.guest_session_id)
    return {"analysis_id": analysis.analysis_id}


@router.get("/me/analyses/{analysis_id}", response_model=AnalysisResponse)
def read_guest_analysis(analysis_id: int, guest: Guest, db: Db, response: Response):
    analysis = db.scalar(select(Analysis).where(Analysis.analysis_id == analysis_id,
                                               Analysis.guest_session_id == guest.guest_session_id))
    if analysis is None:
        raise HTTPException(404, "비회원 분석 결과를 찾을 수 없습니다.")
    response.headers["Cache-Control"] = "no-store"
    return analysis
