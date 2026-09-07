from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.auth import UserOut
from app.schemas.paper import UserSummary

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserOut)
def read_current_user(current_user: User = Depends(get_current_user)):
    return current_user


@router.get("/search", response_model=list[UserSummary])
def search_users(
    q: str = Query(min_length=1, description="Matches against name or email"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Used by the paper-upload co-author tagger to find existing users by
    name/email -- never creates a user, only looks one up."""
    return UserRepository(db).search(q)
