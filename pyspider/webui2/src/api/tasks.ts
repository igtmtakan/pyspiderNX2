import apiClient from './client';

// タスク関連の型定義
export interface Task {
  id: number;
  url: string;
  status: 'PENDING' | 'RUNNING' | 'SUCCESS' | 'FAILED';
  retries: number;
  priority: number;
  schedule_time: string;
  start_time: string | null;
  end_time: string | null;
  created_at: string;
  updated_at: string;
  error: string | null;
  project_id: number;
  project_name: string;
}

// タスク統計の型定義
export interface TaskStats {
  pending: number;
  running: number;
  success: number;
  failed: number;
  total: number;
}

export interface CreateTaskRequest {
  url: string;
  project_id: number;
  priority?: number;
  schedule_time?: string;
}

export interface UpdateTaskRequest {
  url?: string;
  status?: 'PENDING' | 'RUNNING' | 'SUCCESS' | 'FAILED';
  priority?: number;
  schedule_time?: string;
  error?: string;
}

// タスク一覧取得
export const getTasks = async (params?: {
  project_id?: number;
  status?: string;
  skip?: number;
  limit?: number;
}): Promise<Task[]> => {
  const response = await apiClient.get<Task[]>('/api/tasks', { params });
  return response.data;
};

// タスク詳細取得
export const getTask = async (taskId: number): Promise<Task> => {
  const response = await apiClient.get<Task>(`/api/tasks/${taskId}`);
  return response.data;
};

// タスク作成
export const createTask = async (data: CreateTaskRequest): Promise<Task> => {
  const response = await apiClient.post<Task>('/api/tasks', data);
  return response.data;
};

// タスク更新
export const updateTask = async (taskId: number, data: UpdateTaskRequest): Promise<Task> => {
  const response = await apiClient.put<Task>(`/api/tasks/${taskId}`, data);
  return response.data;
};

// タスクステータス更新
export const updateTaskStatus = async (
  taskId: number,
  status: 'PENDING' | 'RUNNING' | 'SUCCESS' | 'FAILED',
  error?: string
): Promise<Task> => {
  const response = await apiClient.put<Task>(`/api/tasks/${taskId}/status`, { status, error });
  return response.data;
};

// タスク削除
export const deleteTask = async (taskId: number): Promise<{ success: boolean; message: string }> => {
  const response = await apiClient.delete<{ success: boolean; message: string }>(`/api/tasks/${taskId}`);
  return response.data;
};

// プロジェクトのタスク統計取得
export const getProjectTaskStats = async (projectId: number): Promise<TaskStats> => {
  const response = await apiClient.get<TaskStats>(`/api/projects/${projectId}/task-stats`);
  return response.data;
};
