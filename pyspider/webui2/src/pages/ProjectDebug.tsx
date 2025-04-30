import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { FiSave, FiArrowLeft, FiRefreshCw } from 'react-icons/fi';
import MonacoEditor from '@monaco-editor/react';
import DebugPanel from '../components/DebugPanel';
import { projectsApi, debugApi } from '../api';
import { Project } from '../api/projects';

const ProjectDebug = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [project, setProject] = useState<Project | null>(null);
  const [loading, setLoading] = useState(true);
  const [script, setScript] = useState('');
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [editorHeight, setEditorHeight] = useState('calc(100vh - 200px)');

  // ウィンドウのリサイズを監視
  useEffect(() => {
    const handleResize = () => {
      setEditorHeight(`calc(100vh - 200px)`);
    };

    window.addEventListener('resize', handleResize);
    handleResize();

    return () => {
      window.removeEventListener('resize', handleResize);
    };
  }, []);

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
  }, [id]);

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

  return (
    <div>
      <div className="flex items-center mb-6">
        <button
          onClick={() => navigate(`/projects/${id}`)}
          className="mr-4 p-2 rounded-md text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700"
        >
          <FiArrowLeft />
        </button>
        {loading ? (
          <div className="h-8 w-48 bg-gray-200 dark:bg-gray-700 rounded animate-pulse"></div>
        ) : (
          <div className="flex items-center">
            <h1 className="text-2xl font-bold text-gray-800 dark:text-white mr-4">
              {project?.name} - デバッグ
            </h1>
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
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4" style={{ height: editorHeight }}>
          {/* 左側: デバッグパネル */}
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow overflow-auto">
            <DebugPanel
              projectId={project?.id ? parseInt(project.id) : 0}
              script={script}
              onRunTest={handleRunTest}
              onFollowUrl={handleFollowUrl}
              onSaveResult={handleSaveResult}
            />
          </div>

          {/* 右側: スクリプトエディタ */}
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow overflow-hidden">
            <div className="p-4 border-b border-gray-300 dark:border-gray-700 flex justify-between items-center">
              <h2 className="text-lg font-semibold text-gray-700 dark:text-gray-200">スクリプト</h2>
              <div className="flex space-x-2">
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
                <button
                  onClick={fetchProject}
                  className="px-4 py-2 bg-gray-500 text-white rounded-md hover:bg-gray-600 transition-colors"
                >
                  <FiRefreshCw className="inline mr-2" />
                  リロード
                </button>
              </div>
            </div>
            <div style={{ height: 'calc(100% - 60px)' }}>
              <MonacoEditor
                height="100%"
                language="python"
                theme="vs-dark"
                value={script}
                onChange={(value) => setScript(value || '')}
                options={{
                  minimap: { enabled: true },
                  scrollBeyondLastLine: false,
                  fontSize: 14,
                  lineNumbers: 'on',
                  renderLineHighlight: 'all',
                  automaticLayout: true,
                }}
              />
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ProjectDebug;
