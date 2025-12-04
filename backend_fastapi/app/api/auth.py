from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
import uuid

from app.db.base import get_db
from app.models.user import User, UserRole
from app.models.user_balance import UserBalance
from app.schemas.user import UserCreate, UserLogin, UserResponse, GuestResponse
from app.schemas.token import Token
from app.core.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    decode_access_token
)

router = APIRouter()
security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """
    Dependency to get the current authenticated user from JWT token.
    Used by other endpoints to protect routes.
    """
    token = credentials.credentials
    payload = decode_access_token(token)

    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"}
        )

    user_id: str = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
            headers={"WWW-Authenticate": "Bearer"}
        )

    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"}
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is deactivated"
        )

    return user


@router.post("/register", response_model=Token)
async def register(user_data: UserCreate, db: Session = Depends(get_db)):
    """
    Register a new user account.
    Creates user and initial balance record.
    """
    # Check if email already exists
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    # Create new user
    user_id = str(uuid.uuid4())
    hashed_password = get_password_hash(user_data.password)

    new_user = User(
        id=user_id,
        email=user_data.email,
        password_hash=hashed_password,
        role=UserRole.USER,
        is_active=True
    )

    db.add(new_user)

    # Create initial balance (10.00 for new users)
    user_balance = UserBalance(
        user_id=user_id,
        balance=10.00
    )
    db.add(user_balance)

    db.commit()
    db.refresh(new_user)

    # Generate token
    access_token = create_access_token(data={"sub": user_id})

    return Token(
        token=access_token,
        user={
            "id": new_user.id,
            "email": new_user.email,
            "role": new_user.role.value
        }
    )


@router.post("/login", response_model=Token)
async def login(user_data: UserLogin, db: Session = Depends(get_db)):
    """
    Authenticate user and return JWT token.
    """
    user = db.query(User).filter(User.email == user_data.email).first()

    if not user or not verify_password(user_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is deactivated"
        )

    access_token = create_access_token(data={"sub": user.id})

    return Token(
        token=access_token,
        user={
            "id": user.id,
            "email": user.email,
            "role": user.role.value
        }
    )


@router.post("/guest", response_model=GuestResponse)
async def create_guest(db: Session = Depends(get_db)):
    """
    Create a guest user account with limited balance.
    No email or password required.
    """
    user_id = str(uuid.uuid4())
    guest_email = f"guest_{user_id[:8]}@guest.local"

    # Create guest user with random password
    guest_password = str(uuid.uuid4())
    hashed_password = get_password_hash(guest_password)

    new_user = User(
        id=user_id,
        email=guest_email,
        password_hash=hashed_password,
        role=UserRole.USER,
        is_active=True
    )

    db.add(new_user)

    # Create initial balance (5.00 for guest users)
    user_balance = UserBalance(
        user_id=user_id,
        balance=5.00
    )
    db.add(user_balance)

    db.commit()

    access_token = create_access_token(data={"sub": user_id})

    return GuestResponse(
        token=access_token,
        user_id=user_id,
        message="Guest account created. Balance: 5.00"
    )


@router.get("/me", response_model=UserResponse)
async def get_me(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get current user's profile information.
    """
    # Get user's balance
    balance_record = db.query(UserBalance).filter(
        UserBalance.user_id == current_user.id
    ).first()

    balance = balance_record.balance if balance_record else 0

    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        role=current_user.role.value,
        is_active=current_user.is_active,
        balance=balance
    )
