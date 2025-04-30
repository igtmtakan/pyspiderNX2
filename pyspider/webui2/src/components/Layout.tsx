import { ReactNode } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { FiHome, FiList, FiCheckSquare, FiDatabase, FiSettings, FiSun, FiMoon, FiLogOut, FiUser, FiActivity } from 'react-icons/fi';
import { useAuth } from '../contexts/AuthContext';

interface LayoutProps {
  children: ReactNode;
  darkMode: boolean;
  toggleDarkMode: () => void;
}

const Layout = ({ children, darkMode, toggleDarkMode }: LayoutProps) => {
  const location = useLocation();
  const navigate = useNavigate();
  const { user, logout } = useAuth();

  const isActive = (path: string) => {
    return location.pathname === path;
  };

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <div className="flex h-screen bg-gray-100 dark:bg-gray-900">
      {/* Sidebar */}
      <div className="w-64 bg-white dark:bg-gray-800 shadow-md">
        <div className="p-4 border-b border-gray-200 dark:border-gray-700">
          <h1 className="text-2xl font-bold text-primary-600 dark:text-primary-400">PySpiderNX3</h1>
          <p className="text-sm text-gray-500 dark:text-gray-400">Web Crawler System</p>
        </div>
        <nav className="p-4">
          <ul className="space-y-2">
            <li>
              <Link
                to="/"
                className={`flex items-center p-2 rounded-md ${
                  isActive('/')
                    ? 'bg-primary-100 text-primary-700 dark:bg-primary-900 dark:text-primary-300'
                    : 'text-gray-700 hover:bg-gray-100 dark:text-gray-300 dark:hover:bg-gray-700'
                }`}
              >
                <FiHome className="mr-3" />
                Dashboard
              </Link>
            </li>
            <li>
              <Link
                to="/projects"
                className={`flex items-center p-2 rounded-md ${
                  isActive('/projects')
                    ? 'bg-primary-100 text-primary-700 dark:bg-primary-900 dark:text-primary-300'
                    : 'text-gray-700 hover:bg-gray-100 dark:text-gray-300 dark:hover:bg-gray-700'
                }`}
              >
                <FiList className="mr-3" />
                Projects
              </Link>
            </li>
            <li>
              <Link
                to="/tasks"
                className={`flex items-center p-2 rounded-md ${
                  isActive('/tasks')
                    ? 'bg-primary-100 text-primary-700 dark:bg-primary-900 dark:text-primary-300'
                    : 'text-gray-700 hover:bg-gray-100 dark:text-gray-300 dark:hover:bg-gray-700'
                }`}
              >
                <FiCheckSquare className="mr-3" />
                Tasks
              </Link>
            </li>
            <li>
              <Link
                to="/results"
                className={`flex items-center p-2 rounded-md ${
                  isActive('/results')
                    ? 'bg-primary-100 text-primary-700 dark:bg-primary-900 dark:text-primary-300'
                    : 'text-gray-700 hover:bg-gray-100 dark:text-gray-300 dark:hover:bg-gray-700'
                }`}
              >
                <FiDatabase className="mr-3" />
                Results
              </Link>
            </li>
            <li>
              <Link
                to="/monitor"
                className={`flex items-center p-2 rounded-md ${
                  isActive('/monitor')
                    ? 'bg-primary-100 text-primary-700 dark:bg-primary-900 dark:text-primary-300'
                    : 'text-gray-700 hover:bg-gray-100 dark:text-gray-300 dark:hover:bg-gray-700'
                }`}
              >
                <FiActivity className="mr-3" />
                Monitor
              </Link>
            </li>
            <li>
              <Link
                to="/settings"
                className={`flex items-center p-2 rounded-md ${
                  isActive('/settings')
                    ? 'bg-primary-100 text-primary-700 dark:bg-primary-900 dark:text-primary-300'
                    : 'text-gray-700 hover:bg-gray-100 dark:text-gray-300 dark:hover:bg-gray-700'
                }`}
              >
                <FiSettings className="mr-3" />
                Settings
              </Link>
            </li>
          </ul>
        </nav>
      </div>

      {/* Main content */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Header */}
        <header className="bg-white dark:bg-gray-800 shadow-sm">
          <div className="flex items-center justify-between p-4">
            <div className="flex items-center">
              <div className="flex items-center text-gray-700 dark:text-gray-300">
                <FiUser className="mr-2" />
                <span className="font-medium">{user?.username || 'ゲスト'}</span>
                {user?.role === 'admin' && (
                  <span className="ml-2 px-2 py-1 text-xs rounded-full bg-primary-100 text-primary-800 dark:bg-primary-900 dark:text-primary-300">
                    管理者
                  </span>
                )}
              </div>
            </div>
            <div className="flex items-center space-x-2">
              <button
                onClick={toggleDarkMode}
                className="p-2 rounded-md text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700"
                aria-label="Toggle dark mode"
              >
                {darkMode ? <FiSun /> : <FiMoon />}
              </button>
              <button
                onClick={handleLogout}
                className="p-2 rounded-md text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700"
                aria-label="Logout"
              >
                <FiLogOut />
              </button>
            </div>
          </div>
        </header>

        {/* Content */}
        <main className="flex-1 overflow-auto p-6 bg-gray-100 dark:bg-gray-900">
          {children}
        </main>
      </div>
    </div>
  );
};

export default Layout;
