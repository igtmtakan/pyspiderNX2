import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { FiRefreshCw, FiExternalLink, FiEye, FiDownload, FiTrash2 } from 'react-icons/fi';
import { resultsApi, projectsApi } from '../api';
import { Result } from '../api/results';
import { Project } from '../api/projects';

const Results = () => {
  const [results, setResults] = useState<Result[]>([]);
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [filter, setFilter] = useState('');
  const [projectFilter, setProjectFilter] = useState<number | ''>('');
  const [selectedResult, setSelectedResult] = useState<Result | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [itemsPerPage] = useState(10);

  useEffect(() => {
    loadProjects();
    loadResults();
  }, [page, projectFilter]);

  const loadProjects = async () => {
    try {
      const data = await projectsApi.getProjects();
      setProjects(data);
    } catch (err: any) {
      console.error('Error fetching projects:', err);
      setError(err.response?.data?.error || 'プロジェクトの取得に失敗しました');
    }
  };

  const loadResults = async () => {
    setLoading(true);
    setError(null);

    try {
      const params: any = {
        skip: (page - 1) * itemsPerPage,
        limit: itemsPerPage,
      };

      if (projectFilter) {
        params.project_id = projectFilter;
      }

      const data = await resultsApi.getResults(params);

      // フィルタリング（URLによる）
      const filteredData = filter
        ? data.filter(result => result.url.toLowerCase().includes(filter.toLowerCase()))
        : data;

      setResults(filteredData);

      // 最初の結果を選択
      if (filteredData.length > 0 && !selectedResult) {
        setSelectedResult(filteredData[0]);
      } else if (filteredData.length === 0) {
        setSelectedResult(null);
      }

      // 合計ページ数の計算（実際のAPIでは、合計数を返すエンドポイントが必要）
      // ここでは簡易的に実装
      setTotalPages(Math.max(1, Math.ceil(data.length / itemsPerPage)));
    } catch (err: any) {
      console.error('Error fetching results:', err);
      setError(err.response?.data?.error || '結果の取得に失敗しました');
    } finally {
      setLoading(false);
    }
  };

  const handleRefresh = () => {
    loadResults();
  };

  const handleViewResult = (result: Result) => {
    setSelectedResult(result);
  };

  const handleDownloadResult = (result: Result) => {
    const resultText = JSON.stringify(result.data, null, 2);
    const blob = new Blob([resultText], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `result-${result.id}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const handleDeleteResult = async (resultId: number) => {
    if (!confirm('この結果を削除してもよろしいですか？')) {
      return;
    }

    try {
      await resultsApi.deleteResult(resultId);

      // 選択中の結果が削除された場合、選択を解除
      if (selectedResult && selectedResult.id === resultId) {
        setSelectedResult(null);
      }

      loadResults();
    } catch (err: any) {
      console.error('Error deleting result:', err);
      setError(err.response?.data?.error || '結果の削除に失敗しました');
    }
  };

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold text-gray-800 dark:text-white">結果</h1>
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

          <div className="flex items-end">
            <button
              onClick={() => {
                setFilter('');
                setProjectFilter('');
                loadResults();
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
      ) : results.length === 0 ? (
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-8 text-center">
          <p className="text-gray-600 dark:text-gray-400 mb-4">結果が見つかりません</p>
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
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <div className="lg:col-span-2">
              <div className="bg-white dark:bg-gray-800 rounded-lg shadow overflow-hidden">
                <div className="overflow-x-auto">
                  <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
                    <thead className="bg-gray-50 dark:bg-gray-700">
                      <tr>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">URL</th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">プロジェクト</th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">作成日時</th>
                        <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">アクション</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
                      {results.map((result) => (
                        <tr
                          key={result.id}
                          className={selectedResult?.id === result.id ? 'bg-primary-50 dark:bg-primary-900' : ''}
                          onClick={() => handleViewResult(result)}
                          style={{ cursor: 'pointer' }}
                        >
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-700 dark:text-gray-300">
                            <div className="max-w-xs truncate">{result.url}</div>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-700 dark:text-gray-300">
                            <Link
                              to={`/projects/${result.project_id}`}
                              className="text-primary-600 hover:text-primary-900 dark:text-primary-400 dark:hover:text-primary-300"
                              onClick={(e) => e.stopPropagation()}
                            >
                              {projects.find(p => p.id === result.project_id)?.name || `プロジェクト ${result.project_id}`}
                            </Link>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-700 dark:text-gray-300">
                            {new Date(result.created_at).toLocaleString()}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                            <div className="flex justify-end space-x-2">
                              <button
                                onClick={(e) => {
                                  e.stopPropagation();
                                  handleViewResult(result);
                                }}
                                className="text-primary-600 hover:text-primary-900 dark:text-primary-400 dark:hover:text-primary-300"
                                title="詳細を表示"
                              >
                                <FiEye />
                              </button>
                              <a
                                href={result.url}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="text-primary-600 hover:text-primary-900 dark:text-primary-400 dark:hover:text-primary-300"
                                onClick={(e) => e.stopPropagation()}
                                title="URLを開く"
                              >
                                <FiExternalLink />
                              </a>
                              <button
                                onClick={(e) => {
                                  e.stopPropagation();
                                  handleDownloadResult(result);
                                }}
                                className="text-primary-600 hover:text-primary-900 dark:text-primary-400 dark:hover:text-primary-300"
                                title="ダウンロード"
                              >
                                <FiDownload />
                              </button>
                              <button
                                onClick={(e) => {
                                  e.stopPropagation();
                                  handleDeleteResult(result.id);
                                }}
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
            </div>

            <div>
              <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6 sticky top-6">
                <h2 className="text-lg font-semibold mb-4 text-gray-700 dark:text-gray-200">結果の詳細</h2>

                {selectedResult ? (
                  <div>
                    <div className="mb-4">
                      <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400">URL</h3>
                      <p className="mt-1 text-sm text-gray-800 dark:text-gray-200 break-all">
                        <a
                          href={selectedResult.url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-primary-600 hover:text-primary-900 dark:text-primary-400 dark:hover:text-primary-300"
                        >
                          {selectedResult.url}
                        </a>
                      </p>
                    </div>

                    <div className="mb-4">
                      <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400">プロジェクト</h3>
                      <p className="mt-1 text-sm text-gray-800 dark:text-gray-200">
                        <Link
                          to={`/projects/${selectedResult.project_id}`}
                          className="text-primary-600 hover:text-primary-900 dark:text-primary-400 dark:hover:text-primary-300"
                        >
                          {projects.find(p => p.id === selectedResult.project_id)?.name || `プロジェクト ${selectedResult.project_id}`}
                        </Link>
                      </p>
                    </div>

                    <div className="mb-4">
                      <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400">作成日時</h3>
                      <p className="mt-1 text-sm text-gray-800 dark:text-gray-200">
                        {new Date(selectedResult.created_at).toLocaleString()}
                      </p>
                    </div>

                    <div className="mb-4">
                      <div className="flex justify-between items-center">
                        <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400">データ</h3>
                        <div className="flex space-x-2">
                          <button
                            onClick={() => handleDownloadResult(selectedResult)}
                            className="text-primary-600 hover:text-primary-900 dark:text-primary-400 dark:hover:text-primary-300"
                            title="ダウンロード"
                          >
                            <FiDownload />
                          </button>
                        </div>
                      </div>
                      <div className="mt-2 p-3 bg-gray-100 dark:bg-gray-700 rounded-md overflow-auto max-h-96">
                        <pre className="text-xs text-gray-800 dark:text-gray-200">
                          {JSON.stringify(selectedResult.data, null, 2)}
                        </pre>
                      </div>
                    </div>

                    <div className="flex justify-end">
                      <button
                        onClick={() => handleDeleteResult(selectedResult.id)}
                        className="px-3 py-1 bg-red-500 text-white rounded-md hover:bg-red-600 transition-colors"
                      >
                        <FiTrash2 className="inline mr-1" />
                        削除
                      </button>
                    </div>
                  </div>
                ) : (
                  <div className="text-center py-8 text-gray-500 dark:text-gray-400">
                    結果を選択して詳細を表示
                  </div>
                )}
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  );
};

export default Results;
