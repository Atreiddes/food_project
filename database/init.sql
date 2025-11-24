-- Database initialization script

-- Create users table
CREATE TABLE IF NOT EXISTS users (
    id VARCHAR(255) PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(50) NOT NULL DEFAULT 'user',
    balance DECIMAL(10, 2) NOT NULL DEFAULT 0,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Create ml_models table
CREATE TABLE IF NOT EXISTS ml_models (
    id VARCHAR(255) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    type VARCHAR(100) NOT NULL,
    version VARCHAR(50) NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'active',
    cost_per_request DECIMAL(10, 2) NOT NULL,
    endpoint VARCHAR(500) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Create transactions table
CREATE TABLE IF NOT EXISTS transactions (
    id VARCHAR(255) PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    type VARCHAR(50) NOT NULL,
    amount DECIMAL(10, 2) NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'pending',
    description TEXT NOT NULL,
    related_prediction_id VARCHAR(255),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Create predictions table
CREATE TABLE IF NOT EXISTS predictions (
    id VARCHAR(255) PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    model_id VARCHAR(255) NOT NULL REFERENCES ml_models(id) ON DELETE CASCADE,
    input_data JSONB NOT NULL,
    result JSONB,
    status VARCHAR(50) NOT NULL DEFAULT 'pending',
    cost_charged DECIMAL(10, 2) NOT NULL,
    validation_errors JSONB,
    error_message TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_transactions_user_id ON transactions(user_id);
CREATE INDEX IF NOT EXISTS idx_predictions_user_id ON predictions(user_id);
CREATE INDEX IF NOT EXISTS idx_predictions_model_id ON predictions(model_id);
CREATE INDEX IF NOT EXISTS idx_predictions_status ON predictions(status);

-- Insert demo admin user (password: admin123)
INSERT INTO users (id, email, password_hash, role, balance, is_active)
VALUES (
    'admin-001',
    'admin@mlservice.com',
    '$2b$10$example.hash.replace.with.real.hash',
    'admin',
    10000,
    TRUE
) ON CONFLICT (email) DO NOTHING;

-- Insert demo regular user (password: user123)
INSERT INTO users (id, email, password_hash, role, balance, is_active)
VALUES (
    'user-001',
    'user@mlservice.com',
    '$2b$10$example.hash.replace.with.real.hash',
    'user',
    1000,
    TRUE
) ON CONFLICT (email) DO NOTHING;

-- Insert demo ML model
INSERT INTO ml_models (id, name, description, type, version, status, cost_per_request, endpoint)
VALUES (
    'model-001',
    'Nutrition Advisor',
    'ML model for providing nutrition recommendations based on user queries',
    'nutrition_recommendation',
    '1.0.0',
    'active',
    10.00,
    'http://ollama:11434/api/generate'
) ON CONFLICT (id) DO NOTHING;
