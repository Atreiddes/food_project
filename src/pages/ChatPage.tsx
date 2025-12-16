import { useState, useRef, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { chatApi, ApiError } from '../services/api';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Card } from '../components/ui/card';
import { toast } from 'sonner';
import { Link } from 'react-router-dom';

interface Message {
  role: 'user' | 'assistant';
  content: string;
}

export default function ChatPage() {
  const { user, logout, refreshBalance } = useAuth();
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [pendingPredictionId, setPendingPredictionId] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    if (pendingPredictionId) {
      const interval = setInterval(async () => {
        await checkPredictionStatus(pendingPredictionId);
      }, 2000);

      return () => clearInterval(interval);
    }
  }, [pendingPredictionId]);

  const checkPredictionStatus = async (predictionId: string) => {
    try {
      const data = await chatApi.getStatus(predictionId);

      if (data.status === 'completed' && data.result?.response) {
        setMessages(prev => [
          ...prev.filter(m => m.content !== 'Обработка запроса...'),
          { role: 'assistant', content: data.result.response }
        ]);
        setPendingPredictionId(null);
        setLoading(false);
        await refreshBalance();
      } else if (data.status === 'failed') {
        setMessages(prev => prev.filter(m => m.content !== 'Обработка запроса...'));
        toast.error(data.error_message || 'Ошибка обработки запроса');
        setPendingPredictionId(null);
        setLoading(false);
      }
    } catch (error) {
      console.error('Error checking prediction:', error);
    }
  };

  const handleSend = async () => {
    if (!input.trim() || loading) return;

    const userMessage = input.trim();
    setInput('');
    setMessages(prev => [...prev, { role: 'user', content: userMessage }]);
    setLoading(true);

    try {
      const conversationHistory = messages.map(m => ({
        role: m.role,
        content: m.content,
      }));

      const data = await chatApi.sendMessage({
        message: userMessage,
        conversation_history: conversationHistory,
      });

      setMessages(prev => [...prev, { role: 'assistant', content: 'Обработка запроса...' }]);
      setPendingPredictionId(data.id);

    } catch (error) {
      if (error instanceof ApiError) {
        if (error.status === 402) {
          toast.error('Недостаточно средств на балансе');
        } else {
          toast.error(error.message);
        }
      } else {
        toast.error('Ошибка отправки сообщения');
      }
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-green-50 to-blue-50">
      <nav className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16 items-center">
            <h1 className="text-xl font-semibold">ML Сервис Питания</h1>
            <div className="flex items-center gap-4">
              <Link to="/balance" className="text-sm hover:underline">
                Баланс: {user?.balance?.toFixed(2)} кредитов
              </Link>
              <Link to="/history" className="text-sm hover:underline">
                История
              </Link>
              <Button variant="ghost" size="sm" onClick={logout}>
                Выход
              </Button>
            </div>
          </div>
        </div>
      </nav>

      <div className="max-w-4xl mx-auto p-4 h-[calc(100vh-4rem)] flex flex-col">
        <Card className="flex-1 flex flex-col mb-4">
          <div className="flex-1 overflow-y-auto p-6 space-y-4">
            {messages.length === 0 && (
              <div className="text-center text-gray-500 mt-8">
                <p className="text-lg font-medium">Добро пожаловать!</p>
                <p className="text-sm mt-2">Задайте вопрос о правильном питании</p>
              </div>
            )}
            {messages.map((message, index) => (
              <div
                key={index}
                className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                <div
                  className={`max-w-[80%] rounded-lg px-4 py-2 ${
                    message.role === 'user'
                      ? 'bg-primary text-primary-foreground'
                      : 'bg-muted'
                  }`}
                >
                  <p className="text-sm whitespace-pre-wrap">{message.content}</p>
                </div>
              </div>
            ))}
            <div ref={messagesEndRef} />
          </div>

          <div className="border-t p-4">
            <div className="flex gap-2">
              <Input
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && handleSend()}
                placeholder="Напишите ваш вопрос..."
                disabled={loading}
              />
              <Button onClick={handleSend} disabled={loading || !input.trim()}>
                Отправить
              </Button>
            </div>
          </div>
        </Card>
      </div>
    </div>
  );
}
