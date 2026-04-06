from datetime import timezone, datetime

from authlib.integrations.starlette_client import OAuth
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import RedirectResponse
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.config import settings
from app.db.session import get_db
from app.models.invite_code import InviteCode
from app.models.user import User
from app.schemas.auth import LoginRequest, RegisterRequest, RegisterResponse, TokenResponse
from app.schemas.user import UserRead
from app.services.auth_service import (
    authenticate_user,
    create_or_update_google_user,
    create_user,
    get_user_by_email,
    issue_token_for_user,
)

router = APIRouter(prefix='/auth', tags=['auth'])

oauth = OAuth()
oauth.register(
    name='google',
    client_id=settings.google_client_id,
    client_secret=settings.google_client_secret,
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={'scope': 'openid email profile'},
)


@router.post('/register', response_model=RegisterResponse, status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest, db: Session = Depends(get_db)) -> RegisterResponse:
    existing_user = get_user_by_email(db, payload.email)
    if existing_user:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail='Email already registered')

    is_admin_signup = settings.is_admin_email(payload.email)
    requires_invite = settings.registration_requires_invite and not is_admin_signup

    invite_code_record: InviteCode | None = None
    if requires_invite:
        code = (payload.invite_code or '').strip()
        if not code:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='Invite code is required')

        invite_stmt = select(InviteCode).where(InviteCode.code == code, InviteCode.used_at.is_(None))
        invite_code_record = db.scalar(invite_stmt)
        if not invite_code_record:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='Invalid or already used invite code')

    try:
        user = create_user(
            db,
            email=payload.email,
            password=payload.password,
            full_name=payload.full_name,
            is_active=is_admin_signup or not settings.require_admin_approval,
            commit=not requires_invite,
        )

        if invite_code_record:
            invite_code_record.used_by_user_id = user.id
            invite_code_record.used_at = datetime.now(timezone.utc)
            db.add(invite_code_record)
            db.commit()
            db.refresh(user)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail='Email already registered') from None

    if settings.require_admin_approval and not is_admin_signup:
        return RegisterResponse(
            message='Registration submitted. Your account is pending admin approval.',
            pending_approval=True,
        )

    return RegisterResponse(message='Registration successful.', pending_approval=False)


@router.post('/login', response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    user = get_user_by_email(db, payload.email)
    if user and not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='Account pending admin approval')

    authenticated = authenticate_user(db, email=payload.email, password=payload.password)
    if not authenticated:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Invalid email or password')

    return TokenResponse(access_token=issue_token_for_user(authenticated))


@router.get('/google/login')
async def google_login(request: Request):
    if not settings.google_client_id or not settings.google_client_secret:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Google OAuth is not configured')
    redirect_uri = settings.google_redirect_uri
    return await oauth.google.authorize_redirect(request, redirect_uri)


@router.get('/google/callback', response_model=TokenResponse)
async def google_callback(request: Request, db: Session = Depends(get_db)) -> TokenResponse:
    if not settings.google_client_id or not settings.google_client_secret:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Google OAuth is not configured')

    token = await oauth.google.authorize_access_token(request)
    user_info = token.get('userinfo')
    if not user_info:
        user_info = await oauth.google.userinfo(token=token)

    email = user_info.get('email')
    google_sub = user_info.get('sub')
    full_name = user_info.get('name')

    if not email or not google_sub:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Google did not return required user info')

    try:
        user = create_or_update_google_user(
            db,
            email=email,
            google_sub=google_sub,
            full_name=full_name,
            is_active_for_new=settings.is_admin_email(email) or not settings.require_admin_approval,
        )
    except IntegrityError:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail='Could not create user from Google account') from None

    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='Account pending admin approval')

    return TokenResponse(access_token=issue_token_for_user(user))


@router.get('/google/callback/web')
async def google_callback_for_web(request: Request, db: Session = Depends(get_db)):
    token_response = await google_callback(request, db)
    return RedirectResponse(url=f'{settings.frontend_url}/oauth/success?token={token_response.access_token}')


@router.get('/me', response_model=UserRead)
def me(current_user: User = Depends(get_current_user)) -> UserRead:
    return UserRead(
        id=current_user.id,
        email=current_user.email,
        full_name=current_user.full_name,
        is_active=current_user.is_active,
        is_admin=settings.is_admin_email(current_user.email),
        created_at=current_user.created_at,
    )
