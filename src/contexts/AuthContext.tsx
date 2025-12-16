import React, { createContext, useContext, useState, useEffect } from 'react';
import { authApi, balanceApi } from '../services/api';

interface User {
  id: string;
  email: string;
  role: string;
  balance: number;
}

interface AuthContextType {
  user: User | null;
  token: string | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string) => Promise<void>;
  loginAsGuest: () => Promise<void>;
  logout: () => void;
  updateBalance: (newBalance: number) => void;
  refreshBalance: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(localStorage.getItem('token'));
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (token) {
      fetchCurrentUser();
    } else {
      setLoading(false);
    }
  }, [token]);

  const fetchCurrentUser = async () => {
    try {
      const data = await authApi.getCurrentUser();
      const balance = data.balance !== null ? Number(data.balance) : 0;

      setUser({
        id: data.id,
        email: data.email,
        role: data.role,
        balance: balance,
      });
    } catch (error) {
      console.error('Failed to fetch user:', error);
      logout();
    } finally {
      setLoading(false);
    }
  };

  const login = async (email: string, password: string) => {
    const data = await authApi.login(email, password);

    localStorage.setItem('token', data.token);
    setToken(data.token);

    const userData = await authApi.getCurrentUser();
    setUser({
      id: userData.id,
      email: userData.email,
      role: userData.role,
      balance: userData.balance !== null ? Number(userData.balance) : 0,
    });
  };

  const register = async (email: string, password: string) => {
    const data = await authApi.register(email, password);

    localStorage.setItem('token', data.token);
    setToken(data.token);

    const userData = await authApi.getCurrentUser();
    setUser({
      id: userData.id,
      email: userData.email,
      role: userData.role,
      balance: userData.balance !== null ? Number(userData.balance) : 0,
    });
  };

  const loginAsGuest = async () => {
    const data = await authApi.loginAsGuest();

    localStorage.setItem('token', data.token);
    setToken(data.token);

    const userData = await authApi.getCurrentUser();
    setUser({
      id: userData.id,
      email: userData.email,
      role: userData.role,
      balance: userData.balance !== null ? Number(userData.balance) : 0,
    });
  };

  const logout = () => {
    setUser(null);
    setToken(null);
    localStorage.removeItem('token');
  };

  const updateBalance = (newBalance: number) => {
    if (user) {
      setUser({ ...user, balance: newBalance });
    }
  };

  const refreshBalance = async () => {
    try {
      const data = await balanceApi.getBalance();
      const balance = Number(data.balance);
      if (user) {
        setUser({ ...user, balance });
      }
    } catch (error) {
      console.error('Failed to refresh balance:', error);
    }
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        loading,
        login,
        register,
        loginAsGuest,
        logout,
        updateBalance,
        refreshBalance,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
