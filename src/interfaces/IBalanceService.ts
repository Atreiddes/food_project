import { Transaction, TransactionType } from '../models/Transaction';

/**
 * Интерфейс сервиса управления балансом
 * Принцип SOLID: Single Responsibility - отдельный сервис для управления балансом
 */
export interface IBalanceService {
  addBalance(userId: string, amount: number, description: string): Promise<Transaction>;
  deductBalance(userId: string, amount: number, description: string, predictionId?: string): Promise<Transaction>;
  refundBalance(userId: string, amount: number, description: string, predictionId?: string): Promise<Transaction>;
  getBalance(userId: string): Promise<number>;
  hasPositiveBalance(userId: string): Promise<boolean>;
  getTransactionHistory(userId: string): Promise<Transaction[]>;
  getAllTransactions(): Promise<Transaction[]>;
}
