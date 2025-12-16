import { useEffect, useState } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { historyApi, HistoryItem } from '../services/api';
import { Button } from '../components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Link } from 'react-router-dom';

interface Prediction {
  id: string;
  userMessage: string;
  recommendation: string | null;
  status: string;
  cost: number;
  createdAt: string;
}

function mapHistoryItem(item: HistoryItem): Prediction {
  return {
    id: item.id,
    userMessage: item.input_data?.message || '',
    recommendation: item.result?.response || null,
    status: item.status,
    cost: item.cost_charged,
    createdAt: item.created_at,
  };
}

export default function HistoryPage() {
  const { user, logout } = useAuth();
  const [predictions, setPredictions] = useState<Prediction[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchHistory();
  }, []);

  const fetchHistory = async () => {
    try {
      const data = await historyApi.getHistory();
      const mapped = data.predictions.map(mapHistoryItem);
      setPredictions(mapped);
    } catch (error) {
      console.error('Error fetching history:', error);
    } finally {
      setLoading(false);
    }
  };

  const getStatusLabel = (status: string) => {
    switch (status) {
      case 'completed':
        return 'Завершено';
      case 'failed':
        return 'Ошибка';
      case 'pending':
        return 'Ожидание';
      case 'processing':
        return 'Обработка';
      default:
        return status;
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-green-50 to-blue-50">
      <nav className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16 items-center">
            <h1 className="text-xl font-semibold">История запросов</h1>
            <div className="flex items-center gap-4">
              <Link to="/" className="text-sm hover:underline">
                Чат
              </Link>
              <Link to="/balance" className="text-sm hover:underline">
                Баланс: {user?.balance?.toFixed(2)} кредитов
              </Link>
              <Button variant="ghost" size="sm" onClick={logout}>
                Выход
              </Button>
            </div>
          </div>
        </div>
      </nav>

      <div className="max-w-4xl mx-auto p-4">
        {loading ? (
          <div className="text-center py-8">Загрузка...</div>
        ) : predictions.length === 0 ? (
          <Card>
            <CardContent className="p-8 text-center text-gray-500">
              <p>История запросов пуста</p>
              <Link to="/" className="text-primary hover:underline mt-2 inline-block">
                Перейти к чату
              </Link>
            </CardContent>
          </Card>
        ) : (
          <div className="space-y-4">
            {predictions.map((prediction) => (
              <Card key={prediction.id}>
                <CardHeader>
                  <div className="flex justify-between items-start">
                    <CardTitle className="text-sm font-normal text-gray-500">
                      {new Date(prediction.createdAt).toLocaleString('ru-RU')}
                    </CardTitle>
                    <div className="flex items-center gap-2">
                      <span className={`text-xs px-2 py-1 rounded ${
                        prediction.status === 'completed' ? 'bg-green-100 text-green-800' :
                        prediction.status === 'failed' ? 'bg-red-100 text-red-800' :
                        'bg-yellow-100 text-yellow-800'
                      }`}>
                        {getStatusLabel(prediction.status)}
                      </span>
                      <span className="text-xs text-gray-500">
                        {prediction.cost.toFixed(2)} кредитов
                      </span>
                    </div>
                  </div>
                </CardHeader>
                <CardContent className="space-y-3">
                  <div>
                    <p className="text-xs text-gray-500 mb-1">Ваш запрос:</p>
                    <p className="text-sm">{prediction.userMessage}</p>
                  </div>
                  {prediction.recommendation && (
                    <div>
                      <p className="text-xs text-gray-500 mb-1">Рекомендация:</p>
                      <p className="text-sm whitespace-pre-wrap">{prediction.recommendation}</p>
                    </div>
                  )}
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
