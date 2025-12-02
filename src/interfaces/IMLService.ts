import { MLModel, ModelType } from '../models/MLModel';
import { Prediction, PredictionInput } from '../models/Prediction';

/**
 * Интерфейс ML сервиса
 * Принцип SOLID: Dependency Inversion
 */
export interface IMLService {
  getModelById(id: string): Promise<MLModel | null>;
  getModelsByType(type: ModelType): Promise<MLModel[]>;
  getAvailableModels(): Promise<MLModel[]>;
  createPrediction(userId: string, modelId: string, input: PredictionInput): Promise<Prediction>;
  getPredictionById(id: string): Promise<Prediction | null>;
  getUserPredictions(userId: string): Promise<Prediction[]>;
}
