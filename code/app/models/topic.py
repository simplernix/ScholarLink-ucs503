import uuid

from sqlalchemy import Float, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base
from app.models.mixins import TimestampMixin


class Topic(Base, TimestampMixin):
    __tablename__ = "topics"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    # Canonical display name. Matching against this (case-insensitive/fuzzy)
    # happens in the service layer before a new row is ever created here.
    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    # Lowercased, whitespace-normalized form used for fast exact-match lookups.
    normalized_name: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=False, index=True
    )

    paper_links: Mapped[list["PaperTopic"]] = relationship(
        back_populates="topic", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Topic id={self.id} name={self.name!r}>"


class PaperTopic(Base, TimestampMixin):
    """Join table linking a Paper to its (AI-generated) Topics."""

    __tablename__ = "paper_topics"
    __table_args__ = (UniqueConstraint("paper_id", "topic_id", name="uq_paper_topic"),)

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    paper_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("papers.id"), nullable=False
    )
    topic_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("topics.id"), nullable=False
    )
    # Optional confidence score from the LLM extraction step.
    relevance_score: Mapped[float | None] = mapped_column(Float, nullable=True)

    paper: Mapped["Paper"] = relationship(back_populates="topic_links")
    topic: Mapped["Topic"] = relationship(back_populates="paper_links")


class PaperInsight(Base, TimestampMixin):
    """LLM-generated summary + future-scope text for a Paper. One row per
    paper -- reprocessing upserts this row rather than creating a new one."""

    __tablename__ = "paper_insights"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    paper_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("papers.id"), unique=True, nullable=False
    )
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    future_scope: Mapped[str] = mapped_column(Text, nullable=False)
    # Raw model output kept for debugging/audit, not surfaced to users.
    raw_llm_response: Mapped[str | None] = mapped_column(Text, nullable=True)

    paper: Mapped["Paper"] = relationship(back_populates="insight")
