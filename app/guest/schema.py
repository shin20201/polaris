from datetime import datetime

from pydantic import BaseModel


class GuestSessionCreated(BaseModel):
    guest_token: str
    expires_at: datetime


class GuestClaimResponse(BaseModel):
    medication_record_count: int
    analysis_count: int
