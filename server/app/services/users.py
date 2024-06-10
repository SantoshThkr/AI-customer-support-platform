from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import User, UserRole
from app.services.security import hash_password


def normalize_email(email: str) -> str:
    return email.strip().lower()


def get_user_by_email(db: Session, email: str) -> User | None:
    return db.scalar(select(User).where(User.email == normalize_email(email)))


def _email_taken() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_409_CONFLICT,
        detail="An account with this email already exists",
    )


def create_user(
    db: Session, *, email: str, name: str, password: str, role: UserRole = UserRole.CUSTOMER
) -> User:
    if get_user_by_email(db, email) is not None:
        raise _email_taken()

    user = User(
        email=normalize_email(email),
        name=name.strip(),
        password_hash=hash_password(password),
        role=role,
    )
    db.add(user)
    try:
        db.commit()
    except IntegrityError as exc:
        # Two registrations for the same email can race past the check above.
        db.rollback()
        raise _email_taken() from exc
    db.refresh(user)
    return user
