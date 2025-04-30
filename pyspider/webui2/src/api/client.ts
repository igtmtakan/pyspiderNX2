import axios, { AxiosInstance, AxiosRequestConfig } from 'axios';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:5001';

const getToken = (): string | null => {
  return localStorage.getItem('access_token');
};

const createClient = (): AxiosInstance => {
  console.log('Creating API client with baseURL:', API_URL);
  const client = axios.create({
    baseURL: API_URL,
    headers: {
      'Content-Type': 'application/json',
    },
    withCredentials: true,
    timeout: 10000, // タイムアウトを延長
  });

  client.interceptors.request.use(
    (config: AxiosRequestConfig) => {
      const token = getToken();
      if (token && config.headers) {
        config.headers['Authorization'] = `Bearer ${token}`;
      }
      // Ensure CORS credentials are always included
      config.withCredentials = true;
      return config;
    },
    (error) => {
      return Promise.reject(error);
    }
  );

  // レスポンスインターセプター
  client.interceptors.response.use(
    (response) => response,
    async (error) => {
      console.error('API Error:', error);

      // ネットワークエラーの場合
      if (error.code === 'ERR_NETWORK') {
        console.error('Network error - Backend server may be down');
        // カスタムエラーメッセージを設定
        error.response = {
          data: {
            error: 'バックエンドサーバーに接続できません。サーバーが起動しているか確認してください。'
          }
        };
      }

      // タイムアウトエラーの場合
      if (error.code === 'ECONNABORTED') {
        console.error('Request timeout');
        // カスタムエラーメッセージを設定
        error.response = {
          data: {
            error: 'リクエストがタイムアウトしました。サーバーの負荷が高いか、ネットワーク接続に問題がある可能性があります。'
          }
        };
      }

      return Promise.reject(error);
    }
  );

  return client;
};

export default createClient();
