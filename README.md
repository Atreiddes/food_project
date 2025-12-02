# ML Сервис - Личный кабинет пользователя

Проект представляет собой веб-приложение для работы с ML сервисом по рекомендациям правильного питания.

## Задание №1: Объектная модель сервиса

**Описание:** Проектирование объектной модели с применением принципов ООП (инкапсуляция, наследование, полиморфизм) и SOLID.

**Документация:** См. [OBJECT_MODEL.md](OBJECT_MODEL.md) для полного описания объектной модели.

### Реализованные сущности (Python/SQLAlchemy)

#### Базовые модели
- `Base` ([backend_fastapi/app/db/base.py](backend_fastapi/app/db/base.py)) - базовый класс SQLAlchemy для всех моделей
- `User` ([backend_fastapi/app/models/user.py](backend_fastapi/app/models/user.py)) - модель пользователя с аутентификацией
- `UserBalance` ([backend_fastapi/app/models/user_balance.py](backend_fastapi/app/models/user_balance.py)) - модель баланса пользователя (SRP)
- `Transaction` ([backend_fastapi/app/models/transaction.py](backend_fastapi/app/models/transaction.py)) - модель финансовых транзакций
- `Prediction` ([backend_fastapi/app/models/prediction.py](backend_fastapi/app/models/prediction.py)) - модель запросов к ML сервису

#### Pydantic Schemas (валидация)
- `UserCreate` ([backend_fastapi/app/schemas/user.py](backend_fastapi/app/schemas/user.py)) - схема создания пользователя
- `UserResponse` ([backend_fastapi/app/schemas/user.py](backend_fastapi/app/schemas/user.py)) - схема ответа с данными пользователя
- `UserBalanceInfo` ([backend_fastapi/app/schemas/user.py](backend_fastapi/app/schemas/user.py)) - схема информации о балансе

#### Helper функции
- `get_user_with_balance()` ([backend_fastapi/app/core/user_helpers.py](backend_fastapi/app/core/user_helpers.py)) - загрузка пользователя с балансом (N+1 prevention)

### Применение принципов ООП

#### Инкапсуляция
- Приватные поля через SQLAlchemy ORM
- Контролируемый доступ через методы и properties
- Валидация данных через Pydantic schemas

#### Наследование
- Все модели наследуются от `Base`
- Enum классы наследуются от `str` и `enum.Enum`
- Schemas наследуются от `BaseModel`

#### Полиморфизм
- `UserRole` - роли пользователей (USER/ADMIN)
- `TransactionType` - типы транзакций (DEPOSIT/WITHDRAWAL)
- `TransactionStatus` - статусы транзакций (PENDING/COMPLETED/FAILED)
- `PredictionStatus` - статусы предсказаний (PENDING/COMPLETED/FAILED)

### Применение SOLID принципов

#### Single Responsibility Principle (SRP)
- `User` - только аутентификация и профиль
- `UserBalance` - только управление балансом
- `Transaction` - только история транзакций
- `Prediction` - только ML запросы

#### Open/Closed Principle (OCP)
- Модели расширяются через relationships
- Новые Enum значения добавляются легко
- Новые поля не ломают существующий код

#### Dependency Inversion Principle (DIP)
- API зависит от абстракций (schemas, Depends)
- Database session через dependency injection
- Разделение моделей и бизнес-логики

### Database Migration
- [002_separate_user_balance.sql](database/migrations/002_separate_user_balance.sql) - миграция для вынесения баланса в отдельную таблицу

## Структура проекта

```
backend_fastapi/
├── app/
│   ├── models/              # SQLAlchemy модели
│   │   ├── user.py          # Пользователь
│   │   ├── user_balance.py  # Баланс (SRP)
│   │   ├── transaction.py   # Транзакция
│   │   └── prediction.py    # Предсказание
│   ├── schemas/             # Pydantic schemas
│   │   ├── user.py          # User schemas
│   │   ├── balance.py       # Balance schemas
│   │   └── prediction.py    # Prediction schemas
│   ├── api/                 # API endpoints
│   │   ├── auth.py          # Аутентификация
│   │   ├── balance.py       # Управление балансом
│   │   └── predictions.py   # ML предсказания
│   ├── core/                # Бизнес-логика
│   │   ├── user_helpers.py  # User helper функции
│   │   ├── security.py      # Безопасность
│   │   └── config.py        # Конфигурация
│   └── db/                  # Database
│       └── base.py          # Base model
└── database/
    └── migrations/          # SQL миграции
        └── 002_separate_user_balance.sql
```

