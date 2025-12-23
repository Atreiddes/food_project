"""
Tests for chat/predictions API endpoints.
"""
import pytest
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from decimal import Decimal

from app.models.user import User
from app.models.prediction import Prediction, PredictionStatus


class TestSendMessage:
    """Tests for POST /api/chat/message"""

    @patch('app.api.predictions.TaskPublisherFactory.get_publisher')
    def test_send_message_success(
        self,
        mock_get_publisher,
        client: TestClient,
        test_user_with_balance: User,
        auth_headers: dict,
        db_session: Session
    ):
        """Test successfully sending a message to ML model."""
        # Arrange
        mock_publisher = AsyncMock()
        mock_publisher.publish = AsyncMock(return_value=True)
        mock_get_publisher.return_value = mock_publisher

        message_data = {
            "message": "What should I eat today?",
            "conversation_history": []
        }

        initial_balance = Decimal("1000.00")

        # Act
        response = client.post("/api/chat/message", json=message_data, headers=auth_headers)

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert data["status"] == "pending"
        assert data["user_id"] == test_user_with_balance.id
        assert data["result"] is None

        # Verify prediction was created
        prediction = db_session.query(Prediction).filter(Prediction.id == data["id"]).first()
        assert prediction is not None
        assert prediction.status == PredictionStatus.PENDING

        # Verify balance was deducted
        from app.models.user_balance import UserBalance
        balance = db_session.query(UserBalance).filter(
            UserBalance.user_id == test_user_with_balance.id
        ).first()
        assert balance.balance == initial_balance - Decimal("10.00")

    @patch('app.api.predictions.TaskPublisherFactory.get_publisher')
    def test_send_message_with_conversation_history(
        self,
        mock_get_publisher,
        client: TestClient,
        test_user_with_balance: User,
        auth_headers: dict
    ):
        """Test sending message with conversation history."""
        # Arrange
        mock_publisher = AsyncMock()
        mock_publisher.publish = AsyncMock(return_value=True)
        mock_get_publisher.return_value = mock_publisher

        message_data = {
            "message": "And what about dinner?",
            "conversation_history": [
                {"role": "user", "content": "What should I eat for lunch?"},
                {"role": "assistant", "content": "Try a salad with protein."}
            ]
        }

        # Act
        response = client.post("/api/chat/message", json=message_data, headers=auth_headers)

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "pending"

    def test_send_message_insufficient_balance(
        self,
        client: TestClient,
        test_user_low_balance: User,
        db_session: Session
    ):
        """Test sending message with insufficient balance."""
        # Arrange
        from app.core.security import create_access_token
        token = create_access_token({"sub": test_user_low_balance.id})
        headers = {"Authorization": f"Bearer {token}"}

        message_data = {
            "message": "What should I eat today?",
            "conversation_history": []
        }

        # Act
        response = client.post("/api/chat/message", json=message_data, headers=headers)

        # Assert
        assert response.status_code == 402  # Payment Required
        assert "Insufficient balance" in response.json()["detail"]

    def test_send_message_unauthorized(self, client: TestClient):
        """Test sending message without authentication."""
        # Arrange
        message_data = {
            "message": "What should I eat today?",
            "conversation_history": []
        }

        # Act
        response = client.post("/api/chat/message", json=message_data)

        # Assert
        assert response.status_code == 403

    def test_send_message_empty_message(
        self,
        client: TestClient,
        test_user_with_balance: User,
        auth_headers: dict
    ):
        """Test sending empty message."""
        # Arrange
        message_data = {
            "message": "",
            "conversation_history": []
        }

        # Act
        response = client.post("/api/chat/message", json=message_data, headers=auth_headers)

        # Assert
        assert response.status_code == 422  # Validation error

    def test_send_message_missing_message(
        self,
        client: TestClient,
        test_user_with_balance: User,
        auth_headers: dict
    ):
        """Test sending request without message field."""
        # Arrange
        message_data = {
            "conversation_history": []
        }

        # Act
        response = client.post("/api/chat/message", json=message_data, headers=auth_headers)

        # Assert
        assert response.status_code == 422  # Validation error

    @patch('app.api.predictions.TaskPublisherFactory.get_publisher')
    def test_send_message_publisher_failure(
        self,
        mock_get_publisher,
        client: TestClient,
        test_user_with_balance: User,
        auth_headers: dict,
        db_session: Session
    ):
        """Test handling when message publishing fails."""
        # Arrange
        mock_publisher = AsyncMock()
        mock_publisher.publish = AsyncMock(return_value=False)  # Publish fails
        mock_get_publisher.return_value = mock_publisher

        message_data = {
            "message": "What should I eat today?",
            "conversation_history": []
        }

        # Act
        response = client.post("/api/chat/message", json=message_data, headers=auth_headers)

        # Assert
        # Should still return 200 and create prediction
        # (Publisher failure is logged but doesn't fail the request)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "pending"


class TestGetPredictionStatus:
    """Tests for GET /api/chat/status/{prediction_id}"""

    def test_get_status_pending(
        self,
        client: TestClient,
        test_user_with_balance: User,
        test_prediction_pending: Prediction,
        auth_headers: dict
    ):
        """Test getting status of pending prediction."""
        # Act
        response = client.get(f"/api/chat/status/{test_prediction_pending.id}", headers=auth_headers)

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_prediction_pending.id
        assert data["status"] == "pending"
        assert data["result"] is None

    def test_get_status_completed(
        self,
        client: TestClient,
        test_user_with_balance: User,
        test_prediction_completed: Prediction,
        auth_headers: dict
    ):
        """Test getting status of completed prediction."""
        # Act
        response = client.get(f"/api/chat/status/{test_prediction_completed.id}", headers=auth_headers)

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_prediction_completed.id
        assert data["status"] == "completed"
        assert data["result"] is not None

    def test_get_status_failed(
        self,
        client: TestClient,
        test_user_with_balance: User,
        test_prediction_failed: Prediction,
        auth_headers: dict
    ):
        """Test getting status of failed prediction."""
        # Act
        response = client.get(f"/api/chat/status/{test_prediction_failed.id}", headers=auth_headers)

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_prediction_failed.id
        assert data["status"] == "failed"
        assert data["error_message"] is not None

    def test_get_status_not_found(
        self,
        client: TestClient,
        test_user_with_balance: User,
        auth_headers: dict
    ):
        """Test getting status of non-existent prediction."""
        # Act
        response = client.get("/api/chat/status/nonexistent-id", headers=auth_headers)

        # Assert
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_get_status_other_user_prediction(
        self,
        client: TestClient,
        test_user: User,
        test_prediction_pending: Prediction,
        db_session: Session
    ):
        """Test getting status of another user's prediction (should fail)."""
        # Arrange - create token for different user
        from app.core.security import create_access_token
        token = create_access_token({"sub": test_user.id})
        headers = {"Authorization": f"Bearer {token}"}

        # Act
        response = client.get(f"/api/chat/status/{test_prediction_pending.id}", headers=headers)

        # Assert
        assert response.status_code == 404  # Not found (user can't access other's predictions)

    def test_get_status_unauthorized(self, client: TestClient, test_prediction_pending: Prediction):
        """Test getting status without authentication."""
        # Act
        response = client.get(f"/api/chat/status/{test_prediction_pending.id}")

        # Assert
        assert response.status_code == 403
