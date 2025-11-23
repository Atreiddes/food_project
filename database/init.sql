-- Database initialization script for NutriMarket ML Service

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create updated_at trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- ============================================================
-- PROFILES TABLE (User information)
-- ============================================================
CREATE TABLE IF NOT EXISTS profiles (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  email TEXT NOT NULL UNIQUE,
  full_name TEXT,
  username TEXT UNIQUE,
  balance DECIMAL(10, 2) NOT NULL DEFAULT 0.00 CHECK (balance >= 0),
  total_predictions INTEGER NOT NULL DEFAULT 0,
  total_spent DECIMAL(10, 2) NOT NULL DEFAULT 0.00,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_profiles_email ON profiles(email);
CREATE INDEX idx_profiles_balance ON profiles(balance);

CREATE TRIGGER update_profiles_updated_at
  BEFORE UPDATE ON profiles
  FOR EACH ROW
  EXECUTE FUNCTION update_updated_at_column();

-- ============================================================
-- ML MODELS TABLE
-- ============================================================
CREATE TABLE IF NOT EXISTS ml_models (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  name TEXT NOT NULL,
  description TEXT,
  version TEXT NOT NULL DEFAULT '1.0',
  cost_per_prediction DECIMAL(10, 2) NOT NULL CHECK (cost_per_prediction >= 0),
  input_schema JSONB NOT NULL DEFAULT '{}'::jsonb,
  output_schema JSONB NOT NULL DEFAULT '{}'::jsonb,
  is_active BOOLEAN NOT NULL DEFAULT true,
  model_type TEXT NOT NULL DEFAULT 'classification',
  endpoint_url TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_ml_models_active ON ml_models(is_active);
CREATE INDEX idx_ml_models_type ON ml_models(model_type);

CREATE TRIGGER update_ml_models_updated_at
  BEFORE UPDATE ON ml_models
  FOR EACH ROW
  EXECUTE FUNCTION update_updated_at_column();

-- Insert sample ML models
INSERT INTO ml_models (name, description, cost_per_prediction, input_schema, model_type) VALUES
  (
    'Recipe Nutrition Predictor',
    'Predicts nutrition values based on ingredients',
    5.0,
    '{"type": "object", "required": ["ingredients"], "properties": {"ingredients": {"type": "array"}}}'::jsonb,
    'regression'
  ),
  (
    'Meal Plan Optimizer',
    'Optimizes weekly meal plans',
    10.0,
    '{"type": "object", "required": ["budget", "calories_target"]}'::jsonb,
    'optimization'
  ),
  (
    'Ingredient Substitution',
    'Suggests ingredient alternatives',
    3.0,
    '{"type": "object", "required": ["ingredient"]}'::jsonb,
    'recommendation'
  );

-- ============================================================
-- PREDICTIONS TABLE
-- ============================================================
CREATE TYPE prediction_status AS ENUM ('pending', 'processing', 'completed', 'failed');

CREATE TABLE IF NOT EXISTS predictions (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
  model_id UUID NOT NULL REFERENCES ml_models(id) ON DELETE RESTRICT,
  input_data JSONB NOT NULL,
  output_data JSONB,
  status prediction_status NOT NULL DEFAULT 'pending',
  error_message TEXT,
  cost DECIMAL(10, 2) NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  started_at TIMESTAMPTZ,
  completed_at TIMESTAMPTZ,
  processing_time_ms INTEGER
);

CREATE INDEX idx_predictions_user_id ON predictions(user_id);
CREATE INDEX idx_predictions_status ON predictions(status);
CREATE INDEX idx_predictions_created_at ON predictions(created_at DESC);

-- ============================================================
-- TRANSACTIONS TABLE
-- ============================================================
CREATE TYPE transaction_type AS ENUM ('top_up', 'deduction', 'refund', 'admin_adjustment');

CREATE TABLE IF NOT EXISTS transactions (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
  prediction_id UUID REFERENCES predictions(id) ON DELETE SET NULL,
  type transaction_type NOT NULL,
  amount DECIMAL(10, 2) NOT NULL,
  balance_before DECIMAL(10, 2) NOT NULL,
  balance_after DECIMAL(10, 2) NOT NULL,
  description TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_transactions_user_id ON transactions(user_id);
CREATE INDEX idx_transactions_created_at ON transactions(created_at DESC);

-- ============================================================
-- HELPER FUNCTIONS
-- ============================================================

-- Top-up balance
CREATE OR REPLACE FUNCTION create_top_up_transaction(
  target_user_id UUID,
  top_up_amount DECIMAL
)
RETURNS UUID AS $$
DECLARE
  current_balance DECIMAL;
  new_balance DECIMAL;
  transaction_id UUID;
BEGIN
  SELECT COALESCE(balance, 0) INTO current_balance
  FROM profiles WHERE id = target_user_id;
  
  new_balance := current_balance + top_up_amount;
  
  UPDATE profiles SET balance = new_balance WHERE id = target_user_id;
  
  INSERT INTO transactions (user_id, type, amount, balance_before, balance_after, description)
  VALUES (target_user_id, 'top_up', top_up_amount, current_balance, new_balance, 'Balance top-up')
  RETURNING id INTO transaction_id;
  
  RETURN transaction_id;
END;
$$ LANGUAGE plpgsql;

-- Deduct balance
CREATE OR REPLACE FUNCTION create_deduction_transaction(
  target_user_id UUID,
  deduction_amount DECIMAL,
  target_prediction_id UUID,
  deduction_description TEXT
)
RETURNS UUID AS $$
DECLARE
  current_balance DECIMAL;
  new_balance DECIMAL;
  transaction_id UUID;
BEGIN
  SELECT COALESCE(balance, 0) INTO current_balance
  FROM profiles WHERE id = target_user_id;
  
  IF current_balance < deduction_amount THEN
    RAISE EXCEPTION 'Insufficient balance';
  END IF;
  
  new_balance := current_balance - deduction_amount;
  
  UPDATE profiles
  SET balance = new_balance,
      total_predictions = total_predictions + 1,
      total_spent = total_spent + deduction_amount
  WHERE id = target_user_id;
  
  INSERT INTO transactions 
    (user_id, prediction_id, type, amount, balance_before, balance_after, description)
  VALUES 
    (target_user_id, target_prediction_id, 'deduction', deduction_amount, 
     current_balance, new_balance, deduction_description)
  RETURNING id INTO transaction_id;
  
  RETURN transaction_id;
END;
$$ LANGUAGE plpgsql;

-- Create demo user
INSERT INTO profiles (email, full_name, balance) VALUES
  ('demo@nutrimarket.com', 'Demo User', 100.00)
ON CONFLICT (email) DO NOTHING;

-- Success message
DO $$
BEGIN
  RAISE NOTICE 'Database initialized successfully!';
END $$;
