from pydantic import BaseModel, ConfigDict, Field


class GuardianResponse(BaseModel):

    model_config = ConfigDict(from_attributes=True)

    guardian_id: int
    name: str = Field(validation_alias="nickname")  # 명세서의 "name" = 카카오 닉네임
    profile_image_url: str | None
    kakao_email: str | None