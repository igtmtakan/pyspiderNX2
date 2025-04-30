import React, { useState, useEffect, useRef } from 'react';
import { FiPlay, FiPause, FiRefreshCw, FiDownload, FiCopy, FiTrash2, FiSave } from 'react-icons/fi';
import MonacoEditor from '@monaco-editor/react';

interface DebugPanelProps {
  projectId: number;
  script: string;
  onRunTest: (url: string, fetcherType: string, callbackType: string) => Promise<any>;
  onFollowUrl: (url: string, fetcherType: string, callbackType: string) => Promise<any>;
  onSaveResult: (result: any) => Promise<void>;
  onSaveFollows?: (follows: string[]) => Promise<void>;
}

const DebugPanel: React.FC<DebugPanelProps> = ({
  projectId,
  script,
  onRunTest,
  onFollowUrl,
  onSaveResult,
  onSaveFollows,
}) => {
  const [testUrl, setTestUrl] = useState<string>('');
  const [fetcherType, setFetcherType] = useState<string>('requests');
  const [callbackType, setCallbackType] = useState<string>('auto');
  const [loading, setLoading] = useState<boolean>(false);
  const [result, setResult] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'response' | 'parsed' | 'follows' | 'json_editor'>('response');
  const [jsonEditorValue, setJsonEditorValue] = useState<string>('{}');
  const [follows, setFollows] = useState<string[]>([]);

  const responseRef = useRef<HTMLDivElement>(null);

  // 利用可能なフェッチャーのリスト
  const availableFetchers = [
    { value: 'requests', label: 'Requests' },
    { value: 'playwright', label: 'Playwright' },
    { value: 'puppeteer', label: 'Puppeteer' }
  ];

  // 利用可能なコールバック関数のリスト
  const availableCallbacks = [
    { value: 'auto', label: '自動選択' },
    { value: 'on_start', label: 'on_start' },
    { value: 'index_page', label: 'index_page' },
    { value: 'detail_page', label: 'detail_page' },
    { value: 'on_result', label: 'on_result' }
  ];

  // URLからドメインを抽出する関数
  const extractDomain = (url: string): string => {
    try {
      const urlObj = new URL(url);
      return urlObj.hostname;
    } catch (e) {
      return '';
    }
  };

  // フォローURLの数値を解釈する関数
  const interpretFollowValue = (value: number): string => {
    switch (value) {
      case 1:
        return 'detail_page';
      case 2:
        return 'index_page';
      default:
        return 'unknown';
    }
  };

  // テストURLを実行
  const handleRunTest = async () => {
    if (!testUrl) {
      setError('URLを入力してください');
      return;
    }

    setLoading(true);
    setError(null);
    setResult(null);
    setFollows([]);

    try {
      const data = await onRunTest(testUrl, fetcherType, callbackType);
      setResult(data);

      // フォローURLを抽出
      if (data && data.follows && Array.isArray(data.follows)) {
        setFollows(data.follows);
      }

      setActiveTab('response');
    } catch (err: any) {
      console.error('Error running test:', err);
      setError(err.response?.data?.error || 'テスト実行中にエラーが発生しました');
    } finally {
      setLoading(false);
    }
  };

  // フォローURLを実行
  const handleFollowUrl = async (url: string) => {
    setLoading(true);
    setError(null);

    try {
      const data = await onFollowUrl(url, fetcherType, callbackType);
      setResult(data);

      // フォローURLを抽出して更新
      if (data && data.follows && Array.isArray(data.follows)) {
        setFollows(data.follows);
      }

      setActiveTab('response');
    } catch (err: any) {
      console.error('Error following URL:', err);
      setError(err.response?.data?.error || 'URL取得中にエラーが発生しました');
    } finally {
      setLoading(false);
    }
  };

  // 結果をコピー
  const handleCopyResult = () => {
    if (!result) return;

    const resultText = JSON.stringify(result, null, 2);
    navigator.clipboard.writeText(resultText)
      .then(() => {
        alert('結果をクリップボードにコピーしました');
      })
      .catch((err) => {
        console.error('Failed to copy result:', err);
        alert('結果のコピーに失敗しました');
      });
  };

  // 結果をダウンロード
  const handleDownloadResult = () => {
    if (!result) return;

    const resultText = JSON.stringify(result, null, 2);
    const blob = new Blob([resultText], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `result-${new Date().toISOString()}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  // 結果を保存
  const handleSaveResult = async () => {
    if (!result) return;

    try {
      await onSaveResult(result);
      alert('結果を保存しました');
    } catch (err: any) {
      console.error('Error saving result:', err);
      alert('結果の保存に失敗しました');
    }
  };

  // フォローURLをタスクとして保存
  const handleSaveFollows = async () => {
    if (!follows.length || !onSaveFollows) return;

    try {
      setLoading(true);
      await onSaveFollows(follows);
      alert(`${follows.length}件のURLをタスクとして保存しました`);
    } catch (err: any) {
      console.error('Error saving follows:', err);
      alert('フォローURLの保存に失敗しました');
    } finally {
      setLoading(false);
    }
  };

  // 結果をクリア
  const handleClearResult = () => {
    setResult(null);
    setFollows([]);
    setError(null);
  };

  // 自動的にURLを入力欄に設定
  useEffect(() => {
    // スクリプトからURLを抽出
    const urlMatch = script.match(/self\.crawl\(['"]([^'"]+)['"]/);
    if (urlMatch && urlMatch[1]) {
      setTestUrl(urlMatch[1]);
    }
  }, [script]);

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-4 h-full overflow-auto">
      <h2 className="text-lg font-semibold mb-4 text-gray-700 dark:text-gray-200">デバッグパネル</h2>

      <div className="mb-4">
        <div className="flex space-x-2 mb-2">
          <input
            type="text"
            value={testUrl}
            onChange={(e) => setTestUrl(e.target.value)}
            placeholder="テストするURL"
            className="flex-1 px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:outline-none focus:ring-primary-500 focus:border-primary-500 dark:bg-gray-700 dark:text-white"
            disabled={loading}
          />
          <button
            onClick={handleRunTest}
            disabled={loading}
            className={`px-4 py-2 bg-primary-500 text-white rounded-md hover:bg-primary-600 transition-colors ${
              loading ? 'opacity-70 cursor-not-allowed' : ''
            }`}
          >
            {loading ? (
              <FiRefreshCw className="animate-spin" />
            ) : (
              <FiPlay />
            )}
            <span className="ml-2">実行</span>
          </button>
        </div>

        <div className="flex space-x-2 mb-2">
          <div className="flex-1">
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              フェッチャー
            </label>
            <select
              value={fetcherType}
              onChange={(e) => setFetcherType(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:outline-none focus:ring-primary-500 focus:border-primary-500 dark:bg-gray-700 dark:text-white"
              disabled={loading}
            >
              {availableFetchers.map((fetcher) => (
                <option key={fetcher.value} value={fetcher.value}>
                  {fetcher.label}
                </option>
              ))}
            </select>
          </div>

          <div className="flex-1">
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              コールバック関数
            </label>
            <select
              value={callbackType}
              onChange={(e) => setCallbackType(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:outline-none focus:ring-primary-500 focus:border-primary-500 dark:bg-gray-700 dark:text-white"
              disabled={loading}
            >
              {availableCallbacks.map((callback) => (
                <option key={callback.value} value={callback.value}>
                  {callback.label}
                </option>
              ))}
            </select>
          </div>
        </div>

        {error && (
          <div className="mt-2 p-2 bg-red-100 text-red-700 dark:bg-red-900 dark:text-red-300 rounded-md text-sm">
            {error}
          </div>
        )}
      </div>

      {result && (
        <div className="border border-gray-300 dark:border-gray-600 rounded-md overflow-hidden">
          <div className="flex border-b border-gray-300 dark:border-gray-600">
            <button
              className={`px-4 py-2 text-sm ${
                activeTab === 'response'
                  ? 'bg-primary-100 dark:bg-primary-900 text-primary-700 dark:text-primary-300 font-medium'
                  : 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300'
              }`}
              onClick={() => setActiveTab('response')}
            >
              レスポンス
            </button>
            <button
              className={`px-4 py-2 text-sm ${
                activeTab === 'parsed'
                  ? 'bg-primary-100 dark:bg-primary-900 text-primary-700 dark:text-primary-300 font-medium'
                  : 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300'
              }`}
              onClick={() => setActiveTab('parsed')}
            >
              パース結果
            </button>
            <button
              className={`px-4 py-2 text-sm ${
                activeTab === 'json_editor'
                  ? 'bg-primary-100 dark:bg-primary-900 text-primary-700 dark:text-primary-300 font-medium'
                  : 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300'
              }`}
              onClick={() => {
                // JSONエディタを開くときに現在の結果をセット
                if (result && result.result) {
                  try {
                    setJsonEditorValue(JSON.stringify(result.result, null, 2));
                  } catch (e) {
                    setJsonEditorValue('{}');
                  }
                }
                setActiveTab('json_editor');
              }}
            >
              JSONエディタ
            </button>
            <button
              className={`px-4 py-2 text-sm ${
                activeTab === 'follows'
                  ? 'bg-primary-100 dark:bg-primary-900 text-primary-700 dark:text-primary-300 font-medium'
                  : 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300'
              } ${follows.length > 0 ? 'relative' : ''}`}
              onClick={() => setActiveTab('follows')}
            >
              フォローURL
              {follows.length > 0 && (
                <span className="absolute top-1 right-1 bg-primary-500 text-white text-xs rounded-full w-4 h-4 flex items-center justify-center">
                  {follows.length}
                </span>
              )}
            </button>

            <div className="flex-1"></div>

            <button
              onClick={handleCopyResult}
              className="px-2 py-2 text-gray-600 dark:text-gray-400 hover:text-gray-800 dark:hover:text-gray-200"
              title="結果をコピー"
            >
              <FiCopy />
            </button>
            <button
              onClick={handleDownloadResult}
              className="px-2 py-2 text-gray-600 dark:text-gray-400 hover:text-gray-800 dark:hover:text-gray-200"
              title="結果をダウンロード"
            >
              <FiDownload />
            </button>
            <button
              onClick={handleSaveResult}
              className="px-2 py-2 text-primary-600 dark:text-primary-400 hover:text-primary-800 dark:hover:text-primary-200"
              title="結果を保存"
            >
              <FiPlay />
            </button>
            <button
              onClick={handleClearResult}
              className="px-2 py-2 text-red-600 dark:text-red-400 hover:text-red-800 dark:hover:text-red-200"
              title="結果をクリア"
            >
              <FiTrash2 />
            </button>
          </div>

          <div className="p-4">
            {activeTab === 'response' && (
              <div ref={responseRef} className="h-96 overflow-auto">
                {result.response ? (
                  <div>
                    <div className="mb-2">
                      <span className="font-medium">URL:</span> {result.response.url}
                    </div>
                    <div className="mb-2">
                      <span className="font-medium">ステータス:</span> {result.response.status_code}
                    </div>
                    <div className="mb-2">
                      <span className="font-medium">時間:</span> {result.response.time.toFixed(3)}s
                    </div>
                    <div className="mb-4">
                      <span className="font-medium">サイズ:</span> {(result.response.content?.length || 0) / 1024} KB
                    </div>

                    <div className="mb-2 font-medium">ヘッダー:</div>
                    <div className="mb-4 bg-gray-100 dark:bg-gray-700 p-2 rounded-md overflow-auto max-h-32">
                      <pre className="text-xs">{JSON.stringify(result.response.headers, null, 2)}</pre>
                    </div>

                    <div className="mb-2 font-medium">コンテンツ:</div>
                    <div className="bg-gray-100 dark:bg-gray-700 p-2 rounded-md overflow-auto max-h-96">
                      <pre className="text-xs whitespace-pre-wrap">{result.response.text}</pre>
                    </div>
                  </div>
                ) : (
                  <div className="text-gray-500 dark:text-gray-400">レスポンスデータがありません</div>
                )}
              </div>
            )}

            {activeTab === 'parsed' && (
              <div className="h-96">
                <MonacoEditor
                  height="100%"
                  language="json"
                  theme="vs-dark"
                  value={JSON.stringify(result.result || {}, null, 2)}
                  options={{
                    readOnly: true,
                    minimap: { enabled: false },
                    scrollBeyondLastLine: false,
                    fontSize: 14,
                  }}
                />
              </div>
            )}

            {activeTab === 'follows' && (
              <div className="h-96 overflow-auto">
                {follows.length > 0 ? (
                  <div className="space-y-4">
                    <p className="text-sm text-gray-500 dark:text-gray-400">
                      以下のURLをクリックすると、そのURLに対してスクレイピングを実行します。
                    </p>
                    <div className="overflow-y-auto h-full">
                      <div className="flex justify-between mb-2">
                        <div className="flex items-center space-x-2">
                          <div className="text-sm text-gray-500 dark:text-gray-400">
                            合計: {follows.length} URL
                          </div>
                          {onSaveFollows && (
                            <button
                              onClick={handleSaveFollows}
                              disabled={loading}
                              className={`px-2 py-1 bg-primary-500 text-white text-xs rounded-md hover:bg-primary-600 transition-colors flex items-center ${
                                loading ? 'opacity-70 cursor-not-allowed' : ''
                              }`}
                              title="フォローURLをタスクとして保存"
                            >
                              <FiSave className="mr-1" />
                              <span>タスクとして保存</span>
                            </button>
                          )}
                        </div>
                        <div className="text-sm">
                          <select
                            className="px-2 py-1 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:outline-none focus:ring-primary-500 focus:border-primary-500 dark:bg-gray-700 dark:text-white text-xs"
                            onChange={(e) => {
                              const value = e.target.value;
                              if (value === 'domain') {
                                // ドメインでグループ化
                                const grouped = follows.reduce((acc, url) => {
                                  const domain = extractDomain(url);
                                  if (!acc[domain]) acc[domain] = [];
                                  acc[domain].push(url);
                                  return acc;
                                }, {} as Record<string, string[]>);

                                // グループ化されたURLを表示
                                const sortedDomains = Object.keys(grouped).sort();
                                const sortedFollows = sortedDomains.flatMap(domain => grouped[domain]);
                                setFollows(sortedFollows);
                              } else if (value === 'original') {
                                // 元の順序に戻す（再取得）
                                if (result && result.follows && Array.isArray(result.follows)) {
                                  setFollows(result.follows);
                                }
                              }
                            }}
                          >
                            <option value="original">元の順序</option>
                            <option value="domain">ドメインでソート</option>
                          </select>
                        </div>
                      </div>

                      <table className="min-w-full divide-y divide-gray-300 dark:divide-gray-600">
                        <thead className="bg-gray-50 dark:bg-gray-700 sticky top-0">
                          <tr>
                            <th scope="col" className="px-2 py-1 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider w-10">
                              #
                            </th>
                            <th scope="col" className="px-2 py-1 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider w-1/5">
                              ドメイン
                            </th>
                            <th scope="col" className="px-2 py-1 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                              URL
                            </th>
                            <th scope="col" className="px-2 py-1 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider w-16">
                              アクション
                            </th>
                          </tr>
                        </thead>
                        <tbody className="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-700">
                          {follows.map((url, index) => (
                            <tr key={index} className={index % 2 === 0 ? 'bg-white dark:bg-gray-800' : 'bg-gray-50 dark:bg-gray-700'}>
                              <td className="px-2 py-1 whitespace-nowrap text-xs text-gray-500 dark:text-gray-400">
                                {index + 1}
                              </td>
                              <td className="px-2 py-1 whitespace-nowrap text-xs text-gray-500 dark:text-gray-400 truncate">
                                {extractDomain(url)}
                              </td>
                              <td className="px-2 py-1 text-xs text-gray-500 dark:text-gray-400 break-all">
                                <div className="truncate max-w-xs" title={url}>
                                  {url}
                                </div>
                              </td>
                              <td className="px-2 py-1 whitespace-nowrap text-xs">
                                <button
                                  onClick={() => handleFollowUrl(url)}
                                  className="text-blue-500 hover:text-blue-700 dark:hover:text-blue-300 font-medium"
                                  disabled={loading}
                                >
                                  実行
                                </button>
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                ) : (
                  <div className="text-gray-500 dark:text-gray-400 text-center py-8">
                    フォローURLがありません
                  </div>
                )}
              </div>
            )}

            {activeTab === 'json_editor' && (
              <div className="h-96">
                <div className="flex justify-between items-center mb-2 p-2 bg-gray-100 dark:bg-gray-700">
                  <div className="text-sm text-gray-700 dark:text-gray-300">
                    JSONエディタ - 結果を編集できます
                  </div>
                  <div>
                    <button
                      onClick={() => {
                        try {
                          // JSONをパース
                          const parsedJson = JSON.parse(jsonEditorValue);

                          // 結果を更新
                          if (result) {
                            const newResult = { ...result, result: parsedJson };
                            setResult(newResult);
                          }

                          // パース結果タブに切り替え
                          setActiveTab('parsed');
                        } catch (e) {
                          alert('JSONの形式が正しくありません');
                        }
                      }}
                      className="px-3 py-1 bg-primary-500 text-white text-xs rounded-md hover:bg-primary-600 transition-colors"
                    >
                      適用
                    </button>
                  </div>
                </div>
                <MonacoEditor
                  height="calc(100% - 36px)"
                  language="json"
                  theme="vs-dark"
                  value={jsonEditorValue}
                  onChange={(value) => setJsonEditorValue(value || '{}')}
                  options={{
                    minimap: { enabled: false },
                    scrollBeyondLastLine: false,
                    fontSize: 14,
                    formatOnPaste: true,
                    formatOnType: true,
                  }}
                />
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default DebugPanel;
