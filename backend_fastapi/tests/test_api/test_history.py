"""
Tests for history API endpoints.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from decimal import Decimal

from app.models.user import User
from app.models.prediction import Prediction, PredictionStatus


class TestGetHistory:
    """Tests for GET /api/history"""

    def test_get_history_success(
        self,
        client: TestClient,
        test_user_with_balance: User,
        test_prediction_completed: Prediction,
        auth_headers: dict
    ):
        """Test getting prediction history."""
        # Act
        response = client.get("/api/history/", headers=auth_headers)

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "predictions" in data
        assert len(data["predictions"]) > 0

        # Verify prediction details
        prediction = data["predictions"][0]
        assert "id" in prediction
        assert "status" in prediction
        assert "cost_charged" in prediction
        assert "created_at" in prediction

    def test_get_history_empty(
        self,
        client: TestClient,
        test_user: User,
        auth_headers: dict
    ):
        """Test getting history when there are no predictions."""
        # Act
        response = client.get("/api/history/", headers=auth_headers)

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "predictions" in data
        assert len(data["predictions"]) == 0

    def test_get_history_multiple_predictions(
        self,
        client: TestClient,
        test_user_with_balance: User,
        test_ml_model,
        auth_headers: dict,
        db_session: Session
    ):
        """Test getting multiple predictions ordered by date."""
        # Arrange - create multiple predictions
        for i in range(5):
            prediction = Prediction(
                user_id=test_user_with_balance.id,
                model_id=test_ml_model.id,
                message=f"Test message {i}",
                conversation_history=[],
                cost_charged=Decimal("10.00"),
                status=PredictionStatus.COMPLETED if i % 2 == 0 else PredictionStatus.PENDING
            )
            db_session.add(prediction)
        db_session.commit()

        # Act
        response = client.get("/api/history/", headers=auth_headers)

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert len(data["predictions"]) == 5

        # Verify ordering (most recent first)
        predictions = data["predictions"]
        for i in range(len(predictions) - 1):
            assert predictions[i]["created_at"] >= predictions[i + 1]["created_at"]

    def test_get_history_limit(
        self,
        client: TestClient,
        test_user_with_balance: User,
        test_ml_model,
        auth_headers: dict,
        db_session: Session
    ):
        """Test that history is limited to 50 predictions."""
        # Arrange - create 60 predictions
        for i in range(60):
            prediction = Prediction(
                user_id=test_user_with_balance.id,
                model_id=test_ml_model.id,
                message=f"Test message {i}",
                conversation_history=[],
                cost_charged=Decimal("10.00"),
                status=PredictionStatus.COMPLETED
            )
            db_session.add(prediction)
        db_session.commit()

        # Act
        response = client.get("/api/history/", headers=auth_headers)

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert len(data["predictions"]) == 50  # Limited to 50

    def test_get_history_only_own_predictions(
        self,
        client: TestClient,
        test_user_with_balance: User,
        test_ml_model,
        auth_headers: dict,
        db_session: Session
    ):
        """Test that user only sees their own predictions."""
        # Arrange - create another user with predictions
        other_user = User(
            email="other@example.com",
            username="otheruser",
            hashed_password="hash"
        )
        db_session.add(other_user)
        db_session.commit()

        other_prediction = Prediction(
            user_id=other_user.id,
            model_id=test_ml_model.id,
            message="Other user's prediction",
            conversation_history=[],
            cost_charged=Decimal("10.00"),
            status=PredictionStatus.COMPLETED
        )
        db_session.add(other_prediction)
        db_session.commit()

        # Act
        response = client.get("/api/history/", headers=auth_headers)

        # Assert
        assert response.status_code == 200
        data = response.json()

        # Verify no other user's predictions are returned
        for prediction in data["predictions"]:
            assert prediction.get("input_data") != {"message": "Other user's prediction"}

    def test_get_history_different_statuses(
        self,
        client: TestClient,
        test_user_with_balance: User,
        test_ml_model,
        auth_headers: dict,
        db_session: Session
    ):
        """Test getting predictions with different statuses."""
        # Arrange
        statuses = [PredictionStatus.PENDING, PredictionStatus.COMPLETED, PredictionStatus.FAILED]
        for status in statuses:
            prediction = Prediction(
                user_id=test_user_with_balance.id,
                model_id=test_ml_model.id,
                message=f"Message with status {status.value}",
                conversation_history=[],
                cost_charged=Decimal("10.00"),
                status=status
            )
            db_session.add(prediction)
        db_session.commit()

        # Act
        response = client.get("/api/history/", headers=auth_headers)

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert len(data["predictions"]) >= 3

        # Verify all statuses are represented
        returned_statuses = {p["status"] for p in data["predictions"]}
        assert "pending" in returned_statuses
        assert "completed" in returned_statuses
        assert "failed" in returned_statuses

    def test_get_history_unauthorized(self, client: TestClient):
        """Test getting history without authentication."""
        # Act
        response = client.get("/api/history/")

        # Assert
        assert response.status_code == 403


class TestGetPredictionById:
    """Tests for GET /api/history/{prediction_id}"""

    def test_get_prediction_by_id_success(
        self,
        client: TestClient,
        test_user_with_balance: User,
        test_prediction_completed: Prediction,
        auth_headers: dict
    ):
        """Test getting specific prediction by ID."""
        # Act
        response = client.get(f"/api/history/{test_prediction_completed.id}", headers=auth_headers)

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_prediction_completed.id
        assert data["status"] == "completed"
        assert data["result"] is not None

    def test_get_prediction_by_id_pending(
        self,
        client: TestClient,
        test_user_with_balance: User,
        test_prediction_pending: Prediction,
        auth_headers: dict
    ):
        """Test getting pending prediction by ID."""
        # Act
        response = client.get(f"/api/history/{test_prediction_pending.id}", headers=auth_headers)

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_prediction_pending.id
        assert data["status"] == "pending"
        assert data["result"] is None

    def test_get_prediction_by_id_failed(
        self,
        client: TestClient,
        test_user_with_balance: User,
        test_prediction_failed: Prediction,
        auth_headers: dict
    ):
        """Test getting failed prediction by ID."""
        # Act
        response = client.get(f"/api/history/{test_prediction_failed.id}", headers=auth_headers)

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_prediction_failed.id
        assert data["status"] == "failed"
        assert data["error_message"] is not None

    def test_get_prediction_by_id_not_found(
        self,
        client: TestClient,
        test_user_with_balance: User,
        auth_headers: dict
    ):
        """Test getting non-existent prediction."""
        # Act
        response = client.get("/api/history/nonexistent-id", headers=auth_headers)

        # Assert
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_get_prediction_by_id_other_user(
        self,
        client: TestClient,
        test_user: User,
        test_prediction_completed: Prediction,
        db_session: Session
    ):
        """Test getting another user's prediction (should fail)."""
        # Arrange - create token for different user
        from app.core.security import create_access_token
        token = create_access_token({"sub": test_user.id})
        headers = {"Authorization": f"Bearer {token}"}

        # Act
        response = client.get(f"/api/history/{test_prediction_completed.id}", headers=headers)

        # Assert
        assert response.status_code == 404  # Not found (can't access other's predictions)

    def test_get_prediction_by_id_unauthorized(
        self,
        client: TestClient,
        test_prediction_completed: Prediction
    ):
        """Test getting prediction without authentication."""
        # Act
        response = client.get(f"/api/history/{test_prediction_completed.id}")

        # Assert
        assert response.status_code == 403

    def test_get_prediction_by_id_with_cost(
        self,
        client: TestClient,
        test_user_with_balance: User,
        test_prediction_completed: Prediction,
        auth_headers: dict
    ):
        """Test that prediction includes cost information."""
        # Act
        response = client.get(f"/api/history/{test_prediction_completed.id}", headers=auth_headers)

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "cost_charged" in data
        assert float(data["cost_charged"]) == 10.00
