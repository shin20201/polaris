from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.analysis import service
from app.analysis.model import Analysis
from app.analysis.model_gateway import AnalysisModel, get_analysis_model
from app.analysis.schema import AnalysisCreated, AnalysisRequest, AnalysisResponse, AnalysisSummary
from app.auth.dependencies import get_current_user
from app.db.database import get_db
from app.user.model import User

router = APIRouter(prefix="/api/v1/analyses", tags=["analyses"])
Db = Annotated[Session, Depends(get_db)]
CurrentUser = Annotated[User, Depends(get_current_user)]


@router.post("", response_model=AnalysisCreated)
def create_analysis(body: AnalysisRequest, user: CurrentUser, db: Db,
                    model: Annotated[AnalysisModel, Depends(get_analysis_model)]):
    return {"analysis_id": service.analyze(db, user.user_id, body, model).analysis_id}


@router.get("", response_model=list[AnalysisSummary])
def list_analyses(user: CurrentUser, db: Db):
    return list(db.scalars(select(Analysis).where(Analysis.user_id == user.user_id)
                          .order_by(Analysis.analyzed_at.desc(), Analysis.analysis_id.desc())))


@router.get("/{analysis_id}", response_model=AnalysisResponse)
def read_analysis(analysis_id: int, user: CurrentUser, db: Db):
    return service.get_owned(db, user.user_id, analysis_id)


@router.delete("")
def delete_analyses(user: CurrentUser, db: Db):
    service.delete_all(db, user.user_id)
    return {"message": "분석 기록을 모두 삭제했습니다."}
