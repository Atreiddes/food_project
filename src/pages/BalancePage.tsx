import { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { balanceApi, ApiError } from '../services/api';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../components/ui/card';
import { Link } from 'react-router-dom';
import { toast } from 'sonner';

interface Transaction {
  id: string;
  type: string;
  amount: number;
  status: string;
  description: string;
  created_at: string;
}

export default function BalancePage() {
  const { user, logout, updateBalance } = useAuth();
  const [amount, setAmount] = useState('');
  const [loading, setLoading] = useState(false);
  const [transactions, setTransactions] = useState<Transaction[]>([]);

  useEffect(() => {
    fetchTransactions();
  }, []);

  const fetchTransactions = async () => {
    try {
      const data = await balanceApi.getTransactions();
      setTransactions(data.transactions);
    } catch (error) {
      console.error('Error fetching transactions:', error);
    }
  };

  const handleAddBalance = async () => {
    if (!amount || parseFloat(amount) <= 0) {
      toast.error('Введите корректную сумму');
      return;
    }

    setLoading(true);

    try {
      const data = await balanceApi.addBalance(parseFloat(amount));
      updateBalance(Number(data.balance));
      toast.success(`Баланс пополнен на ${amount} кредитов`);
      setAmount('');
      fetchTransactions();
    } catch (error) {
      if (error instanceof ApiError) {
        toast.error(error.message);
      } else {
        toast.error('Ошибка пополнения баланса');
      }
    } finally {
      setLoading(false);
    }
  };

  const formatAmount = (transaction: Transaction) => {
    const isPositive = transaction.amount > 0;
    const absAmount = Math.abs(transaction.amount);
    return {
      text: `${isPositive ? '+' : '-'}${absAmount.toFixed(2)}`,
      isPositive,
    };
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-green-50 to-blue-50">
      <nav className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16 items-center">
            <h1 className="text-xl font-semibold">Управление балансом</h1>
            <div className="flex items-center gap-4">
              <Link to="/" className="text-sm hover:underline">
                Чат
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

      <div className="max-w-4xl mx-auto p-4 space-y-4">
        <Card>
          <CardHeader>
            <CardTitle>Текущий баланс</CardTitle>
            <CardDescription>Ваш баланс в условных кредитах</CardDescription>
          </CardHeader>
          <CardContent>
            <p className="text-4xl font-bold text-primary">
              {user?.balance?.toFixed(2)} кредитов
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Пополнить баланс</CardTitle>
            <CardDescription>Добавьте кредиты на ваш счет</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="flex gap-2">
              <Input
                type="number"
                placeholder="Сумма"
                value={amount}
                onChange={(e) => setAmount(e.target.value)}
                min="1"
                max="10000"
                disabled={loading}
              />
              <Button onClick={handleAddBalance} disabled={loading || !amount}>
                {loading ? 'Обработка...' : 'Пополнить'}
              </Button>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>История транзакций</CardTitle>
          </CardHeader>
          <CardContent>
            {transactions.length === 0 ? (
              <p className="text-gray-500 text-center py-4">Транзакций пока нет</p>
            ) : (
              <div className="space-y-3">
                {transactions.map((transaction) => {
                  const { text, isPositive } = formatAmount(transaction);
                  return (
                    <div
                      key={transaction.id}
                      className="flex justify-between items-center p-3 bg-gray-50 rounded-lg"
                    >
                      <div>
                        <p className="text-sm font-medium">{transaction.description}</p>
                        <p className="text-xs text-gray-500">
                          {new Date(transaction.created_at).toLocaleString('ru-RU')}
                        </p>
                      </div>
                      <div className="text-right">
                        <p className={`text-sm font-semibold ${
                          isPositive ? 'text-green-600' : 'text-red-600'
                        }`}>
                          {text}
                        </p>
                        <p className="text-xs text-gray-500">{transaction.status}</p>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
