from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import create_access_token, get_password_hash, verify_password
from app.models.user import User


def get_user_by_email(db: Session, email: str) -> User | None:
    stmt = select(User).where(User.email == email)
    return db.scalar(stmt)


def get_user_by_google_sub(db: Session, google_sub: str) -> User | None:
    stmt = select(User).where(User.google_sub == google_sub)
    return db.scalar(stmt)


def create_user(db: Session, *, email: str, password: str, full_name: str | None = None) -> User:
    user = User(email=email, hashed_password=get_password_hash(password), full_name=full_name)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def create_or_update_google_user(db: Session, *, email: str, google_sub: str, full_name: str | None = None) -> User:
    user = get_user_by_google_sub(db, google_sub)
    if user:
        return user

    user = get_user_by_email(db, email)
    if user:
        user.google_sub = google_sub
        if not user.full_name and full_name:
            user.full_name = full_name
        db.add(user)
        db.commit()
        db.refresh(user)
        return user

    user = User(email=email, full_name=full_name, google_sub=google_sub, hashed_password=None)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def authenticate_user(db: Session, *, email: str, password: str) -> User | None:
    user = get_user_by_email(db, email)
    if not user or not user.hashed_password:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user


def issue_token_for_user(user: User) -> str:
    return create_access_token(subject=str(user.id), extra={"email": user.email})
