from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional
from decimal import Decimal


class UserCreate(BaseModel):
    """Schema for user registration."""
    email: EmailStr
    password: str

    @field_validator('password')
    @classmethod
    def validate_password(cls, v: str) -> str:
        if len(v) < 6:
            raise ValueError('Password must be at least 6 characters')
        if len(v) > 100:
            raise ValueError('Password is too long (max 100 characters)')
        return v


class UserLogin(BaseModel):
    """Schema for user login."""
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    """Schema for user response (without sensitive data)."""
    id: str
    email: str
    role: str
    is_active: bool
    balance: Optional[Decimal] = None

    class Config:
        from_attributes = True


class GuestResponse(BaseModel):
    """Schema for guest user creation response."""
    token: str
    user_id: str
    message: str = "Guest account created successfully"
