import { ValidationError } from '../models/Prediction';

/**
 * Интерфейс валидатора данных
 * Принцип SOLID: Single Responsibility - отдельный компонент для валидации
 */
export interface IValidator<T> {
  validate(data: T): ValidationError[];
  isValid(data: T): boolean;
}

/**
 * Интерфейс валидатора входных данных для ML модели
 */
export interface IMLInputValidator extends IValidator<any> {
  getExpectedSchema(): object;
}
