import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.core.enums import PaperStatus


class UserSummary(BaseModel):
    id: uuid.UUID
    full_name: str
    email: str

    model_config = {"from_attributes": True}


class PaperOut(BaseModel):
    id: uuid.UUID
    title: str
    abstract: str
    status: PaperStatus
    file_storage_key: str | None
    extracted_text: str | None
    uploaded_by_id: uuid.UUID
    authors: list[UserSummary]
    created_at: datetime

    model_config = {"from_attributes": True}


def paper_to_out(paper) -> "PaperOut":
    """Builds a PaperOut from an ORM Paper. Needed because `paper.authors`
    is a list of PaperAuthor join rows, not Users -- Pydantic's
    `from_attributes` can't flatten that relationship on its own."""
    sorted_links = sorted(paper.authors, key=lambda link: link.author_order)
    return PaperOut(
        id=paper.id,
        title=paper.title,
        abstract=paper.abstract,
        status=paper.status,
        file_storage_key=paper.file_storage_key,
        extracted_text=paper.extracted_text,
        uploaded_by_id=paper.uploaded_by_id,
        authors=[UserSummary.model_validate(link.user) for link in sorted_links],
        created_at=paper.created_at,
    )


class PaperCreateForm(BaseModel):
    """Not used directly as a FastAPI body (the endpoint takes multipart
    form fields since a file is involved) -- documents the shape for
    reference and for any future JSON-only client."""

    title: str = Field(min_length=1, max_length=500)
    abstract: str = Field(min_length=1)
    co_author_ids: list[uuid.UUID] = Field(default_factory=list)
