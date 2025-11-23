# ML Service - Object Model

Проект для курса по разработке. Реализация объектной модели ML сервиса.

## Структура

- `src/types/ml-service.ts` - основные классы
- `database/init.sql` - схема БД

## Классы

- **BaseEntity** - базовый класс
- **User** - пользователь с балансом  
- **MLModel** - модель ML
- **Prediction** - предсказание
- **Transaction** - транзакция

## Установка

```bash
npm install
npm run dev
```

## База данных

PostgreSQL с таблицами profiles, ml_models, predictions, transactions.

## Запуск

```bash
docker-compose up
```
