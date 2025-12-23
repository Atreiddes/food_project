"""
Tests for balance API endpoints.
"""
import pytest
from decimal import Decimal
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.user import User
from app.models.user_balance import UserBalance
from app.models.transaction import Transaction, TransactionType


class TestGetBalance:
    """Tests for GET /api/balance"""

    def test_get_balance_success(self, client: TestClient, test_user_with_balance: User, auth_headers: dict):
        """Test getting user balance."""
        # Act
        response = client.get("/api/balance/", headers=auth_headers)

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "balance" in data
        assert float(data["balance"]) == 1000.00

    def test_get_balance_no_balance_record(
        self,
        client: TestClient,
        test_user: User,
        auth_headers: dict,
        db_session: Session
    ):
        """Test getting balance when no balance record exists (should create one)."""
        # Act
        response = client.get("/api/balance/", headers=auth_headers)

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert float(data["balance"]) == 0.00

        # Verify balance record was created
        balance = db_session.query(UserBalance).filter(UserBalance.user_id == test_user.id).first()
        assert balance is not None
        assert float(balance.balance) == 0.00

    def test_get_balance_unauthorized(self, client: TestClient):
        """Test getting balance without authentication."""
        # Act
        response = client.get("/api/balance/")

        # Assert
        assert response.status_code == 403


class TestAddBalance:
    """Tests for POST /api/balance/add"""

    def test_add_balance_success(
        self,
        client: TestClient,
        test_user_with_balance: User,
        auth_headers: dict,
        db_session: Session
    ):
        """Test successfully adding funds to balance."""
        # Arrange
        initial_balance = db_session.query(UserBalance).filter(
            UserBalance.user_id == test_user_with_balance.id
        ).first().balance

        add_data = {"amount": 500}

        # Act
        response = client.post("/api/balance/add", json=add_data, headers=auth_headers)

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert float(data["balance"]) == float(initial_balance) + 500

        # Verify transaction was created
        transaction = db_session.query(Transaction).filter(
            Transaction.user_id == test_user_with_balance.id,
            Transaction.type == TransactionType.DEPOSIT
        ).first()
        assert transaction is not None
        assert float(transaction.amount) == 500

    def test_add_balance_creates_balance_record(
        self,
        client: TestClient,
        test_user: User,
        auth_headers: dict,
        db_session: Session
    ):
        """Test adding balance when no balance record exists."""
        # Arrange
        add_data = {"amount": 100}

        # Act
        response = client.post("/api/balance/add", json=add_data, headers=auth_headers)

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert float(data["balance"]) == 100.00

        # Verify balance record was created
        balance = db_session.query(UserBalance).filter(UserBalance.user_id == test_user.id).first()
        assert balance is not None

    def test_add_balance_negative_amount(
        self,
        client: TestClient,
        test_user_with_balance: User,
        auth_headers: dict
    ):
        """Test adding negative amount (should fail)."""
        # Arrange
        add_data = {"amount": -100}

        # Act
        response = client.post("/api/balance/add", json=add_data, headers=auth_headers)

        # Assert
        assert response.status_code == 400
        assert "positive" in response.json()["detail"].lower()

    def test_add_balance_zero_amount(
        self,
        client: TestClient,
        test_user_with_balance: User,
        auth_headers: dict
    ):
        """Test adding zero amount (should fail)."""
        # Arrange
        add_data = {"amount": 0}

        # Act
        response = client.post("/api/balance/add", json=add_data, headers=auth_headers)

        # Assert
        assert response.status_code == 400
        assert "positive" in response.json()["detail"].lower()

    def test_add_balance_exceeds_maximum(
        self,
        client: TestClient,
        test_user_with_balance: User,
        auth_headers: dict
    ):
        """Test adding amount that exceeds maximum limit."""
        # Arrange
        add_data = {"amount": 10001}

        # Act
        response = client.post("/api/balance/add", json=add_data, headers=auth_headers)

        # Assert
        assert response.status_code == 400
        assert "Maximum" in response.json()["detail"]

    def test_add_balance_at_maximum(
        self,
        client: TestClient,
        test_user_with_balance: User,
        auth_headers: dict
    ):
        """Test adding maximum allowed amount."""
        # Arrange
        add_data = {"amount": 10000}

        # Act
        response = client.post("/api/balance/add", json=add_data, headers=auth_headers)

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert float(data["balance"]) == 11000.00  # 1000 initial + 10000

    def test_add_balance_unauthorized(self, client: TestClient):
        """Test adding balance without authentication."""
        # Arrange
        add_data = {"amount": 100}

        # Act
        response = client.post("/api/balance/add", json=add_data)

        # Assert
        assert response.status_code == 403


