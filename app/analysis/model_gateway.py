from typing import Protocol

from fastapi import HTTPException

from app.analysis.schema import AnalysisRequest, ModelOutput


class AnalysisModel(Protocol):
    def analyze(self, request: AnalysisRequest) -> ModelOutput: ...


def get_analysis_model() -> AnalysisModel:
    raise HTTPException(503, "분석 모델이 아직 연결되지 않았습니다.")
