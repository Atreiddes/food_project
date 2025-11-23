// ML Service - модель данных
// Классы для работы с ML сервисом

// ============================================================================
// ENUMS
// ============================================================================

export enum UserRole {
  USER = 'user',
  ADMIN = 'admin'
}

export enum PredictionStatus {
  PENDING = 'pending',
  PROCESSING = 'processing',
  COMPLETED = 'completed',
  FAILED = 'failed'
}

export enum TransactionType {
  TOP_UP = 'top_up',
  DEDUCTION = 'deduction',
  REFUND = 'refund',
  ADMIN_ADJUSTMENT = 'admin_adjustment'
}

export enum ModelType {
  CLASSIFICATION = 'classification',
  REGRESSION = 'regression',
  RECOMMENDATION = 'recommendation',
  OPTIMIZATION = 'optimization'
}

// ============================================================================
// VALIDATION ERROR TYPES
// ============================================================================

export interface ValidationError {
  field: string;
  message: string;
  value?: any;
  code?: string;
}

export interface PredictionValidationError {
  row?: number;
  field: string;
  message: string;
  invalidValue?: any;
}

export class ValidationResult {
  constructor(
    public isValid: boolean,
    public errors: ValidationError[] = []
  ) { }

  addError(error: ValidationError): void {
    this.errors.push(error);
    this.isValid = false;
  }

  hasErrors(): boolean {
    return this.errors.length > 0;
  }

  getErrorMessages(): string[] {
    return this.errors.map(e => e.message);
  }
}

// Базовый класс для наследования

export abstract class BaseEntity {
  id?: string;
  created_at?: string;
  updated_at?: string;

  constructor(data?: Partial<BaseEntity>) {
    if (data) {
      Object.assign(this, data);
    }
  }

  isNew(): boolean {
    return !this.id;
  }

  getAge(): number {
    if (!this.created_at) return 0;
    return Date.now() - new Date(this.created_at).getTime();
  }
}

// Класс пользователя

export interface UserProfile {
  id: string;
  email: string;
  full_name?: string;
  username?: string;
  role?: UserRole;
  balance: number;
  total_predictions: number;
  total_spent: number;
  created_at: string;
  updated_at: string;
}

export class User extends BaseEntity {
  email: string;
  full_name?: string;
  username?: string;
  role: UserRole;
  private _balance: number;
  total_predictions: number;
  total_spent: number;

  constructor(data: Partial<UserProfile>) {
    super(data);
    this.email = data.email || '';
    this.full_name = data.full_name;
    this.username = data.username;
    this.role = data.role || UserRole.USER;
    this._balance = data.balance || 0;
    this.total_predictions = data.total_predictions || 0;
    this.total_spent = data.total_spent || 0;
  }

  // Методы для работы с балансом
  getBalance(): number {
    return this._balance;
  }

  hasSufficientBalance(amount: number): boolean {
    return this._balance >= amount;
  }

  canAffordPrediction(cost: number): boolean {
    return this.hasSufficientBalance(cost);
  }

  // TODO: добавить защиту, вызывать только из бэкенда
  addCredits(amount: number): void {
    if (amount < 0) {
      throw new Error('Cannot add negative credits');
    }
    this._balance += amount;
  }

  deductCredits(amount: number): void {
    if (amount < 0) {
      throw new Error('Cannot deduct negative credits');
    }
    if (!this.hasSufficientBalance(amount)) {
      throw new Error('Insufficient balance');
    }
    this._balance -= amount;
    this.total_spent += amount;
    this.total_predictions += 1;
  }

  isAdmin(): boolean {
    return this.role === UserRole.ADMIN;
  }

  toJSON(): UserProfile {
    return {
      id: this.id!,
      email: this.email,
      full_name: this.full_name,
      username: this.username,
      role: this.role,
      balance: this._balance,
      total_predictions: this.total_predictions,
      total_spent: this.total_spent,
      created_at: this.created_at!,
      updated_at: this.updated_at!
    };
  }
}

