from pydantic import BaseModel
from decimal import Decimal


class BalanceResponse(BaseModel):
    balance: Decimal


class BalanceAdd(BaseModel):
    amount: Decimal
