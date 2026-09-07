"""
Business logic for registration/login. No direct DB access (that's the
repository's job) and no HTTP/FastAPI concerns (that's the route's job).
"""
from app.core.enums import UserRole
from app.core.exceptions import (
    EmailAlreadyRegisteredError,
    InactiveUserError,
    InvalidCredentialsError,
)
from app.core.security import create_access_token, hash_password, verify_password
from app.models.user import User
from app.repositories.user_repository import UserRepository


class AuthService:
    def __init__(self, user_repository: UserRepository):
        self.users = user_repository

    def register(
        self, *, email: str, password: str, full_name: str, role: UserRole
    ) -> User:
        existing = self.users.get_by_email(email)
        if existing is not None:
            # Clean, specific conflict -- never a raw DB IntegrityError leak.
            raise EmailAlreadyRegisteredError(f"Email already registered: {email}")

        domain = email.split("@")[-1].lower() if "@" in email else None
        return self.users.create(
            email=email,
            hashed_password=hash_password(password),
            full_name=full_name,
            role=role,
            institutional_email_domain=domain,
        )

    def authenticate(self, *, email: str, password: str) -> User:
        user = self.users.get_by_email(email)
        if user is None or not verify_password(password, user.hashed_password):
            raise InvalidCredentialsError("Incorrect email or password")
        if not user.is_active:
            raise InactiveUserError("This account has been deactivated")
        return user

    def login(self, *, email: str, password: str) -> tuple[User, str]:
        user = self.authenticate(email=email, password=password)
        token = create_access_token(subject=str(user.id), extra_claims={"role": user.role.value})
        return user, token
