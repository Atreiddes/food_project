# Объектная модель сервиса (Python)

## Базовые сущности

### Base (backend_fastapi/app/db/base.py)
Абстрактный базовый класс для всех моделей SQLAlchemy.

```python
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()
```

### User (backend_fastapi/app/models/user.py)
Модель пользователя с ролями и аутентификацией.

**Ответственность:** Аутентификация, профиль пользователя

**Поля:**
- `id: str` - уникальный идентификатор (PK)
- `email: str` - email пользователя (unique, indexed)
- `password_hash: str` - хэш пароля (bcrypt)
- `role: UserRole` - роль (USER/ADMIN) - Enum
- `is_active: bool` - активность аккаунта
- `created_at: DateTime` - дата создания
- `updated_at: DateTime` - дата обновления

**Relationships:**
- `balance_info: UserBalance` - связь 1:1 с балансом (cascade delete)

**Принципы ООП:**
- ✅ Инкапсуляция: приватные поля через ORM
- ✅ Наследование: extends Base
- ✅ Полиморфизм: UserRole Enum

### UserBalance (backend_fastapi/app/models/user_balance.py)
Модель баланса пользователя (отдельная сущность по SRP).

**Ответственность:** Финансы, управление балансом

**Поля:**
- `user_id: str` - ID пользователя (PK, FK to User)
- `balance: Decimal` - текущий баланс
- `created_at: DateTime` - дата создания
- `updated_at: DateTime` - дата обновления

**Relationships:**
- `user: User` - обратная связь к пользователю

**Применение SOLID:**
- ✅ SRP: Отвечает только за финансы (User - только за аутентификацию)
- ✅ OCP: Можно расширить (история баланса, лимиты)

### Transaction (backend_fastapi/app/models/transaction.py)
Модель финансовых транзакций.

**Ответственность:** История финансовых операций

**Поля:**
- `id: str` - уникальный идентификатор (PK)
- `user_id: str` - ID пользователя (FK to User)
- `type: TransactionType` - тип (DEPOSIT/WITHDRAWAL) - Enum
- `amount: Decimal` - сумма транзакции
- `status: TransactionStatus` - статус (PENDING/COMPLETED/FAILED) - Enum
- `description: str` - описание операции
- `created_at: DateTime` - дата создания

**Relationships:**
- `user: User` - связь с пользователем (cascade delete)

**Принципы ООП:**
- ✅ Полиморфизм: TransactionType, TransactionStatus Enum

### Prediction (backend_fastapi/app/models/prediction.py)
Модель запроса к ML сервису и результата.

**Ответственность:** Запросы к ML модели, хранение результатов

**Поля:**
- `id: str` - уникальный идентификатор (PK)
- `user_id: str` - ID пользователя (FK to User)
- `model_id: str` - идентификатор ML модели
- `input_data: dict` - входные данные (JSON)
- `result: dict` - результат предсказания (JSON, nullable)
- `status: PredictionStatus` - статус (PENDING/COMPLETED/FAILED) - Enum
- `cost_charged: Decimal` - стоимость запроса
- `error_message: str` - сообщение об ошибке (nullable)
- `created_at: DateTime` - дата создания
- `updated_at: DateTime` - дата обновления

**Relationships:**
- `user: User` - связь с пользователем (cascade delete)

**Принципы ООП:**
- ✅ Полиморфизм: PredictionStatus Enum
- ✅ Инкапсуляция: JSON данные через SQLAlchemy JSON type

## Enums (Полиморфизм)

### UserRole (backend_fastapi/app/models/user.py)
```python
class UserRole(str, enum.Enum):
    USER = "user"
    ADMIN = "admin"
```

### TransactionType (backend_fastapi/app/models/transaction.py)
```python
class TransactionType(str, enum.Enum):
    DEPOSIT = "deposit"
    WITHDRAWAL = "withdrawal"
```

### TransactionStatus (backend_fastapi/app/models/transaction.py)
```python
class TransactionStatus(str, enum.Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
```

### PredictionStatus (backend_fastapi/app/models/prediction.py)
```python
class PredictionStatus(str, enum.Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
```

## Schemas (Pydantic для валидации)

### UserCreate (backend_fastapi/app/schemas/user.py)
Схема для создания пользователя.

**Поля:**
- `email: EmailStr` - валидация email
- `password: str` - валидация пароля (мин 8 символов, буквы + цифры)

