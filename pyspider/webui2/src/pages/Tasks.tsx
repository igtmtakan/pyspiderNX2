import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { FiRefreshCw, FiExternalLink, FiTrash2, FiPlay, FiPause } from 'react-icons/fi';
import { tasksApi, projectsApi } from '../api';
import { Task } from '../api/tasks';
import { Project } from '../api/projects';

const Tasks = () => {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [filter, setFilter] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [projectFilter, setProjectFilter] = useState<number | ''>('');
  const [error, setError] = useState<string | null>(null);
  const [itemsPerPage] = useState(10);

  useEffect(() => {
    loadProjects();
    loadTasks();
  }, [page, statusFilter, projectFilter]);

  const loadProjects = async () => {
    try {
      const data = await projectsApi.getProjects();
      setProjects(data);
    } catch (err: any) {
      console.error('Error fetching projects:', err);
      setError(err.response?.data?.error || 'プロジェクトの取得に失敗しました');
    }
  };

  const loadTasks = async () => {
    setLoading(true);
    setError(null);

    try {
      const params: any = {
        skip: (page - 1) * itemsPerPage,
        limit: itemsPerPage,
      };

      if (statusFilter) {
        params.status = statusFilter;
      }

      if (projectFilter) {
        params.project_id = projectFilter;
      }

      const data = await tasksApi.getTasks(params);

      // フィルタリング（URLによる）
      const filteredData = filter
        ? data.filter(task => task.url.toLowerCase().includes(filter.toLowerCase()))
        : data;

      setTasks(filteredData);

      // 合計ページ数の計算（実際のAPIでは、合計数を返すエンドポイントが必要）
      // ここでは簡易的に実装
      setTotalPages(Math.max(1, Math.ceil(data.length / itemsPerPage)));
    } catch (err: any) {
      console.error('Error fetching tasks:', err);
      setError(err.response?.data?.error || 'タスクの取得に失敗しました');
    } finally {
      setLoading(false);
    }
  };

  const handleRefresh = () => {
    loadTasks();
  };

  const handleRetryTask = async (taskId: number) => {
    try {
      await tasksApi.updateTaskStatus(taskId, 'PENDING');
      loadTasks();
    } catch (err: any) {
      console.error('Error retrying task:', err);
      setError(err.response?.data?.error || 'タスクの再試行に失敗しました');
    }
  };

  const handleCancelTask = async (taskId: number) => {
    if (!confirm('このタスクをキャンセルしてもよろしいですか？')) {
      return;
    }

    try {
      await tasksApi.updateTaskStatus(taskId, 'FAILED', 'Cancelled by user');
      loadTasks();
    } catch (err: any) {
      console.error('Error cancelling task:', err);
      setError(err.response?.data?.error || 'タスクのキャンセルに失敗しました');
    }
  };

  const handleDeleteTask = async (taskId: number) => {
    if (!confirm('このタスクを削除してもよろしいですか？')) {
      return;
    }

    try {
      await tasksApi.deleteTask(taskId);
      loadTasks();
    } catch (err: any) {
      console.error('Error deleting task:', err);
      setError(err.response?.data?.error || 'タスクの削除に失敗しました');
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'SUCCESS':
        return <span className="px-2 py-1 text-xs rounded-full bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-300">Success</span>;
      case 'RUNNING':
        return <span className="px-2 py-1 text-xs rounded-full bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-300">Running</span>;
      case 'PENDING':
        return <span className="px-2 py-1 text-xs rounded-full bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-300">Pending</span>;
      case 'FAILED':
        return <span className="px-2 py-1 text-xs rounded-full bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-300">Failed</span>;
      default:
        return <span className="px-2 py-1 text-xs rounded-full bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300">{status}</span>;
    }
  };

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold text-gray-800 dark:text-white">タスク</h1>
        <button
          onClick={handleRefresh}
          className="flex items-center px-4 py-2 bg-primary-500 text-white rounded-md hover:bg-primary-600 transition-colors"
          disabled={loading}
        >
          <FiRefreshCw className={`mr-2 ${loading ? 'animate-spin' : ''}`} />
          更新
        </button>
      </div>

      {error && (
        <div className="mb-4 p-3 bg-red-100 text-red-700 dark:bg-red-900 dark:text-red-300 rounded-md">
          {error}
        </div>
      )}

      <div className="bg-white dark:bg-gray-800 rounded-lg shadow mb-6 p-4">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              URL検索
            </label>
            <input
              type="text"
              value={filter}
              onChange={(e) => setFilter(e.target.value)}
              placeholder="URLで検索..."
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:outline-none focus:ring-primary-500 focus:border-primary-500 dark:bg-gray-700 dark:text-white"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              ステータス
            </label>
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:outline-none focus:ring-primary-500 focus:border-primary-500 dark:bg-gray-700 dark:text-white"
            >
              <option value="">すべてのステータス</option>
              <option value="PENDING">待機中</option>
              <option value="RUNNING">実行中</option>
              <option value="SUCCESS">成功</option>
              <option value="FAILED">失敗</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              プロジェクト
            </label>
            <select
              value={projectFilter}
              onChange={(e) => setProjectFilter(e.target.value ? parseInt(e.target.value) : '')}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:outline-none focus:ring-primary-500 focus:border-primary-500 dark:bg-gray-700 dark:text-white"
            >
              <option value="">すべてのプロジェクト</option>
              {projects.map((project) => (
                <option key={project.id} value={project.id}>
                  {project.name}
                </option>
              ))}
            </select>
          </div>

          <div className="md:col-span-3 flex justify-end">
            <button
              onClick={() => {
                setFilter('');
                setStatusFilter('');
                setProjectFilter('');
                loadTasks();
              }}
              className="px-4 py-2 border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 rounded-md hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
            >
              フィルターをクリア
            </button>
          </div>
        </div>
      </div>

      {loading ? (
        <div className="flex justify-center items-center h-64">
          <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-primary-500"></div>
        </div>
      ) : tasks.length === 0 ? (
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-8 text-center">
          <p className="text-gray-600 dark:text-gray-400 mb-4">タスクが見つかりません</p>
          <button
            onClick={handleRefresh}
            className="inline-flex items-center px-4 py-2 bg-primary-500 text-white rounded-md hover:bg-primary-600 transition-colors"
          >
            <FiRefreshCw className="mr-2" />
            更新
          </button>
        </div>
      ) : (
        <>
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow overflow-hidden">
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
                <thead className="bg-gray-50 dark:bg-gray-700">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">URL</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">ステータス</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">プロジェクト</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">リトライ</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">作成日時</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">更新日時</th>
                    <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">アクション</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
                  {tasks.map((task) => (
                    <tr key={task.id}>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-700 dark:text-gray-300">
                        <div className="max-w-xs truncate">{task.url}</div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        {getStatusBadge(task.status)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-700 dark:text-gray-300">
                        <Link to={`/projects/${task.project_id}`} className="text-primary-600 hover:text-primary-900 dark:text-primary-400 dark:hover:text-primary-300">
                          {projects.find(p => p.id === task.project_id)?.name || `プロジェクト ${task.project_id}`}
                        </Link>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-700 dark:text-gray-300">
                        {task.retries || 0}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-700 dark:text-gray-300">
                        {new Date(task.created_at).toLocaleString()}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-700 dark:text-gray-300">
                        {new Date(task.updated_at).toLocaleString()}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                        <div className="flex justify-end space-x-2">
                          <a
                            href={task.url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-primary-600 hover:text-primary-900 dark:text-primary-400 dark:hover:text-primary-300"
                            title="URLを開く"
                          >
                            <FiExternalLink />
                          </a>

                          {task.status === 'FAILED' && (
                            <button
                              onClick={() => handleRetryTask(task.id)}
                              className="text-green-600 hover:text-green-900 dark:text-green-400 dark:hover:text-green-300"
                              title="再試行"
                            >
                              <FiPlay />
                            </button>
                          )}

                          {task.status === 'RUNNING' && (
                            <button
                              onClick={() => handleCancelTask(task.id)}
                              className="text-yellow-600 hover:text-yellow-900 dark:text-yellow-400 dark:hover:text-yellow-300"
                              title="キャンセル"
                            >
                              <FiPause />
                            </button>
                          )}

                          <button
                            onClick={() => handleDeleteTask(task.id)}
                            className="text-red-600 hover:text-red-900 dark:text-red-400 dark:hover:text-red-300"
                            title="削除"
                          >
                            <FiTrash2 />
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          <div className="flex justify-between items-center mt-6">
            <div className="text-sm text-gray-700 dark:text-gray-300">
              {page} / {totalPages} ページ目を表示
            </div>
            <div className="flex space-x-2">
              <button
                onClick={() => setPage(Math.max(1, page - 1))}
                disabled={page === 1}
                className={`px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-md ${
                  page === 1
                    ? 'opacity-50 cursor-not-allowed'
                    : 'hover:bg-gray-100 dark:hover:bg-gray-700'
                } transition-colors`}
              >
                前へ
              </button>
              <button
                onClick={() => setPage(Math.min(totalPages, page + 1))}
                disabled={page === totalPages}
                className={`px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-md ${
                  page === totalPages
                    ? 'opacity-50 cursor-not-allowed'
                    : 'hover:bg-gray-100 dark:hover:bg-gray-700'
                } transition-colors`}
              >
                次へ
              </button>
            </div>
          </div>
        </>
      )}
    </div>
  );
};

export default Tasks;
