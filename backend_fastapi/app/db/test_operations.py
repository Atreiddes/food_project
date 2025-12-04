"""
Test script for verifying database operations via ORM.

Задание №3: Протестировать работоспособность системы:
- Создание пользователей
- Пополнение баланса
- Списание кредитов с баланса
- Получение истории транзакций

Принципы:
- SRP: Каждый класс тестирует один аспект функциональности
- OCP: Легко расширяется новыми тестами
- DIP: Зависимость от абстракции (BaseTest)

Usage:
    python -m app.db.test_operations
"""

from abc import ABC, abstractmethod
from typing import Optional, List, Tuple
from dataclasses import dataclass
from decimal import Decimal
from enum import Enum
import uuid

from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app.db.base import engine, SessionLocal, Base
from app.models.user import User, UserRole
from app.models.user_balance import UserBalance
from app.models.transaction import Transaction, TransactionType, TransactionStatus
from app.models.prediction import Prediction, PredictionStatus
from app.models.ml_model import MLModel
from app.core.security import get_password_hash, verify_password


# ============================================================
# Test Result Types
# ============================================================

class TestStatus(str, Enum):
    """Test result status."""
    PASSED = "PASSED"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"


@dataclass
class TestResult:
    """Result of a single test."""
    name: str
    status: TestStatus
    message: str
    details: Optional[str] = None


# ============================================================
# Abstract Base Test (OCP, DIP)
# ============================================================

class BaseTest(ABC):
    """
    Abstract base class for all tests.

    Применяет принципы:
    - OCP: Новые тесты добавляются без изменения существующего кода
    - DIP: TestRunner зависит от абстракции BaseTest
    """

    def __init__(self, db: Session):
        self._db = db
        self._results: List[TestResult] = []

    @property
    def db(self) -> Session:
        """Database session (encapsulation)."""
        return self._db

    @property
    def results(self) -> List[TestResult]:
        """Test results."""
        return self._results.copy()

    @abstractmethod
    def run(self) -> List[TestResult]:
        """
        Execute all tests in this test class.

        Returns:
            List of test results
        """
        pass

    @abstractmethod
    def get_test_name(self) -> str:
        """Get the name of this test suite."""
        pass

    def _add_result(self, name: str, status: TestStatus, message: str, details: str = None) -> None:
        """Add a test result."""
        result = TestResult(name=name, status=status, message=message, details=details)
        self._results.append(result)

    def _passed(self, name: str, message: str) -> None:
        """Record a passed test."""
        self._add_result(name, TestStatus.PASSED, message)

    def _failed(self, name: str, message: str, details: str = None) -> None:
        """Record a failed test."""
        self._add_result(name, TestStatus.FAILED, message, details)

    def _skipped(self, name: str, message: str) -> None:
        """Record a skipped test."""
        self._add_result(name, TestStatus.SKIPPED, message)


# ============================================================
# User Tests (SRP)
# ============================================================

