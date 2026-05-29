from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.core.config import settings
from app.core.logging_config import logger
from app.core.security import (
    create_access_token, create_refresh_token, decode_token, hash_password
)
from app.db.session import get_db
from app.schemas.user import LoginRequest, TokenResponse, UserCreate, UserOut, UserRole
from app.services.user_service import authenticate_user, create_user
from app.models.user import User
from app.core.dependencies import get_current_user, require_bot_secret
from sqlalchemy.orm import Session

import secrets
import random
from datetime import datetime, timedelta, timezone
from pydantic import BaseModel, EmailStr

limiter = Limiter(key_func=get_remote_address)
router = APIRouter(prefix="/auth", tags=["Authentication"])


class OTPResponse(BaseModel):
    otp: str
    expires_in_minutes: int = 5


class TelegramLinkRequest(BaseModel):
    chat_id: str
    otp: str


class BotLoginRequest(BaseModel):
    chat_id: str


class BotLoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


class PasswordResetRequest(BaseModel):
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    token: str
    new_password: str


def _get_request_user(request: Request, db: Session) -> User | None:
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return None

    payload = decode_token(auth_header[7:])
    if payload is None or payload.get("type") != "access":
        return None

    user_id = payload.get("sub")
    if not user_id:
        return None

    return db.query(User).filter(
        User.id == user_id,
        User.is_active == True,
    ).first()


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register(request: Request, user_data: UserCreate, db: Session = Depends(get_db)):
    users_exist = db.query(User).first() is not None
    actor = _get_request_user(request, db)

    if not users_exist:
        if user_data.role != UserRole.admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="The first account must be an admin account",
            )
    elif actor is None or actor.role != UserRole.admin.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can create new accounts",
        )

    try:
        user = create_user(db, user_data)
        logger.info(f"New user registered: {user.email} (role: {user.role})")
        return user
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/login", response_model=TokenResponse)
@limiter.limit("5/minute")
def login(
    request: Request,
    response: Response,
    credentials: LoginRequest,
    db: Session = Depends(get_db),
):
    user = authenticate_user(db, credentials.email, credentials.password)
    if not user:
        logger.warning(f"Failed login attempt for: {credentials.email}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token({"sub": str(user.id), "role": user.role})
    refresh_token = create_refresh_token({"sub": str(user.id)})
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=settings.ENVIRONMENT != "development",
        samesite="lax",
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
        path="/",
    )
    logger.info(f"Successful login: {user.email}")
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        user=UserOut.model_validate(user),
    )


@router.post("/refresh")
async def refresh_token_endpoint(
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
):
    """
    Accepts refresh_token either from cookie (browser) or Authorization header (bot/API).
    Returns a fresh access_token.
    """
    # Try cookie first, then fall back to Authorization header
    token = request.cookies.get("refresh_token")
    if not token:
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header[7:]

    if not token:
        raise HTTPException(status_code=401, detail="No refresh token provided")

    payload = decode_token(token)
    if payload is None:
        raise HTTPException(status_code=401, detail="Invalid or expired refresh token")
    if payload.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Not a refresh token")

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Malformed token")

    user = db.query(User).filter(User.id == user_id).first()
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="User not found or inactive")

    new_access_token = create_access_token({"sub": str(user.id), "role": user.role})
    new_refresh_token = create_refresh_token({"sub": str(user.id)})
    response.set_cookie(
        key="refresh_token",
        value=new_refresh_token,
        httponly=True,
        secure=settings.ENVIRONMENT != "development",
        samesite="lax",
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
        path="/",
    )
    logger.info(f"Token refreshed for: {user.email}")
    return {"access_token": new_access_token, "token_type": "bearer"}


@router.post("/logout")
def logout(
    response: Response,
    current_user: User = Depends(get_current_user),
):
    """
    Clears the refresh_token cookie.
    The access_token expires on its own (15 min TTL).
    Frontend should delete the access_token from localStorage on receipt of this response.
    """
    response.delete_cookie("refresh_token", httponly=True, samesite="lax")
    logger.info(f"User logged out: {current_user.email}")
    return {"message": "Logged out successfully"}


