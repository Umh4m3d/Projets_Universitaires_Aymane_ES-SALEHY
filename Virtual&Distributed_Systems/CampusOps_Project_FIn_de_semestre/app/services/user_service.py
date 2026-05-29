from sqlalchemy.orm import Session

from app.core.security import hash_password, verify_password
from app.models.user import User
from app.schemas.user import UserCreate


def get_user_by_email(db: Session, email: str) -> User | None:
    return db.query(User).filter(User.email == email.lower()).first()


def create_user(db: Session, user_data: UserCreate) -> User:
    existing = get_user_by_email(db, user_data.email)
    if existing:
        raise ValueError("Email already registered")

    user = User(
        email=user_data.email.lower(),
        hashed_password=hash_password(user_data.password),
        full_name=user_data.full_name.strip(),
        role=user_data.role.value,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

# A real bcrypt hash of the word "dummy" — computed once at startup
# This is used only to waste time when a user is not found
DUMMY_HASH = "$2b$12$Hae3A8nFRgEuPkuK.EjGEeH6xKG96h9DxhNVMVCKVojfI2G3qsPk."


def authenticate_user(db: Session, email: str, password: str) -> User | None:
    user = get_user_by_email(db, email)

    # Always run bcrypt — even if user doesn't exist
    # This makes both code paths take the same amount of time
    hash_to_check = user.hashed_password if user else DUMMY_HASH
    password_matches = verify_password(password, hash_to_check)

    if not user or not password_matches or not user.is_active:
        return None

    return user
