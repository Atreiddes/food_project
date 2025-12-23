"""
Tests for worker handlers.
"""
import pytest
from decimal import Decimal
from sqlalchemy.orm import Session

from app.workers.handlers import PredictionResultHandler, PredictionStatusUpdater
from app.workers.base import WorkerResult
from app.models.user import User
from app.models.prediction import Prediction, PredictionStatus
from app.models.user_balance import UserBalance
from app.models.transaction import Transaction, TransactionType


class TestPredictionResultHandler:
    """Tests for PredictionResultHandler"""

    def test_handle_successful_result(
        self,
        db_session: Session,
        test_prediction_pending: Prediction
    ):
        """Test handling successful prediction result."""
        # Arrange
        handler = PredictionResultHandler()
        result = WorkerResult(
            prediction_id=test_prediction_pending.id,
            success=True,
            response="You should eat a balanced meal.",
            processing_time_ms=1500,
            error=None
        )

        # Act
        success = handler.handle(result, db_session)

        # Assert
        assert success is True

        # Verify prediction was updated
        db_session.refresh(test_prediction_pending)
        assert test_prediction_pending.status == PredictionStatus.COMPLETED
        assert test_prediction_pending.result is not None
        assert "response" in test_prediction_pending.result
        assert test_prediction_pending.error_message is None

    def test_handle_failed_result_with_refund(
        self,
        db_session: Session,
        test_user_with_balance: User,
        test_prediction_pending: Prediction
    ):
        """Test handling failed prediction result with automatic refund."""
        # Arrange
        handler = PredictionResultHandler()

        # Get initial balance
        initial_balance = db_session.query(UserBalance).filter(
            UserBalance.user_id == test_user_with_balance.id
        ).first().balance

        result = WorkerResult(
            prediction_id=test_prediction_pending.id,
            success=False,
            response=None,
            processing_time_ms=0,
            error="Model timeout"
        )

        # Act
        success = handler.handle(result, db_session)

        # Assert
        assert success is True

        # Verify prediction was marked as failed
        db_session.refresh(test_prediction_pending)
        assert test_prediction_pending.status == PredictionStatus.FAILED
        assert test_prediction_pending.error_message == "Model timeout"

        # Verify refund was issued
        balance = db_session.query(UserBalance).filter(
            UserBalance.user_id == test_user_with_balance.id
        ).first()
        expected_balance = initial_balance + test_prediction_pending.cost_charged
        assert balance.balance == expected_balance

        # Verify refund transaction was created
        refund_transaction = db_session.query(Transaction).filter(
            Transaction.user_id == test_user_with_balance.id,
            Transaction.type == TransactionType.REFUND
        ).first()
        assert refund_transaction is not None
        assert refund_transaction.amount == test_prediction_pending.cost_charged

    def test_handle_nonexistent_prediction(self, db_session: Session):
        """Test handling result for non-existent prediction."""
        # Arrange
        handler = PredictionResultHandler()
        result = WorkerResult(
            prediction_id="nonexistent-id",
            success=True,
            response="Test response",
            processing_time_ms=1000,
            error=None
        )

        # Act
        success = handler.handle(result, db_session)

        # Assert
        assert success is False

    def test_refund_with_zero_cost(
        self,
        db_session: Session,
        test_user_with_balance: User,
        test_ml_model
    ):
        """Test that refund doesn't happen for zero cost."""
        # Arrange
        handler = PredictionResultHandler()

        # Create prediction with zero cost
        prediction = Prediction(
            user_id=test_user_with_balance.id,
            model_id=test_ml_model.id,
            input_data={
                "message": "Free message",
                "conversation_history": []
            },
            cost_charged=Decimal("0.00"),
            status=PredictionStatus.PENDING
        )
        db_session.add(prediction)
        db_session.commit()

        initial_balance = db_session.query(UserBalance).filter(
            UserBalance.user_id == test_user_with_balance.id
        ).first().balance

        result = WorkerResult(
            prediction_id=prediction.id,
            success=False,
            response=None,
            processing_time_ms=0,
            error="Error"
        )

        # Act
        success = handler.handle(result, db_session)

        # Assert
        assert success is True

        # Verify no refund transaction was created
        refund_count = db_session.query(Transaction).filter(
            Transaction.user_id == test_user_with_balance.id,
            Transaction.type == TransactionType.REFUND
        ).count()
        assert refund_count == 0

        # Verify balance didn't change
        balance = db_session.query(UserBalance).filter(
            UserBalance.user_id == test_user_with_balance.id
        ).first()
        assert balance.balance == initial_balance

    def test_handle_success_no_refund(
        self,
        db_session: Session,
        test_user_with_balance: User,
        test_prediction_pending: Prediction
    ):
        """Test that successful result doesn't trigger refund."""
        # Arrange
        handler = PredictionResultHandler()

        initial_balance = db_session.query(UserBalance).filter(
            UserBalance.user_id == test_user_with_balance.id
        ).first().balance

        result = WorkerResult(
            prediction_id=test_prediction_pending.id,
            success=True,
            response="Success response",
            processing_time_ms=1000,
            error=None
        )

        # Act
        success = handler.handle(result, db_session)

        # Assert
        assert success is True

        # Verify no refund transaction was created
        refund_count = db_session.query(Transaction).filter(
            Transaction.user_id == test_user_with_balance.id,
            Transaction.type == TransactionType.REFUND
        ).count()
        assert refund_count == 0

        # Verify balance didn't change
        balance = db_session.query(UserBalance).filter(
            UserBalance.user_id == test_user_with_balance.id
        ).first()
        assert balance.balance == initial_balance


