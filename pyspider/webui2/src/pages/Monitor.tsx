import { useState, useEffect, useRef } from 'react';
import { FiRefreshCw, FiActivity, FiServer, FiCpu, FiDatabase, FiAlertCircle, FiCheckCircle } from 'react-icons/fi';
import { monitorApi } from '../api';
import { PerformanceStats, ComponentStatus } from '../api/monitor';
import { io, Socket } from 'socket.io-client';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:5001';

const Monitor = () => {
  const [performanceStats, setPerformanceStats] = useState<PerformanceStats | null>(null);
  const [componentStatus, setComponentStatus] = useState<ComponentStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);
  const [isRealtime, setIsRealtime] = useState(true);
  const socketRef = useRef<Socket | null>(null);

  // WebSocketの接続を管理
  useEffect(() => {
    if (isRealtime) {
      try {
        // WebSocketの接続
        // プロキシを使用するため、相対パスで接続
        socketRef.current = io('/', {
          path: '/socket.io',
          transports: ['polling'],  // WebSocketを無効化して、pollingのみを使用
          reconnectionAttempts: 5,
          reconnectionDelay: 1000,
          withCredentials: true,
        });

        // 接続イベント
        socketRef.current.on('connect', () => {
          console.log('WebSocket connected');
          socketRef.current?.emit('monitor_subscribe', { type: 'performance' });
        });

        // 切断イベント
        socketRef.current.on('disconnect', () => {
          console.log('WebSocket disconnected');
        });

        // 接続エラーイベント
        socketRef.current.on('connect_error', (error) => {
          console.error('WebSocket connection error:', error);
          // WebSocketが接続できない場合はポーリングモードに切り替え
          setIsRealtime(false);
        });

        // パフォーマンス統計の更新イベント
        socketRef.current.on('performance_update', (data: PerformanceStats) => {
          setPerformanceStats(data);
          setLastUpdated(new Date());
        });

        // クリーンアップ
        return () => {
          if (socketRef.current) {
            socketRef.current.disconnect();
            socketRef.current = null;
          }
        };
      } catch (error) {
        console.error('Error initializing WebSocket:', error);
        // エラーが発生した場合はポーリングモードに切り替え
        setIsRealtime(false);
      }
    } else {
      // WebSocketの切断
      if (socketRef.current) {
        socketRef.current.disconnect();
        socketRef.current = null;
      }
    }
  }, [isRealtime]);

  // 初期データの読み込み
  useEffect(() => {
    loadData();
  }, []);

  // 定期的なデータの更新（リアルタイムモードがオフの場合）
  useEffect(() => {
    if (!isRealtime) {
      const interval = setInterval(() => {
        loadData();
      }, 5000);

      return () => clearInterval(interval);
    }
  }, [isRealtime]);

  const loadData = async () => {
    setLoading(true);
    setError(null);

    try {
      // パフォーマンス統計の取得
      try {
        const stats = await monitorApi.getPerformanceStats();
        setPerformanceStats(stats);
      } catch (err: any) {
        console.error('Error fetching performance stats:', err);
        // パフォーマンス統計の取得に失敗しても、コンポーネント状態の取得は続行
      }

      // コンポーネント状態の取得
      try {
        const components = await monitorApi.getComponentStatus();
        setComponentStatus(components);
      } catch (err: any) {
        console.error('Error fetching component status:', err);
        // コンポーネント状態の取得に失敗しても、エラーメッセージは表示しない
      }

      setLastUpdated(new Date());
    } catch (err: any) {
      console.error('Error fetching monitor data:', err);
      setError(err.response?.data?.error || 'モニターデータの取得に失敗しました');
    } finally {
      setLoading(false);
    }
  };

  const handleRefresh = () => {
    loadData();
  };

  const handleResetStats = async () => {
    try {
      await monitorApi.resetPerformanceStats();
      loadData();
    } catch (err: any) {
      console.error('Error resetting performance stats:', err);
      setError(err.response?.data?.error || 'パフォーマンス統計のリセットに失敗しました');
    }
  };

  const toggleRealtime = () => {
    setIsRealtime(!isRealtime);
  };

  // コンポーネントの状態に応じたアイコンとカラーを返す
  const getStatusIcon = (status: string) => {
    if (status === 'running') {
      return <FiCheckCircle className="text-green-500" />;
    } else {
      return <FiAlertCircle className="text-red-500" />;
    }
  };

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold text-gray-800 dark:text-white">パフォーマンスモニター</h1>
        <div className="flex space-x-2">
          <button
            onClick={toggleRealtime}
            className={`px-3 py-2 rounded-md ${
              isRealtime
                ? 'bg-primary-500 text-white'
                : 'bg-gray-200 text-gray-700 dark:bg-gray-700 dark:text-gray-300'
            }`}
          >
            リアルタイム更新
          </button>
          <button
            onClick={handleRefresh}
            className="px-3 py-2 rounded-md bg-gray-200 text-gray-700 dark:bg-gray-700 dark:text-gray-300 flex items-center"
            disabled={loading}
          >
            <FiRefreshCw className={`mr-1 ${loading ? 'animate-spin' : ''}`} />
            更新
          </button>
          <button
            onClick={handleResetStats}
            className="px-3 py-2 rounded-md bg-red-500 text-white flex items-center"
            disabled={loading}
          >
            リセット
          </button>
        </div>
      </div>

      {error && (
        <div className="mb-4 p-3 bg-red-100 text-red-700 rounded-md">
          <p>{error}</p>
        </div>
      )}

      <div className="mb-4 text-sm text-gray-500 dark:text-gray-400">
        {lastUpdated && (
          <p>最終更新: {lastUpdated.toLocaleString()}</p>
        )}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
        {/* コンポーネント状態 */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
          <h2 className="text-xl font-semibold mb-4 flex items-center">
            <FiServer className="mr-2" />
            コンポーネント状態
          </h2>

          {loading && !componentStatus ? (
            <p className="text-gray-500 dark:text-gray-400">読み込み中...</p>
          ) : (
            <div className="space-y-4">
              {/* APIサーバー */}
              <div className="flex justify-between items-center p-3 bg-gray-50 dark:bg-gray-700 rounded-md">
                <div className="flex items-center">
                  <FiServer className="mr-2" />
                  <span>APIサーバー</span>
                </div>
                <div className="flex items-center">
                  {componentStatus?.api && getStatusIcon(componentStatus.api.status)}
                  <span className="ml-2">
                    {componentStatus?.api?.status === 'running' ? '実行中' : 'エラー'}
                  </span>
                </div>
              </div>

              {/* スケジューラー */}
              <div className="flex justify-between items-center p-3 bg-gray-50 dark:bg-gray-700 rounded-md">
                <div className="flex items-center">
                  <FiCpu className="mr-2" />
                  <span>スケジューラー</span>
                </div>
                <div className="flex items-center">
                  {componentStatus?.scheduler && getStatusIcon(componentStatus.scheduler.status)}
                  <span className="ml-2">
                    {componentStatus?.scheduler?.status === 'running' ? '実行中' : 'エラー'}
                  </span>
                </div>
              </div>

              {/* タスク数 */}
              {componentStatus?.scheduler?.task_count && (
                <div className="mt-4">
                  <h3 className="font-medium mb-2">タスク数</h3>
                  <div className="grid grid-cols-2 gap-2">
                    <div className="p-2 bg-gray-50 dark:bg-gray-700 rounded-md">
                      <p className="text-sm text-gray-500 dark:text-gray-400">合計</p>
                      <p className="text-lg font-semibold">{componentStatus.scheduler.task_count.total}</p>
                    </div>
                    <div className="p-2 bg-gray-50 dark:bg-gray-700 rounded-md">
                      <p className="text-sm text-gray-500 dark:text-gray-400">保留中</p>
                      <p className="text-lg font-semibold">{componentStatus.scheduler.task_count.pending}</p>
                    </div>
                    <div className="p-2 bg-gray-50 dark:bg-gray-700 rounded-md">
                      <p className="text-sm text-gray-500 dark:text-gray-400">実行中</p>
                      <p className="text-lg font-semibold">{componentStatus.scheduler.task_count.running}</p>
                    </div>
                    <div className="p-2 bg-gray-50 dark:bg-gray-700 rounded-md">
                      <p className="text-sm text-gray-500 dark:text-gray-400">成功</p>
                      <p className="text-lg font-semibold">{componentStatus.scheduler.task_count.success}</p>
                    </div>
                  </div>
                </div>
              )}

              {/* エラーメッセージ */}
              {componentStatus?.scheduler?.error && (
                <div className="mt-4 p-3 bg-red-100 text-red-700 rounded-md">
                  <p className="font-medium">エラー:</p>
                  <p>{componentStatus.scheduler.error}</p>
                </div>
              )}
            </div>
          )}
        </div>

        {/* パフォーマンス統計 */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
          <h2 className="text-xl font-semibold mb-4 flex items-center">
            <FiActivity className="mr-2" />
            パフォーマンス統計
          </h2>

          {loading && !performanceStats ? (
            <p className="text-gray-500 dark:text-gray-400">読み込み中...</p>
          ) : (
            <div>
              {performanceStats?.counters && Object.keys(performanceStats.counters).length > 0 ? (
                <div className="space-y-4">
                  <h3 className="font-medium">カウンター</h3>
                  <div className="grid grid-cols-2 gap-2">
                    {Object.entries(performanceStats.counters).map(([key, value]) => (
                      <div key={key} className="p-3 bg-gray-50 dark:bg-gray-700 rounded-md">
                        <p className="text-sm text-gray-500 dark:text-gray-400">{key}</p>
                        <p className="text-lg font-semibold">{value}</p>
                      </div>
                    ))}
                  </div>
                </div>
              ) : (
                <p className="text-gray-500 dark:text-gray-400">
                  パフォーマンスデータがありません。システムが動作を開始すると、ここにデータが表示されます。
                </p>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default Monitor;
