import uuid

from app.core.exceptions import UserNotFoundError
from app.models.user import User
from app.repositories.user_repository import UserRepository


class UserService:
    def __init__(self, user_repository: UserRepository):
        self.users = user_repository

    def _get_or_raise(self, user_id: uuid.UUID) -> User:
        user = self.users.get_by_id(user_id)
        if user is None:
            raise UserNotFoundError(f"No user with id {user_id}")
        return user

    def verify_institution(self, user_id: uuid.UUID) -> User:
        """Admin action: mark a user's institutional email domain verified.
        Idempotent -- verifying an already-verified user is a no-op save."""
        user = self._get_or_raise(user_id)
        if not user.is_institution_verified:
            user.is_institution_verified = True
            self.users.save(user)
        return user

    def deactivate(self, user_id: uuid.UUID) -> User:
        """Admin action: deactivate a user. Idempotent -- deactivating an
        already-deactivated user does not error or double-mutate state."""
        user = self._get_or_raise(user_id)
        if user.is_active:
            user.is_active = False
            self.users.save(user)
        return user