class TestGetTransactions:
    """Tests for GET /api/balance/transactions"""

    def test_get_transactions_success(
        self,
        client: TestClient,
        test_user_with_balance: User,
        test_transaction: Transaction,
        auth_headers: dict
    ):
        """Test getting transaction history."""
        # Act
        response = client.get("/api/balance/transactions", headers=auth_headers)

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "transactions" in data
        assert len(data["transactions"]) > 0

        # Verify transaction details
        transaction = data["transactions"][0]
        assert "id" in transaction
        assert "type" in transaction
        assert "amount" in transaction
        assert "status" in transaction
        assert "description" in transaction
        assert "created_at" in transaction

    def test_get_transactions_empty(
        self,
        client: TestClient,
        test_user: User,
        auth_headers: dict
    ):
        """Test getting transactions when there are none."""
        # Act
        response = client.get("/api/balance/transactions", headers=auth_headers)

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "transactions" in data
        assert len(data["transactions"]) == 0

    def test_get_transactions_limit(
        self,
        client: TestClient,
        test_user_with_balance: User,
        auth_headers: dict,
        db_session: Session
    ):
        """Test getting transactions with custom limit."""
        # Arrange - create 10 transactions
        for i in range(10):
            transaction = Transaction(
                user_id=test_user_with_balance.id,
                amount=Decimal(f"{i + 1}.00"),
                type=TransactionType.DEPOSIT,
                description=f"Test transaction {i + 1}"
            )
            db_session.add(transaction)
        db_session.commit()

        # Act
        response = client.get("/api/balance/transactions?limit=5", headers=auth_headers)

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert len(data["transactions"]) == 5

    def test_get_transactions_ordered_by_date(
        self,
        client: TestClient,
        test_user_with_balance: User,
        auth_headers: dict,
        db_session: Session
    ):
        """Test that transactions are ordered by created_at desc."""
        # Arrange - create multiple transactions
        for i in range(3):
            transaction = Transaction(
                user_id=test_user_with_balance.id,
                amount=Decimal(f"{(i + 1) * 10}.00"),
                type=TransactionType.DEPOSIT,
                description=f"Transaction {i + 1}"
            )
            db_session.add(transaction)
        db_session.commit()

        # Act
        response = client.get("/api/balance/transactions", headers=auth_headers)

        # Assert
        assert response.status_code == 200
        data = response.json()
        transactions = data["transactions"]

        # Verify ordering (most recent first)
        for i in range(len(transactions) - 1):
            assert transactions[i]["created_at"] >= transactions[i + 1]["created_at"]

    def test_get_transactions_only_own_transactions(
        self,
        client: TestClient,
        test_user_with_balance: User,
        auth_headers: dict,
        db_session: Session
    ):
        """Test that user can only see their own transactions."""
        # Arrange - create another user with transactions
        other_user = User(
            email="other@example.com",
            username="otheruser",
            hashed_password="hash"
        )
        db_session.add(other_user)
        db_session.commit()

        other_transaction = Transaction(
            user_id=other_user.id,
            amount=Decimal("999.00"),
            type=TransactionType.DEPOSIT,
            description="Other user's transaction"
        )
        db_session.add(other_transaction)
        db_session.commit()

        # Act
        response = client.get("/api/balance/transactions", headers=auth_headers)

        # Assert
        assert response.status_code == 200
        data = response.json()

        # Verify no other user's transactions are returned
        for transaction in data["transactions"]:
            assert transaction["description"] != "Other user's transaction"

    def test_get_transactions_unauthorized(self, client: TestClient):
        """Test getting transactions without authentication."""
        # Act
        response = client.get("/api/balance/transactions")

        # Assert
        assert response.status_code == 403
