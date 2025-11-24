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

## Технологии

- **Python 3.11** - основной язык
- **FastAPI** - веб-фреймворк
- **SQLAlchemy** - ORM
- **Pydantic** - валидация данных
- **PostgreSQL** - база данных
