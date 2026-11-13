from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.medication_record.schema import MedicationRecordCreate


class PatientInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    age: int = Field(ge=0, le=150)


class AnalysisRequest(MedicationRecordCreate):
    patient: PatientInput


class MedicationRef(BaseModel):
    model_config = ConfigDict(extra="forbid")
    line_no: int = Field(ge=0)
    source_index: int = Field(ge=0)


class ModelFinding(BaseModel):
    model_config = ConfigDict(extra="allow", allow_inf_nan=False)
    finding_id: str = Field(min_length=1, max_length=100)
    rule_type: str = Field(min_length=1, max_length=100)
    severity: int = Field(ge=0)
    medication_refs: list[MedicationRef] = Field(min_length=1)


class ModelResult(BaseModel):
    model_config = ConfigDict(extra="allow", allow_inf_nan=False)
    findings: list[ModelFinding]

    @model_validator(mode="after")
    def unique_findings(self):
        ids = [f.finding_id for f in self.findings]
        if len(ids) != len(set(ids)):
            raise ValueError("중복된 finding_id")
        return self


class ModelOutput(BaseModel):
    rule_version: str = Field(min_length=1, max_length=255)
    result: ModelResult


class AnalysisCreated(BaseModel):
    analysis_id: int


class AnalysisSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    analysis_id: int
    medication_record_id: int
    analyzed_at: datetime


class AnalysisResponse(AnalysisSummary):
    rule_version: str
    result: dict[str, Any]
