import { BaseEntity } from './base';

/**
 * Статус предсказания
 */
export enum PredictionStatus {
  PENDING = 'pending',
  PROCESSING = 'processing',
  COMPLETED = 'completed',
  FAILED = 'failed',
  VALIDATION_ERROR = 'validation_error'
}

/**
 * Интерфейс для входных данных
 */
export interface PredictionInput {
  [key: string]: any;
}

/**
 * Интерфейс для результата предсказания
 */
export interface PredictionResult {
  recommendation: string;
  confidence?: number;
  metadata?: {
    [key: string]: any;
  };
}

/**
 * Интерфейс для ошибок валидации
 */
export interface ValidationError {
  field: string;
  message: string;
  invalidValue: any;
}

/**
 * Класс предсказания (история запросов к ML сервису)
 * Инкапсуляция: управление жизненным циклом предсказания
 */
export class Prediction extends BaseEntity {
  private userId: string;
  private modelId: string;
  private inputData: PredictionInput;
  private result?: PredictionResult;
  private status: PredictionStatus;
  private costCharged: number;
  private validationErrors: ValidationError[];
  private errorMessage?: string;

  constructor(
    userId: string,
    modelId: string,
    inputData: PredictionInput,
    costCharged: number,
    id?: string
  ) {
    super(id);
    this.userId = userId;
    this.modelId = modelId;
    this.inputData = inputData;
    this.status = PredictionStatus.PENDING;
    this.costCharged = costCharged;
    this.validationErrors = [];
  }

  // Геттеры
  public getUserId(): string {
    return this.userId;
  }

  public getModelId(): string {
    return this.modelId;
  }

  public getInputData(): PredictionInput {
    return { ...this.inputData };
  }

  public getResult(): PredictionResult | undefined {
    return this.result ? { ...this.result } : undefined;
  }

  public getStatus(): PredictionStatus {
    return this.status;
  }

  public getCostCharged(): number {
    return this.costCharged;
  }

  public getValidationErrors(): ValidationError[] {
    return [...this.validationErrors];
  }

  public getErrorMessage(): string | undefined {
    return this.errorMessage;
  }

  // Методы управления статусом
  public markAsProcessing(): void {
    this.status = PredictionStatus.PROCESSING;
    this.updateTimestamp();
  }

  public setResult(result: PredictionResult): void {
    this.result = result;
    this.status = PredictionStatus.COMPLETED;
    this.updateTimestamp();
  }

  public setValidationErrors(errors: ValidationError[]): void {
    this.validationErrors = errors;
    this.status = PredictionStatus.VALIDATION_ERROR;
    this.updateTimestamp();
  }

  public fail(errorMessage: string): void {
    this.errorMessage = errorMessage;
    this.status = PredictionStatus.FAILED;
    this.updateTimestamp();
  }

  public hasValidationErrors(): boolean {
    return this.validationErrors.length > 0;
  }

  public isCompleted(): boolean {
    return this.status === PredictionStatus.COMPLETED;
  }

  public validate(): boolean {
    return (
      this.userId.length > 0 &&
      this.modelId.length > 0 &&
      this.inputData !== null &&
      this.costCharged >= 0
    );
  }

  public toJSON(): object {
    return {
      id: this.getId(),
      userId: this.userId,
      modelId: this.modelId,
      inputData: this.inputData,
      result: this.result,
      status: this.status,
      costCharged: this.costCharged,
      validationErrors: this.validationErrors,
      errorMessage: this.errorMessage,
      createdAt: this.getCreatedAt(),
      updatedAt: this.getUpdatedAt()
    };
  }
}
