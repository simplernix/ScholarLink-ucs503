"""
UserRepository: the only place in the app that issues SQLAlchemy queries
against the `users` table. Contains no business rules -- those live in
`app.services.auth_service` / `app.services.user_service`.
"""
import uuid

from sqlalchemy.orm import Session

from app.core.enums import UserRole
from app.models.user import User


class UserRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, user_id: uuid.UUID) -> User | None:
        return self.db.get(User, user_id)

    def get_by_email(self, email: str) -> User | None:
        return self.db.query(User).filter(User.email == email.lower()).first()

    def create(
        self,
        *,
        email: str,
        hashed_password: str,
        full_name: str,
        role: UserRole,
        institutional_email_domain: str | None = None,
    ) -> User:
        user = User(
            email=email.lower(),
            hashed_password=hashed_password,
            full_name=full_name,
            role=role,
            institutional_email_domain=institutional_email_domain,
        )
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def save(self, user: User) -> User:
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def search(self, query: str, *, limit: int = 10) -> list[User]:
        """Used by co-author tagging: search existing users by name or
        email. Never creates anything -- callers must link to an existing
        User, never spin up a new one from an upload flow."""
        like = f"%{query.strip()}%"
        return (
            self.db.query(User)
            .filter((User.full_name.ilike(like)) | (User.email.ilike(like)))
            .order_by(User.full_name)
            .limit(limit)
            .all()
        )
