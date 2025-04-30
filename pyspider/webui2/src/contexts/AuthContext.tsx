import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { authApi } from '../api';
import { User, LoginRequest } from '../api/auth';

// 認証コンテキストの型定義
interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
  login: (data: LoginRequest) => Promise<void>;
  logout: () => void;
  checkAuth: () => Promise<boolean>;
}

// 認証コンテキストの作成
const AuthContext = createContext<AuthContextType | undefined>(undefined);

// 認証プロバイダーのプロパティ
interface AuthProviderProps {
  children: ReactNode;
}

// 認証プロバイダーコンポーネント
export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // 初期化時に認証状態を確認
  useEffect(() => {
    const initAuth = async () => {
      try {
        await checkAuth();
      } catch (error) {
        console.error('Auth initialization failed:', error);
        setError('認証の初期化に失敗しました');
      } finally {
        setIsLoading(false);
      }
    };

    initAuth();
  }, []);

  // 認証状態の確認
  const checkAuth = async (): Promise<boolean> => {
    setError(null);
    const token = localStorage.getItem('access_token');
    if (!token) {
      setUser(null);
      return false;
    }

    try {
      const userData = await authApi.getCurrentUser();
      setUser(userData);
      return true;
    } catch (error: any) {
      console.error('Authentication check failed:', error);
      if (error.code === 'ERR_NETWORK') {
        setError('バックエンドサーバーに接続できません');
      } else {
        setError('認証チェックに失敗しました');
      }
      setUser(null);
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
      return false;
    }
  };

  // ログイン処理
  const login = async (data: LoginRequest): Promise<void> => {
    setError(null);
    try {
      const response = await authApi.login(data);
      localStorage.setItem('access_token', response.access_token);
      localStorage.setItem('refresh_token', response.refresh_token);
      setUser(response.user);
    } catch (error: any) {
      console.error('Login failed:', error);
      if (error.code === 'ERR_NETWORK') {
        throw new Error('バックエンドサーバーに接続できません');
      }
      throw error;
    }
  };

  // ログアウト処理
  const logout = (): void => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    setUser(null);
    setError(null);
  };

  // コンテキスト値
  const value = {
    user,
    isAuthenticated: !!user,
    isLoading,
    error,
    login,
    logout,
    checkAuth,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

// 認証コンテキストを使用するためのフック
export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
