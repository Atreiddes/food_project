# 🏗️ Refactoring Guide: Применение SRP к User Balance

## Проблема

**Текущая архитектура нарушает SRP (Single Responsibility Principle):**

```python
class User(Base):
    id: str
    email: str              # ✅ Ответственность: Аутентификация
    password_hash: str      # ✅ Ответственность: Аутентификация
    role: str               # ✅ Ответственность: Авторизация
    balance: Decimal        # ❌ Ответственность: Финансы (не по месту!)
    is_active: bool         # ✅ Ответственность: Управление пользователем
```

**Почему это плохо:**
1. User класс отвечает за 3 разные вещи: auth, authorization, finance
2. Сложно тестировать (нужно мокать финансы для тестов аутентификации)
3. Сложно масштабировать (финансы нельзя вынести на отдельный сервис)
4. Нарушение Open/Closed Principle (изменения в финансах затрагивают User)

## Решение: Separate Balance Entity

### Новая архитектура (SRP compliant)

```python
# Ответственность: Аутентификация и профиль
class User(Base):
    id: str
    email: str
    password_hash: str
    role: str
    is_active: bool
    # Relationship
    balance_info: UserBalance  # Композиция

# Ответственность: Финансы
class UserBalance(Base):
    user_id: str  # FK to User
    balance: Decimal
    created_at: datetime
    updated_at: datetime
```

**Преимущества:**
- ✅ Разделение ответственности
- ✅ Легче тестировать
- ✅ Можно масштабировать (разные БД/сервисы)
- ✅ Проще добавлять финансовую логику

## Созданные файлы

### 1. Модель UserBalance

**Файл:** `backend_fastapi/app/models/user_balance.py`

```python
class UserBalance(Base):
    __tablename__ = "user_balances"

    user_id = Column(String(255), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    balance = Column(Numeric(10, 2), nullable=False, default=0)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="balance_info")
```

### 2. Обновленная модель User

**Файл:** `backend_fastapi/app/models/user.py`

```python
class User(Base):
    # ... все поля кроме balance

    # Relationship 1:1
    balance_info = relationship(
        "UserBalance",
        back_populates="user",
        uselist=False,  # Один к одному
        cascade="all, delete-orphan"  # При удалении User удаляется Balance
    )
```

### 3. Миграция БД

**Файл:** `database/migrations/002_separate_user_balance.sql`

```sql
-- Создаем таблицу
CREATE TABLE user_balances (
    user_id VARCHAR(255) PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    balance DECIMAL(10, 2) NOT NULL DEFAULT 0,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Мигрируем данные
INSERT INTO user_balances (user_id, balance, created_at, updated_at)
SELECT id, balance, created_at, updated_at FROM users;

-- Удаляем старую колонку
ALTER TABLE users DROP COLUMN balance;
```

### 4. Обновленные Schemas

**Файл:** `backend_fastapi/app/schemas/user.py`

```python
class UserBalanceInfo(BaseModel):
    balance: Decimal
    updated_at: datetime

class UserResponse(BaseModel):
    id: str
    email: str
    role: str
    is_active: bool
    created_at: datetime
    balance_info: Optional[UserBalanceInfo] = None  # Вложенный объект

    @property
    def balance(self) -> Decimal:
        """Обратная совместимость"""
        return self.balance_info.balance if self.balance_info else Decimal(0)
```

### 5. Helper Functions

**Файл:** `backend_fastapi/app/core/user_helpers.py`

```python
def get_user_with_balance(db: Session, user_id: str) -> User:
    """
    Eager loading баланса (один SQL запрос вместо двух).

    Решает N+1 problem.
    """
    return db.query(User).options(
        joinedload(User.balance_info)
    ).filter(User.id == user_id).first()
```

## Как обновить API endpoints

### До (нарушение SRP)

```python
@router.post("/register")
async def register(user_data: UserCreate, db: Session = Depends(get_db)):
    user = User(
        id=str(uuid.uuid4()),
        email=user_data.email,
        password_hash=get_password_hash(user_data.password),
        role=UserRole.USER,
        balance=1000,  # ❌ Смешиваем auth и finance
        is_active=True
    )
    db.add(user)
    db.commit()

    return {
        "user": {
            "id": user.id,
            "email": user.email,
            "balance": user.balance  # ❌ Прямой доступ
        }
    }
```

### После (SRP compliant)

```python
@router.post("/register")
async def register(user_data: UserCreate, db: Session = Depends(get_db)):
    user_id = str(uuid.uuid4())

    # 1. Создаем User (аутентификация)
    user = User(
        id=user_id,
        email=user_data.email,
        password_hash=get_password_hash(user_data.password),
        role=UserRole.USER,
        is_active=True
    )

    # 2. Создаем UserBalance (финансы) - отдельно!
    user_balance = UserBalance(
        user_id=user_id,
        balance=settings.DEFAULT_USER_BALANCE
    )

    db.add(user)
    db.add(user_balance)
    db.commit()

    # 3. Загружаем с балансом для ответа
    user_with_balance = get_user_with_balance(db, user_id)

    # 4. Используем UserResponse schema (автоматически форматирует)
    return {
        "user": UserResponse.from_orm(user_with_balance)
    }
```

## Обновление других endpoints

### Balance API

**До:**
```python
@router.post("/add")
async def add_balance(amount: Decimal, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    current_user.balance += amount  # ❌ Модифицируем User напрямую
    db.commit()
    return {"balance": current_user.balance}
```

**После:**
```python
@router.post("/add")
async def add_balance(amount: Decimal, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    # Работаем только с UserBalance
    user_balance = db.query(UserBalance).filter(UserBalance.user_id == current_user.id).first()

    if not user_balance:
        raise HTTPException(status_code=404, detail="Balance not found")

    user_balance.balance += amount
    db.commit()

    return {"balance": user_balance.balance}
```

