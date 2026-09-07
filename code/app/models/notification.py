import uuid

from sqlalchemy import Boolean, Enum, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base
from app.core.enums import NotificationEventType
from app.models.mixins import TimestampMixin


class Notification(Base, TimestampMixin):
    __tablename__ = "notifications"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    event_type: Mapped[NotificationEventType] = mapped_column(
        Enum(NotificationEventType, name="notification_event_type"), nullable=False
    )
    # Generic pointer to whatever triggered the notification (a Paper id,
    # a CollaborationRequest id, ...). Kept loose on purpose since the
    # event types point at different entities.
    related_object_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    is_read: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    user: Mapped["User"] = relationship(back_populates="notifications")
