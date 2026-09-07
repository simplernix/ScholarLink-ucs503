"""
Test fixtures.

ASSUMPTION (flagged for confirmation): tests run against an in-memory
SQLite database rather than the real Postgres instance, so the suite is
fast and needs no external services in CI's `test` job before Docker is
involved. Every column type used in the models (UUID, Enum, DateTime,
Text) is supported by SQLAlchemy's SQLite dialect, so behavior under test
matches Postgres for everything Phase 1 exercises. Integration tests in
later phases that need Postgres-only features (if any) should target the
`postgres` service directly instead.
"""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

from app import models as _models  # noqa: F401  -- ensure all models are registered
from app.core.db import Base, get_db
from app.core.enums import UserRole
from app.core.security import hash_password
from app.main import app
from app.repositories.user_repository import UserRepository


@pytest.fixture()
def engine():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    yield engine
    Base.metadata.drop_all(engine)


@pytest.fixture()
def db_session(engine):
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture()
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture()
def make_user(db_session):
    """Factory fixture: create a user directly via the repository (bypassing
    the HTTP layer) with a known plaintext password, for use as test fixtures
    rather than as the thing under test."""

    def _make(
        email: str = "user@example.com",
        password: str = "password123",
        full_name: str = "Test User",
        role: UserRole = UserRole.STUDENT,
        is_active: bool = True,
    ):
        repo = UserRepository(db_session)
        user = repo.create(
            email=email,
            hashed_password=hash_password(password),
            full_name=full_name,
            role=role,
        )
        if not is_active:
            user.is_active = False
            repo.save(user)
        return user

    return _make


def auth_headers(client: TestClient, email: str, password: str) -> dict:
    resp = client.post("/auth/login", json={"email": email, "password": password})
    assert resp.status_code == 200, resp.text
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture()
def upload_dir(tmp_path, monkeypatch):
    """Point file storage at a per-test temp directory instead of the real
    UPLOAD_DIR, so tests never touch disk outside the sandbox and never
    interfere with each other."""
    from app.core.config import settings

    d = tmp_path / "uploads"
    d.mkdir()
    monkeypatch.setattr(settings, "UPLOAD_DIR", str(d))
    return d


def make_pdf_bytes(text: str = "Hello ScholarLink") -> bytes:
    """Builds a tiny real PDF in-memory (via PyMuPDF) so extraction tests
    don't depend on any file fixture on disk."""
    import fitz

    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((72, 72), text)
    data = doc.tobytes()
    doc.close()
    return data
