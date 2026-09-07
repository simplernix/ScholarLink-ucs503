"""
PaperRepository: the only place issuing SQLAlchemy queries against
`papers` / `paper_authors`. No business rules here -- see
`app.services.paper_service`.
"""
import uuid
from datetime import datetime, timezone

from sqlalchemy.orm import Session, selectinload

from app.core.enums import PaperStatus
from app.models.paper import Paper, PaperAuthor


class PaperRepository:
    def __init__(self, db: Session):
        self.db = db

    def _with_authors(self):
        return self.db.query(Paper).options(
            selectinload(Paper.authors).selectinload(PaperAuthor.user)
        )

    def get_by_id(self, paper_id: uuid.UUID) -> Paper | None:
        return self._with_authors().filter(Paper.id == paper_id).first()

    def find_recent_by_uploader_and_title(
        self, uploaded_by_id: uuid.UUID, title: str, window_seconds: int
    ) -> Paper | None:
        """Idempotency guard for accidental double-submits: the most recent
        paper this uploader created with this exact title, if it was created
        within the last `window_seconds`. Comparison is done in Python (not
        a DB-specific datetime function) so it behaves the same on SQLite
        (tests) and Postgres (real deployments)."""
        candidate = (
            self._with_authors()
            .filter(Paper.uploaded_by_id == uploaded_by_id, Paper.title == title)
            .order_by(Paper.created_at.desc())
            .first()
        )
        if candidate is None:
            return None

        created = candidate.created_at
        if created.tzinfo is None:
            created = created.replace(tzinfo=timezone.utc)
        age_seconds = (datetime.now(timezone.utc) - created).total_seconds()
        return candidate if age_seconds <= window_seconds else None

    def create(
        self, *, title: str, abstract: str, file_storage_key: str, uploaded_by_id: uuid.UUID
    ) -> Paper:
        paper = Paper(
            title=title,
            abstract=abstract,
            file_storage_key=file_storage_key,
            uploaded_by_id=uploaded_by_id,
            status=PaperStatus.PROCESSING,
        )
        self.db.add(paper)
        self.db.commit()
        self.db.refresh(paper)
        return paper

    def add_author_link(
        self, paper_id: uuid.UUID, user_id: uuid.UUID, author_order: int
    ) -> PaperAuthor:
        """get_or_create -- linking the same (paper, user) pair twice is a
        no-op, never a duplicate row (enforced by the unique constraint too,
        but checked here first so callers never hit an IntegrityError)."""
        existing = (
            self.db.query(PaperAuthor)
            .filter(PaperAuthor.paper_id == paper_id, PaperAuthor.user_id == user_id)
            .first()
        )
        if existing is not None:
            return existing

        link = PaperAuthor(paper_id=paper_id, user_id=user_id, author_order=author_order)
        self.db.add(link)
        self.db.commit()
        self.db.refresh(link)
        return link

    def update_extracted_text(self, paper_id: uuid.UUID, text: str) -> Paper:
        """Overwrites `extracted_text` on the existing row -- re-running
        extraction never appends or creates a second record."""
        paper = self.db.get(Paper, paper_id)
        if paper is None:
            return None
        paper.extracted_text = text
        self.db.add(paper)
        self.db.commit()
        self.db.refresh(paper)
        return self.get_by_id(paper_id)

    def set_status(self, paper_id: uuid.UUID, status: PaperStatus) -> Paper | None:
        paper = self.db.get(Paper, paper_id)
        if paper is None:
            return None
        if paper.status != status:
            paper.status = status
            self.db.add(paper)
            self.db.commit()
            self.db.refresh(paper)
        return self.get_by_id(paper_id)
