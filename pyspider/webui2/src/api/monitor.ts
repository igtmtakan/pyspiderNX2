import apiClient from './client';

// パフォーマンスモニター関連の型定義
export interface PerformanceStats {
  counters: Record<string, number>;
  system: {
    api_status: string;
    timestamp?: number;
  };
  scheduler?: {
    status: string;
    task_count?: {
      total: number;
      pending: number;
      running: number;
      success: number;
      error: number;
    };
    error?: string;
  };
}

export interface ComponentStatus {
  api: {
    status: string;
  };
  scheduler?: {
    status: string;
    task_count?: {
      total: number;
      pending: number;
      running: number;
      success: number;
      error: number;
    };
    error?: string;
  };
}

// パフォーマンス統計取得
export const getPerformanceStats = async (): Promise<PerformanceStats> => {
  const response = await apiClient.get<PerformanceStats>('/api/monitor/performance');
  return response.data;
};

// コンポーネント状態取得
export const getComponentStatus = async (): Promise<ComponentStatus> => {
  const response = await apiClient.get<ComponentStatus>('/api/monitor/components');
  return response.data;
};

// パフォーマンス統計リセット
export const resetPerformanceStats = async (): Promise<{ success: boolean; message: string }> => {
  const response = await apiClient.post<{ success: boolean; message: string }>('/api/monitor/reset');
  return response.data;
};
