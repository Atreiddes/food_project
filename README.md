# ML Сервис - Личный кабинет пользователя

Проект представляет собой веб-приложение для работы с ML сервисом по рекомендациям правильного питания.

## Задание №1: Объектная модель сервиса

**Описание:** Проектирование объектной модели с применением принципов ООП (инкапсуляция, наследование, полиморфизм) и SOLID.

**Реализованные классы:**

### Базовые сущности
- `BaseEntity` ([src/models/base.ts](src/models/base.ts)) - абстрактный базовый класс для всех моделей
- `User` ([src/models/User.ts](src/models/User.ts)) - модель пользователя с ролями и балансом
- `MLModel` ([src/models/MLModel.ts](src/models/MLModel.ts)) - модель ML сервиса
- `Transaction` ([src/models/Transaction.ts](src/models/Transaction.ts)) - модель финансовых транзакций
- `Prediction` ([src/models/Prediction.ts](src/models/Prediction.ts)) - модель запроса к ML сервису и результата

### Интерфейсы
- `IRepository` ([src/interfaces/IRepository.ts](src/interfaces/IRepository.ts)) - паттерн Repository для работы с БД
- `IUserService` ([src/interfaces/IUserService.ts](src/interfaces/IUserService.ts)) - сервис управления пользователями
- `IBalanceService` ([src/interfaces/IBalanceService.ts](src/interfaces/IBalanceService.ts)) - сервис управления балансом
- `IMLService` ([src/interfaces/IMLService.ts](src/interfaces/IMLService.ts)) - сервис работы с ML моделями
- `IValidator` ([src/interfaces/IValidator.ts](src/interfaces/IValidator.ts)) - валидация данных


## Структура проекта

```
src/
├── models/              # Модели данных
│   ├── base.ts         # Базовый класс
│   ├── User.ts         # Пользователь
│   ├── MLModel.ts      # ML модель
│   ├── Transaction.ts  # Транзакция
│   ├── Prediction.ts   # Предсказание
│   └── index.ts        # Экспорт моделей
└── interfaces/         # Интерфейсы сервисов
    ├── IRepository.ts
    ├── IUserService.ts
    ├── IBalanceService.ts
    ├── IMLService.ts
    └── IValidator.ts
```
