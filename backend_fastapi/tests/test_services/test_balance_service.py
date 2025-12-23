"""
Tests for BalanceService and TransactionService.
"""
import pytest
from decimal import Decimal
from sqlalchemy.orm import Session

from app.services.balance import BalanceService, TransactionService
from app.models.user import User
from app.models.user_balance import UserBalance
from app.models.transaction import Transaction, TransactionType


class TestBalanceService:
    """Tests for BalanceService"""

    def test_get_balance_existing(self, db_session: Session, test_user_with_balance: User):
        """Test getting balance for user with existing balance record."""
        # Arrange
        service = BalanceService(db_session)

        # Act
        balance = service.get_balance(test_user_with_balance.id)

        # Assert
        assert balance == Decimal("1000.00")

    def test_get_balance_nonexistent(self, db_session: Session, test_user: User):
        """Test getting balance for user without balance record."""
        # Arrange
        service = BalanceService(db_session)

        # Act
        balance = service.get_balance(test_user.id)

        # Assert
        assert balance == Decimal("0")

    def test_has_sufficient_balance_true(self, db_session: Session, test_user_with_balance: User):
        """Test checking sufficient balance when user has enough."""
        # Arrange
        service = BalanceService(db_session)

        # Act
        result = service.has_sufficient_balance(test_user_with_balance.id, Decimal("100.00"))

        # Assert
        assert result is True

    def test_has_sufficient_balance_false(self, db_session: Session, test_user_with_balance: User):
        """Test checking sufficient balance when user doesn't have enough."""
        # Arrange
        service = BalanceService(db_session)

        # Act
        result = service.has_sufficient_balance(test_user_with_balance.id, Decimal("2000.00"))

        # Assert
        assert result is False

    def test_has_sufficient_balance_exact_amount(self, db_session: Session, test_user_with_balance: User):
        """Test checking sufficient balance with exact amount."""
        # Arrange
        service = BalanceService(db_session)

        # Act
        result = service.has_sufficient_balance(test_user_with_balance.id, Decimal("1000.00"))

        # Assert
        assert result is True

    def test_has_sufficient_balance_no_record(self, db_session: Session, test_user: User):
        """Test checking sufficient balance for user without balance record."""
        # Arrange
        service = BalanceService(db_session)

        # Act
        result = service.has_sufficient_balance(test_user.id, Decimal("10.00"))

        # Assert
        assert result is False

    def test_deduct_success(self, db_session: Session, test_user_with_balance: User):
        """Test successfully deducting from balance."""
        # Arrange
        service = BalanceService(db_session)
        initial_balance = Decimal("1000.00")
        deduct_amount = Decimal("100.00")

        # Act
        result = service.deduct(test_user_with_balance.id, deduct_amount)

        # Assert
        assert result is True
        db_session.commit()
        db_session.refresh(test_user_with_balance)

        # Verify balance was deducted
        balance_record = db_session.query(UserBalance).filter(
            UserBalance.user_id == test_user_with_balance.id
        ).first()
        assert balance_record.balance == initial_balance - deduct_amount

    def test_deduct_insufficient_balance(self, db_session: Session, test_user_with_balance: User):
        """Test deducting when balance is insufficient."""
        # Arrange
        service = BalanceService(db_session)
        deduct_amount = Decimal("2000.00")

        # Act
        result = service.deduct(test_user_with_balance.id, deduct_amount)

        # Assert
        assert result is False

        # Verify balance wasn't changed
        balance_record = db_session.query(UserBalance).filter(
            UserBalance.user_id == test_user_with_balance.id
        ).first()
        assert balance_record.balance == Decimal("1000.00")

    def test_deduct_no_balance_record(self, db_session: Session, test_user: User):
        """Test deducting when no balance record exists."""
        # Arrange
        service = BalanceService(db_session)

        # Act
        result = service.deduct(test_user.id, Decimal("10.00"))

        # Assert
        assert result is False

    def test_refund_success(self, db_session: Session, test_user_with_balance: User):
        """Test successfully refunding to balance."""
        # Arrange
        service = BalanceService(db_session)
        initial_balance = Decimal("1000.00")
        refund_amount = Decimal("50.00")

        # Act
        result = service.refund(test_user_with_balance.id, refund_amount)

        # Assert
        assert result is True
        db_session.commit()
        db_session.refresh(test_user_with_balance)

        # Verify balance was increased
        balance_record = db_session.query(UserBalance).filter(
            UserBalance.user_id == test_user_with_balance.id
        ).first()
        assert balance_record.balance == initial_balance + refund_amount

    def test_refund_no_balance_record(self, db_session: Session, test_user: User):
        """Test refunding when no balance record exists."""
        # Arrange
        service = BalanceService(db_session)

        # Act
        result = service.refund(test_user.id, Decimal("10.00"))

        # Assert
        assert result is False

    def test_deduct_and_refund_cycle(self, db_session: Session, test_user_with_balance: User):
        """Test deducting and then refunding."""
        # Arrange
        service = BalanceService(db_session)
        initial_balance = Decimal("1000.00")
        amount = Decimal("100.00")

        # Act - Deduct
        deduct_result = service.deduct(test_user_with_balance.id, amount)
        db_session.commit()

        # Act - Refund
        refund_result = service.refund(test_user_with_balance.id, amount)
        db_session.commit()

        # Assert
        assert deduct_result is True
        assert refund_result is True

        balance_record = db_session.query(UserBalance).filter(
            UserBalance.user_id == test_user_with_balance.id
        ).first()
        assert balance_record.balance == initial_balance


