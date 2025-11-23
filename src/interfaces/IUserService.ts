import { User, UserRole } from '../models/User';

/**
 * Интерфейс сервиса пользователей
 * Принцип SOLID: Dependency Inversion - зависимость от абстракции
 * Принцип SOLID: Interface Segregation - специфичный интерфейс
 */
export interface IUserService {
  createUser(email: string, password: string, role?: UserRole): Promise<User>;
  getUserById(id: string): Promise<User | null>;
  getUserByEmail(email: string): Promise<User | null>;
  updateUser(user: User): Promise<User>;
  deleteUser(id: string): Promise<boolean>;
  authenticateUser(email: string, password: string): Promise<User | null>;
  getAllUsers(): Promise<User[]>;
}