### Predictions API

**До:**
```python
@router.post("/message")
async def create_prediction(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.balance < cost:  # ❌ User знает о финансах
        raise InsufficientBalanceError()

    current_user.balance -= cost  # ❌ Модифицируем User
    # ...
```

**После:**
```python
@router.post("/message")
async def create_prediction(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    # Получаем баланс
    user_balance = db.query(UserBalance).filter(UserBalance.user_id == current_user.id).first()

    if not user_balance or user_balance.balance < cost:
        raise InsufficientBalanceError()

    # Списываем с баланса
    user_balance.balance -= cost
    # ...
```

## N+1 Problem и его решение

### Проблема

```python
# Получаем пользователя
user = db.query(User).filter(User.id == '123').first()
# SQL: SELECT * FROM users WHERE id = '123'

# Пытаемся получить баланс
balance = user.balance_info.balance
# SQL: SELECT * FROM user_balances WHERE user_id = '123'

# Итого: 2 запроса!
# Для 100 пользователей: 101 запрос (1 + 100) - N+1 Problem!
```

### Решение: Eager Loading

```python
from sqlalchemy.orm import joinedload

# Один запрос с JOIN
user = db.query(User).options(
    joinedload(User.balance_info)
).filter(User.id == '123').first()

# SQL: SELECT * FROM users LEFT JOIN user_balances ON users.id = user_balances.user_id WHERE users.id = '123'

# Теперь balance уже загружен:
balance = user.balance_info.balance  # Нет дополнительного запроса!

# Для 100 пользователей: всего 1 запрос!
```

## Тестирование

### Unit тесты для User (аутентификация)

```python
def test_user_registration():
    user = User(
        id="test-id",
        email="test@example.com",
        password_hash=hash_password("password123"),
        role=UserRole.USER,
        is_active=True
    )

    # Тестируем ТОЛЬКО аутентификацию
    # Не нужно мокать баланс!
    assert user.email == "test@example.com"
    assert user.is_active == True
```

### Unit тесты для UserBalance (финансы)

```python
def test_balance_operations():
    balance = UserBalance(
        user_id="test-id",
        balance=Decimal("1000.00")
    )

    # Тестируем ТОЛЬКО финансы
    # Не нужно знать о пользователе!
    balance.balance += Decimal("500.00")
    assert balance.balance == Decimal("1500.00")
```

### Integration тесты

```python
def test_user_with_balance(db: Session):
    user_id = "test-id"

    # Создаем User и Balance
    user = User(id=user_id, email="test@example.com", ...)
    balance = UserBalance(user_id=user_id, balance=1000)

    db.add(user)
    db.add(balance)
    db.commit()

    # Загружаем с балансом
    user_with_balance = get_user_with_balance(db, user_id)

    assert user_with_balance.balance_info.balance == 1000
```

## Миграция существующих данных

### Шаг 1: Создать новую таблицу

```bash
docker exec -i nutrimarket_db psql -U nutrimarket_user -d nutrimarket_db < database/migrations/002_separate_user_balance.sql
```

### Шаг 2: Проверить миграцию

```sql
-- Проверяем, что данные перенеслись
SELECT
    u.id,
    u.email,
    ub.balance
FROM users u
LEFT JOIN user_balances ub ON u.id = ub.user_id;

-- Все пользователи должны иметь баланс
SELECT COUNT(*) FROM users WHERE id NOT IN (SELECT user_id FROM user_balances);
-- Результат должен быть: 0
```

### Шаг 3: Обновить код

1. Обновить модели (уже сделано)
2. Обновить schemas (уже сделано)
3. Обновить API endpoints (нужно сделать)
4. Обновить тесты

### Шаг 4: Откатить при проблемах

```sql
-- Если что-то пошло не так, откатываем:
ALTER TABLE users ADD COLUMN balance DECIMAL(10, 2) DEFAULT 0;

UPDATE users u
SET balance = (SELECT balance FROM user_balances WHERE user_id = u.id);

DROP TABLE user_balances;
```

## Best Practices

### 1. Всегда используйте joinedload

```python
# ❌ Плохо - N+1 problem
users = db.query(User).all()
for user in users:
    print(user.balance_info.balance)  # N запросов

# ✅ Хорошо - 1 запрос
users = db.query(User).options(joinedload(User.balance_info)).all()
for user in users:
    print(user.balance_info.balance)  # Уже загружено
```

### 2. Проверяйте наличие баланса

```python
# ❌ Плохо - может быть None
balance = user.balance_info.balance

# ✅ Хорошо - проверяем
if user.balance_info:
    balance = user.balance_info.balance
else:
    raise HTTPException(404, "Balance not found")
```

### 3. Используйте CASCADE

```python
# В модели UserBalance:
user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"))

# Теперь при удалении User автоматически удаляется Balance
db.delete(user)
db.commit()  # UserBalance тоже удалится
```

## Заключение

Рефакторинг применил принцип SRP:
- **User** отвечает за: аутентификацию, профиль, авторизацию
- **UserBalance** отвечает за: финансы, баланс, транзакции

Это делает код:
- ✅ Более тестируемым
- ✅ Более масштабируемым
- ✅ Более поддерживаемым
- ✅ Более соответствующим SOLID принципам

**Следующие шаги:**
1. Применить миграцию к БД
2. Обновить все API endpoints
3. Обновить тесты
4. Задеплоить

---

**Важно:** Это архитектурное улучшение. Для учебного проекта можно оставить как есть (balance в User), но для production рекомендуется разделение.
