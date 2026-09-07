import uuid

from sqlalchemy import Enum, ForeignKey, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base
from app.core.enums import CollaborationRequestStatus
from app.models.mixins import TimestampMixin


class CollaborationRequest(Base, TimestampMixin):
    __tablename__ = "collaboration_requests"
    __table_args__ = (
        # A partial unique index would be ideal (one pending request per
        # requester/recipient/paper triple), but that's Postgres-specific
        # DDL added via the migration; the service layer also guards this
        # at write time so the behavior holds on any backend.
        UniqueConstraint(
            "requester_id", "recipient_id", "paper_id", "status", name="uq_collab_request_state"
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    requester_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    recipient_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    paper_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("papers.id"), nullable=False
    )
    status: Mapped[CollaborationRequestStatus] = mapped_column(
        Enum(CollaborationRequestStatus, name="collaboration_request_status"),
        nullable=False,
        default=CollaborationRequestStatus.PENDING,
    )
    message: Mapped[str | None] = mapped_column(Text, nullable=True)

    requester: Mapped["User"] = relationship(
        back_populates="sent_requests", foreign_keys=[requester_id]
    )
    recipient: Mapped["User"] = relationship(
        back_populates="received_requests", foreign_keys=[recipient_id]
    )
    paper: Mapped["Paper"] = relationship(back_populates="collaboration_requests")
