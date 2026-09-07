import uuid

from sqlalchemy import Enum, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base
from app.core.enums import PaperStatus
from app.models.mixins import TimestampMixin


class Paper(Base, TimestampMixin):
    __tablename__ = "papers"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    abstract: Mapped[str] = mapped_column(Text, nullable=False)

    # UUID-based storage key -- never the raw uploaded filename -- so
    # repeated uploads can never collide or overwrite another file.
    file_storage_key: Mapped[str | None] = mapped_column(String(255), nullable=True, unique=True)

    extracted_text: Mapped[str | None] = mapped_column(Text, nullable=True)

    status: Mapped[PaperStatus] = mapped_column(
        Enum(PaperStatus, name="paper_status"), nullable=False, default=PaperStatus.PROCESSING
    )

    # Uploader of record (may also appear in PaperAuthor).
    uploaded_by_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    uploaded_by: Mapped["User"] = relationship(foreign_keys=[uploaded_by_id])

    authors: Mapped[list["PaperAuthor"]] = relationship(
        back_populates="paper", cascade="all, delete-orphan"
    )
    topic_links: Mapped[list["PaperTopic"]] = relationship(
        back_populates="paper", cascade="all, delete-orphan"
    )
    insight: Mapped["PaperInsight | None"] = relationship(
        back_populates="paper", cascade="all, delete-orphan", uselist=False
    )
    collaboration_requests: Mapped[list["CollaborationRequest"]] = relationship(
        back_populates="paper", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Paper id={self.id} title={self.title!r} status={self.status}>"


class PaperAuthor(Base, TimestampMixin):
    """Join table linking a Paper to its co-authors (existing Users only --
    never a duplicate User created from the upload flow)."""

    __tablename__ = "paper_authors"
    __table_args__ = (UniqueConstraint("paper_id", "user_id", name="uq_paper_author"),)

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    paper_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("papers.id"), nullable=False
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    author_order: Mapped[int] = mapped_column(nullable=False, default=0)

    paper: Mapped["Paper"] = relationship(back_populates="authors")
    user: Mapped["User"] = relationship(back_populates="paper_links")
