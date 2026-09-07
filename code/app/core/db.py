"""
SQLAlchemy engine/session wiring.

`get_db` is the FastAPI dependency every route/service should depend on
(indirectly, via repositories) to get a request-scoped session.
"""
from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import settings

# `pool_pre_ping` avoids handing out dead connections after a DB restart.
engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
