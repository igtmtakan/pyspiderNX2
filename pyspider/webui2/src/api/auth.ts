import apiClient from './client';

// 認証関連の型定義
export interface User {
  id: number;
  username: string;
  role: string;
  created_at: string;
  updated_at: string;
}

export interface LoginRequest {
  username: string;
  password: string;
}

export interface LoginResponse {
  user: User;
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface RefreshResponse {
  access_token: string;
  token_type: string;
}

// ログイン
export const login = async (data: LoginRequest): Promise<LoginResponse> => {
  console.log('Login request to:', apiClient.defaults.baseURL + '/api/auth/login');
  console.log('Login data:', data);
  try {
    const response = await apiClient.post<LoginResponse>('/api/auth/login', data);
    console.log('Login response:', response);
    return response.data;
  } catch (error) {
    console.error('Login error details:', error);
    throw error;
  }
};

// トークンのリフレッシュ
export const refreshToken = async (): Promise<RefreshResponse> => {
  const refreshToken = localStorage.getItem('refresh_token');
  if (!refreshToken) {
    throw new Error('No refresh token available');
  }

  const response = await apiClient.post<RefreshResponse>(
    '/api/auth/refresh',
    {},
    {
      headers: {
        'Authorization': `Bearer ${refreshToken}`,
      },
    }
  );
  return response.data;
};

// 現在のユーザー情報を取得
export const getCurrentUser = async (): Promise<User> => {
  const response = await apiClient.get<User>('/api/auth/me');
  return response.data;
};

// ユーザー登録（管理者のみ）
export const registerUser = async (data: { username: string; password: string; role?: string }): Promise<User> => {
  const response = await apiClient.post<User>('/api/auth/register', data);
  return response.data;
};

// ユーザー一覧取得（管理者のみ）
export const getUsers = async (): Promise<User[]> => {
  const response = await apiClient.get<User[]>('/api/auth/users');
  return response.data;
};

// ユーザー削除（管理者のみ）
export const deleteUser = async (userId: number): Promise<{ success: boolean; message: string }> => {
  const response = await apiClient.delete<{ success: boolean; message: string }>(`/api/auth/users/${userId}`);
  return response.data;
};
