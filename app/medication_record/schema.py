from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator


class MedicationItem(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)

    # 두 번호의 의미는 연동 규격 확정 전까지 해석하지 않고 그대로 보존합니다.
    line_no: int = Field(ge=0)
    source_index: int = Field(ge=0)
    raw_name: str = Field(min_length=1)
    ocr_confidence: float | None = Field(default=None, ge=0, le=1)
    dose_per_time: float | None = Field(default=None, gt=0)
    dose_unit: str | None = Field(default=None, min_length=1)
    freq_per_day: int | None = Field(default=None, gt=0)
    duration_days: int | None = Field(default=None, gt=0)


class InstitutionMedications(BaseModel):
    model_config = ConfigDict(extra="forbid")

    institution_name: str | None = Field(default=None, min_length=1)
    drugs: list[MedicationItem] = Field(min_length=1)


class MedicationRecordCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    medications: list[InstitutionMedications] = Field(min_length=1)

    @model_validator(mode="after")
    def unique_item_keys(self):
        keys = [(item.line_no, item.source_index)
                for group in self.medications for item in group.drugs]
        if len(keys) != len(set(keys)):
            raise ValueError("같은 기록 안에서 line_no와 source_index 조합은 중복될 수 없습니다.")
        return self


class MedicationRecordResponse(MedicationRecordCreate):
    model_config = ConfigDict(from_attributes=True)

    medication_record_id: int
    created_at: datetime