class TestTransactionService:
    """Tests for TransactionService"""

    def test_create_ml_request_transaction(self, db_session: Session, test_user: User):
        """Test creating ML request transaction."""
        # Arrange
        service = TransactionService(db_session)
        amount = Decimal("10.00")
        description = "ML request: test message"

        # Act
        transaction = service.create_ml_request_transaction(
            user_id=test_user.id,
            amount=amount,
            description=description
        )
        db_session.commit()

        # Assert
        assert transaction is not None
        assert transaction.user_id == test_user.id
        assert transaction.type == TransactionType.ML_REQUEST
        assert transaction.amount == -amount  # Negative for deduction
        assert transaction.description == description

        # Verify it was saved to database
        saved_transaction = db_session.query(Transaction).filter(
            Transaction.id == transaction.id
        ).first()
        assert saved_transaction is not None

    def test_create_refund_transaction(self, db_session: Session, test_user: User):
        """Test creating refund transaction."""
        # Arrange
        service = TransactionService(db_session)
        amount = Decimal("10.00")
        description = "Refund for failed ML request"

        # Act
        transaction = service.create_refund_transaction(
            user_id=test_user.id,
            amount=amount,
            description=description
        )
        db_session.commit()

        # Assert
        assert transaction is not None
        assert transaction.user_id == test_user.id
        assert transaction.type == TransactionType.REFUND
        assert transaction.amount == amount  # Positive for refund
        assert transaction.description == description

        # Verify it was saved to database
        saved_transaction = db_session.query(Transaction).filter(
            Transaction.id == transaction.id
        ).first()
        assert saved_transaction is not None

    def test_multiple_transactions_for_user(self, db_session: Session, test_user: User):
        """Test creating multiple transactions for same user."""
        # Arrange
        service = TransactionService(db_session)

        # Act
        transaction1 = service.create_ml_request_transaction(
            user_id=test_user.id,
            amount=Decimal("10.00"),
            description="First request"
        )
        transaction2 = service.create_refund_transaction(
            user_id=test_user.id,
            amount=Decimal("10.00"),
            description="Refund first request"
        )
        transaction3 = service.create_ml_request_transaction(
            user_id=test_user.id,
            amount=Decimal("10.00"),
            description="Second request"
        )
        db_session.commit()

        # Assert
        transactions = db_session.query(Transaction).filter(
            Transaction.user_id == test_user.id
        ).all()
        assert len(transactions) == 3
        assert transaction1.id != transaction2.id != transaction3.id
