"""User helper functions for eager loading balance data."""
from sqlalchemy.orm import Session, joinedload
from app.models.user import User


def get_user_with_balance(db: Session, user_id: str) -> User:
    """
    Получает пользователя с загруженным балансом.

    Использует joinedload для eager loading (один запрос вместо двух).

    Без joinedload:
    - SELECT * FROM users WHERE id = '123'        (Query 1)
    - SELECT * FROM user_balances WHERE user_id = '123'  (Query 2)

    С joinedload:
    - SELECT * FROM users JOIN user_balances ... WHERE id = '123'  (Query 1)

    Это называется N+1 problem решение.
    """
    return db.query(User).options(
        joinedload(User.balance_info)
    ).filter(User.id == user_id).first()


def get_user_by_email_with_balance(db: Session, email: str) -> User:
    """Получает пользователя по email с балансом."""
    return db.query(User).options(
        joinedload(User.balance_info)
    ).filter(User.email == email).first()
