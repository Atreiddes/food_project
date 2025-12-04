"""
Seed script for database initialization with demo data.

Задание №3: Подготовить сценарий инициализации базы данных стандартными данными:
- Демо пользователь
- Демо администратор
- Базовые модели доступные для работы

Принципы:
- SRP: Каждый класс отвечает за создание своего типа данных
- OCP: Легко расширяется новыми Seeder классами
- DIP: Зависимость от абстракции (BaseSeeder)

Usage:
    python -m app.db.seed
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import uuid

from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app.db.base import engine, SessionLocal, Base
from app.models.user import User, UserRole
from app.models.user_balance import UserBalance
from app.models.transaction import Transaction, TransactionType, TransactionStatus
from app.models.ml_model import MLModel
from app.core.security import get_password_hash


# ============================================================
# Data Transfer Objects (DTOs)
# ============================================================

@dataclass
class UserSeedData:
    """DTO for user seed data."""
    email: str
    password: str
    role: UserRole
    balance: float
    is_active: bool = True


@dataclass
class MLModelSeedData:
    """DTO for ML model seed data."""
    id: str
    name: str
    description: str
    model_type: str
    version: str
    cost_per_request: float
    endpoint: str
    status: str = "active"


@dataclass
class TransactionSeedData:
    """DTO for transaction seed data."""
    type: TransactionType
    amount: float
    status: TransactionStatus
    description: str


# ============================================================
# Abstract Base Seeder (OCP, DIP)
# ============================================================

class BaseSeeder(ABC):
    """
    Abstract base class for all seeders.

    Применяет принципы:
    - OCP: Новые seeders добавляются без изменения существующего кода
    - DIP: DatabaseSeeder зависит от абстракции BaseSeeder
    """

    def __init__(self, db: Session):
        self._db = db
        self._created_items: List[str] = []

    @property
    def db(self) -> Session:
        """Database session (encapsulation)."""
        return self._db

    @property
    def created_items(self) -> List[str]:
        """List of created item IDs."""
        return self._created_items.copy()

    @abstractmethod
    def seed(self) -> List[str]:
        """
        Execute seeding logic.

        Returns:
            List of created item IDs
        """
        pass

    @abstractmethod
    def get_seed_data(self) -> List[Any]:
        """
        Get data to seed.

        Returns:
            List of seed data objects
        """
        pass

    def _log_created(self, message: str) -> None:
        """Log successful creation."""
        print(f"  ✓ {message}")

    def _log_skipped(self, message: str) -> None:
        """Log skipped item."""
        print(f"  → {message}")

    def _log_error(self, message: str) -> None:
        """Log error."""
        print(f"  ✗ {message}")


# ============================================================
# Concrete Seeders (SRP - each handles one entity type)
# ============================================================

class UserSeeder(BaseSeeder):
    """
    Seeder for User and UserBalance entities.

    SRP: Отвечает только за создание пользователей и их балансов.
    """

    def get_seed_data(self) -> List[UserSeedData]:
        """Get demo users to create."""
        return [
            UserSeedData(
                email="demo@nutrimarket.com",
                password="demo123456",
                role=UserRole.USER,
                balance=1000.00
            ),
            UserSeedData(
                email="admin@nutrimarket.com",
                password="admin123456",
                role=UserRole.ADMIN,
                balance=10000.00
            ),
            UserSeedData(
                email="test@nutrimarket.com",
                password="test123456",
                role=UserRole.USER,
                balance=500.00
            )
        ]

    def seed(self) -> List[str]:
        """Create demo users with their balances."""
        for user_data in self.get_seed_data():
            user_id = self._create_user(user_data)
            if user_id:
                self._created_items.append(user_id)

        return self.created_items

    def _create_user(self, data: UserSeedData) -> Optional[str]:
        """
        Create a single user with balance.

        Args:
            data: User seed data

        Returns:
            User ID if created, None if skipped
        """
        user_id = str(uuid.uuid4())

        user = User(
            id=user_id,
            email=data.email,
            password_hash=get_password_hash(data.password),
            role=data.role,
            is_active=data.is_active
        )

        user_balance = UserBalance(
            user_id=user_id,
            balance=data.balance
        )

        try:
            self.db.add(user)
            self.db.add(user_balance)
            self.db.commit()

            role_str = "admin" if data.role == UserRole.ADMIN else "user"
            self._log_created(f"User ({role_str}): {data.email} / {data.password}")
            return user_id

        except IntegrityError:
            self.db.rollback()
            self._log_skipped(f"User '{data.email}' already exists")
            return None


class MLModelSeeder(BaseSeeder):
    """
    Seeder for ML Model entities.

    SRP: Отвечает только за создание ML моделей.
    """

    def get_seed_data(self) -> List[MLModelSeedData]:
        """Get ML models to create."""
        return [
            MLModelSeedData(
                id="mistral",
                name="Mistral Model",
                description="Модель для рекомендаций по питанию и планирования рациона",
                model_type="chat",
                version="1.0",
                cost_per_request=10.00,
                endpoint="http://ollama:11434/api/generate",
                status="active"
            ),
            MLModelSeedData(
                id="nutrition-predictor",
                name="Nutrition Predictor",
                description="Predicts nutritional values based on ingredients list",
                model_type="prediction",
                version="1.0",
                cost_per_request=5.00,
                endpoint="http://ollama:11434/api/generate",
                status="active"
            ),
            MLModelSeedData(
                id="meal-optimizer",
                name="Meal Plan Optimizer",
                description="Optimizes weekly meal plans based on dietary goals",
                model_type="optimization",
                version="1.0",
                cost_per_request=15.00,
                endpoint="http://ollama:11434/api/generate",
                status="active"
            ),
            MLModelSeedData(
                id="ingredient-substitute",
                name="Ingredient Substitution",
                description="Suggests healthy ingredient alternatives",
                model_type="recommendation",
                version="1.0",
                cost_per_request=3.00,
                endpoint="http://ollama:11434/api/generate",
                status="inactive"
            )
        ]

    def seed(self) -> List[str]:
        """Create ML models."""
        for model_data in self.get_seed_data():
            model_id = self._create_model(model_data)
            if model_id:
                self._created_items.append(model_id)

        return self.created_items

    def _create_model(self, data: MLModelSeedData) -> Optional[str]:
        """
        Create a single ML model.

        Args:
            data: ML model seed data

        Returns:
            Model ID if created, None if skipped
        """
        ml_model = MLModel(
            id=data.id,
            name=data.name,
            description=data.description,
            type=data.model_type,
            version=data.version,
            status=data.status,
            cost_per_request=data.cost_per_request,
            endpoint=data.endpoint
        )

        try:
            self.db.add(ml_model)
            self.db.commit()

            self._log_created(f"ML Model: {data.name} [{data.status}]")
            return data.id

        except IntegrityError:
            self.db.rollback()
            self._log_skipped(f"ML Model '{data.name}' already exists")
            return None


class TransactionSeeder(BaseSeeder):
    """
    Seeder for Transaction entities.

    SRP: Отвечает только за создание транзакций.
    """

    def __init__(self, db: Session, user_id: Optional[str] = None):
        super().__init__(db)
        self._user_id = user_id

    def get_seed_data(self) -> List[TransactionSeedData]:
        """Get demo transactions to create."""
        return [
            TransactionSeedData(
                type=TransactionType.DEPOSIT,
                amount=500.00,
                status=TransactionStatus.COMPLETED,
                description="Initial deposit"
            ),
            TransactionSeedData(
                type=TransactionType.DEPOSIT,
                amount=500.00,
                status=TransactionStatus.COMPLETED,
                description="Bonus credits"
            ),
            TransactionSeedData(
                type=TransactionType.WITHDRAW,
                amount=10.00,
                status=TransactionStatus.COMPLETED,
                description="ML prediction: Nutrition analysis"
            ),
            TransactionSeedData(
                type=TransactionType.WITHDRAW,
                amount=10.00,
                status=TransactionStatus.COMPLETED,
                description="ML prediction: Meal planning"
            )
        ]

    def seed(self) -> List[str]:
        """Create demo transactions."""
        if not self._user_id:
            self._log_skipped("No user ID provided for transactions")
            return []

        for tx_data in self.get_seed_data():
            tx_id = self._create_transaction(tx_data)
            if tx_id:
                self._created_items.append(tx_id)

        if self._created_items:
            self._log_created(f"Created {len(self._created_items)} demo transactions")

        return self.created_items

    def _create_transaction(self, data: TransactionSeedData) -> Optional[str]:
        """
        Create a single transaction.

        Args:
            data: Transaction seed data

        Returns:
            Transaction ID if created, None if failed
        """
        transaction = Transaction(
            id=str(uuid.uuid4()),
            user_id=self._user_id,
            type=data.type,
            amount=data.amount,
            status=data.status,
            description=data.description
        )

        try:
            self.db.add(transaction)
            self.db.commit()
            return transaction.id

        except IntegrityError:
            self.db.rollback()
            return None


# ============================================================
# Database Seeder Orchestrator
# ============================================================

class DatabaseSeeder:
    """
    Orchestrator for database seeding.

    Применяет принципы:
    - SRP: Координирует процесс seeding, не занимается созданием данных
    - DIP: Работает с абстракцией BaseSeeder
    - OCP: Новые seeders добавляются через register_seeder()
    """

    def __init__(self):
        self._db: Optional[Session] = None
        self._results: Dict[str, List[str]] = {}

    def seed(self) -> Dict[str, List[str]]:
        """
        Execute full database seeding.

        Returns:
            Dictionary with seeder names and created item IDs
        """
        self._print_header()
        self._create_tables()
        self._db = SessionLocal()

        try:
            # Seed users
            print("\n[Users]")
            user_seeder = UserSeeder(self._db)
            user_ids = user_seeder.seed()
            self._results['users'] = user_ids

            # Seed ML models
            print("\n[ML Models]")
            model_seeder = MLModelSeeder(self._db)
            model_ids = model_seeder.seed()
            self._results['ml_models'] = model_ids

            # Seed transactions (for first user)
            print("\n[Transactions]")
            first_user_id = user_ids[0] if user_ids else None
            tx_seeder = TransactionSeeder(self._db, first_user_id)
            tx_ids = tx_seeder.seed()
            self._results['transactions'] = tx_ids

            self._print_summary()
            return self._results

        except Exception as e:
            self._db.rollback()
            print(f"\n✗ Error during seeding: {e}")
            raise

        finally:
            self._db.close()

    def _create_tables(self) -> None:
        """Create all database tables."""
        print("\n[Database Tables]")
        Base.metadata.create_all(bind=engine)
        print("  ✓ Tables created/verified successfully")

    def _print_header(self) -> None:
        """Print script header."""
        print("\n" + "=" * 55)
        print("   Database Seed Script - NutriMarket ML Service")
        print("   Задание №3: Инициализация демо-данных")
        print("=" * 55)

    def _print_summary(self) -> None:
        """Print seeding summary."""
        print("\n" + "=" * 55)
        print("   Seed completed successfully!")
        print("=" * 55)
        print("\n  Demo credentials:")
        print("    User:  demo@nutrimarket.com / demo123456")
        print("    Admin: admin@nutrimarket.com / admin123456")
        print("    Test:  test@nutrimarket.com / test123456")
        print("\n  Available ML models:")
        for model_id in self._results.get('ml_models', []):
            print(f"    - {model_id}")
        print("\n" + "=" * 55 + "\n")


# ============================================================
# Entry Point
# ============================================================

def seed_database() -> Dict[str, List[str]]:
    """
    Main function to seed the database.

    Returns:
        Dictionary with seeding results
    """
    seeder = DatabaseSeeder()
    return seeder.seed()


if __name__ == "__main__":
    seed_database()
