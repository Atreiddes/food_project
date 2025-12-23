"""
Tests for authentication API endpoints.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.user import User
from app.models.user_balance import UserBalance


class TestRegister:
    """Tests for POST /api/auth/register"""

    def test_register_success(self, client: TestClient, db_session: Session):
        """Test successful user registration."""
        # Arrange
        user_data = {
            "email": "newuser@example.com",
            "password": "securepassword123"
        }

        # Act
        response = client.post("/api/auth/register", json=user_data)

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "token" in data
        assert "user" in data
        assert data["user"]["email"] == user_data["email"]
        assert data["user"]["role"] == "user"

        # Verify user was created in database
        user = db_session.query(User).filter(User.email == user_data["email"]).first()
        assert user is not None
        assert user.is_active is True

        # Verify initial balance was created
        balance = db_session.query(UserBalance).filter(UserBalance.user_id == user.id).first()
        assert balance is not None
        assert float(balance.balance) == 10.00

    def test_register_duplicate_email(self, client: TestClient, test_user: User):
        """Test registration with already existing email."""
        # Arrange
        user_data = {
            "email": test_user.email,
            "password": "anotherpassword123"
        }

        # Act
        response = client.post("/api/auth/register", json=user_data)

        # Assert
        assert response.status_code == 400
        assert "Email already registered" in response.json()["detail"]

    def test_register_invalid_email(self, client: TestClient):
        """Test registration with invalid email format."""
        # Arrange
        user_data = {
            "email": "not-an-email",
            "password": "securepassword123"
        }

        # Act
        response = client.post("/api/auth/register", json=user_data)

        # Assert
        assert response.status_code == 422  # Validation error

    def test_register_missing_password(self, client: TestClient):
        """Test registration without password."""
        # Arrange
        user_data = {
            "email": "newuser@example.com"
        }

        # Act
        response = client.post("/api/auth/register", json=user_data)

        # Assert
        assert response.status_code == 422  # Validation error


class TestLogin:
    """Tests for POST /api/auth/login"""

    def test_login_success(self, client: TestClient, test_user: User):
        """Test successful login with correct credentials."""
        # Arrange
        login_data = {
            "email": test_user.email,
            "password": "testpassword123"
        }

        # Act
        response = client.post("/api/auth/login", json=login_data)

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "token" in data
        assert "user" in data
        assert data["user"]["email"] == test_user.email
        assert data["user"]["id"] == test_user.id

    def test_login_wrong_password(self, client: TestClient, test_user: User):
        """Test login with incorrect password."""
        # Arrange
        login_data = {
            "email": test_user.email,
            "password": "wrongpassword"
        }

        # Act
        response = client.post("/api/auth/login", json=login_data)

        # Assert
        assert response.status_code == 401
        assert "Incorrect email or password" in response.json()["detail"]

    def test_login_nonexistent_user(self, client: TestClient):
        """Test login with non-existent email."""
        # Arrange
        login_data = {
            "email": "nonexistent@example.com",
            "password": "somepassword"
        }

        # Act
        response = client.post("/api/auth/login", json=login_data)

        # Assert
        assert response.status_code == 401
        assert "Incorrect email or password" in response.json()["detail"]

    def test_login_inactive_user(self, client: TestClient, db_session: Session, test_user: User):
        """Test login with deactivated user account."""
        # Arrange
        test_user.is_active = False
        db_session.commit()

        login_data = {
            "email": test_user.email,
            "password": "testpassword123"
        }

        # Act
        response = client.post("/api/auth/login", json=login_data)

        # Assert
        assert response.status_code == 403
        assert "deactivated" in response.json()["detail"].lower()


class TestGuest:
    """Tests for POST /api/auth/guest"""

    def test_create_guest_success(self, client: TestClient, db_session: Session):
        """Test successful guest account creation."""
        # Act
        response = client.post("/api/auth/guest")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "token" in data
        assert "user_id" in data
        assert "message" in data
        assert "5.00" in data["message"]

        # Verify guest user was created
        user = db_session.query(User).filter(User.id == data["user_id"]).first()
        assert user is not None
        assert "guest" in user.email

        # Verify guest has limited balance
        balance = db_session.query(UserBalance).filter(UserBalance.user_id == user.id).first()
        assert balance is not None
        assert float(balance.balance) == 5.00

    def test_create_multiple_guests(self, client: TestClient, db_session: Session):
        """Test creating multiple guest accounts."""
        # Act
        response1 = client.post("/api/auth/guest")
        response2 = client.post("/api/auth/guest")

        # Assert
        assert response1.status_code == 200
        assert response2.status_code == 200

        user_id1 = response1.json()["user_id"]
        user_id2 = response2.json()["user_id"]

        # Verify both guests are unique
        assert user_id1 != user_id2


class TestGetMe:
    """Tests for GET /api/auth/me"""

    def test_get_me_success(self, client: TestClient, test_user_with_balance: User, auth_headers: dict):
        """Test getting current user profile."""
        # Act
        response = client.get("/api/auth/me", headers=auth_headers)

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_user_with_balance.id
        assert data["email"] == test_user_with_balance.email
        assert data["role"] == "user"
        assert data["is_active"] is True
        assert "balance" in data
        assert float(data["balance"]) == 1000.00

    def test_get_me_unauthorized(self, client: TestClient):
        """Test getting profile without authentication."""
        # Act
        response = client.get("/api/auth/me")

        # Assert
        assert response.status_code == 403  # No auth header

    def test_get_me_invalid_token(self, client: TestClient):
        """Test getting profile with invalid token."""
        # Arrange
        invalid_headers = {"Authorization": "Bearer invalid_token_here"}

        # Act
        response = client.get("/api/auth/me", headers=invalid_headers)

        # Assert
        assert response.status_code == 401

    def test_get_me_guest_user(self, client: TestClient, test_guest_user: User, guest_headers: dict, db_session: Session):
        """Test getting guest user profile."""
        # Arrange - create balance for guest
        balance = UserBalance(user_id=test_guest_user.id, balance=5.00)
        db_session.add(balance)
        db_session.commit()

        # Act
        response = client.get("/api/auth/me", headers=guest_headers)

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_guest_user.id
        assert "guest" in data["email"]
        assert float(data["balance"]) == 5.00
