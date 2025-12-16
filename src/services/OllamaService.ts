/**
 * Сервис для работы с Ollama ML моделью
 * ВАЖНО: Используется только термин "ML" (Machine Learning), без упоминаний AI
 */

export interface OllamaMessage {
  role: 'user' | 'assistant' | 'system';
  content: string;
}

export interface OllamaResponse {
  model: string;
  created_at: string;
  message: {
    role: string;
    content: string;
  };
  done: boolean;
}

export class OllamaService {
  private baseUrl: string;
  private model: string;

  constructor(baseUrl: string = 'http://localhost:11434', model: string = 'mistral') {
    this.baseUrl = baseUrl;
    this.model = model;
  }

  /**
   * Отправка запроса к ML модели для получения рекомендаций по питанию
   */
  async generateNutritionRecommendation(
    userMessage: string,
    conversationHistory: OllamaMessage[] = []
  ): Promise<string> {
    const systemPrompt: OllamaMessage = {
      role: 'system',
      content: `Вы - эксперт по правильному питанию и здоровому образу жизни.
Ваша задача - давать полезные, научно обоснованные рекомендации по питанию.
Отвечайте на русском языке, кратко и по существу.
Учитывайте индивидуальные особенности пользователя.`
    };

    const messages: OllamaMessage[] = [
      systemPrompt,
      ...conversationHistory,
      { role: 'user', content: userMessage }
    ];

    try {
      const response = await fetch(`${this.baseUrl}/api/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          model: this.model,
          messages: messages,
          stream: false,
        }),
      });

      if (!response.ok) {
        throw new Error(`Ollama API error: ${response.statusText}`);
      }

      const data: OllamaResponse = await response.json();
      return data.message.content;
    } catch (error) {
      console.error('Error calling Ollama:', error);
      throw new Error('Не удалось получить рекомендацию от ML сервиса');
    }
  }

  /**
   * Проверка доступности ML сервиса
   */
  async isAvailable(): Promise<boolean> {
    try {
      const response = await fetch(`${this.baseUrl}/api/tags`);
      return response.ok;
    } catch {
      return false;
    }
  }

  /**
   * Получение списка доступных моделей
   */
  async getAvailableModels(): Promise<string[]> {
    try {
      const response = await fetch(`${this.baseUrl}/api/tags`);
      if (!response.ok) return [];

      const data = await response.json();
      return data.models?.map((m: any) => m.name) || [];
    } catch {
      return [];
    }
  }
}

// Экспорт singleton instance
export const ollamaService = new OllamaService(
  import.meta.env.VITE_OLLAMA_URL || 'http://localhost:11434',
  import.meta.env.VITE_OLLAMA_MODEL || 'mistral'
);