// ============================================================================
// ML MODEL CLASS (with input validation)
// ============================================================================

export interface MLModelData {
  id: string;
  name: string;
  description?: string;
  version: string;
  cost_per_prediction: number;
  input_schema: Record<string, any>;
  output_schema: Record<string, any>;
  is_active: boolean;
  model_type: ModelType;
  endpoint_url?: string;
  created_at: string;
  updated_at: string;
}

export class MLModel extends BaseEntity {
  name: string;
  description?: string;
  version: string;
  cost_per_prediction: number;
  input_schema: Record<string, any>;
  output_schema: Record<string, any>;
  is_active: boolean;
  model_type: ModelType;
  endpoint_url?: string;

  constructor(data: Partial<MLModelData>) {
    super(data);
    this.name = data.name || '';
    this.description = data.description;
    this.version = data.version || '1.0';
    this.cost_per_prediction = data.cost_per_prediction || 0;
    this.input_schema = data.input_schema || {};
    this.output_schema = data.output_schema || {};
    this.is_active = data.is_active ?? true;
    this.model_type = data.model_type || ModelType.CLASSIFICATION;
    this.endpoint_url = data.endpoint_url;
  }

  getCost(): number {
    return this.cost_per_prediction;
  }

  isAvailable(): boolean {
    return this.is_active;
  }

  validateInput(inputData: any): ValidationResult {
    const result = new ValidationResult(true);

    if (!this.input_schema || !this.input_schema.properties) {
      return result;
    }

    const { required = [], properties = {} } = this.input_schema;

    // Check required fields
    for (const field of required) {
      if (!(field in inputData)) {
        result.addError({
          field,
          message: `Required field '${field}' is missing`,
          code: 'REQUIRED_FIELD_MISSING'
        });
      }
    }

    // Validate field types
    for (const [field, schema] of Object.entries(properties) as [string, any][]) {
      if (field in inputData) {
        const value = inputData[field];
        const expectedType = schema.type;

        if (!this.validateType(value, expectedType)) {
          result.addError({
            field,
            message: `Field '${field}' must be of type ${expectedType}`,
            value,
            code: 'INVALID_TYPE'
          });
        }
      }
    }

    return result;
  }

  private validateType(value: any, expectedType: string): boolean {
    switch (expectedType) {
      case 'string':
        return typeof value === 'string';
      case 'number':
      case 'integer':
        return typeof value === 'number';
      case 'boolean':
        return typeof value === 'boolean';
      case 'array':
        return Array.isArray(value);
      case 'object':
        return typeof value === 'object' && !Array.isArray(value);
      default:
        return true;
    }
  }

  getInputFields(): string[] {
    return Object.keys(this.input_schema.properties || {});
  }

  getRequiredFields(): string[] {
    return this.input_schema.required || [];
  }
}

// ============================================================================
// PREDICTION CLASS (with status management)
// ============================================================================

export interface PredictionData {
  id: string;
  user_id: string;
  model_id: string;
  input_data: Record<string, any>;
  output_data?: Record<string, any>;
  status: PredictionStatus;
  error_message?: string;
  validation_errors?: PredictionValidationError[];
  cost: number;
  created_at: string;
  started_at?: string;
  completed_at?: string;
  processing_time_ms?: number;
  model_version?: string;
}

export class Prediction extends BaseEntity {
  user_id: string;
  model_id: string;
  input_data: Record<string, any>;
  output_data?: Record<string, any>;
  status: PredictionStatus;
  error_message?: string;
  validation_errors?: PredictionValidationError[];
  cost: number;
  started_at?: string;
  completed_at?: string;
  processing_time_ms?: number;
  model_version?: string;

  constructor(data: Partial<PredictionData>) {
    super(data);
    this.user_id = data.user_id || '';
    this.model_id = data.model_id || '';
    this.input_data = data.input_data || {};
    this.output_data = data.output_data;
    this.status = data.status || PredictionStatus.PENDING;
    this.error_message = data.error_message;
    this.validation_errors = data.validation_errors;
    this.cost = data.cost || 0;
    this.started_at = data.started_at;
    this.completed_at = data.completed_at;
    this.processing_time_ms = data.processing_time_ms;
    this.model_version = data.model_version;
  }

