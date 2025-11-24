from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from sqlalchemy.exc import OperationalError
from app.db.base import get_db
from app.models.user import User
from app.models.user_balance import UserBalance
from app.models.transaction import Transaction, TransactionType, TransactionStatus
from app.schemas.balance import BalanceResponse, BalanceAdd
from app.api.auth import get_current_user
from app.core.exceptions import DatabaseError
from app.core.rate_limit import limiter
import uuid

router = APIRouter()


@router.get("/", response_model=BalanceResponse)
async def get_balance(current_user: User = Depends(get_current_user)):
    """
    Get current user balance.
    User is loaded with balance_info via get_current_user dependency.
    """
    if not current_user.balance_info:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Balance not found"
        )
    return BalanceResponse(balance=current_user.balance_info.balance)


@router.post("/add")
@limiter.limit("20/hour")
async def add_balance(
    request: Request,
    balance_data: BalanceAdd,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Add balance to user account.
    Works with separate UserBalance entity (SRP).
    """
    if balance_data.amount <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Amount must be positive"
        )

    # Get UserBalance entity
    user_balance = db.query(UserBalance).filter(
        UserBalance.user_id == current_user.id
    ).first()

    if not user_balance:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Balance not found"
        )

    transaction = Transaction(
        id=str(uuid.uuid4()),
        user_id=current_user.id,
        type=TransactionType.DEPOSIT,
        amount=balance_data.amount,
        status=TransactionStatus.COMPLETED,
        description="Balance deposit"
    )

    # Modify UserBalance, not User
    user_balance.balance += balance_data.amount

    db.add(transaction)
    try:
        db.commit()
        db.refresh(user_balance)
    except OperationalError as e:
        db.rollback()
        raise DatabaseError(f"Database connection error: {str(e)}")
    except Exception as e:
        db.rollback()
        raise DatabaseError(f"Failed to add balance: {str(e)}")

    return {
        "balance": float(user_balance.balance),
        "message": "Balance added successfully"
    }


@router.get("/transactions")
async def get_transactions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    transactions = db.query(Transaction).filter(
        Transaction.user_id == current_user.id
    ).order_by(Transaction.created_at.desc()).limit(50).all()

    return {
        "transactions": [
            {
                "id": t.id,
                "type": t.type.value,
                "amount": float(t.amount),
                "status": t.status.value,
                "description": t.description,
                "created_at": t.created_at
            }
            for t in transactions
        ]
    }
