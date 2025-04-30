import apiClient from './client';

// 結果関連の型定義
export interface Result {
  id: number;
  data: any;
  created_at: string;
  task_id: number;
  project_id: number;
  url: string;
  project_name: string;
}

// 結果一覧取得
export const getResults = async (params?: {
  project_id?: number;
  skip?: number;
  limit?: number;
}): Promise<Result[]> => {
  const response = await apiClient.get<Result[]>('/api/results', { params });
  return response.data;
};

// 結果詳細取得
export const getResult = async (resultId: number): Promise<Result> => {
  const response = await apiClient.get<Result>(`/api/results/${resultId}`);
  return response.data;
};

// タスクIDによる結果取得
export const getResultByTask = async (taskId: number): Promise<Result> => {
  const response = await apiClient.get<Result>(`/api/results/task/${taskId}`);
  return response.data;
};

// 結果作成
export const createResult = async (taskId: number, data: any): Promise<Result> => {
  const response = await apiClient.post<Result>(`/api/results/task/${taskId}`, data);
  return response.data;
};

// 結果削除
export const deleteResult = async (resultId: number): Promise<{ success: boolean; message: string }> => {
  const response = await apiClient.delete<{ success: boolean; message: string }>(`/api/results/${resultId}`);
  return response.data;
};