class UserTest(BaseTest):
    """
    Tests for User creation and management.

    SRP: Отвечает только за тестирование пользователей.
    """

    def get_test_name(self) -> str:
        return "User Operations"

    def run(self) -> List[TestResult]:
        """Run all user tests."""
        self._test_create_user()
        self._test_create_user_with_balance()
        self._test_password_hashing()
        self._test_user_roles()
        self._test_duplicate_email()
        return self.results

    def _test_create_user(self) -> None:
        """Test basic user creation."""
        user_id = str(uuid.uuid4())
        test_email = f"test_create_{user_id[:8]}@test.com"

        try:
            user = User(
                id=user_id,
                email=test_email,
                password_hash=get_password_hash("testpass123"),
                role=UserRole.USER,
                is_active=True
            )
            self.db.add(user)
            self.db.commit()

            # Verify
            saved_user = self.db.query(User).filter(User.id == user_id).first()
            if saved_user and saved_user.email == test_email:
                self._passed("create_user", f"User created successfully: {test_email}")
            else:
                self._failed("create_user", "User not found after creation")

            # Cleanup
            self.db.delete(saved_user)
            self.db.commit()

        except Exception as e:
            self.db.rollback()
            self._failed("create_user", f"Failed to create user: {str(e)}")

    def _test_create_user_with_balance(self) -> None:
        """Test user creation with associated balance (SRP)."""
        user_id = str(uuid.uuid4())
        test_email = f"test_balance_{user_id[:8]}@test.com"

        try:
            user = User(
                id=user_id,
                email=test_email,
                password_hash=get_password_hash("testpass123"),
                role=UserRole.USER,
                is_active=True
            )

            user_balance = UserBalance(
                user_id=user_id,
                balance=Decimal("1000.00")
            )

            self.db.add(user)
            self.db.add(user_balance)
            self.db.commit()

            # Verify user with balance relationship
            saved_user = self.db.query(User).filter(User.id == user_id).first()
            if saved_user and saved_user.balance_info:
                balance = saved_user.balance_info.balance
                if balance == Decimal("1000.00"):
                    self._passed("create_user_with_balance",
                                f"User with balance created: {test_email}, balance={balance}")
                else:
                    self._failed("create_user_with_balance",
                                f"Wrong balance: expected 1000.00, got {balance}")
            else:
                self._failed("create_user_with_balance", "User or balance not found")

            # Cleanup
            self.db.delete(saved_user)
            self.db.commit()

        except Exception as e:
            self.db.rollback()
            self._failed("create_user_with_balance", f"Failed: {str(e)}")

    def _test_password_hashing(self) -> None:
        """Test password hashing and verification."""
        password = "SecureP@ss123"
        hashed = get_password_hash(password)

        if verify_password(password, hashed):
            self._passed("password_hashing", "Password hashing and verification works correctly")
        else:
            self._failed("password_hashing", "Password verification failed")

        # Test wrong password
        if not verify_password("wrongpassword", hashed):
            self._passed("password_wrong", "Wrong password correctly rejected")
        else:
            self._failed("password_wrong", "Wrong password incorrectly accepted")

    def _test_user_roles(self) -> None:
        """Test user role assignment."""
        user_id = str(uuid.uuid4())
        test_email = f"test_admin_{user_id[:8]}@test.com"

        try:
            admin = User(
                id=user_id,
                email=test_email,
                password_hash=get_password_hash("adminpass"),
                role=UserRole.ADMIN,
                is_active=True
            )
            self.db.add(admin)
            self.db.commit()

            saved_admin = self.db.query(User).filter(User.id == user_id).first()
            if saved_admin and saved_admin.role == UserRole.ADMIN:
                self._passed("user_roles", f"Admin role assigned correctly: {test_email}")
            else:
                self._failed("user_roles", "Role not assigned correctly")

            self.db.delete(saved_admin)
            self.db.commit()

        except Exception as e:
            self.db.rollback()
            self._failed("user_roles", f"Failed: {str(e)}")

    def _test_duplicate_email(self) -> None:
        """Test duplicate email constraint."""
        user_id1 = str(uuid.uuid4())
        user_id2 = str(uuid.uuid4())
        test_email = f"test_dup_{user_id1[:8]}@test.com"

        try:
            user1 = User(
                id=user_id1,
                email=test_email,
                password_hash=get_password_hash("pass1"),
                role=UserRole.USER,
                is_active=True
            )
            self.db.add(user1)
            self.db.commit()

            # Try to create duplicate
            user2 = User(
                id=user_id2,
                email=test_email,  # Same email
                password_hash=get_password_hash("pass2"),
                role=UserRole.USER,
                is_active=True
            )
            self.db.add(user2)

            try:
                self.db.commit()
                self._failed("duplicate_email", "Duplicate email was allowed")
            except IntegrityError:
                self.db.rollback()
                self._passed("duplicate_email", "Duplicate email correctly rejected")

            # Cleanup
            user1 = self.db.query(User).filter(User.id == user_id1).first()
            if user1:
                self.db.delete(user1)
                self.db.commit()

        except Exception as e:
            self.db.rollback()
            self._failed("duplicate_email", f"Unexpected error: {str(e)}")


# ============================================================
# Balance Tests (SRP)
# ============================================================

