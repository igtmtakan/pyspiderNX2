import { useState, useEffect } from 'react';
import { useNavigate, Navigate } from 'react-router-dom';
import { FiLogIn, FiAlertCircle } from 'react-icons/fi';
import { useAuth } from '../contexts/AuthContext';

const Login = () => {
  const { isAuthenticated, login, isLoading, error: authError } = useAuth();
  const navigate = useNavigate();
  
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  
  useEffect(() => {
    if (authError) {
      setError(authError);
    }
  }, [authError]);
  
  // 既に認証済みの場合はダッシュボードにリダイレクト
  if (isAuthenticated && !isLoading) {
    return <Navigate to="/" />;
  }
  
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!username || !password) {
      setError('ユーザー名とパスワードを入力してください');
      return;
    }
    
    setLoading(true);
    setError(null);
    
    try {
      await login({ username, password });
      navigate('/');
    } catch (err: any) {
      setError(err.message || err.response?.data?.error || 'ログインに失敗しました');
    } finally {
      setLoading(false);
    }
  };
  
  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-100 dark:bg-gray-900 px-4">
      <div className="max-w-md w-full bg-white dark:bg-gray-800 rounded-lg shadow-md p-8">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-primary-600 dark:text-primary-400">PySpiderNX3</h1>
          <p className="text-gray-600 dark:text-gray-400 mt-2">ログインしてください</p>
        </div>
        
        {error && (
          <div className="mb-4 p-3 bg-red-100 text-red-700 dark:bg-red-900 dark:text-red-300 rounded-md flex items-center">
            <FiAlertCircle className="mr-2" />
            <span>{error}</span>
          </div>
        )}
        
        <form onSubmit={handleSubmit}>
          <div className="mb-4">
            <label htmlFor="username" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              ユーザー名
            </label>
            <input
              id="username"
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:outline-none focus:ring-primary-500 focus:border-primary-500 dark:bg-gray-700 dark:text-white"
              placeholder="ユーザー名を入力"
              disabled={loading}
            />
          </div>
          
          <div className="mb-6">
            <label htmlFor="password" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              パスワード
            </label>
            <input
              id="password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:outline-none focus:ring-primary-500 focus:border-primary-500 dark:bg-gray-700 dark:text-white"
              placeholder="パスワードを入力"
              disabled={loading}
            />
          </div>
          
          <button
            type="submit"
            className={`w-full flex justify-center items-center px-4 py-2 bg-primary-500 text-white rounded-md hover:bg-primary-600 transition-colors ${
              loading ? 'opacity-70 cursor-not-allowed' : ''
            }`}
            disabled={loading}
          >
            {loading ? (
              <>
                <span className="animate-spin rounded-full h-4 w-4 border-t-2 border-b-2 border-white mr-2"></span>
                ログイン中...
              </>
            ) : (
              <>
                <FiLogIn className="mr-2" />
                ログイン
              </>
            )}
          </button>
        </form>
        
        <div className="mt-6 text-center text-sm text-gray-500 dark:text-gray-400">
          <p>デフォルトの認証情報:</p>
          <p>ユーザー名: admin / パスワード: admin</p>
        </div>
      </div>
    </div>
  );
};

export default Login;
