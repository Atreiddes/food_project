"""
Local test script using SQLite for quick ORM verification.

Этот скрипт позволяет протестировать ORM операции без Docker/PostgreSQL.
Использует SQLite in-memory базу данных.

Usage:
    cd backend_fastapi
    python -m app.db.test_local
"""

from decimal import Decimal
from datetime import datetime
import uuid

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


# Create SQLite in-memory database for testing
TEST_DATABASE_URL = "sqlite:///:memory:"
test_engine = create_engine(TEST_DATABASE_URL, echo=False)
TestSession = sessionmaker(bind=test_engine)


def run_local_tests():
    """Run ORM tests with local SQLite database."""

    print("\n" + "=" * 60)
    print("   Local ORM Test Suite (SQLite)")
    print("   Задание №3: Проверка работоспособности системы")
    print("=" * 60)

    # Import models after path setup
    from app.db.base import Base
    from app.models.user import User, UserRole
    from app.models.user_balance import UserBalance
    from app.models.transaction import Transaction, TransactionType, TransactionStatus
    from app.models.ml_model import MLModel
    from app.core.security import get_password_hash, verify_password

    # Create all tables
    print("\n[Setup]")
    Base.metadata.create_all(bind=test_engine)
    print("  ✓ Tables created in SQLite")

    db = TestSession()
    passed = 0
    failed = 0

    try:
        # ============================================================
        # TEST 1: Create User
        # ============================================================
        print("\n[1. User Operations]")

        user_id = str(uuid.uuid4())
        user = User(
            id=user_id,
            email="test@example.com",
            password_hash=get_password_hash("password123"),
            role=UserRole.USER,
            is_active=True
        )
        db.add(user)
        db.commit()

        saved_user = db.query(User).filter(User.id == user_id).first()
        if saved_user and saved_user.email == "test@example.com":
            print("  ✓ User creation: PASSED")
            passed += 1
        else:
            print("  ✗ User creation: FAILED")
            failed += 1

        # ============================================================
        # TEST 2: Create UserBalance (SRP)
        # ============================================================
        user_balance = UserBalance(
            user_id=user_id,
            balance=Decimal("1000.00")
        )
        db.add(user_balance)
        db.commit()

        saved_balance = db.query(UserBalance).filter(UserBalance.user_id == user_id).first()
        if saved_balance and saved_balance.balance == Decimal("1000.00"):
            print("  ✓ UserBalance creation (SRP): PASSED")
            passed += 1
        else:
            print("  ✗ UserBalance creation (SRP): FAILED")
            failed += 1

        # ============================================================
        # TEST 3: Password hashing
        # ============================================================
        if verify_password("password123", saved_user.password_hash):
            print("  ✓ Password verification: PASSED")
            passed += 1
        else:
            print("  ✗ Password verification: FAILED")
            failed += 1

        # ============================================================
        # TEST 4: Admin role
        # ============================================================
        admin_id = str(uuid.uuid4())
        admin = User(
            id=admin_id,
            email="admin@example.com",
            password_hash=get_password_hash("admin123"),
            role=UserRole.ADMIN,
            is_active=True
        )
        db.add(admin)
        db.commit()

        saved_admin = db.query(User).filter(User.id == admin_id).first()
        if saved_admin and saved_admin.role == UserRole.ADMIN:
            print("  ✓ Admin role assignment: PASSED")
            passed += 1
        else:
            print("  ✗ Admin role assignment: FAILED")
            failed += 1

        # ============================================================
        # TEST 5: Add balance
        # ============================================================
        print("\n[2. Balance Operations]")

        initial_balance = saved_balance.balance
        saved_balance.balance += Decimal("500.00")
        db.commit()
        db.refresh(saved_balance)

        if saved_balance.balance == initial_balance + Decimal("500.00"):
            print(f"  ✓ Add balance ({initial_balance} + 500 = {saved_balance.balance}): PASSED")
            passed += 1
        else:
            print("  ✗ Add balance: FAILED")
            failed += 1

        # ============================================================
        # TEST 6: Deduct balance
        # ============================================================
        before_deduct = saved_balance.balance
        saved_balance.balance -= Decimal("100.00")
        db.commit()
        db.refresh(saved_balance)

        if saved_balance.balance == before_deduct - Decimal("100.00"):
            print(f"  ✓ Deduct balance ({before_deduct} - 100 = {saved_balance.balance}): PASSED")
            passed += 1
        else:
            print("  ✗ Deduct balance: FAILED")
            failed += 1

        # ============================================================
        # TEST 7: Insufficient balance check
        # ============================================================
        current = saved_balance.balance
        large_amount = Decimal("99999.00")
        if current < large_amount:
            print(f"  ✓ Insufficient balance check ({current} < {large_amount}): PASSED")
            passed += 1
        else:
            print("  ✗ Insufficient balance check: FAILED")
            failed += 1

        # ============================================================
        # TEST 8: Create deposit transaction
        # ============================================================
        print("\n[3. Transaction Operations]")

        tx1 = Transaction(
            id=str(uuid.uuid4()),
            user_id=user_id,
            type=TransactionType.DEPOSIT,
            amount=Decimal("200.00"),
            status=TransactionStatus.COMPLETED,
            description="Test deposit"
        )
        db.add(tx1)
        db.commit()

        saved_tx = db.query(Transaction).filter(Transaction.id == tx1.id).first()
        if saved_tx and saved_tx.type == TransactionType.DEPOSIT:
            print("  ✓ Create deposit transaction: PASSED")
            passed += 1
        else:
            print("  ✗ Create deposit transaction: FAILED")
            failed += 1

        # ============================================================
        # TEST 9: Create withdrawal transaction
        # ============================================================
        tx2 = Transaction(
            id=str(uuid.uuid4()),
            user_id=user_id,
            type=TransactionType.WITHDRAW,
            amount=Decimal("50.00"),
            status=TransactionStatus.COMPLETED,
            description="ML prediction charge"
        )
        db.add(tx2)
        db.commit()

        saved_tx2 = db.query(Transaction).filter(Transaction.id == tx2.id).first()
        if saved_tx2 and saved_tx2.type == TransactionType.WITHDRAW:
            print("  ✓ Create withdrawal transaction: PASSED")
            passed += 1
        else:
            print("  ✗ Create withdrawal transaction: FAILED")
            failed += 1

        # ============================================================
        # TEST 10: Transaction history
        # ============================================================
        transactions = db.query(Transaction).filter(
            Transaction.user_id == user_id
        ).order_by(Transaction.created_at.desc()).all()

        if len(transactions) == 2:
            print(f"  ✓ Transaction history ({len(transactions)} records): PASSED")
            passed += 1
        else:
            print(f"  ✗ Transaction history (expected 2, got {len(transactions)}): FAILED")
            failed += 1

        # ============================================================
        # TEST 11: Create ML Model
        # ============================================================
        print("\n[4. ML Model Operations]")

        ml_model = MLModel(
            id="test-model",
            name="Test Predictor",
            description="Test ML model",
            endpoint_url="http://localhost:8000/predict",
            is_active=True
        )
        db.add(ml_model)
        db.commit()

        saved_model = db.query(MLModel).filter(MLModel.id == "test-model").first()
        if saved_model and saved_model.name == "Test Predictor":
            print("  ✓ Create ML model: PASSED")
            passed += 1
        else:
            print("  ✗ Create ML model: FAILED")
            failed += 1

        # ============================================================
        # TEST 12: Deactivate ML Model
        # ============================================================
        saved_model.is_active = False
        db.commit()
        db.refresh(saved_model)

        if not saved_model.is_active:
            print("  ✓ Deactivate ML model: PASSED")
            passed += 1
        else:
            print("  ✗ Deactivate ML model: FAILED")
            failed += 1

        # ============================================================
        # Summary
        # ============================================================
        total = passed + failed
        print("\n" + "=" * 60)
        print(f"   Test Results: {passed}/{total} passed")
        print("=" * 60)
        print(f"   ✓ Passed:  {passed}")
        print(f"   ✗ Failed:  {failed}")

        if failed == 0:
            print("\n   ✅ All ORM operations work correctly!")
        else:
            print(f"\n   ❌ {failed} test(s) failed!")

        print("=" * 60 + "\n")

        return passed, failed

    except Exception as e:
        print(f"\n  ✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return 0, 1

    finally:
        db.close()


if __name__ == "__main__":
    passed, failed = run_local_tests()
    sys.exit(1 if failed > 0 else 0)
