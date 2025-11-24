-- ===================================================
-- Migration: Separate User Balance
-- Date: 2025-11-24
-- Description: Вынос баланса в отдельную таблицу (SRP)
-- ===================================================

-- Шаг 1: Создаем новую таблицу user_balances
CREATE TABLE IF NOT EXISTS user_balances (
    user_id VARCHAR(255) PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    balance DECIMAL(10, 2) NOT NULL DEFAULT 0,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Шаг 2: Мигрируем данные из users в user_balances
INSERT INTO user_balances (user_id, balance, created_at, updated_at)
SELECT id, balance, created_at, updated_at
FROM users
ON CONFLICT (user_id) DO NOTHING;

-- Шаг 3: Создаем индекс для оптимизации
CREATE INDEX IF NOT EXISTS idx_user_balances_user_id ON user_balances(user_id);

-- Шаг 4: Удаляем колонку balance из users
-- ВНИМАНИЕ: В PostgreSQL нельзя просто удалить колонку в транзакции
-- с данными, поэтому делаем это отдельно
ALTER TABLE users DROP COLUMN IF EXISTS balance;

-- Шаг 5: Обновляем статистику
ANALYZE users;
ANALYZE user_balances;

-- ===================================================
-- Объяснение:
-- ===================================================
--
-- Было (нарушение SRP):
-- users
-- ├── id
-- ├── email
-- ├── password_hash
-- ├── balance          ← Смешанная ответственность!
-- └── ...
--
-- Стало (следование SRP):
-- users                user_balances
-- ├── id               ├── user_id (FK)
-- ├── email            ├── balance
-- ├── password_hash    └── ...
-- └── ...
--
-- Преимущества:
-- 1. Разделение ответственности (User = auth, UserBalance = finance)
-- 2. Легче масштабировать (можно вынести balances на отдельный сервер)
-- 3. Проще тестировать (независимые компоненты)
-- 4. Удобнее добавлять финансовую логику (история балансов, лимиты)
-- ===================================================
