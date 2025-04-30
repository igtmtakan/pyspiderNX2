import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { FiSave, FiArrowLeft } from 'react-icons/fi';
import MonacoEditor from '@monaco-editor/react';
import { projectsApi } from '../api';
import { Project } from '../api/projects';

const DEFAULT_SCRIPT = `from pyspider.core.base_handler import BaseHandler

class Handler(BaseHandler):
    crawl_config = {
        "headers": {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        }
    }

    def on_start(self):
        self.crawl("https://example.com", callback=self.index_page)

    def index_page(self, response):
        for each in response.doc("a[href^='http']").items():
            self.crawl(each.attr.href, callback=self.detail_page)

    def detail_page(self, response):
        return {
            "url": response.url,
            "title": response.doc("title").text(),
        }`;

const ProjectForm = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const isEditMode = !!id;

  const [project, setProject] = useState<Partial<Project>>({
    name: '',
    rate: 1.0,
    burst: 10,
    script: DEFAULT_SCRIPT,
    status: 'STOPPED',
  });

  const [loading, setLoading] = useState(isEditMode);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (isEditMode) {
      fetchProject();
    }
  }, [id]);

  const fetchProject = async () => {
    if (!id) return;

    setLoading(true);
    setError(null);

    try {
      const projectId = parseInt(id);
      const data = await projectsApi.getProject(projectId);
      setProject(data);
    } catch (err: any) {
      console.error('Error fetching project:', err);
      setError(err.response?.data?.error || 'プロジェクトの取得に失敗しました');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!project.name) {
      setError('プロジェクト名を入力してください');
      return;
    }

    if (!project.script) {
      setError('スクリプトを入力してください');
      return;
    }

    setSaving(true);
    setError(null);

    try {
      if (isEditMode && id) {
        const projectId = parseInt(id);
        await projectsApi.updateProject(projectId, project);
        navigate(`/projects/${projectId}`);
      } else {
        const newProject = await projectsApi.createProject(project);
        navigate(`/projects/${newProject.id}`);
      }
    } catch (err: any) {
      console.error('Error saving project:', err);
      setError(err.response?.data?.error || 'プロジェクトの保存に失敗しました');
      setSaving(false);
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
        <h1 className="text-2xl font-bold text-gray-800 dark:text-white">
          {isEditMode ? 'プロジェクトの編集' : '新規プロジェクト'}
        </h1>
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
        <form onSubmit={handleSubmit}>
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6 mb-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  プロジェクト名 <span className="text-red-500">*</span>
                </label>
                <input
                  type="text"
                  value={project.name}
                  onChange={(e) => setProject({ ...project, name: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:outline-none focus:ring-primary-500 focus:border-primary-500 dark:bg-gray-700 dark:text-white"
                  placeholder="プロジェクト名を入力"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  ステータス
                </label>
                <select
                  value={project.status}
                  onChange={(e) => setProject({ ...project, status: e.target.value as any })}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:outline-none focus:ring-primary-500 focus:border-primary-500 dark:bg-gray-700 dark:text-white"
                  disabled={!isEditMode}
                >
                  <option value="STOPPED">停止</option>
                  <option value="RUNNING">実行中</option>
                  <option value="PAUSED">一時停止</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  レート（リクエスト/秒）
                </label>
                <input
                  type="number"
                  value={project.rate}
                  onChange={(e) => setProject({ ...project, rate: parseFloat(e.target.value) })}
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
                  value={project.burst}
                  onChange={(e) => setProject({ ...project, burst: parseInt(e.target.value) })}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:outline-none focus:ring-primary-500 focus:border-primary-500 dark:bg-gray-700 dark:text-white"
                  step="1"
                  min="1"
                />
              </div>
            </div>
          </div>

          <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6 mb-6">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-lg font-semibold text-gray-700 dark:text-gray-200">スクリプト <span className="text-red-500">*</span></h2>
            </div>
            <div className="h-96 border border-gray-300 dark:border-gray-600 rounded-md overflow-hidden">
              <MonacoEditor
                height="100%"
                language="python"
                theme="vs-dark"
                value={project.script}
                onChange={(value) => setProject({ ...project, script: value || '' })}
                options={{
                  minimap: { enabled: false },
                  scrollBeyondLastLine: false,
                  fontSize: 14,
                }}
              />
            </div>
          </div>

          <div className="flex justify-end">
            <button
              type="button"
              onClick={() => navigate('/projects')}
              className="px-4 py-2 border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 rounded-md hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors mr-2"
            >
              キャンセル
            </button>
            <button
              type="submit"
              disabled={saving}
              className={`px-4 py-2 bg-primary-500 text-white rounded-md hover:bg-primary-600 transition-colors ${
                saving ? 'opacity-50 cursor-not-allowed' : ''
              }`}
            >
              <FiSave className="inline mr-2" />
              {saving ? '保存中...' : '保存'}
            </button>
          </div>
        </form>
      )}
    </div>
  );
};

export default ProjectForm;
