"""
Business logic for the paper upload pipeline. No direct DB access (that's
the repository's job) and no HTTP/FastAPI concerns (that's the route's job).
"""
import uuid

from app.core.exceptions import PaperFileMissingError, PaperNotFoundError
from app.core.storage import UploadStorage
from app.models.paper import Paper
from app.models.user import User
from app.repositories.paper_repository import PaperRepository
from app.repositories.user_repository import UserRepository
from app.repositories.topic_repository import TopicRepository
from app.services.groq_service import GroqService
from app.services.pdf_extraction import extract_pdf_text

DEFAULT_DEDUPE_WINDOW_SECONDS = 10


class PaperService:
    def __init__(
        self,
        paper_repository: PaperRepository,
        user_repository: UserRepository,
        storage: UploadStorage,
        topic_repository: TopicRepository,
        groq_service: GroqService,
    ):
        self.papers = paper_repository
        self.users = user_repository
        self.storage = storage
        self.topics = topic_repository
        self.groq = groq_service

    def create_paper(
        self,
        *,
        uploader: User,
        title: str,
        abstract: str,
        filename: str | None,
        file_bytes: bytes,
        co_author_ids: list[uuid.UUID] | None = None,
        dedupe_window_seconds: int = DEFAULT_DEDUPE_WINDOW_SECONDS,
    ) -> Paper:
        # Server-side half of the double-submit guard (the client also
        # disables its submit button while a request is in flight). If the
        # same uploader submitted a paper with this exact title moments ago,
        # return that existing record instead of creating a second one --
        # and skip re-saving the file, so a double-click never orphans an
        # extra upload on disk either.
        existing = self.papers.find_recent_by_uploader_and_title(
            uploader.id, title, dedupe_window_seconds
        )
        if existing is not None:
            return existing

        storage_key = self.storage.save(file_bytes, filename)
        paper = self.papers.create(
            title=title,
            abstract=abstract,
            file_storage_key=storage_key,
            uploaded_by_id=uploader.id,
        )

        # The uploader is always author #0.
        self.papers.add_author_link(paper.id, uploader.id, author_order=0)

        order = 1
        for co_author_id in co_author_ids or []:
            if co_author_id == uploader.id:
                continue  # already linked above -- avoid a duplicate row
            co_author = self.users.get_by_id(co_author_id)
            if co_author is None:
                # Unknown id: skip rather than error, so one bad id in a
                # co-author list doesn't fail the whole upload. Never
                # creates a new User from this flow.
                continue
            self.papers.add_author_link(paper.id, co_author.id, author_order=order)
            order += 1

        return self.papers.get_by_id(paper.id)

    def extract_text(self, paper_id: uuid.UUID) -> Paper:
        paper = self.papers.get_by_id(paper_id)

        if paper is None:
           raise PaperNotFoundError(f"No paper with id {paper_id}")

        if not paper.file_storage_key or not self.storage.exists(
           paper.file_storage_key
        ):
           raise PaperFileMissingError(f"No stored file for paper {paper_id}")

        # 1. Read the stored PDF
        file_bytes = self.storage.read(paper.file_storage_key)

        # 2. Extract text from PDF
        text = extract_pdf_text(file_bytes)

        # 3. Save extracted text
        paper = self.papers.update_extracted_text(paper.id, text)

        # 4. Ask Groq for research topics
        topics = self.groq.extract_topics(text)

        # 5. Save/link topics
        for topic_name in topics:
            normalized_name = " ".join(topic_name.lower().split())

            topic = self.topics.get_by_normalized_name(normalized_name)

            if topic is None:
                topic = self.topics.create(
                    name=topic_name,
                    normalized_name=normalized_name,
                )

            self.topics.add_paper_link(
                paper_id=paper.id,
                topic_id=topic.id,
            )

        return self.papers.get_by_id(paper.id)
