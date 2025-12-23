"""
Tests for PredictionService.
"""
import pytest
from decimal import Decimal
from sqlalchemy.orm import Session

from app.services.prediction import PredictionService
from app.models.user import User
from app.models.prediction import Prediction, PredictionStatus


class TestPredictionService:
    """Tests for PredictionService"""

    def test_create_pending(self, db_session: Session, test_user: User):
        """Test creating a pending prediction."""
        # Arrange
        service = PredictionService(db_session)
        message = "What should I eat today?"
        conversation_history = [{"role": "user", "content": "Hello"}]
        cost = Decimal("10.00")

        # Act
        prediction = service.create_pending(
            user_id=test_user.id,
            model_id="mistral",
            message=message,
            conversation_history=conversation_history,
            cost=cost
        )
        db_session.commit()

        # Assert
        assert prediction is not None
        assert prediction.user_id == test_user.id
        assert prediction.model_id == "mistral"
        assert prediction.status == PredictionStatus.PENDING
        assert prediction.cost_charged == cost
        assert prediction.input_data["message"] == message
        assert prediction.input_data["conversation_history"] == conversation_history

        # Verify it was saved to database
        saved_prediction = db_session.query(Prediction).filter(
            Prediction.id == prediction.id
        ).first()
        assert saved_prediction is not None

    def test_create_pending_empty_conversation_history(self, db_session: Session, test_user: User):
        """Test creating prediction with empty conversation history."""
        # Arrange
        service = PredictionService(db_session)

        # Act
        prediction = service.create_pending(
            user_id=test_user.id,
            model_id="mistral",
            message="Test message",
            conversation_history=[],
            cost=Decimal("10.00")
        )
        db_session.commit()

        # Assert
        assert prediction is not None
        assert prediction.input_data["conversation_history"] == []

    def test_get_by_id_existing(self, db_session: Session, test_prediction_pending: Prediction):
        """Test getting prediction by ID when it exists."""
        # Arrange
        service = PredictionService(db_session)

        # Act
        prediction = service.get_by_id(test_prediction_pending.id)

        # Assert
        assert prediction is not None
        assert prediction.id == test_prediction_pending.id

    def test_get_by_id_nonexistent(self, db_session: Session):
        """Test getting prediction by ID when it doesn't exist."""
        # Arrange
        service = PredictionService(db_session)

        # Act
        prediction = service.get_by_id("nonexistent-id")

        # Assert
        assert prediction is None

    def test_get_by_id_and_user_existing(
        self,
        db_session: Session,
        test_user_with_balance: User,
        test_prediction_pending: Prediction
    ):
        """Test getting prediction by ID and user when it exists."""
        # Arrange
        service = PredictionService(db_session)

        # Act
        prediction = service.get_by_id_and_user(
            test_prediction_pending.id,
            test_user_with_balance.id
        )

        # Assert
        assert prediction is not None
        assert prediction.id == test_prediction_pending.id
        assert prediction.user_id == test_user_with_balance.id

    def test_get_by_id_and_user_wrong_user(
        self,
        db_session: Session,
        test_user: User,
        test_prediction_pending: Prediction
    ):
        """Test getting prediction when it belongs to different user."""
        # Arrange
        service = PredictionService(db_session)

        # Act
        prediction = service.get_by_id_and_user(
            test_prediction_pending.id,
            test_user.id  # Different user
        )

        # Assert
        assert prediction is None

    def test_get_by_id_and_user_nonexistent(
        self,
        db_session: Session,
        test_user: User
    ):
        """Test getting prediction by ID and user when it doesn't exist."""
        # Arrange
        service = PredictionService(db_session)

        # Act
        prediction = service.get_by_id_and_user("nonexistent-id", test_user.id)

        # Assert
        assert prediction is None

    def test_create_multiple_predictions(self, db_session: Session, test_user: User):
        """Test creating multiple predictions for same user."""
        # Arrange
        service = PredictionService(db_session)

        # Act
        prediction1 = service.create_pending(
            user_id=test_user.id,
            model_id="mistral",
            message="First message",
            conversation_history=[],
            cost=Decimal("10.00")
        )
        prediction2 = service.create_pending(
            user_id=test_user.id,
            model_id="mistral",
            message="Second message",
            conversation_history=[],
            cost=Decimal("10.00")
        )
        db_session.commit()

        # Assert
        assert prediction1.id != prediction2.id
        predictions = db_session.query(Prediction).filter(
            Prediction.user_id == test_user.id
        ).all()
        assert len(predictions) == 2

    def test_create_pending_with_different_costs(self, db_session: Session, test_user: User):
        """Test creating predictions with different costs."""
        # Arrange
        service = PredictionService(db_session)

        # Act
        prediction1 = service.create_pending(
            user_id=test_user.id,
            model_id="mistral",
            message="Cheap request",
            conversation_history=[],
            cost=Decimal("5.00")
        )
        prediction2 = service.create_pending(
            user_id=test_user.id,
            model_id="gpt-4",
            message="Expensive request",
            conversation_history=[],
            cost=Decimal("50.00")
        )
        db_session.commit()

        # Assert
        assert prediction1.cost_charged == Decimal("5.00")
        assert prediction2.cost_charged == Decimal("50.00")
