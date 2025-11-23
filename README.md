# ML Service Project

Проект содержит два задания для курса.

---

## 📋 ЗАДАНИЕ 1: Object Model (ООП)

**Цель:** Спроектировать объектную модель сервиса с применением ООП и SOLID принципов.

### Файлы задания 1:

```
src/types/ml-service.ts   ← Классы: User, MLModel, Prediction, Transaction
database/init.sql          ← Схема PostgreSQL
```

### Реализованные принципы ООП:

- **Inheritance** - BaseEntity (базовый класс для всех)
- **Encapsulation** - User._balance (приватное поле)
- **Polymorphism** - Prediction.getStatusColor() (разное поведение)

### Реализованные принципы SOLID:

- **Single Responsibility** - MLModel (только работа с моделью)
- **Open/Closed** - Transaction.getTypeLabel() (легко расширить)

---

## 🐳 ЗАДАНИЕ 2: Docker (4 сервиса)

**Цель:** Организовать структуру проекта с использованием Docker.

### Файлы задания 2:

```
docker-compose.yml         ← Конфигурация 4 сервисов
backend/Dockerfile         ← Dockerfile для app (7 команд)
backend/server.js          ← Node.js API
backend/package.json       ← Зависимости backend
Dockerfile.frontend        ← Multi-stage build для web-proxy
.env.example               ← Пример переменных окружения
.dockerignore              ← Оптимизация образов
backend/.dockerignore      ← Оптимизация backend образа
```

### 4 сервиса:

1. **database** - PostgreSQL (порт 5432)
2. **rabbitmq** - Очередь сообщений (порты 5672, 15672)
3. **app** - Node.js API (порт 3001)
4. **web-proxy** - Nginx (порты 80, 443)

### Выполненные требования:

- ✅ 4 сервиса (database, rabbitmq, app, web-proxy)
- ✅ Конфигурация через env_file
- ✅ Volumes для хранения данных
- ✅ web-proxy на Nginx (порты 80 и 443)
- ✅ rabbitmq (порты 5672 и 15672, volume)
- ✅ database на PostgreSQL (с volume)
- ✅ Dockerfile с командами: FROM, WORKDIR, COPY, RUN, EXPOSE, CMD

---

## 🚀 Запуск проекта

```bash
# 1. Скопировать .env
cp .env.example .env

# 2. Заполнить переменные в .env
# DB_PASSWORD, HUGGINGFACE_API_KEY и т.д.

# 3. Запустить все сервисы
docker-compose up --build
```

Откроется на http://localhost

---

## 📊 Структура проекта

```
.
├── ЗАДАНИЕ 1 (Object Model):
│   ├── src/types/ml-service.ts    ← Классы
│   └── database/init.sql          ← БД
│
├── ЗАДАНИЕ 2 (Docker):
│   ├── docker-compose.yml         ← 4 сервиса
│   ├── backend/
│   │   ├── Dockerfile             ← app сервис
│   │   ├── server.js
│   │   └── package.json
│   ├── Dockerfile.frontend        ← web-proxy
│   └── .env.example
│
└── README.md                      ← Этот файл
```