class TestPredictionStatusUpdater:
    """Tests for PredictionStatusUpdater"""

    def test_mark_processing(
        self,
        db_session: Session,
        test_prediction_pending: Prediction
    ):
        """Test marking prediction as processing."""
        # Arrange
        updater = PredictionStatusUpdater(db_session)

        # Act
        success = updater.mark_processing(test_prediction_pending.id)

        # Assert
        assert success is True
        db_session.refresh(test_prediction_pending)
        assert test_prediction_pending.status == PredictionStatus.PROCESSING

    def test_mark_processing_nonexistent(self, db_session: Session):
        """Test marking non-existent prediction as processing."""
        # Arrange
        updater = PredictionStatusUpdater(db_session)

        # Act
        success = updater.mark_processing("nonexistent-id")

        # Assert
        assert success is False

    def test_mark_failed(
        self,
        db_session: Session,
        test_prediction_pending: Prediction
    ):
        """Test marking prediction as failed."""
        # Arrange
        updater = PredictionStatusUpdater(db_session)
        error_message = "Connection timeout"

        # Act
        success = updater.mark_failed(test_prediction_pending.id, error_message)

        # Assert
        assert success is True
        db_session.refresh(test_prediction_pending)
        assert test_prediction_pending.status == PredictionStatus.FAILED
        assert test_prediction_pending.error_message == error_message

    def test_mark_failed_nonexistent(self, db_session: Session):
        """Test marking non-existent prediction as failed."""
        # Arrange
        updater = PredictionStatusUpdater(db_session)

        # Act
        success = updater.mark_failed("nonexistent-id", "Error")

        # Assert
        assert success is False

    def test_status_transitions(
        self,
        db_session: Session,
        test_prediction_pending: Prediction
    ):
        """Test multiple status transitions."""
        # Arrange
        updater = PredictionStatusUpdater(db_session)

        # Act & Assert - Pending -> Processing
        assert test_prediction_pending.status == PredictionStatus.PENDING

        success = updater.mark_processing(test_prediction_pending.id)
        assert success is True
        db_session.refresh(test_prediction_pending)
        assert test_prediction_pending.status == PredictionStatus.PROCESSING

        # Act & Assert - Processing -> Failed
        success = updater.mark_failed(test_prediction_pending.id, "Error occurred")
        assert success is True
        db_session.refresh(test_prediction_pending)
        assert test_prediction_pending.status == PredictionStatus.FAILED
        assert test_prediction_pending.error_message == "Error occurred"
