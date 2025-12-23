"""
Pytest configuration and shared fixtures for testing.
"""
import pytest
from typing import Generator
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from datetime import datetime, timedelta
from decimal import Decimal

from app.main import app
from app.db.base import Base, get_db
from app.core.security import create_access_token, get_password_hash
from app.models.user import User
from app.models.user_balance import UserBalance
from app.models.transaction import Transaction, TransactionType
from app.models.prediction import Prediction, PredictionStatus
from app.models.ml_model import MLModel


# Test database URL - using in-memory SQLite
TEST_DATABASE_URL = "sqlite:///:memory:"


@pytest.fixture(scope="function")
def db_engine():
    """Create a test database engine."""
    engine = create_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture(scope="function")
def db_session(db_engine) -> Generator[Session, None, None]:
    """Create a test database session."""
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=db_engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture(scope="function")
def client(db_session: Session) -> Generator[TestClient, None, None]:
    """Create a test client with overridden database dependency."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def test_user(db_session: Session) -> User:
    """Create a test user."""
    user = User(
        email="test@example.com",
        username="testuser",
        hashed_password=get_password_hash("testpassword123"),
        is_guest=False
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def test_guest_user(db_session: Session) -> User:
    """Create a test guest user."""
    user = User(
        email=f"guest_{datetime.utcnow().timestamp()}@guest.local",
        username=f"guest_{datetime.utcnow().timestamp()}",
        hashed_password=get_password_hash("guest"),
        is_guest=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def test_user_with_balance(db_session: Session, test_user: User) -> User:
    """Create a test user with balance."""
    balance = UserBalance(
        user_id=test_user.id,
        balance=Decimal("1000.00")
    )
    db_session.add(balance)
    db_session.commit()
    return test_user


@pytest.fixture
def test_user_low_balance(db_session: Session) -> User:
    """Create a test user with low balance."""
    user = User(
        email="lowbalance@example.com",
        username="lowbalanceuser",
        hashed_password=get_password_hash("testpassword123"),
        is_guest=False
    )
    db_session.add(user)
    db_session.commit()

    balance = UserBalance(
        user_id=user.id,
        balance=Decimal("5.00")
    )
    db_session.add(balance)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def auth_token(test_user: User) -> str:
    """Create a JWT token for test user."""
    return create_access_token({"sub": test_user.id})


@pytest.fixture
def auth_headers(auth_token: str) -> dict:
    """Create authorization headers with JWT token."""
    return {"Authorization": f"Bearer {auth_token}"}


@pytest.fixture
def guest_token(test_guest_user: User) -> str:
    """Create a JWT token for guest user."""
    return create_access_token({"sub": test_guest_user.id})


@pytest.fixture
def guest_headers(guest_token: str) -> dict:
    """Create authorization headers for guest user."""
    return {"Authorization": f"Bearer {guest_token}"}


@pytest.fixture
def test_ml_model(db_session: Session) -> MLModel:
    """Create a test ML model."""
    model = MLModel(
        name="mistral",
        description="Mistral AI model for testing",
        cost_per_request=Decimal("10.00"),
        is_active=True
    )
    db_session.add(model)
    db_session.commit()
    db_session.refresh(model)
    return model


@pytest.fixture
def test_transaction(db_session: Session, test_user_with_balance: User) -> Transaction:
    """Create a test transaction."""
    transaction = Transaction(
        user_id=test_user_with_balance.id,
        amount=Decimal("100.00"),
        transaction_type=TransactionType.DEPOSIT,
        description="Test deposit"
    )
    db_session.add(transaction)
    db_session.commit()
    db_session.refresh(transaction)
    return transaction


@pytest.fixture
def test_prediction_pending(db_session: Session, test_user_with_balance: User, test_ml_model: MLModel) -> Prediction:
    """Create a pending prediction."""
    prediction = Prediction(
        user_id=test_user_with_balance.id,
        model_id=test_ml_model.id,
        input_data={
            "message": "What should I eat today?",
            "conversation_history": []
        },
        cost_charged=Decimal("10.00"),
        status=PredictionStatus.PENDING
    )
    db_session.add(prediction)
    db_session.commit()
    db_session.refresh(prediction)
    return prediction


@pytest.fixture
def test_prediction_completed(db_session: Session, test_user_with_balance: User, test_ml_model: MLModel) -> Prediction:
    """Create a completed prediction."""
    prediction = Prediction(
        user_id=test_user_with_balance.id,
        model_id=test_ml_model.id,
        input_data={
            "message": "What should I eat today?",
            "conversation_history": [{"role": "user", "content": "What should I eat today?"}]
        },
        result={"response": "You should eat a balanced meal with vegetables and protein."},
        cost_charged=Decimal("10.00"),
        status=PredictionStatus.COMPLETED
    )
    db_session.add(prediction)
    db_session.commit()
    db_session.refresh(prediction)
    return prediction


@pytest.fixture
def test_prediction_failed(db_session: Session, test_user_with_balance: User, test_ml_model: MLModel) -> Prediction:
    """Create a failed prediction."""
    prediction = Prediction(
        user_id=test_user_with_balance.id,
        model_id=test_ml_model.id,
        input_data={
            "message": "Invalid message",
            "conversation_history": []
        },
        error_message="Model timeout",
        cost_charged=Decimal("10.00"),
        status=PredictionStatus.FAILED
    )
    db_session.add(prediction)
    db_session.commit()
    db_session.refresh(prediction)
    return prediction


@pytest.fixture
def mock_ollama_response():
    """Mock Ollama API response."""
    return {
        "model": "mistral",
        "message": {
            "role": "assistant",
            "content": "You should eat a balanced meal with vegetables and protein."
        },
        "done": True
    }
