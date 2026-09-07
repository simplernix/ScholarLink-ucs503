"""initial schema - all core entities

Revision ID: 4fd2798321d2
Revises:
Create Date: 2026-09-06

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "4fd2798321d2"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # --- users -----------------------------------------------------------
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("hashed_password", sa.String(255), nullable=False),
        sa.Column("full_name", sa.String(255), nullable=False),
        sa.Column(
            "role",
            sa.Enum("STUDENT", "PROFESSOR", "ADMIN", name="user_role"),
            nullable=False,
        ),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("institutional_email_domain", sa.String(255), nullable=True),
        sa.Column(
            "is_institution_verified", sa.Boolean(), nullable=False, server_default=sa.false()
        ),
        sa.Column("bio", sa.String(2000), nullable=True),
        sa.Column("department", sa.String(255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("email", name="uq_users_email"),
    )
    op.create_index("ix_users_email", "users", ["email"])

    # --- papers ------------------------------------------------------------
    op.create_table(
        "papers",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("abstract", sa.Text(), nullable=False),
        sa.Column("file_storage_key", sa.String(255), nullable=True),
        sa.Column("extracted_text", sa.Text(), nullable=True),
        sa.Column(
            "status",
            sa.Enum("PROCESSING", "PUBLISHED", name="paper_status"),
            nullable=False,
        ),
        sa.Column("uploaded_by_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("file_storage_key", name="uq_papers_file_storage_key"),
    )

    # --- paper_authors -------------------------------------------------------
    op.create_table(
        "paper_authors",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("paper_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("papers.id"), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("author_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("paper_id", "user_id", name="uq_paper_author"),
    )

    # --- topics --------------------------------------------------------------
    op.create_table(
        "topics",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("normalized_name", sa.String(255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("name", name="uq_topics_name"),
        sa.UniqueConstraint("normalized_name", name="uq_topics_normalized_name"),
    )
    op.create_index("ix_topics_name", "topics", ["name"])
    op.create_index("ix_topics_normalized_name", "topics", ["normalized_name"])

    # --- paper_topics ----------------------------------------------------------
    op.create_table(
        "paper_topics",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("paper_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("papers.id"), nullable=False),
        sa.Column("topic_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("topics.id"), nullable=False),
        sa.Column("relevance_score", sa.Float(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("paper_id", "topic_id", name="uq_paper_topic"),
    )

    # --- paper_insights --------------------------------------------------------
    op.create_table(
        "paper_insights",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("paper_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("papers.id"), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("future_scope", sa.Text(), nullable=False),
        sa.Column("raw_llm_response", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("paper_id", name="uq_paper_insights_paper_id"),
    )

    # --- collaboration_requests --------------------------------------------------
    op.create_table(
        "collaboration_requests",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("requester_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("recipient_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("paper_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("papers.id"), nullable=False),
        sa.Column(
            "status",
            sa.Enum("PENDING", "ACCEPTED", "DECLINED", name="collaboration_request_status"),
            nullable=False,
        ),
        sa.Column("message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint(
            "requester_id", "recipient_id", "paper_id", "status", name="uq_collab_request_state"
        ),
    )

    # --- notifications ----------------------------------------------------------
    op.create_table(
        "notifications",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column(
            "event_type",
            sa.Enum(
                "REQUEST_SENT",
                "REQUEST_ACCEPTED",
                "REQUEST_DECLINED",
                "PAPER_PROCESSING_COMPLETE",
                name="notification_event_type",
            ),
            nullable=False,
        ),
        sa.Column("related_object_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("is_read", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("notifications")
    op.drop_table("collaboration_requests")
    op.drop_table("paper_insights")
    op.drop_table("paper_topics")
    op.drop_index("ix_topics_normalized_name", table_name="topics")
    op.drop_index("ix_topics_name", table_name="topics")
    op.drop_table("topics")
    op.drop_table("paper_authors")
    op.drop_table("papers")
    op.drop_index("ix_users_email", table_name="users")
    op.drop_table("users")

    # Enum types created implicitly by sa.Enum(...) above must be dropped
    # explicitly on downgrade, or a re-`upgrade()` after a downgrade will
    # fail with "type already exists".
    for enum_name in (
        "notification_event_type",
        "collaboration_request_status",
        "paper_status",
        "user_role",
    ):
        sa.Enum(name=enum_name).drop(op.get_bind(), checkfirst=True)
