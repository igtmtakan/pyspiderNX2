import { useState } from 'react';
import { FiSave, FiRefreshCw } from 'react-icons/fi';

const Settings = () => {
  const [generalSettings, setGeneralSettings] = useState({
    apiUrl: 'http://localhost:5001',
    autoRefresh: true,
    refreshInterval: 30,
    defaultPageSize: 20,
  });

  const [fetcherSettings, setFetcherSettings] = useState({
    fetcherType: 'playwright',
    headless: true,
    userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    timeout: 60,
    retries: 3,
    proxy: '',
  });

  const [schedulerSettings, setSchedulerSettings] = useState({
    defaultRate: 1.0,
    defaultBurst: 10,
    maxRunningTasks: 100,
    maxPendingTasks: 1000,
  });

  const [saving, setSaving] = useState(false);

  const handleSaveGeneral = () => {
    setSaving(true);

    // Simulate API call
    setTimeout(() => {
      setSaving(false);
    }, 1000);
  };

  const handleSaveFetcher = () => {
    setSaving(true);

    // Simulate API call
    setTimeout(() => {
      setSaving(false);
    }, 1000);
  };

  const handleSaveScheduler = () => {
    setSaving(true);

    // Simulate API call
    setTimeout(() => {
      setSaving(false);
    }, 1000);
  };

  const handleResetSettings = () => {
    if (window.confirm('Are you sure you want to reset all settings to default values?')) {
      setGeneralSettings({
        apiUrl: 'http://localhost:5000',
        autoRefresh: true,
        refreshInterval: 30,
        defaultPageSize: 20,
      });

      setFetcherSettings({
        fetcherType: 'playwright',
        headless: true,
        userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        timeout: 60,
        retries: 3,
        proxy: '',
      });

      setSchedulerSettings({
        defaultRate: 1.0,
        defaultBurst: 10,
        maxRunningTasks: 100,
        maxPendingTasks: 1000,
      });
    }
  };

  return (
    <div>
      <h1 className="text-2xl font-bold mb-6 text-gray-800 dark:text-white">Settings</h1>

      <div className="grid grid-cols-1 gap-6">
        {/* General Settings */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-lg font-semibold text-gray-700 dark:text-gray-200">General Settings</h2>
            <button
              onClick={handleSaveGeneral}
              disabled={saving}
              className={`px-4 py-2 bg-primary-500 text-white rounded-md hover:bg-primary-600 transition-colors ${
                saving ? 'opacity-50 cursor-not-allowed' : ''
              }`}
            >
              <FiSave className="inline mr-2" />
              {saving ? 'Saving...' : 'Save'}
            </button>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                API URL
              </label>
              <input
                type="text"
                value={generalSettings.apiUrl}
                onChange={(e) => setGeneralSettings({ ...generalSettings, apiUrl: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:outline-none focus:ring-primary-500 focus:border-primary-500 dark:bg-gray-700 dark:text-white"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Default Page Size
              </label>
              <input
                type="number"
                value={generalSettings.defaultPageSize}
                onChange={(e) => setGeneralSettings({ ...generalSettings, defaultPageSize: parseInt(e.target.value) })}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:outline-none focus:ring-primary-500 focus:border-primary-500 dark:bg-gray-700 dark:text-white"
                min="1"
                max="100"
              />
            </div>

            <div>
              <label className="flex items-center">
                <input
                  type="checkbox"
                  checked={generalSettings.autoRefresh}
                  onChange={(e) => setGeneralSettings({ ...generalSettings, autoRefresh: e.target.checked })}
                  className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded"
                />
                <span className="ml-2 text-sm text-gray-700 dark:text-gray-300">Auto Refresh</span>
              </label>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Refresh Interval (seconds)
              </label>
              <input
                type="number"
                value={generalSettings.refreshInterval}
                onChange={(e) => setGeneralSettings({ ...generalSettings, refreshInterval: parseInt(e.target.value) })}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:outline-none focus:ring-primary-500 focus:border-primary-500 dark:bg-gray-700 dark:text-white"
                min="5"
                max="3600"
                disabled={!generalSettings.autoRefresh}
              />
            </div>
          </div>
        </div>

        {/* Fetcher Settings */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-lg font-semibold text-gray-700 dark:text-gray-200">Fetcher Settings</h2>
            <button
              onClick={handleSaveFetcher}
              disabled={saving}
              className={`px-4 py-2 bg-primary-500 text-white rounded-md hover:bg-primary-600 transition-colors ${
                saving ? 'opacity-50 cursor-not-allowed' : ''
              }`}
            >
              <FiSave className="inline mr-2" />
              {saving ? 'Saving...' : 'Save'}
            </button>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Fetcher Type
              </label>
              <select
                value={fetcherSettings.fetcherType}
                onChange={(e) => setFetcherSettings({ ...fetcherSettings, fetcherType: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:outline-none focus:ring-primary-500 focus:border-primary-500 dark:bg-gray-700 dark:text-white"
              >
                <option value="playwright">Playwright (Python)</option>
                <option value="puppeteer">Puppeteer (Node.js)</option>
                <option value="playwright-nodejs">Playwright (Node.js)</option>
              </select>
            </div>

            <div>
              <label className="flex items-center">
                <input
                  type="checkbox"
                  checked={fetcherSettings.headless}
                  onChange={(e) => setFetcherSettings({ ...fetcherSettings, headless: e.target.checked })}
                  className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded"
                />
                <span className="ml-2 text-sm text-gray-700 dark:text-gray-300">Headless Mode</span>
              </label>
            </div>

            <div className="md:col-span-2">
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                User Agent
              </label>
              <input
                type="text"
                value={fetcherSettings.userAgent}
                onChange={(e) => setFetcherSettings({ ...fetcherSettings, userAgent: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:outline-none focus:ring-primary-500 focus:border-primary-500 dark:bg-gray-700 dark:text-white"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Timeout (seconds)
              </label>
              <input
                type="number"
                value={fetcherSettings.timeout}
                onChange={(e) => setFetcherSettings({ ...fetcherSettings, timeout: parseInt(e.target.value) })}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:outline-none focus:ring-primary-500 focus:border-primary-500 dark:bg-gray-700 dark:text-white"
                min="1"
                max="300"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Retries
              </label>
              <input
                type="number"
                value={fetcherSettings.retries}
                onChange={(e) => setFetcherSettings({ ...fetcherSettings, retries: parseInt(e.target.value) })}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:outline-none focus:ring-primary-500 focus:border-primary-500 dark:bg-gray-700 dark:text-white"
                min="0"
                max="10"
              />
            </div>

            <div className="md:col-span-2">
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Proxy (optional)
              </label>
              <input
                type="text"
                value={fetcherSettings.proxy}
                onChange={(e) => setFetcherSettings({ ...fetcherSettings, proxy: e.target.value })}
                placeholder="http://user:pass@host:port"
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:outline-none focus:ring-primary-500 focus:border-primary-500 dark:bg-gray-700 dark:text-white"
              />
            </div>
          </div>
        </div>

        {/* Scheduler Settings */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-lg font-semibold text-gray-700 dark:text-gray-200">Scheduler Settings</h2>
            <button
              onClick={handleSaveScheduler}
              disabled={saving}
              className={`px-4 py-2 bg-primary-500 text-white rounded-md hover:bg-primary-600 transition-colors ${
                saving ? 'opacity-50 cursor-not-allowed' : ''
              }`}
            >
              <FiSave className="inline mr-2" />
              {saving ? 'Saving...' : 'Save'}
            </button>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Default Rate (requests/second)
              </label>
              <input
                type="number"
                value={schedulerSettings.defaultRate}
                onChange={(e) => setSchedulerSettings({ ...schedulerSettings, defaultRate: parseFloat(e.target.value) })}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:outline-none focus:ring-primary-500 focus:border-primary-500 dark:bg-gray-700 dark:text-white"
                step="0.1"
                min="0.1"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Default Burst
              </label>
              <input
                type="number"
                value={schedulerSettings.defaultBurst}
                onChange={(e) => setSchedulerSettings({ ...schedulerSettings, defaultBurst: parseInt(e.target.value) })}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:outline-none focus:ring-primary-500 focus:border-primary-500 dark:bg-gray-700 dark:text-white"
                min="1"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Max Running Tasks
              </label>
              <input
                type="number"
                value={schedulerSettings.maxRunningTasks}
                onChange={(e) => setSchedulerSettings({ ...schedulerSettings, maxRunningTasks: parseInt(e.target.value) })}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:outline-none focus:ring-primary-500 focus:border-primary-500 dark:bg-gray-700 dark:text-white"
                min="1"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Max Pending Tasks
              </label>
              <input
                type="number"
                value={schedulerSettings.maxPendingTasks}
                onChange={(e) => setSchedulerSettings({ ...schedulerSettings, maxPendingTasks: parseInt(e.target.value) })}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:outline-none focus:ring-primary-500 focus:border-primary-500 dark:bg-gray-700 dark:text-white"
                min="1"
              />
            </div>
          </div>
        </div>

        {/* Reset Settings */}
        <div className="flex justify-end">
          <button
            onClick={handleResetSettings}
            className="px-4 py-2 bg-red-500 text-white rounded-md hover:bg-red-600 transition-colors"
          >
            <FiRefreshCw className="inline mr-2" />
            Reset to Defaults
          </button>
        </div>
      </div>
    </div>
  );
};

export default Settings;
