import apiClient from './client';

// プロジェクト関連の型定義
export interface Project {
  id: number;
  name: string;
  status: 'RUNNING' | 'PAUSED' | 'STOPPED';
  rate: number;
  burst: number;
  script: string;
  created_at: string;
  updated_at: string;
}

export interface CreateProjectRequest {
  name: string;
  rate?: number;
  burst?: number;
  script?: string;
}

export interface UpdateProjectRequest {
  name?: string;
  status?: 'RUNNING' | 'PAUSED' | 'STOPPED';
  rate?: number;
  burst?: number;
  script?: string;
}

// プロジェクト一覧取得
export const getProjects = async (): Promise<Project[]> => {
  const response = await apiClient.get<Project[]>('/api/projects');
  return response.data;
};

// プロジェクト詳細取得
export const getProject = async (projectId: number): Promise<Project> => {
  const response = await apiClient.get<Project>(`/api/projects/${projectId}`);
  return response.data;
};

// プロジェクト作成
export const createProject = async (data: CreateProjectRequest): Promise<Project> => {
  const response = await apiClient.post<Project>('/api/projects', data);
  return response.data;
};

// プロジェクト更新
export const updateProject = async (projectId: number, data: UpdateProjectRequest): Promise<Project> => {
  const response = await apiClient.put<Project>(`/api/projects/${projectId}`, data);
  return response.data;
};

// プロジェクト削除
export const deleteProject = async (projectId: number): Promise<{ success: boolean; message: string }> => {
  const response = await apiClient.delete<{ success: boolean; message: string }>(`/api/projects/${projectId}`);
  return response.data;
};

// プロジェクト開始
export const startProject = async (projectId: number): Promise<Project> => {
  return updateProject(projectId, { status: 'RUNNING' });
};

// プロジェクト一時停止
export const pauseProject = async (projectId: number): Promise<Project> => {
  return updateProject(projectId, { status: 'PAUSED' });
};

// プロジェクト停止
export const stopProject = async (projectId: number): Promise<Project> => {
  return updateProject(projectId, { status: 'STOPPED' });
};
