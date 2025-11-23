import { BaseEntity } from '../models/base';

/**
 * Интерфейс репозитория (паттерн Repository)
 * Принцип SOLID: Dependency Inversion - абстракция для работы с БД
 * Полиморфизм: один интерфейс для разных типов сущностей
 */
export interface IRepository<T extends BaseEntity> {
  create(entity: T): Promise<T>;
  findById(id: string): Promise<T | null>;
  findAll(): Promise<T[]>;
  update(entity: T): Promise<T>;
  delete(id: string): Promise<boolean>;
}

/**
 * Расширенный интерфейс репозитория пользователей
 */
export interface IUserRepository<T extends BaseEntity> extends IRepository<T> {
  findByEmail(email: string): Promise<T | null>;
}

/**
 * Расширенный интерфейс репозитория транзакций
 */
export interface ITransactionRepository<T extends BaseEntity> extends IRepository<T> {
  findByUserId(userId: string): Promise<T[]>;
}

/**
 * Расширенный интерфейс репозитория предсказаний
 */
export interface IPredictionRepository<T extends BaseEntity> extends IRepository<T> {
  findByUserId(userId: string): Promise<T[]>;
  findByModelId(modelId: string): Promise<T[]>;
}
