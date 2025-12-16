from decimal import Decimal
from typing import Optional
import uuid

from sqlalchemy.orm import Session

from app.models.user_balance import UserBalance
from app.models.transaction import Transaction, TransactionType, TransactionStatus


class BalanceService:
    """Service for managing user balance operations."""

    def __init__(self, db: Session):
        self._db = db

    def get_balance(self, user_id: str) -> Decimal:
        """Get user's current balance."""
        record = self._db.query(UserBalance).filter(
            UserBalance.user_id == user_id
        ).first()
        return record.balance if record else Decimal("0")

    def has_sufficient_balance(self, user_id: str, amount: Decimal) -> bool:
        """Check if user has enough balance for the operation."""
        return self.get_balance(user_id) >= amount

    def deduct(self, user_id: str, amount: Decimal) -> bool:
        """Deduct amount from user's balance."""
        record = self._db.query(UserBalance).filter(
            UserBalance.user_id == user_id
        ).first()

        if not record or record.balance < amount:
            return False

        record.balance -= amount
        return True

    def refund(self, user_id: str, amount: Decimal) -> bool:
        """Refund amount to user's balance."""
        record = self._db.query(UserBalance).filter(
            UserBalance.user_id == user_id
        ).first()

        if not record:
            return False

        record.balance += amount
        return True


class TransactionService:
    """Service for managing transaction records."""

    def __init__(self, db: Session):
        self._db = db

    def create_ml_request_transaction(
        self,
        user_id: str,
        amount: Decimal,
        description: str
    ) -> Transaction:
        """Create a transaction record for ML request."""
        transaction = Transaction(
            id=str(uuid.uuid4()),
            user_id=user_id,
            type=TransactionType.ML_REQUEST,
            amount=-amount,
            status=TransactionStatus.COMPLETED,
            description=description
        )
        self._db.add(transaction)
        return transaction

    def create_refund_transaction(
        self,
        user_id: str,
        amount: Decimal,
        description: str
    ) -> Transaction:
        """Create a refund transaction record."""
        transaction = Transaction(
            id=str(uuid.uuid4()),
            user_id=user_id,
            type=TransactionType.REFUND,
            amount=amount,
            status=TransactionStatus.COMPLETED,
            description=description
        )
        self._db.add(transaction)
        return transaction
