from pydantic import BaseModel, ConfigDict


class UserResponse(BaseModel):
 
    model_config = ConfigDict(from_attributes=True)

    name: str
    email: str | None = None
    analysis_count: int
    guardian_count: int

    guardian_notification: bool | None


class GuardianNotificationUpdate(BaseModel):

    guardian_notification: bool


class GuardianNotificationResponse(BaseModel):

    model_config = ConfigDict(from_attributes=True)

    guardian_notification: bool