  isPending(): boolean {
    return this.status === PredictionStatus.PENDING;
  }

  isProcessing(): boolean {
    return this.status === PredictionStatus.PROCESSING;
  }

  isCompleted(): boolean {
    return this.status === PredictionStatus.COMPLETED;
  }

  isFailed(): boolean {
    return this.status === PredictionStatus.FAILED;
  }

  isFinished(): boolean {
    return this.isCompleted() || this.isFailed();
  }

  getStatusColor(): string {
    switch (this.status) {
      case PredictionStatus.PENDING:
        return 'yellow';
      case PredictionStatus.PROCESSING:
        return 'blue';
      case PredictionStatus.COMPLETED:
        return 'green';
      case PredictionStatus.FAILED:
        return 'red';
      default:
        return 'gray';
    }
  }

  getProcessingTime(): number | null {
    if (!this.processing_time_ms) return null;
    return this.processing_time_ms;
  }

  getProcessingTimeSeconds(): number | null {
    const ms = this.getProcessingTime();
    return ms ? ms / 1000 : null;
  }

  hasValidationErrors(): boolean {
    return !!this.validation_errors && this.validation_errors.length > 0;
  }
}

// ============================================================================
// TRANSACTION CLASS (for audit trail)
// ============================================================================

export interface TransactionData {
  id: string;
  user_id: string;
  prediction_id?: string;
  type: TransactionType;
  amount: number;
  balance_before: number;
  balance_after: number;
  description?: string;
  metadata?: Record<string, any>;
  created_by?: string;
  created_at: string;
}

export class Transaction extends BaseEntity {
  user_id: string;
  prediction_id?: string;
  type: TransactionType;
  amount: number;
  balance_before: number;
  balance_after: number;
  description?: string;
  metadata?: Record<string, any>;
  created_by?: string;

  constructor(data: Partial<TransactionData>) {
    super(data);
    this.user_id = data.user_id || '';
    this.prediction_id = data.prediction_id;
    this.type = data.type || TransactionType.DEDUCTION;
    this.amount = data.amount || 0;
    this.balance_before = data.balance_before || 0;
    this.balance_after = data.balance_after || 0;
    this.description = data.description;
    this.metadata = data.metadata;
    this.created_by = data.created_by;
  }

  isTopUp(): boolean {
    return this.type === TransactionType.TOP_UP;
  }

  isDeduction(): boolean {
    return this.type === TransactionType.DEDUCTION;
  }

  isRefund(): boolean {
    return this.type === TransactionType.REFUND;
  }

  getBalanceChange(): number {
    return this.balance_after - this.balance_before;
  }

  getTypeColor(): string {
    switch (this.type) {
      case TransactionType.TOP_UP:
        return 'green';
      case TransactionType.DEDUCTION:
        return 'red';
      case TransactionType.REFUND:
        return 'blue';
      case TransactionType.ADMIN_ADJUSTMENT:
        return 'purple';
      default:
        return 'gray';
    }
  }

  getTypeLabel(): string {
    switch (this.type) {
      case TransactionType.TOP_UP:
        return 'Top Up';
      case TransactionType.DEDUCTION:
        return 'Payment';
      case TransactionType.REFUND:
        return 'Refund';
      case TransactionType.ADMIN_ADJUSTMENT:
        return 'Admin Adjustment';
      default:
        return 'Unknown';
    }
  }
}

// ============================================================================
// HELPER TYPES
// ============================================================================

export interface CreatePredictionRequest {
  model_id: string;
  input_data: Record<string, any>;
}

export interface PredictionWithModel extends PredictionData {
  model: MLModelData;
}

export interface TransactionWithUser extends TransactionData {
  user: {
    email: string;
    full_name?: string;
  };
}
