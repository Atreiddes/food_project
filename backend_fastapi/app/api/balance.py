from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from decimal import Decimal
import uuid

from app.db.base import get_db
from app.models.user import User
from app.models.user_balance import UserBalance
from app.models.transaction import Transaction, TransactionType, TransactionStatus
from app.schemas.balance import BalanceResponse, BalanceAdd
from app.api.auth import get_current_user

router = APIRouter()


@router.get("/", response_model=BalanceResponse)
async def get_balance(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get current user's balance.
    """
    balance_record = db.query(UserBalance).filter(
        UserBalance.user_id == current_user.id
    ).first()

    if not balance_record:
        # Create balance record if it doesn't exist
        balance_record = UserBalance(
            user_id=current_user.id,
            balance=Decimal("0.00")
        )
        db.add(balance_record)
        db.commit()
        db.refresh(balance_record)

    return BalanceResponse(balance=balance_record.balance)


@router.post("/add", response_model=BalanceResponse)
async def add_balance(
    balance_data: BalanceAdd,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Add funds to user's balance.
    Creates a deposit transaction record.
    """
    if balance_data.amount <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Amount must be positive"
        )

    if balance_data.amount > 10000:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Maximum deposit amount is 10000"
        )

    # Get or create balance record
    balance_record = db.query(UserBalance).filter(
        UserBalance.user_id == current_user.id
    ).first()

    if not balance_record:
        balance_record = UserBalance(
            user_id=current_user.id,
            balance=Decimal("0.00")
        )
        db.add(balance_record)

    # Update balance
    balance_record.balance += balance_data.amount

    # Create transaction record
    transaction = Transaction(
        id=str(uuid.uuid4()),
        user_id=current_user.id,
        type=TransactionType.DEPOSIT,
        amount=balance_data.amount,
        status=TransactionStatus.COMPLETED,
        description=f"Deposit: +{balance_data.amount}"
    )
    db.add(transaction)

    db.commit()
    db.refresh(balance_record)

    return BalanceResponse(balance=balance_record.balance)


@router.get("/transactions")
async def get_transactions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    limit: int = 50
):
    """
    Get user's transaction history.
    Returns last 50 transactions by default.
    """
    transactions = db.query(Transaction).filter(
        Transaction.user_id == current_user.id
    ).order_by(Transaction.created_at.desc()).limit(limit).all()

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
