import uuid
from pydantic import BaseModel, Field
from app.models.report import ReportTypeEnum
from datetime import datetime

class ReportCreate(BaseModel):
    """Schema for a user submitting a new report."""
    reported_user_id: uuid.UUID
    report_type: ReportTypeEnum
    reason: str = Field(..., max_length=255)
    details: str | None = Field(None, max_length=2000)
    content_reference_id: str | None = Field(None, max_length=255)

class ReportRead(ReportCreate):
    """Schema for reading a report (e.g., for admins)."""
    report_id: uuid.UUID
    reporter_id: uuid.UUID
    created_at: datetime
    status: str

    class Config:
        from_attributes = True