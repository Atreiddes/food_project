import { BaseEntity } from './base';

/**
 * Перечисление ролей пользователя
 * Применение принципа SOLID - Single Responsibility
 */
export enum UserRole {
  USER = 'user',
  ADMIN = 'admin'
}

/**
 * Класс пользователя системы
 * Инкапсуляция: приватные поля с геттерами/сеттерами
 */
export class User extends BaseEntity {
  private email: string;
  private passwordHash: string;
  private role: UserRole;
  private balance: number;
  private isActive: boolean;

  constructor(
    email: string,
    passwordHash: string,
    role: UserRole = UserRole.USER,
    balance: number = 0,
    id?: string
  ) {
    super(id);
    this.email = email;
    this.passwordHash = passwordHash;
    this.role = role;
    this.balance = balance;
    this.isActive = true;
  }

  // Геттеры (инкапсуляция)
  public getEmail(): string {
    return this.email;
  }

  public getRole(): UserRole {
    return this.role;
  }

  public getBalance(): number {
    return this.balance;
  }

  public getIsActive(): boolean {
    return this.isActive;
  }

  public getPasswordHash(): string {
    return this.passwordHash;
  }

  // Методы управления балансом
  public addBalance(amount: number): void {
    if (amount <= 0) {
      throw new Error('Amount must be positive');
    }
    this.balance += amount;
    this.updateTimestamp();
  }

  public deductBalance(amount: number): boolean {
    if (amount <= 0) {
      throw new Error('Amount must be positive');
    }
    if (this.balance < amount) {
      return false;
    }
    this.balance -= amount;
    this.updateTimestamp();
    return true;
  }

  public hasPositiveBalance(): boolean {
    return this.balance > 0;
  }

  // Методы управления статусом
  public deactivate(): void {
    this.isActive = false;
    this.updateTimestamp();
  }

  public activate(): void {
    this.isActive = true;
    this.updateTimestamp();
  }

  public isAdmin(): boolean {
    return this.role === UserRole.ADMIN;
  }

  public setRole(role: UserRole): void {
    this.role = role;
    this.updateTimestamp();
  }

  public changePassword(newPasswordHash: string): void {
    this.passwordHash = newPasswordHash;
    this.updateTimestamp();
  }

  public validate(): boolean {
    return (
      this.email.length > 0 &&
      this.email.includes('@') &&
      this.passwordHash.length > 0 &&
      this.balance >= 0
    );
  }

  // Для сериализации (без пароля)
  public toJSON(): object {
    return {
      id: this.getId(),
      email: this.email,
      role: this.role,
      balance: this.balance,
      isActive: this.isActive,
      createdAt: this.getCreatedAt(),
      updatedAt: this.getUpdatedAt()
    };
  }
}
