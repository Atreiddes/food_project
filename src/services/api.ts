const API_URL = import.meta.env.VITE_API_URL || '';

class ApiError extends Error {
  status: number;

  constructor(message: string, status: number) {
    super(message);
    this.status = status;
    this.name = 'ApiError';
  }
}

function getAuthHeaders(): HeadersInit {
  const token = localStorage.getItem('token');
  const headers: HeadersInit = {
    'Content-Type': 'application/json',
  };

  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  return headers;
}

async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    const message = errorData.detail || errorData.error || 'Request failed';
    throw new ApiError(message, response.status);
  }
  return response.json();
}

// Auth types
export interface UserData {
  id: string;
  email: string;
  role: string;
}

export interface LoginResponse {
  token: string;
  user: UserData;
}

export interface GuestResponse {
  token: string;
  user_id: string;
  message: string;
}

export interface CurrentUserResponse {
  id: string;
  email: string;
  role: string;
  is_active: boolean;
  balance: string | number | null;
}

// Prediction types
export interface PredictionResponse {
  id: string;
  user_id: string;
  model_id: string;
  status: string;
  cost_charged: string | number;
  result: { response?: string } | null;
  error_message: string | null;
  created_at: string;
}

export interface PredictionCreateRequest {
  message: string;
  conversation_history?: Array<{ role: string; content: string }>;
}

// Balance types
export interface BalanceResponse {
  balance: string | number;
}

export interface TransactionData {
  id: string;
  type: string;
  amount: number;
  status: string;
  description: string;
  created_at: string;
}

export interface TransactionsResponse {
  transactions: TransactionData[];
}

// History types
export interface HistoryItem {
  id: string;
  status: string;
  cost_charged: number;
  created_at: string;
  input_data: { message?: string; conversation_history?: unknown[] };
  result: { response?: string } | null;
}

export interface HistoryResponse {
  predictions: HistoryItem[];
}

// Auth API
export const authApi = {
  async login(email: string, password: string): Promise<LoginResponse> {
    const response = await fetch(`${API_URL}/api/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password }),
    });
    return handleResponse<LoginResponse>(response);
  },

  async register(email: string, password: string): Promise<LoginResponse> {
    const response = await fetch(`${API_URL}/api/auth/register`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password }),
    });
    return handleResponse<LoginResponse>(response);
  },

  async loginAsGuest(): Promise<GuestResponse> {
    const response = await fetch(`${API_URL}/api/auth/guest`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
    });
    return handleResponse<GuestResponse>(response);
  },

  async getCurrentUser(): Promise<CurrentUserResponse> {
    const response = await fetch(`${API_URL}/api/auth/me`, {
      headers: getAuthHeaders(),
    });
    return handleResponse<CurrentUserResponse>(response);
  },
};

// Chat/Predictions API
export const chatApi = {
  async sendMessage(data: PredictionCreateRequest): Promise<PredictionResponse> {
    const response = await fetch(`${API_URL}/api/chat/message`, {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify(data),
    });
    return handleResponse<PredictionResponse>(response);
  },

  async getStatus(predictionId: string): Promise<PredictionResponse> {
    const response = await fetch(`${API_URL}/api/chat/status/${predictionId}`, {
      headers: getAuthHeaders(),
    });
    return handleResponse<PredictionResponse>(response);
  },
};

// Balance API
export const balanceApi = {
  async getBalance(): Promise<BalanceResponse> {
    const response = await fetch(`${API_URL}/api/balance/`, {
      headers: getAuthHeaders(),
    });
    return handleResponse<BalanceResponse>(response);
  },

  async addBalance(amount: number): Promise<BalanceResponse> {
    const response = await fetch(`${API_URL}/api/balance/add`, {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify({ amount }),
    });
    return handleResponse<BalanceResponse>(response);
  },

  async getTransactions(): Promise<TransactionsResponse> {
    const response = await fetch(`${API_URL}/api/balance/transactions`, {
      headers: getAuthHeaders(),
    });
    return handleResponse<TransactionsResponse>(response);
  },
};

// History API
export const historyApi = {
  async getHistory(): Promise<HistoryResponse> {
    const response = await fetch(`${API_URL}/api/history/`, {
      headers: getAuthHeaders(),
    });
    return handleResponse<HistoryResponse>(response);
  },

  async getPrediction(id: string): Promise<PredictionResponse> {
    const response = await fetch(`${API_URL}/api/history/${id}`, {
      headers: getAuthHeaders(),
    });
    return handleResponse<PredictionResponse>(response);
  },
};

export { ApiError };
