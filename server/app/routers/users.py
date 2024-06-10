from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies.auth import require_admin, require_staff
from app.models import STAFF_ROLES, User, UserRole
from app.schemas.common import Page
from app.schemas.user import UserBrief, UserCreate, UserOut, UserUpdate
from app.services.security import hash_password
from app.services.users import create_user

router = APIRouter(prefix="/api/users", tags=["users"])


@router.get("", response_model=Page[UserOut])
def list_users(
    search: str | None = Query(default=None, max_length=100),
    role: UserRole | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    query = select(User)
    if role:
        query = query.where(User.role == role)
    if search:
        pattern = f"%{search.strip()}%"
        query = query.where(or_(User.email.ilike(pattern), User.name.ilike(pattern)))

    total = db.scalar(select(func.count()).select_from(query.subquery()))
    users = db.scalars(
        query.order_by(User.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
    ).all()
    return Page.build(users, total, page, page_size)


@router.get("/agents", response_model=list[UserBrief])
def list_agents(db: Session = Depends(get_db), _: User = Depends(require_staff)):
    """Active support staff who can be assigned tickets."""
    return db.scalars(
        select(User)
        .where(User.role.in_(STAFF_ROLES), User.is_active.is_(True))
        .order_by(User.name)
    ).all()


@router.post("", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def create_user_as_admin(
    payload: UserCreate, db: Session = Depends(get_db), _: User = Depends(require_admin)
):
    return create_user(
        db, email=payload.email, name=payload.name, password=payload.password, role=payload.role
    )


@router.patch("/{user_id}", response_model=UserOut)
def update_user(
    user_id: int,
    payload: UserUpdate,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    if user.id == admin.id and (
        payload.is_active is False or (payload.role and payload.role != UserRole.ADMIN)
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot deactivate or demote your own account",
        )

    if payload.name is not None:
        user.name = payload.name.strip()
    if payload.role is not None:
        user.role = payload.role
    if payload.is_active is not None:
        user.is_active = payload.is_active
    if payload.password:
        user.password_hash = hash_password(payload.password)

    db.commit()
    db.refresh(user)
    return user