**Validators:**
- `validate_password()` - проверка сложности пароля

### UserResponse (backend_fastapi/app/schemas/user.py)
Схема ответа с данными пользователя.

**Поля:**
- `id: str`
- `email: str`
- `role: str`
- `is_active: bool`
- `created_at: datetime`
- `balance_info: Optional[UserBalanceInfo]` - вложенный объект баланса

**Properties:**
- `balance: Decimal` - обратная совместимость (из balance_info)

### UserBalanceInfo (backend_fastapi/app/schemas/user.py)
Схема информации о балансе.

**Поля:**
- `balance: Decimal`
- `updated_at: datetime`

## Helper функции (DRY принцип)

### user_helpers.py (backend_fastapi/app/core/user_helpers.py)
Вспомогательные функции для работы с пользователями.

**Функции:**
- `get_user_with_balance(db, user_id)` - загрузка пользователя с балансом (eager loading)
- `get_user_by_email_with_balance(db, email)` - загрузка по email с балансом

**Оптимизации:**
- ✅ Использует `joinedload` для предотвращения N+1 проблемы
- ✅ Один SQL запрос вместо двух

## Применение принципов ООП и SOLID

### Инкапсуляция
- ✅ Приватные поля через SQLAlchemy ORM
- ✅ Контролируемый доступ через методы и properties
- ✅ Валидация данных через Pydantic schemas

### Наследование
- ✅ Все модели наследуются от `Base`
- ✅ Enum классы наследуются от `str` и `enum.Enum`
- ✅ Schemas наследуются от `BaseModel`

### Полиморфизм
- ✅ Enum типы: UserRole, TransactionType, TransactionStatus, PredictionStatus
- ✅ Единый интерфейс для всех моделей (Base)
- ✅ Различное поведение через Enum values

### Single Responsibility Principle (SRP)
- ✅ User - только аутентификация и профиль
- ✅ UserBalance - только финансы
- ✅ Transaction - только история транзакций
- ✅ Prediction - только ML запросы

### Open/Closed Principle (OCP)
- ✅ Модели можно расширять без изменения существующего кода
- ✅ Новые Enum значения добавляются легко
- ✅ Relationships позволяют добавлять новые связи

### Dependency Inversion Principle (DIP)
- ✅ API зависит от абстракций (Depends, schemas)
- ✅ Database session через dependency injection
- ✅ Разделение моделей и бизнес-логики

## Диаграмма связей

```
┌─────────────┐       1:1        ┌──────────────┐
│    User     │◄─────────────────┤ UserBalance  │
│             │                  │              │
│ - id        │                  │ - user_id    │
│ - email     │                  │ - balance    │
│ - password  │                  └──────────────┘
│ - role      │
└─────────────┘
       │ 1:N
       ├──────────────┐
       │              │
       ▼              ▼
┌─────────────┐ ┌──────────────┐
│ Transaction │ │  Prediction  │
│             │ │              │
│ - id        │ │ - id         │
│ - user_id   │ │ - user_id    │
│ - type      │ │ - model_id   │
│ - amount    │ │ - input_data │
│ - status    │ │ - result     │
└─────────────┘ └──────────────┘
```

## Модификаторы доступа

SQLAlchemy не поддерживает явные private/public модификаторы, но обеспечивает инкапсуляцию через:
- ORM layer (контролируемый доступ к БД)
- Pydantic schemas (валидация на уровне API)
- Dependencies (контроль доступа через Depends)

## Типы данных

**Строки:**
- `String(255)` - email, ID, model_id
- `Text` - длинные тексты (error_message)

**Числовые:**
- `Numeric(10, 2)` - деньги (balance, amount)
- `Decimal` - точные финансовые расчеты

**Даты:**
- `DateTime` - timestamp с timezone
- `func.now()` - автоматические timestamp

**JSON:**
- `JSON` - структурированные данные (input_data, result)

**Boolean:**
- `Boolean` - флаги (is_active)

**Enum:**
- `SQLEnum` - статусы, типы, роли

## Заключение

Объектная модель построена на принципах:
- ✅ Чистая архитектура (Clean Architecture)
- ✅ SOLID принципы
- ✅ DRY (Don't Repeat Yourself)
- ✅ Разделение ответственности
- ✅ Типобезопасность (через Pydantic)
- ✅ Оптимизация запросов (N+1 prevention)

Модель готова для расширения и масштабирования.
