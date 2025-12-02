/**
 * Базовая сущность с общими полями для всех моделей
 * Применение принципа DRY и наследования
 */
export abstract class BaseEntity {
  protected id: string;
  protected createdAt: Date;
  protected updatedAt: Date;

  constructor(id?: string) {
    this.id = id || this.generateId();
    this.createdAt = new Date();
    this.updatedAt = new Date();
  }

  public getId(): string {
    return this.id;
  }

  public getCreatedAt(): Date {
    return this.createdAt;
  }

  public getUpdatedAt(): Date {
    return this.updatedAt;
  }

  protected updateTimestamp(): void {
    this.updatedAt = new Date();
  }

  private generateId(): string {
    return `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
  }

  public abstract validate(): boolean;
}
