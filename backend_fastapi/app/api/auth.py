from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError, OperationalError
from app.db.base import get_db
from app.models.user import User, UserRole
from app.models.user_balance import UserBalance
from app.schemas.user import UserCreate, UserLogin, UserResponse, GuestResponse
from app.schemas.token import Token
from app.core.security import get_password_hash, verify_password, create_access_token, decode_access_token
from app.core.exceptions import DuplicateError, DatabaseError
from app.core.rate_limit import limiter
from app.core.logging_config import app_logger
from app.core.user_helpers import get_user_with_balance, get_user_by_email_with_balance
from fastapi.security import HTTPBearer
from fastapi.security.http import HTTPAuthorizationCredentials
import uuid
import secrets

router = APIRouter()
security = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    token = credentials.credentials
    payload = decode_access_token(token)

    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials"
        )

    user_id = payload.get("user_id")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials"
        )

    # Load user with balance (eager loading to prevent N+1)
    user = get_user_with_balance(db, user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )

    return user


@router.post("/register", response_model=Token)
@limiter.limit("5/minute")
async def register(request: Request, user_data: UserCreate, db: Session = Depends(get_db)):
    """
    Регистрация нового пользователя.

    Теперь создает:
    1. User (аутентификация)
    2. UserBalance (финансы) - отдельная сущность!
    """
    user_id = str(uuid.uuid4())

    user = User(
        id=user_id,
        email=user_data.email,
        password_hash=get_password_hash(user_data.password),
        role=UserRole.USER,
        is_active=True
    )

    # Создаем баланс отдельно (SRP)
    user_balance = UserBalance(
        user_id=user_id,
        balance=1000  # DEFAULT_USER_BALANCE
    )

    db.add(user)
    db.add(user_balance)

    try:
        db.commit()
        app_logger.info(f"New user registered successfully", extra={"user_id": user.id, "email": user.email})
    except IntegrityError:
        db.rollback()
        app_logger.warning(f"Registration failed: Email already exists", extra={"email": user_data.email})
        raise DuplicateError("Email already registered")
    except OperationalError as e:
        db.rollback()
        app_logger.error(f"Database connection error during registration: {str(e)}")
        raise DatabaseError(f"Database connection error: {str(e)}")
    except Exception as e:
        db.rollback()
        app_logger.error(f"Unexpected error during registration: {str(e)}")
        raise DatabaseError(f"Unexpected error: {str(e)}")

    # Load user with balance for response
    user_with_balance = get_user_with_balance(db, user_id)

    token = create_access_token(
        data={"user_id": user.id, "email": user.email, "role": user.role.value}
    )

    return {
        "token": token,
        "user": {
            "id": user_with_balance.id,
            "email": user_with_balance.email,
            "role": user_with_balance.role.value,
            "balance": user_with_balance.balance_info.balance if user_with_balance.balance_info else 0,
            "is_active": user_with_balance.is_active,
            "created_at": user_with_balance.created_at
        }
    }


@router.post("/login", response_model=Token)
@limiter.limit("5/minute")
async def login(request: Request, user_data: UserLogin, db: Session = Depends(get_db)):
    # Load user with balance using helper
    user = get_user_by_email_with_balance(db, user_data.email)

    if not user or not verify_password(user_data.password, user.password_hash):
        app_logger.warning(f"Failed login attempt", extra={"email": user_data.email})
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive"
        )

    # Create access token
    token = create_access_token(
        data={"user_id": user.id, "email": user.email, "role": user.role.value}
    )

    app_logger.info(f"User logged in successfully", extra={"user_id": user.id, "email": user.email})

    return {
        "token": token,
        "user": {
            "id": user.id,
            "email": user.email,
            "role": user.role.value,
            "balance": user.balance_info.balance if user.balance_info else 0,
            "is_active": user.is_active,
            "created_at": user.created_at
        }
    }


@router.post("/guest", response_model=GuestResponse)
@limiter.limit("10/minute")
async def guest_login(request: Request, db: Session = Depends(get_db)):
    guest_email = f"guest_{int(uuid.uuid4().time)}_{secrets.token_hex(3)}@guest.local"
    user_id = str(uuid.uuid4())

    # Create User (authentication)
    user = User(
        id=user_id,
        email=guest_email,
        password_hash=get_password_hash(secrets.token_hex(32)),
        role=UserRole.USER,
        is_active=True
    )

    # Create UserBalance (finance) - separate entity
    user_balance = UserBalance(
        user_id=user_id,
        balance=1000  # DEFAULT_GUEST_BALANCE
    )

    db.add(user)
    db.add(user_balance)
    try:
        db.commit()
    except Exception as e:
        db.rollback()
        raise DatabaseError(f"Failed to create guest user: {str(e)}")

    # Load user with balance for response
    user_with_balance = get_user_with_balance(db, user_id)

    token = create_access_token(
        data={"user_id": user.id, "email": user.email, "role": user.role.value, "is_guest": True}
    )

    return {
        "user": {
            "id": user_with_balance.id,
            "email": user_with_balance.email,
            "role": user_with_balance.role.value,
            "balance": user_with_balance.balance_info.balance if user_with_balance.balance_info else 0,
            "is_active": user_with_balance.is_active,
            "created_at": user_with_balance.created_at,
            "is_guest": True
        },
        "token": token,
        "message": "Guest session created. Your data will be available for 24 hours."
    }


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """
    Get current user info.
    User is already loaded with balance_info via get_current_user dependency.
    """
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        role=current_user.role.value,
        balance_info=current_user.balance_info,
        is_active=current_user.is_active,
        created_at=current_user.created_at
    )
