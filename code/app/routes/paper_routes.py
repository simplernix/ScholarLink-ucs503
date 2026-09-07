import uuid

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.db import get_db
from app.core.deps import get_current_user
from app.core.exceptions import PaperFileMissingError, PaperNotFoundError
from app.core.storage import UploadStorage
from app.models.user import User
from app.repositories.paper_repository import PaperRepository
from app.repositories.user_repository import UserRepository
from app.schemas.paper import PaperOut, paper_to_out
from app.services.paper_service import PaperService

router = APIRouter(prefix="/papers", tags=["papers"])


def get_paper_service(db: Session = Depends(get_db)) -> PaperService:
    # Read settings.UPLOAD_DIR at call time (not import time) so tests can
    # point it at a temp directory per-test via monkeypatch.
    storage = UploadStorage(settings.UPLOAD_DIR)
    return PaperService(PaperRepository(db), UserRepository(db), storage)


def _parse_co_author_ids(raw: str | None) -> list[uuid.UUID]:
    if not raw:
        return []
    ids: list[uuid.UUID] = []
    for chunk in raw.split(","):
        chunk = chunk.strip()
        if not chunk:
            continue
        try:
            ids.append(uuid.UUID(chunk))
        except ValueError:
            continue  # ignore malformed ids rather than failing the whole upload
    return ids


@router.post("", response_model=PaperOut, status_code=status.HTTP_201_CREATED)
async def upload_paper(
    title: str = Form(...),
    abstract: str = Form(...),
    co_author_ids: str | None = Form(None, description="Comma-separated user UUIDs"),
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    paper_service: PaperService = Depends(get_paper_service),
):
    file_bytes = await file.read()
    paper = paper_service.create_paper(
        uploader=current_user,
        title=title,
        abstract=abstract,
        filename=file.filename,
        file_bytes=file_bytes,
        co_author_ids=_parse_co_author_ids(co_author_ids),
    )
    return paper_to_out(paper)


@router.get("/{paper_id}", response_model=PaperOut)
def get_paper(
    paper_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    paper = PaperRepository(db).get_by_id(paper_id)
    if paper is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Paper not found")
    return paper_to_out(paper)


@router.post("/{paper_id}/extract-text", response_model=PaperOut)
def extract_text(
    paper_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    paper_service: PaperService = Depends(get_paper_service),
):
    # Manual trigger for now -- Phase 3 wires this into the background job
    # queue so it fires automatically when a paper enters `Processing`.
    try:
        return paper_to_out(paper_service.extract_text(paper_id))
    except PaperNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except PaperFileMissingError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