@router.post("/telegram-otp", response_model=OTPResponse)
def generate_telegram_otp(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    otp = str(random.randint(100000, 999999))
    expires = datetime.now(timezone.utc) + timedelta(minutes=5)
    current_user.telegram_otp = otp
    current_user.telegram_otp_expires = expires
    db.commit()
    logger.info(f"Telegram OTP generated for {current_user.email}")
    return OTPResponse(otp=otp)


@router.post("/telegram-link")
def link_telegram(data: TelegramLinkRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.telegram_otp == data.otp).first()
    if not user:
        raise HTTPException(status_code=400, detail="Invalid OTP")
    if not user.telegram_otp_expires:
        raise HTTPException(status_code=400, detail="Invalid OTP")
    if datetime.now(timezone.utc) > user.telegram_otp_expires:
        raise HTTPException(status_code=400, detail="OTP expired")

    existing = db.query(User).filter(User.telegram_chat_id == data.chat_id).first()
    if existing and existing.id != user.id:
        raise HTTPException(
            status_code=409,
            detail="This Telegram account is already linked to another user"
        )
    user.telegram_chat_id = data.chat_id
    user.telegram_otp = None
    user.telegram_otp_expires = None
    db.commit()
    logger.info(f"Telegram linked: {user.email} → chat_id {data.chat_id}")
    return {"message": "Telegram account linked successfully"}


@router.post("/bot-login", response_model=BotLoginResponse)
def bot_login(
    data: BotLoginRequest,
    _: bool = Depends(require_bot_secret),
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(
        User.telegram_chat_id == data.chat_id,
        User.is_active == True,
    ).first()
    if not user:
        logger.warning(f"Bot login failed for chat_id: {data.chat_id}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No active account linked to this Telegram"
        )
    access_token = create_access_token(
        data={"sub": str(user.id), "role": user.role},
        expires_delta=timedelta(hours=1)
    )
    logger.info(f"Bot login: {user.email} via chat_id {data.chat_id}")
    return BotLoginResponse(
        access_token=access_token,
        token_type="bearer",
        user=UserOut.model_validate(user)
    )


@router.post("/forgot-password")
@limiter.limit("3/minute")
def forgot_password(
    request: Request,
    data: PasswordResetRequest,
    db: Session = Depends(get_db),
):
    try:
        from app.services.mail_service import ensure_smtp_configured
        ensure_smtp_configured()
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))

    user = db.query(User).filter(User.email == data.email.lower()).first()
    if user and user.is_active:
        token = secrets.token_urlsafe(32)
        expires = datetime.now(timezone.utc) + timedelta(hours=1)
        user.reset_token = token
        user.reset_token_expires = expires
        db.commit()
 
        # Use notification_email if set (real email), otherwise fall back to platform email
        recipient = user.notification_email or user.email
 
        try:
            from app.services.mail_service import send_password_reset_email
            send_password_reset_email(recipient, user.full_name, token)
        except Exception as e:
            logger.error(f"Failed to send reset email to {recipient}: {e}")
            raise HTTPException(status_code=503, detail="Failed to send reset email")

    logger.info(f"Password reset requested for: {data.email}")
    return {"message": "If that email exists, a reset link has been sent."}

@router.post("/reset-password")
def reset_password(data: PasswordResetConfirm, db: Session = Depends(get_db)):
    """Validates the reset token and sets the new password."""
    user = db.query(User).filter(User.reset_token == data.token).first()
    if not user:
        raise HTTPException(status_code=400, detail="Invalid or expired reset token")
    if not user.reset_token_expires:
        raise HTTPException(status_code=400, detail="Invalid reset token")
    if datetime.now(timezone.utc) > user.reset_token_expires:
        raise HTTPException(status_code=400, detail="Reset token has expired")

    # Validate password strength (reuse schema validator)
    from app.schemas.user import UserCreate
    try:
        UserCreate.model_validate({
            "email": user.email,
            "password": data.new_password,
            "full_name": user.full_name,
            "role": user.role,
        })
    except Exception as e:
        raise HTTPException(status_code=422, detail=str(e))

    user.hashed_password = hash_password(data.new_password)
    user.reset_token = None
    user.reset_token_expires = None
    db.commit()
    logger.info(f"Password reset successful for: {user.email}")
    return {"message": "Password reset successfully. You can now log in."}
