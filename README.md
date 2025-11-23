# ML Service Project

Два задания для курса: объектная модель и Docker.

## Задание 1: Object Model

Объектная модель с применением ООП принципов.

**Файлы:**
- `src/types/ml-service.ts` - классы (User, MLModel, Prediction, Transaction)
- `database/init.sql` - схема PostgreSQL

**Принципы ООП:**
- Наследование (BaseEntity)
- Инкапсуляция (приватные поля)
- Полиморфизм (разное поведение методов)

## Задание 2: Docker

4 сервиса в Docker Compose.

**Файлы:**
- `docker-compose.yml` - конфигурация
- `backend/Dockerfile` - API сервис
- `Dockerfile.frontend` - фронтенд
- `.env.example` - пример переменных

**Сервисы:**
1. **database** - PostgreSQL
2. **rabbitmq** - очередь
3. **app** - Node.js API
4. **web-proxy** - Nginx

## Запуск

```bash
# Скопировать .env
cp .env.example .env

# Заполнить переменные в .env

# Запустить
docker-compose up --build
```

Откроется на http://localhost