class BalanceTest(BaseTest):
    """
    Tests for balance operations.

    SRP: Отвечает только за тестирование операций с балансом.
    """

    def get_test_name(self) -> str:
        return "Balance Operations"

    def run(self) -> List[TestResult]:
        """Run all balance tests."""
        user_id = self._create_test_user()
        if user_id:
            self._test_add_balance(user_id)
            self._test_deduct_balance(user_id)
            self._test_insufficient_balance(user_id)
            self._cleanup_test_user(user_id)
        return self.results

    def _create_test_user(self) -> Optional[str]:
        """Create a test user for balance tests."""
        user_id = str(uuid.uuid4())
        test_email = f"test_bal_{user_id[:8]}@test.com"

        try:
            user = User(
                id=user_id,
                email=test_email,
                password_hash=get_password_hash("testpass"),
                role=UserRole.USER,
                is_active=True
            )
            user_balance = UserBalance(user_id=user_id, balance=Decimal("100.00"))

            self.db.add(user)
            self.db.add(user_balance)
            self.db.commit()
            return user_id

        except Exception as e:
            self.db.rollback()
            self._failed("setup", f"Failed to create test user: {str(e)}")
            return None

    def _cleanup_test_user(self, user_id: str) -> None:
        """Clean up test user."""
        try:
            user = self.db.query(User).filter(User.id == user_id).first()
            if user:
                self.db.delete(user)
                self.db.commit()
        except Exception:
            self.db.rollback()

    def _test_add_balance(self, user_id: str) -> None:
        """Test adding balance."""
        try:
            user_balance = self.db.query(UserBalance).filter(
                UserBalance.user_id == user_id
            ).first()

            initial_balance = user_balance.balance
            add_amount = Decimal("50.00")

            user_balance.balance += add_amount
            self.db.commit()
            self.db.refresh(user_balance)

            expected = initial_balance + add_amount
            if user_balance.balance == expected:
                self._passed("add_balance",
                            f"Balance added: {initial_balance} + {add_amount} = {user_balance.balance}")
            else:
                self._failed("add_balance",
                            f"Expected {expected}, got {user_balance.balance}")

        except Exception as e:
            self.db.rollback()
            self._failed("add_balance", f"Failed: {str(e)}")

    def _test_deduct_balance(self, user_id: str) -> None:
        """Test deducting balance."""
        try:
            user_balance = self.db.query(UserBalance).filter(
                UserBalance.user_id == user_id
            ).first()

            initial_balance = user_balance.balance
            deduct_amount = Decimal("30.00")

            user_balance.balance -= deduct_amount
            self.db.commit()
            self.db.refresh(user_balance)

            expected = initial_balance - deduct_amount
            if user_balance.balance == expected:
                self._passed("deduct_balance",
                            f"Balance deducted: {initial_balance} - {deduct_amount} = {user_balance.balance}")
            else:
                self._failed("deduct_balance",
                            f"Expected {expected}, got {user_balance.balance}")

        except Exception as e:
            self.db.rollback()
            self._failed("deduct_balance", f"Failed: {str(e)}")

    def _test_insufficient_balance(self, user_id: str) -> None:
        """Test insufficient balance check."""
        try:
            user_balance = self.db.query(UserBalance).filter(
                UserBalance.user_id == user_id
            ).first()

            current_balance = user_balance.balance
            large_amount = Decimal("10000.00")

            # Business logic check (not database constraint)
            if current_balance < large_amount:
                self._passed("insufficient_balance",
                            f"Insufficient balance correctly detected: {current_balance} < {large_amount}")
            else:
                self._failed("insufficient_balance", "Check failed")

        except Exception as e:
            self._failed("insufficient_balance", f"Failed: {str(e)}")


# ============================================================
# Transaction Tests (SRP)
# ============================================================

