# ML Сервис - Личный кабинет пользователя

Веб-приложение для работы с ML сервисом по рекомендациям правильного питания.

## Задание №1: Объектная модель сервиса

### Модели данных
- `BaseEntity` ([src/models/base.ts](src/models/base.ts)) - базовый класс
- `User` ([src/models/User.ts](src/models/User.ts)) - пользователь с ролями и балансом
- `MLModel` ([src/models/MLModel.ts](src/models/MLModel.ts)) - модель ML сервиса
- `Transaction` ([src/models/Transaction.ts](src/models/Transaction.ts)) - финансовые транзакции
- `Prediction` ([src/models/Prediction.ts](src/models/Prediction.ts)) - запрос к ML сервису и результат

### Интерфейсы сервисов
- `IRepository` ([src/interfaces/IRepository.ts](src/interfaces/IRepository.ts)) - работа с БД
- `IUserService` ([src/interfaces/IUserService.ts](src/interfaces/IUserService.ts)) - управление пользователями
- `IBalanceService` ([src/interfaces/IBalanceService.ts](src/interfaces/IBalanceService.ts)) - управление балансом
- `IMLService` ([src/interfaces/IMLService.ts](src/interfaces/IMLService.ts)) - работа с ML моделями
- `IValidator` ([src/interfaces/IValidator.ts](src/interfaces/IValidator.ts)) - валидация данных

## Задание №2: Docker конфигурация

### Сервисы
- `app` ([docker-compose.yml](docker-compose.yml)) - основное приложение
- `web-proxy` - Nginx прокси (порты 80, 443)
- `database` - PostgreSQL
- `rabbitmq` - очередь сообщений (порты 5672, 15672)
- `ollama` - ML модель для рекомендаций

## Структура проекта

```
src/
├── models/              # Модели данных
│   ├── base.ts
│   ├── User.ts
│   ├── MLModel.ts
│   ├── Transaction.ts
│   ├── Prediction.ts
│   └── index.ts
└── interfaces/          # Интерфейсы сервисов
    ├── IRepository.ts
    ├── IUserService.ts
    ├── IBalanceService.ts
    ├── IMLService.ts
    └── IValidator.ts
```
