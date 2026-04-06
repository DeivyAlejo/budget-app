from datetime import timezone, datetime
import secrets

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import Select, select
from sqlalchemy.orm import Session

from app.api.deps import get_current_admin_user
from app.db.session import get_db
from app.models.invite_code import InviteCode
from app.models.user import User
from app.schemas.admin import (
    InviteCodeCreateRequest,
    InviteCodeCreateResponse,
    InviteCodeRead,
    PendingUserRead,
)
from app.services.auth_service import activate_user

router = APIRouter(prefix='/admin', tags=['admin'])

CODE_ALPHABET = 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789'


def _generate_code(length: int) -> str:
    return ''.join(secrets.choice(CODE_ALPHABET) for _ in range(length))


def _generate_unique_codes(db: Session, *, count: int, length: int) -> list[str]:
    generated: list[str] = []
    seen = set()

    while len(generated) < count:
        code = _generate_code(length)
        if code in seen:
            continue
        exists = db.scalar(select(InviteCode.id).where(InviteCode.code == code))
        if exists:
            continue
        seen.add(code)
        generated.append(code)

    return generated


@router.get('/pending-users', response_model=list[PendingUserRead])
def list_pending_users(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin_user),
) -> list[PendingUserRead]:
    stmt: Select[tuple[User]] = select(User).where(User.is_active.is_(False)).order_by(User.created_at.asc())
    users = db.scalars(stmt).all()
    return [
        PendingUserRead(id=user.id, email=user.email, full_name=user.full_name, created_at=user.created_at)
        for user in users
    ]


@router.post('/pending-users/{user_id}/approve', response_model=PendingUserRead)
def approve_pending_user(
    user_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin_user),
) -> PendingUserRead:
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='User not found')

    if not user.is_active:
        user = activate_user(db, user)

    return PendingUserRead(id=user.id, email=user.email, full_name=user.full_name, created_at=user.created_at)


@router.post('/invite-codes', response_model=InviteCodeCreateResponse, status_code=status.HTTP_201_CREATED)
def create_invite_codes(
    payload: InviteCodeCreateRequest,
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_current_admin_user),
) -> InviteCodeCreateResponse:
    codes = _generate_unique_codes(db, count=payload.count, length=payload.length)
    now = datetime.now(timezone.utc)

    records = [
        InviteCode(code=code, created_by_user_id=admin_user.id, created_at=now)
        for code in codes
    ]
    db.add_all(records)
    db.commit()

    return InviteCodeCreateResponse(codes=codes)


@router.get('/invite-codes', response_model=list[InviteCodeRead])
def list_invite_codes(
    include_used: bool = Query(default=False),
    limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin_user),
) -> list[InviteCodeRead]:
    stmt = select(InviteCode).order_by(InviteCode.created_at.desc()).limit(limit)
    if not include_used:
        stmt = stmt.where(InviteCode.used_at.is_(None))

    items = db.scalars(stmt).all()
    return [
        InviteCodeRead(
            id=item.id,
            code=item.code,
            created_at=item.created_at,
            used_at=item.used_at,
            used_by_user_id=item.used_by_user_id,
        )
        for item in items
    ]
