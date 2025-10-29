import uuid
import datetime
from sqlalchemy import func, ForeignKey, String, Text, Enum as SQLAlchemyEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql.sqltypes import TIMESTAMP
from app.db.base import Base
import enum

# Define Enum for report types [cite: 252]
class ReportTypeEnum(str, enum.Enum):
    profile = "profile"
    message = "message"
    photo = "photo"
    harassment = "harassment"
    scam = "scam"
    inappropriate_content = "inappropriate_content"
    other = "other"

# Define Enum for report status [cite: 453]
class ReportStatusEnum(str, enum.Enum):
    pending = "pending"
    reviewing = "reviewing"
    resolved = "resolved"
    dismissed = "dismissed"

class Report(Base):
    """Model for the 'reports' table."""

    report_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    
    # User who filed the report
    reporter_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.user_id"), nullable=False, index=True)
    # User who is being reported
    reported_user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.user_id"), nullable=False, index=True)

    report_type: Mapped[ReportTypeEnum] = mapped_column(
        SQLAlchemyEnum(ReportTypeEnum, name="report_type_enum", create_type=True),
        nullable=False,
        index=True
    )
    reason: Mapped[str] = mapped_column(String(255), nullable=False) # Maps to 'reason' [cite: 450]
    details: Mapped[str | None] = mapped_column(Text, nullable=True) # [cite: 451]
    
    # e.g., ID of the message, photo, or "profile"
    content_reference_id: Mapped[str | None] = mapped_column(String(255), nullable=True)

    status: Mapped[ReportStatusEnum] = mapped_column(
        SQLAlchemyEnum(ReportStatusEnum, name="report_status_enum", create_type=True),
        default=ReportStatusEnum.pending,
        nullable=False,
        index=True
    )

    created_at: Mapped[datetime.datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now()
    )
    resolved_at: Mapped[datetime.datetime | None] = mapped_column(TIMESTAMP(timezone=True), nullable=True)