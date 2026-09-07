"""
Reusable FastAPI dependencies for authentication and RBAC.
"""
import uuid
from collections.abc import Callable

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.enums import UserRole
from app.core.security import TokenError, decode_access_token
from app.models.user import User
from app.repositories.user_repository import UserRepository

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login", auto_error=False)

CREDENTIALS_EXCEPTION = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Could not validate credentials",
    headers={"WWW-Authenticate": "Bearer"},
)


def get_current_user(
    token: str | None = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    if token is None:
        raise CREDENTIALS_EXCEPTION
    try:
        payload = decode_access_token(token)
    except TokenError as exc:
        raise CREDENTIALS_EXCEPTION from exc

    user_id = payload.get("sub")
    if user_id is None:
        raise CREDENTIALS_EXCEPTION

    try:
        user = UserRepository(db).get_by_id(uuid.UUID(user_id))
    except ValueError as exc:
        raise CREDENTIALS_EXCEPTION from exc

    if user is None:
        raise CREDENTIALS_EXCEPTION
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="This account has been deactivated"
        )
    return user


def require_role(*allowed_roles: UserRole) -> Callable[[User], User]:
    """Usage: `Depends(require_role(UserRole.ADMIN))`."""

    def dependency(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to perform this action",
            )
        return current_user

    return dependency
