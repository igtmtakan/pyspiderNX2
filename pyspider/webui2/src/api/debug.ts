import apiClient from './client';

// デバッグ関連の型定義
export interface DebugRequest {
  url: string;
  project_id?: number;
  script?: string;
  fetcher_type?: string;
  callback_type?: string;
}

export interface DebugResponse {
  response: {
    url: string;
    status_code: number;
    headers: Record<string, string>;
    text: string;
    time: number;
    orig_url: string;
  };
  result: any;
  follows: string[];
}

export interface SaveResultRequest {
  project_id: number;
  url: string;
  result: any;
}

export interface SaveResultResponse {
  success: boolean;
  message: string;
  task_id: number;
  result_id: number;
}

export interface SaveFollowsRequest {
  project_id: number;
  follows: string[];
}

export interface SaveFollowsResponse {
  success: boolean;
  message: string;
  created_tasks: any[];
  skipped_tasks: string[];
}

// テスト実行
export const runTest = async (data: DebugRequest): Promise<DebugResponse> => {
  console.log('Running test with data:', data);
  try {
    const response = await apiClient.post<DebugResponse>('/api/debug/run', data);
    console.log('Test response:', response.data);
    return response.data;
  } catch (error) {
    console.error('Error running test:', error);
    throw error;
  }
};

// URLをフォロー
export const followUrl = async (data: DebugRequest): Promise<DebugResponse> => {
  const response = await apiClient.post<DebugResponse>('/api/debug/follow', data);
  return response.data;
};

// 結果を保存
export const saveResult = async (data: SaveResultRequest): Promise<SaveResultResponse> => {
  const response = await apiClient.post<SaveResultResponse>('/api/debug/save-result', data);
  return response.data;
};

// フォローURLをタスクとして保存
export const saveFollows = async (data: SaveFollowsRequest): Promise<SaveFollowsResponse> => {
  const response = await apiClient.post<SaveFollowsResponse>('/api/debug/save-follows', data);
  return response.data;
};
