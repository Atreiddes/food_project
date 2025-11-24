from pydantic import BaseModel, EmailStr, field_validator
from datetime import datetime
from decimal import Decimal
from typing import Optional
import re


class UserCreate(BaseModel):
    email: EmailStr
    password: str

    @field_validator('password')
    @classmethod
    def validate_password(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not re.search(r'[A-Za-z]', v):
            raise ValueError('Password must contain at least one letter')
        if not re.search(r'\d', v):
            raise ValueError('Password must contain at least one digit')
        return v


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserBalanceInfo(BaseModel):
    """Схема для информации о балансе."""
    balance: Decimal
    updated_at: datetime

    class Config:
        from_attributes = True


class UserResponse(BaseModel):
    """
    Схема ответа с данными пользователя.

    Теперь баланс вынесен в отдельный объект (SRP).
    """
    id: str
    email: str
    role: str
    is_active: bool
    created_at: datetime
    balance_info: Optional[UserBalanceInfo] = None
    is_guest: Optional[bool] = False

    class Config:
        from_attributes = True

    @property
    def balance(self) -> Decimal:
        """
        Свойство для обратной совместимости.
        Возвращает баланс из balance_info.
        """
        if self.balance_info:
            return self.balance_info.balance
        return Decimal(0)


class GuestResponse(BaseModel):
    user: UserResponse
    token: str
    message: str
