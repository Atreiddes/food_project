import { BaseEntity } from './base';

/**
 * Типы транзакций
 */
export enum TransactionType {
  DEPOSIT = 'deposit',
  DEDUCTION = 'deduction',
  REFUND = 'refund',
  ADMIN_ADJUSTMENT = 'admin_adjustment'
}

/**
 * Статус транзакции
 */
export enum TransactionStatus {
  PENDING = 'pending',
  COMPLETED = 'completed',
  FAILED = 'failed',
  CANCELLED = 'cancelled'
}

/**
 * Класс транзакции
 * Инкапсуляция: управление финансовыми операциями
 */
export class Transaction extends BaseEntity {
  private userId: string;
  private type: TransactionType;
  private amount: number;
  private status: TransactionStatus;
  private description: string;
  private relatedPredictionId?: string;

  constructor(
    userId: string,
    type: TransactionType,
    amount: number,
    description: string,
    relatedPredictionId?: string,
    id?: string
  ) {
    super(id);
    this.userId = userId;
    this.type = type;
    this.amount = amount;
    this.status = TransactionStatus.PENDING;
    this.description = description;
    this.relatedPredictionId = relatedPredictionId;
  }

  // Геттеры
  public getUserId(): string {
    return this.userId;
  }

  public getType(): TransactionType {
    return this.type;
  }

  public getAmount(): number {
    return this.amount;
  }

  public getStatus(): TransactionStatus {
    return this.status;
  }

  public getDescription(): string {
    return this.description;
  }

  public getRelatedPredictionId(): string | undefined {
    return this.relatedPredictionId;
  }

  // Методы управления статусом
  public markAsCompleted(): void {
    this.status = TransactionStatus.COMPLETED;
    this.updateTimestamp();
  }

  public markAsFailed(): void {
    this.status = TransactionStatus.FAILED;
    this.updateTimestamp();
  }

  public cancel(): void {
    if (this.status === TransactionStatus.COMPLETED) {
      throw new Error('Cannot cancel completed transaction');
    }
    this.status = TransactionStatus.CANCELLED;
    this.updateTimestamp();
  }

  public isCompleted(): boolean {
    return this.status === TransactionStatus.COMPLETED;
  }

  public validate(): boolean {
    return (
      this.userId.length > 0 &&
      this.amount > 0 &&
      this.description.length > 0
    );
  }

  public toJSON(): object {
    return {
      id: this.getId(),
      userId: this.userId,
      type: this.type,
      amount: this.amount,
      status: this.status,
      description: this.description,
      relatedPredictionId: this.relatedPredictionId,
      createdAt: this.getCreatedAt(),
      updatedAt: this.getUpdatedAt()
    };
  }
}
