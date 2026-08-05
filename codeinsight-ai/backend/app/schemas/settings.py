from pydantic import BaseModel


class SettingsResponse(BaseModel):
    dark_mode: bool
    email_notifications: bool
    preferred_ai_model: str
    preferred_language: str

    class Config:
        from_attributes = True


class SettingsUpdateRequest(BaseModel):
    dark_mode: bool | None = None
    email_notifications: bool | None = None
    preferred_ai_model: str | None = None
    preferred_language: str | None = None