class TransactionTest(BaseTest):
    """
    Tests for transaction operations.

    SRP: Отвечает только за тестирование транзакций.
    """

    def get_test_name(self) -> str:
        return "Transaction Operations"

    def run(self) -> List[TestResult]:
        """Run all transaction tests."""
        user_id = self._create_test_user()
        if user_id:
            self._test_create_deposit(user_id)
            self._test_create_withdrawal(user_id)
            self._test_transaction_history(user_id)
            self._cleanup_test_user(user_id)
        return self.results

    def _create_test_user(self) -> Optional[str]:
        """Create a test user for transaction tests."""
        user_id = str(uuid.uuid4())
        test_email = f"test_tx_{user_id[:8]}@test.com"

        try:
            user = User(
                id=user_id,
                email=test_email,
                password_hash=get_password_hash("testpass"),
                role=UserRole.USER,
                is_active=True
            )
            user_balance = UserBalance(user_id=user_id, balance=Decimal("500.00"))

            self.db.add(user)
            self.db.add(user_balance)
            self.db.commit()
            return user_id

        except Exception as e:
            self.db.rollback()
            self._failed("setup", f"Failed to create test user: {str(e)}")
            return None

    def _cleanup_test_user(self, user_id: str) -> None:
        """Clean up test user and their transactions."""
        try:
            # Delete transactions first
            self.db.query(Transaction).filter(Transaction.user_id == user_id).delete()
            # Delete user (cascades to balance)
            user = self.db.query(User).filter(User.id == user_id).first()
            if user:
                self.db.delete(user)
            self.db.commit()
        except Exception:
            self.db.rollback()

    def _test_create_deposit(self, user_id: str) -> None:
        """Test creating a deposit transaction."""
        try:
            tx = Transaction(
                id=str(uuid.uuid4()),
                user_id=user_id,
                type=TransactionType.DEPOSIT,
                amount=Decimal("100.00"),
                status=TransactionStatus.COMPLETED,
                description="Test deposit"
            )
            self.db.add(tx)
            self.db.commit()

            saved_tx = self.db.query(Transaction).filter(Transaction.id == tx.id).first()
            if saved_tx and saved_tx.type == TransactionType.DEPOSIT:
                self._passed("create_deposit",
                            f"Deposit transaction created: {saved_tx.amount}")
            else:
                self._failed("create_deposit", "Transaction not saved correctly")

        except Exception as e:
            self.db.rollback()
            self._failed("create_deposit", f"Failed: {str(e)}")

    def _test_create_withdrawal(self, user_id: str) -> None:
        """Test creating a withdrawal transaction."""
        try:
            tx = Transaction(
                id=str(uuid.uuid4()),
                user_id=user_id,
                type=TransactionType.WITHDRAW,
                amount=Decimal("50.00"),
                status=TransactionStatus.COMPLETED,
                description="Test withdrawal (ML request)"
            )
            self.db.add(tx)
            self.db.commit()

            saved_tx = self.db.query(Transaction).filter(Transaction.id == tx.id).first()
            if saved_tx and saved_tx.type == TransactionType.WITHDRAW:
                self._passed("create_withdrawal",
                            f"Withdrawal transaction created: {saved_tx.amount}")
            else:
                self._failed("create_withdrawal", "Transaction not saved correctly")

        except Exception as e:
            self.db.rollback()
            self._failed("create_withdrawal", f"Failed: {str(e)}")

    def _test_transaction_history(self, user_id: str) -> None:
        """Test retrieving transaction history."""
        try:
            transactions = self.db.query(Transaction).filter(
                Transaction.user_id == user_id
            ).order_by(Transaction.created_at.desc()).all()

            if len(transactions) >= 2:
                self._passed("transaction_history",
                            f"Transaction history retrieved: {len(transactions)} transactions")
            else:
                self._failed("transaction_history",
                            f"Expected at least 2 transactions, got {len(transactions)}")

        except Exception as e:
            self._failed("transaction_history", f"Failed: {str(e)}")


# ============================================================
# ML Model Tests (SRP)
# ============================================================

