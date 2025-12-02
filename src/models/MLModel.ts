import { BaseEntity } from './base';

/**
 * Типы ML моделей
 */
export enum ModelType {
  NUTRITION_RECOMMENDATION = 'nutrition_recommendation',
  MEAL_PLANNING = 'meal_planning',
  HEALTH_ANALYSIS = 'health_analysis'
}

/**
 * Статус ML модели
 */
export enum ModelStatus {
  ACTIVE = 'active',
  INACTIVE = 'inactive',
  MAINTENANCE = 'maintenance'
}

/**
 * Класс ML модели
 * Инкапсуляция: управление состоянием модели
 */
export class MLModel extends BaseEntity {
  private name: string;
  private description: string;
  private type: ModelType;
  private version: string;
  private status: ModelStatus;
  private costPerRequest: number;
  private endpoint: string;

  constructor(
    name: string,
    description: string,
    type: ModelType,
    version: string,
    costPerRequest: number,
    endpoint: string,
    id?: string
  ) {
    super(id);
    this.name = name;
    this.description = description;
    this.type = type;
    this.version = version;
    this.status = ModelStatus.ACTIVE;
    this.costPerRequest = costPerRequest;
    this.endpoint = endpoint;
  }

  // Геттеры
  public getName(): string {
    return this.name;
  }

  public getDescription(): string {
    return this.description;
  }

  public getType(): ModelType {
    return this.type;
  }

  public getVersion(): string {
    return this.version;
  }

  public getStatus(): ModelStatus {
    return this.status;
  }

  public getCostPerRequest(): number {
    return this.costPerRequest;
  }

  public getEndpoint(): string {
    return this.endpoint;
  }

  // Методы управления
  public setStatus(status: ModelStatus): void {
    this.status = status;
    this.updateTimestamp();
  }

  public updateCost(newCost: number): void {
    if (newCost < 0) {
      throw new Error('Cost cannot be negative');
    }
    this.costPerRequest = newCost;
    this.updateTimestamp();
  }

  public updateEndpoint(newEndpoint: string): void {
    this.endpoint = newEndpoint;
    this.updateTimestamp();
  }

  public isAvailable(): boolean {
    return this.status === ModelStatus.ACTIVE;
  }

  public validate(): boolean {
    return (
      this.name.length > 0 &&
      this.version.length > 0 &&
      this.costPerRequest >= 0 &&
      this.endpoint.length > 0
    );
  }

  public toJSON(): object {
    return {
      id: this.getId(),
      name: this.name,
      description: this.description,
      type: this.type,
      version: this.version,
      status: this.status,
      costPerRequest: this.costPerRequest,
      endpoint: this.endpoint,
      createdAt: this.getCreatedAt(),
      updatedAt: this.getUpdatedAt()
    };
  }
}
