from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator


class NotificationCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    guardian_id: int = Field(gt=0)
    analysis_id: int = Field(gt=0)
    share_findings: bool = True
    share_medications: bool = False
    share_map: bool = False

    @model_validator(mode="after")
    def validate_selection(self):
        if self.share_map:
            raise ValueError("지도 공유는 현재 지원하지 않습니다.")
        if not (self.share_findings or self.share_medications):
            raise ValueError("전송할 항목을 하나 이상 선택해야 합니다.")
        return self


class NotificationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    notification_id: int
    guardian_id: int
    analysis_id: int
    status: str
    sent_at: datetime | None
    read_at: datetime | None
    payload: dict