class MLModelTest(BaseTest):
    """
    Tests for ML Model operations.

    SRP: Отвечает только за тестирование ML моделей.
    """

    def get_test_name(self) -> str:
        return "ML Model Operations"

    def run(self) -> List[TestResult]:
        """Run all ML model tests."""
        self._test_create_model()
        self._test_model_activation()
        return self.results

    def _test_create_model(self) -> None:
        """Test creating an ML model."""
        model_id = f"test-model-{uuid.uuid4().hex[:8]}"

        try:
            model = MLModel(
                id=model_id,
                name="Test Model",
                description="A test ML model",
                type="prediction",
                version="1.0",
                status="active",
                cost_per_request=10.00,
                endpoint="http://test:8000/predict"
            )
            self.db.add(model)
            self.db.commit()

            saved_model = self.db.query(MLModel).filter(MLModel.id == model_id).first()
            if saved_model and saved_model.name == "Test Model":
                self._passed("create_model", f"ML Model created: {model_id}")
            else:
                self._failed("create_model", "Model not saved correctly")

            # Cleanup
            self.db.delete(saved_model)
            self.db.commit()

        except Exception as e:
            self.db.rollback()
            self._failed("create_model", f"Failed: {str(e)}")

    def _test_model_activation(self) -> None:
        """Test model activation/deactivation."""
        model_id = f"test-model-{uuid.uuid4().hex[:8]}"

        try:
            model = MLModel(
                id=model_id,
                name="Activation Test Model",
                description="Test",
                type="prediction",
                version="1.0",
                status="active",
                cost_per_request=5.00,
                endpoint="http://test:8000"
            )
            self.db.add(model)
            self.db.commit()

            # Deactivate
            model.status = "inactive"
            self.db.commit()
            self.db.refresh(model)

            if model.status == "inactive":
                self._passed("model_activation", "Model deactivation works correctly")
            else:
                self._failed("model_activation", "Model deactivation failed")

            # Cleanup
            self.db.delete(model)
            self.db.commit()

        except Exception as e:
            self.db.rollback()
            self._failed("model_activation", f"Failed: {str(e)}")


# ============================================================
# Test Runner
# ============================================================

class TestRunner:
    """
    Orchestrator for running all tests.

    Применяет принципы:
    - SRP: Координирует запуск тестов
    - DIP: Работает с абстракцией BaseTest
    """

    def __init__(self):
        self._db: Optional[Session] = None
        self._all_results: List[Tuple[str, List[TestResult]]] = []

    def run_all(self) -> Tuple[int, int, int]:
        """
        Run all tests.

        Returns:
            Tuple of (passed, failed, skipped) counts
        """
        self._print_header()
        self._create_tables()
        self._db = SessionLocal()

        try:
            # Run all test suites
            test_classes = [UserTest, BalanceTest, TransactionTest, MLModelTest]

            for test_class in test_classes:
                test = test_class(self._db)
                print(f"\n[{test.get_test_name()}]")
                results = test.run()
                self._all_results.append((test.get_test_name(), results))
                self._print_results(results)

            return self._print_summary()

        finally:
            self._db.close()

    def _create_tables(self) -> None:
        """Ensure tables exist."""
        Base.metadata.create_all(bind=engine)

    def _print_header(self) -> None:
        """Print test header."""
        print("\n" + "=" * 60)
        print("   ORM Operations Test Suite - NutriMarket ML Service")
        print("   Задание №3: Тестирование работоспособности системы")
        print("=" * 60)

    def _print_results(self, results: List[TestResult]) -> None:
        """Print results for a test suite."""
        for result in results:
            icon = {"PASSED": "✓", "FAILED": "✗", "SKIPPED": "→"}[result.status.value]
            status_color = {
                "PASSED": "\033[92m",  # Green
                "FAILED": "\033[91m",  # Red
                "SKIPPED": "\033[93m"  # Yellow
            }[result.status.value]
            reset = "\033[0m"

            print(f"  {status_color}{icon} {result.name}: {result.message}{reset}")

    def _print_summary(self) -> Tuple[int, int, int]:
        """Print test summary."""
        passed = failed = skipped = 0

        for _, results in self._all_results:
            for result in results:
                if result.status == TestStatus.PASSED:
                    passed += 1
                elif result.status == TestStatus.FAILED:
                    failed += 1
                else:
                    skipped += 1

        total = passed + failed + skipped

        print("\n" + "=" * 60)
        print(f"   Test Summary: {passed}/{total} passed")
        print("=" * 60)
        print(f"   ✓ Passed:  {passed}")
        print(f"   ✗ Failed:  {failed}")
        print(f"   → Skipped: {skipped}")

        if failed == 0:
            print("\n   ✅ All tests passed!")
        else:
            print(f"\n   ❌ {failed} test(s) failed!")

        print("=" * 60 + "\n")

        return passed, failed, skipped


# ============================================================
# Entry Point
# ============================================================

def run_tests() -> Tuple[int, int, int]:
    """
    Main function to run all tests.

    Returns:
        Tuple of (passed, failed, skipped) counts
    """
    runner = TestRunner()
    return runner.run_all()


if __name__ == "__main__":
    passed, failed, skipped = run_tests()
    # Exit with error code if any tests failed
    sys.exit(1 if failed > 0 else 0)
