import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.deps import require_role
from app.core.enums import UserRole
from app.core.exceptions import UserNotFoundError
from app.repositories.user_repository import UserRepository
from app.schemas.auth import UserOut
from app.services.user_service import UserService

router = APIRouter(
    prefix="/admin",
    tags=["admin"],
    dependencies=[Depends(require_role(UserRole.ADMIN))],
)


def get_user_service(db: Session = Depends(get_db)) -> UserService:
    return UserService(UserRepository(db))


@router.post("/users/{user_id}/verify-institution", response_model=UserOut)
def verify_institution(user_id: uuid.UUID, user_service: UserService = Depends(get_user_service)):
    try:
        return user_service.verify_institution(user_id)
    except UserNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.post("/users/{user_id}/deactivate", response_model=UserOut)
def deactivate_user(user_id: uuid.UUID, user_service: UserService = Depends(get_user_service)):
    try:
        return user_service.deactivate(user_id)
    except UserNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