## Задание №3: Подключение базы данных с ORM

**Описание:** Подключить к объектной модели приложения (созданной на прошлом уроке) базу данных с использованием ORM фреймворка.

**Требования:**
1. Протестировать работоспособность системы:
   - Создание пользователей
   - Пополнение баланса
   - Списание кредитов с баланса
   - Получение истории транзакций и т.д.

2. Подготовить сценарий инициализации базы данных стандартными данными:
   - Демо пользователь
   - Демо администратор
   - Базовые модели доступные для работы и т.д.

**Формат ответа:** Ссылка на merge request

### Реализация

#### ORM подключение (SQLAlchemy)

Подключение к БД реализовано в [backend_fastapi/app/db/base.py](backend_fastapi/app/db/base.py):

```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

#### Seed скрипт (инициализация демо-данных)

**Файл:** [backend_fastapi/app/db/seed.py](backend_fastapi/app/db/seed.py)

**Запуск:**
```bash
cd backend_fastapi
python -m app.db.seed
```

**Создаваемые данные:**

| Тип | Email | Пароль | Баланс |
|-----|-------|--------|--------|
| User | demo@nutrimarket.com | demo123456 | 1000.00 |
| Admin | admin@nutrimarket.com | admin123456 | 10000.00 |
| User | test@nutrimarket.com | test123456 | 500.00 |

**ML модели:**
- `mistral` - Mistral Model (active)
- `nutrition-predictor` - Nutrition Predictor (active)
- `meal-optimizer` - Meal Plan Optimizer (active)
- `ingredient-substitute` - Ingredient Substitution (inactive)

**Архитектура seed-скрипта (SOLID):**

```
BaseSeeder (Abstract)        <- DIP, OCP
    ├── UserSeeder           <- SRP (только пользователи)
    ├── MLModelSeeder        <- SRP (только ML модели)
    └── TransactionSeeder    <- SRP (только транзакции)

DatabaseSeeder (Orchestrator) <- координация
```

#### Тестовый скрипт (проверка работоспособности)

**Файл:** [backend_fastapi/app/db/test_operations.py](backend_fastapi/app/db/test_operations.py)

**Запуск:**
```bash
cd backend_fastapi
python -m app.db.test_operations
```

**Тестируемые операции:**

1. **User Operations:**
   - Создание пользователя
   - Создание пользователя с балансом (SRP)
   - Хеширование паролей
   - Назначение ролей
   - Проверка уникальности email

2. **Balance Operations:**
   - Пополнение баланса
   - Списание с баланса
   - Проверка недостаточного баланса

3. **Transaction Operations:**
   - Создание депозита (DEPOSIT)
   - Создание списания (WITHDRAW)
   - Получение истории транзакций

4. **ML Model Operations:**
   - Создание ML модели
   - Активация/деактивация модели

**Архитектура тестов (SOLID):**

```
BaseTest (Abstract)          <- DIP, OCP
    ├── UserTest             <- SRP
    ├── BalanceTest          <- SRP
    ├── TransactionTest      <- SRP
    └── MLModelTest          <- SRP

TestRunner (Orchestrator)    <- координация
```

### API Endpoints для работы с данными

| Endpoint | Метод | Описание |
|----------|-------|----------|
| `/api/auth/register` | POST | Регистрация пользователя |
| `/api/auth/login` | POST | Авторизация |
| `/api/auth/guest` | POST | Гостевой вход |
| `/api/auth/me` | GET | Информация о пользователе |
| `/api/balance/` | GET | Получить баланс |
| `/api/balance/add` | POST | Пополнить баланс |
| `/api/balance/transactions` | GET | История транзакций |
| `/api/chat/message` | POST | ML запрос (списание) |

### Пример использования API

```bash
# 1. Регистрация
curl -X POST http://localhost:8001/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "password123"}'

# 2. Получение баланса
curl http://localhost:8001/api/balance/ \
  -H "Authorization: Bearer <token>"

# 3. Пополнение баланса
curl -X POST http://localhost:8001/api/balance/add \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"amount": 100}'

# 4. ML запрос (списание 10 кредитов)
curl -X POST http://localhost:8001/api/chat/message \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"message": "Что посоветуешь на завтрак?"}'

# 5. История транзакций
curl http://localhost:8001/api/balance/transactions \
  -H "Authorization: Bearer <token>"
```

## Технологии

- **Python 3.11** - основной язык
- **FastAPI** - веб-фреймворк
- **SQLAlchemy** - ORM
- **Pydantic** - валидация данных
- **PostgreSQL** - база данных
