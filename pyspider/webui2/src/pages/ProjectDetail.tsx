import { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { FiSave, FiPlay, FiPause, FiSquare, FiTrash2, FiArrowLeft, FiCode, FiTerminal, FiEdit2, FiDownload, FiFileText, FiDatabase, FiRefreshCw } from 'react-icons/fi';
import MonacoEditor from '@monaco-editor/react';
import DebugPanel from '../components/DebugPanel';
import { projectsApi, debugApi } from '../api';
import { Project } from '../api/projects';
import { TaskStats, getProjectTaskStats } from '../api/tasks';

const ProjectDetail = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [project, setProject] = useState<Project | null>(null);
  const [loading, setLoading] = useState(true);
  const [script, setScript] = useState('');
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'script' | 'debug'>('script');
  const [taskStats, setTaskStats] = useState<TaskStats | null>(null);
  const [loadingStats, setLoadingStats] = useState(false);
  const statsIntervalRef = useRef<number | null>(null);

  const fetchProject = async () => {
    if (!id) return;

    setLoading(true);
    setError(null);

    try {
      const projectId = parseInt(id);
      const data = await projectsApi.getProject(projectId);
      setProject(data);
      setScript(data.script);
    } catch (err: any) {
      console.error('Error fetching project:', err);
      setError(err.response?.data?.error || 'プロジェクトの取得に失敗しました');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchProject();

    // プロジェクトが読み込まれたら、タスク統計を取得する
    if (id) {
      fetchTaskStats();

      // 30秒ごとにタスク統計を更新する
      statsIntervalRef.current = window.setInterval(() => {
        fetchTaskStats();
      }, 30000);
    }

    // クリーンアップ関数
    return () => {
      if (statsIntervalRef.current) {
        window.clearInterval(statsIntervalRef.current);
      }
    };
  }, [id]);

  // タスク統計を取得する関数
  const fetchTaskStats = async () => {
    if (!id) return;

    setLoadingStats(true);
    try {
      const projectId = parseInt(id);
      const stats = await getProjectTaskStats(projectId);
      setTaskStats(stats);
    } catch (err: any) {
      console.error('Error fetching task stats:', err);
      // エラーが発生しても、UIにはエラーメッセージを表示しない
    } finally {
      setLoadingStats(false);
    }
  };

  const handleSave = async () => {
    if (!project || !id) return;

    setSaving(true);
    setError(null);

    try {
      const projectId = parseInt(id);
      await projectsApi.updateProject(projectId, { script });
      await fetchProject();
    } catch (err: any) {
      console.error('Error saving project:', err);
      setError(err.response?.data?.error || 'プロジェクトの保存に失敗しました');
    } finally {
      setSaving(false);
    }
  };

  const handleStart = async () => {
    if (!project || !id) return;

    try {
      const projectId = parseInt(id);
      await projectsApi.startProject(projectId);
      await fetchProject();
    } catch (err: any) {
      console.error('Error starting project:', err);
      setError(err.response?.data?.error || 'プロジェクトの開始に失敗しました');
    }
  };

  const handlePause = async () => {
    if (!project || !id) return;

    try {
      const projectId = parseInt(id);
      await projectsApi.pauseProject(projectId);
      await fetchProject();
    } catch (err: any) {
      console.error('Error pausing project:', err);
      setError(err.response?.data?.error || 'プロジェクトの一時停止に失敗しました');
    }
  };

  const handleStop = async () => {
    if (!project || !id) return;

    try {
      const projectId = parseInt(id);
      await projectsApi.stopProject(projectId);
      await fetchProject();
    } catch (err: any) {
      console.error('Error stopping project:', err);
      setError(err.response?.data?.error || 'プロジェクトの停止に失敗しました');
    }
  };

  const handleDelete = async () => {
    if (!project || !id) return;

    if (!confirm('このプロジェクトを削除してもよろしいですか？')) {
      return;
    }

    try {
      const projectId = parseInt(id);
      await projectsApi.deleteProject(projectId);
      navigate('/projects');
    } catch (err: any) {
      console.error('Error deleting project:', err);
      setError(err.response?.data?.error || 'プロジェクトの削除に失敗しました');
    }
  };

  // デバッグ関連の関数
  const handleRunTest = async (url: string, fetcherType: string, callbackType: string) => {
    if (!project || !id) {
      throw new Error('プロジェクトが読み込まれていません');
    }

    const projectId = parseInt(id);
    const response = await debugApi.runTest({
      url,
      project_id: projectId,
      script,
      fetcher_type: fetcherType,
      callback_type: callbackType,
    });

    return response;
  };

  const handleFollowUrl = async (url: string, fetcherType: string, callbackType: string) => {
    if (!project || !id) {
      throw new Error('プロジェクトが読み込まれていません');
    }

    const projectId = parseInt(id);
    const response = await debugApi.followUrl({
      url,
      project_id: projectId,
      script,
      fetcher_type: fetcherType,
      callback_type: callbackType,
    });

    return response;
  };

  const handleSaveResult = async (result: any) => {
    if (!project || !id) {
      throw new Error('プロジェクトが読み込まれていません');
    }

    const projectId = parseInt(id);
    await debugApi.saveResult({
      project_id: projectId,
      url: result.response.url,
      result: result.result,
    });
  };

  // 結果をエクスポートする関数
  const handleExportResults = (format: 'json' | 'csv' | 'xml') => {
    if (!project || !id) return;

    const projectId = parseInt(id);
    const apiUrl = `${import.meta.env.VITE_API_BASE_URL || ''}/api/export/project/${projectId}/results?format=${format}`;

    // 新しいタブでエクスポートURLを開く
    window.open(apiUrl, '_blank');
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'RUNNING':
        return <span className="px-2 py-1 text-xs rounded-full bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-300">Running</span>;
      case 'PAUSED':
        return <span className="px-2 py-1 text-xs rounded-full bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-300">Paused</span>;
      case 'STOPPED':
        return <span className="px-2 py-1 text-xs rounded-full bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300">Stopped</span>;
      default:
        return <span className="px-2 py-1 text-xs rounded-full bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300">{status}</span>;
    }
  };

  return (
    <div>
      <div className="flex items-center mb-6">
        <button
          onClick={() => navigate('/projects')}
          className="mr-4 p-2 rounded-md text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700"
        >
          <FiArrowLeft />
        </button>
        {loading ? (
          <div className="h-8 w-48 bg-gray-200 dark:bg-gray-700 rounded animate-pulse"></div>
        ) : (
          <div className="flex items-center">
            <h1 className="text-2xl font-bold text-gray-800 dark:text-white mr-4">{project?.name}</h1>
            <div className="flex space-x-2">
              <button
                onClick={() => navigate(`/projects/${id}/edit`)}
                className="px-3 py-1 bg-blue-500 text-white rounded-md hover:bg-blue-600 transition-colors"
              >
                <FiEdit2 className="inline mr-1" />
                編集
              </button>
              <button
                onClick={() => navigate(`/projects/${id}/debug`)}
                className="px-3 py-1 bg-green-500 text-white rounded-md hover:bg-green-600 transition-colors"
              >
                <FiTerminal className="inline mr-1" />
                デバッグ画面
              </button>
              <button
                onClick={() => navigate(`/projects/${id}/debug-v2`)}
                className="px-3 py-1 bg-purple-500 text-white rounded-md hover:bg-purple-600 transition-colors"
              >
                <FiTerminal className="inline mr-1" />
                デバッグV2
              </button>
            </div>
          </div>
        )}
      </div>

      {error && (
        <div className="mb-4 p-3 bg-red-100 text-red-700 dark:bg-red-900 dark:text-red-300 rounded-md">
          {error}
        </div>
      )}

      {loading ? (
        <div className="flex justify-center items-center h-64">
          <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-primary-500"></div>
        </div>
      ) : (
        <>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
              <div className="flex justify-between items-center mb-4">
                <h2 className="text-lg font-semibold text-gray-700 dark:text-gray-200">ステータス</h2>
                <button
                  onClick={fetchTaskStats}
                  disabled={loadingStats}
                  className="p-1 rounded-md text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700"
                  title="統計を更新"
                >
                  <FiRefreshCw className={`${loadingStats ? 'animate-spin' : ''}`} />
                </button>
              </div>
              <div className="flex items-center mb-4">
                <span className="text-gray-600 dark:text-gray-400 mr-2">現在のステータス:</span>
                {getStatusBadge(project?.status || 'UNKNOWN')}
              </div>

              {/* タスク統計とプログレスバー */}
              <div className="mb-6">
                <div className="flex justify-between items-center mb-2">
                  <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300">タスク進捗状況</h3>
                  {taskStats && (
                    <span className="text-xs text-gray-500 dark:text-gray-400">
                      合計: {taskStats.total}
                    </span>
                  )}
                </div>

                {loadingStats && !taskStats ? (
                  <div className="h-16 bg-gray-200 dark:bg-gray-700 rounded animate-pulse"></div>
                ) : taskStats ? (
                  <div className="space-y-3">
                    {/* Pending タスク */}
                    <div>
                      <div className="flex justify-between items-center mb-1">
                        <span className="text-xs font-medium text-blue-700 dark:text-blue-300">Pending</span>
                        <span className="text-xs text-gray-500 dark:text-gray-400">
                          {taskStats.pending} ({taskStats.total > 0 ? Math.round((taskStats.pending / taskStats.total) * 100) : 0}%)
                        </span>
                      </div>
                      <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                        <div
                          className="bg-blue-500 h-2 rounded-full"
                          style={{ width: `${taskStats.total > 0 ? (taskStats.pending / taskStats.total) * 100 : 0}%` }}
                        ></div>
                      </div>
                    </div>

                    {/* Running タスク */}
                    <div>
                      <div className="flex justify-between items-center mb-1">
                        <span className="text-xs font-medium text-yellow-700 dark:text-yellow-300">Running</span>
                        <span className="text-xs text-gray-500 dark:text-gray-400">
                          {taskStats.running} ({taskStats.total > 0 ? Math.round((taskStats.running / taskStats.total) * 100) : 0}%)
                        </span>
                      </div>
                      <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                        <div
                          className="bg-yellow-500 h-2 rounded-full"
                          style={{ width: `${taskStats.total > 0 ? (taskStats.running / taskStats.total) * 100 : 0}%` }}
                        ></div>
                      </div>
                    </div>

                    {/* Success タスク */}
                    <div>
                      <div className="flex justify-between items-center mb-1">
                        <span className="text-xs font-medium text-green-700 dark:text-green-300">Success</span>
                        <span className="text-xs text-gray-500 dark:text-gray-400">
                          {taskStats.success} ({taskStats.total > 0 ? Math.round((taskStats.success / taskStats.total) * 100) : 0}%)
                        </span>
                      </div>
                      <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                        <div
                          className="bg-green-500 h-2 rounded-full"
                          style={{ width: `${taskStats.total > 0 ? (taskStats.success / taskStats.total) * 100 : 0}%` }}
                        ></div>
                      </div>
                    </div>

                    {/* Failed タスク */}
                    <div>
                      <div className="flex justify-between items-center mb-1">
                        <span className="text-xs font-medium text-red-700 dark:text-red-300">Failed</span>
                        <span className="text-xs text-gray-500 dark:text-gray-400">
                          {taskStats.failed} ({taskStats.total > 0 ? Math.round((taskStats.failed / taskStats.total) * 100) : 0}%)
                        </span>
                      </div>
                      <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                        <div
                          className="bg-red-500 h-2 rounded-full"
                          style={{ width: `${taskStats.total > 0 ? (taskStats.failed / taskStats.total) * 100 : 0}%` }}
                        ></div>
                      </div>
                    </div>
                  </div>
                ) : (
                  <div className="text-sm text-gray-500 dark:text-gray-400 py-2">
                    タスク統計を読み込めませんでした。
                  </div>
                )}
              </div>

              <div className="flex space-x-2">
                {project?.status !== 'RUNNING' && (
                  <button
                    onClick={handleStart}
                    className="px-3 py-1 bg-green-500 text-white rounded-md hover:bg-green-600 transition-colors"
                  >
                    <FiPlay className="inline mr-1" />
                    開始
                  </button>
                )}
                {project?.status === 'RUNNING' && (
                  <button
                    onClick={handlePause}
                    className="px-3 py-1 bg-yellow-500 text-white rounded-md hover:bg-yellow-600 transition-colors"
                  >
                    <FiPause className="inline mr-1" />
                    一時停止
                  </button>
                )}
                {project?.status !== 'STOPPED' && (
                  <button
                    onClick={handleStop}
                    className="px-3 py-1 bg-red-500 text-white rounded-md hover:bg-red-600 transition-colors"
                  >
                    <FiSquare className="inline mr-1" />
                    停止
                  </button>
                )}
              </div>
            </div>

            <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
              <h2 className="text-lg font-semibold mb-4 text-gray-700 dark:text-gray-200">レート制限</h2>
              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  レート（リクエスト/秒）
                </label>
                <input
                  type="number"
                  value={project?.rate || 1.0}
                  onChange={(e) => setProject(project ? { ...project, rate: parseFloat(e.target.value) } : null)}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:outline-none focus:ring-primary-500 focus:border-primary-500 dark:bg-gray-700 dark:text-white"
                  step="0.1"
                  min="0.1"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  バースト
                </label>
                <input
                  type="number"
                  value={project?.burst || 10}
                  onChange={(e) => setProject(project ? { ...project, burst: parseInt(e.target.value) } : null)}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:outline-none focus:ring-primary-500 focus:border-primary-500 dark:bg-gray-700 dark:text-white"
                  step="1"
                  min="1"
                />
              </div>
            </div>

            <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
              <h2 className="text-lg font-semibold mb-4 text-gray-700 dark:text-gray-200">情報</h2>
              <div className="mb-2">
                <span className="text-gray-600 dark:text-gray-400">作成日時:</span>
                <span className="ml-2 text-gray-800 dark:text-gray-200">
                  {project?.created_at ? new Date(project.created_at).toLocaleString() : '-'}
                </span>
              </div>
              <div className="mb-4">
                <span className="text-gray-600 dark:text-gray-400">ID:</span>
                <span className="ml-2 text-gray-800 dark:text-gray-200">
                  {project?.id || '-'}
                </span>
              </div>

              <div className="mb-4">
                <h3 className="text-md font-semibold mb-2 text-gray-700 dark:text-gray-300">結果のエクスポート</h3>
                <div className="flex space-x-2">
                  <button
                    onClick={() => handleExportResults('json')}
                    className="px-3 py-1 bg-blue-500 text-white rounded-md hover:bg-blue-600 transition-colors"
                    title="JSONとしてエクスポート"
                  >
                    <FiDatabase className="inline mr-1" />
                    JSON
                  </button>
                  <button
                    onClick={() => handleExportResults('csv')}
                    className="px-3 py-1 bg-green-500 text-white rounded-md hover:bg-green-600 transition-colors"
                    title="CSVとしてエクスポート"
                  >
                    <FiFileText className="inline mr-1" />
                    CSV
                  </button>
                  <button
                    onClick={() => handleExportResults('xml')}
                    className="px-3 py-1 bg-purple-500 text-white rounded-md hover:bg-purple-600 transition-colors"
                    title="XMLとしてエクスポート"
                  >
                    <FiCode className="inline mr-1" />
                    XML
                  </button>
                </div>
              </div>

              <button
                onClick={handleDelete}
                className="px-3 py-1 bg-red-500 text-white rounded-md hover:bg-red-600 transition-colors"
              >
                <FiTrash2 className="inline mr-1" />
                プロジェクトを削除
              </button>
            </div>
          </div>

          <div className="mb-6 bg-white dark:bg-gray-800 rounded-lg shadow">
            <div className="flex border-b border-gray-300 dark:border-gray-700">
              <button
                className={`px-4 py-2 flex items-center ${
                  activeTab === 'script'
                    ? 'bg-primary-100 dark:bg-primary-900 text-primary-700 dark:text-primary-300 font-medium border-b-2 border-primary-500'
                    : 'bg-white dark:bg-gray-800 text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700'
                }`}
                onClick={() => setActiveTab('script')}
              >
                <FiCode className="mr-2" />
                スクリプト
              </button>
              <button
                className={`px-4 py-2 flex items-center ${
                  activeTab === 'debug'
                    ? 'bg-primary-100 dark:bg-primary-900 text-primary-700 dark:text-primary-300 font-medium border-b-2 border-primary-500'
                    : 'bg-white dark:bg-gray-800 text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700'
                }`}
                onClick={() => setActiveTab('debug')}
              >
                <FiTerminal className="mr-2" />
                デバッグ
              </button>
            </div>

            {activeTab === 'script' ? (
              <div className="p-6">
                <div className="flex justify-between items-center mb-4">
                  <h2 className="text-lg font-semibold text-gray-700 dark:text-gray-200">スクリプト</h2>
                  <button
                    onClick={handleSave}
                    disabled={saving}
                    className={`px-4 py-2 bg-primary-500 text-white rounded-md hover:bg-primary-600 transition-colors ${
                      saving ? 'opacity-50 cursor-not-allowed' : ''
                    }`}
                  >
                    <FiSave className="inline mr-2" />
                    {saving ? '保存中...' : '保存'}
                  </button>
                </div>
                <div className="h-96 border border-gray-300 dark:border-gray-600 rounded-md overflow-hidden">
                  <MonacoEditor
                    height="100%"
                    language="python"
                    theme="vs-dark"
                    value={script}
                    onChange={(value) => setScript(value || '')}
                    options={{
                      minimap: { enabled: false },
                      scrollBeyondLastLine: false,
                      fontSize: 14,
                    }}
                  />
                </div>
              </div>
            ) : (
              <div className="p-6">
                <DebugPanel
                  projectId={project?.id ? parseInt(project.id) : 0}
                  script={script}
                  onRunTest={handleRunTest}
                  onFollowUrl={handleFollowUrl}
                  onSaveResult={handleSaveResult}
                />
              </div>
            )}
          </div>
        </>
      )}
    </div>
  );
};

export default ProjectDetail;
