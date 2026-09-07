import uuid

from sqlalchemy import Boolean, Enum, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base
from app.core.enums import UserRole
from app.models.mixins import TimestampMixin


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole, name="user_role"), nullable=False, default=UserRole.STUDENT
    )
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    # Institutional email domain, e.g. "stanford.edu" -- used by admins to
    # verify an account belongs to a real institution.
    institutional_email_domain: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_institution_verified: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )

    # Profile fields used by Phase 4 (public profiles) -- modeled now since
    # the schema for all entities is being designed up front.
    bio: Mapped[str | None] = mapped_column(String(2000), nullable=True)
    department: Mapped[str | None] = mapped_column(String(255), nullable=True)

    paper_links: Mapped[list["PaperAuthor"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    sent_requests: Mapped[list["CollaborationRequest"]] = relationship(
        back_populates="requester",
        foreign_keys="CollaborationRequest.requester_id",
        cascade="all, delete-orphan",
    )
    received_requests: Mapped[list["CollaborationRequest"]] = relationship(
        back_populates="recipient",
        foreign_keys="CollaborationRequest.recipient_id",
        cascade="all, delete-orphan",
    )
    notifications: Mapped[list["Notification"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:  # pragma: no cover - debugging aid only
        return f"<User id={self.id} email={self.email!r} role={self.role}>"
