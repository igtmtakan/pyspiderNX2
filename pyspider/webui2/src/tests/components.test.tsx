import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { AuthProvider } from '../contexts/AuthContext';
import ProtectedRoute from '../components/ProtectedRoute';
import Layout from '../components/Layout';
import DebugPanel from '../components/DebugPanel';

// Mock the useAuth hook
jest.mock('../contexts/AuthContext', () => ({
  AuthProvider: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
  useAuth: () => ({
    user: { id: 1, username: 'admin', role: 'admin' },
    isAuthenticated: true,
    isLoading: false,
    login: jest.fn(),
    logout: jest.fn(),
    checkAuth: jest.fn(),
  }),
}));

// Mock the monaco editor
jest.mock('@monaco-editor/react', () => {
  return ({ value, onChange }: any) => (
    <div data-testid="monaco-editor">
      <textarea
        data-testid="monaco-textarea"
        value={value}
        onChange={(e) => onChange && onChange(e.target.value)}
      />
    </div>
  );
});

describe('Layout Component', () => {
  test('renders layout with sidebar and content', () => {
    render(
      <BrowserRouter>
        <Layout darkMode={false} toggleDarkMode={jest.fn()}>
          <div data-testid="content">Content</div>
        </Layout>
      </BrowserRouter>
    );

    // Check if sidebar is rendered
    expect(screen.getByText('ダッシュボード')).toBeInTheDocument();
    expect(screen.getByText('プロジェクト')).toBeInTheDocument();
    expect(screen.getByText('タスク')).toBeInTheDocument();
    expect(screen.getByText('結果')).toBeInTheDocument();
    expect(screen.getByText('設定')).toBeInTheDocument();

    // Check if content is rendered
    expect(screen.getByTestId('content')).toBeInTheDocument();
  });

  test('toggles sidebar on mobile', () => {
    render(
      <BrowserRouter>
        <Layout darkMode={false} toggleDarkMode={jest.fn()}>
          <div>Content</div>
        </Layout>
      </BrowserRouter>
    );

    // Sidebar should be hidden on mobile by default
    const sidebar = screen.getByTestId('sidebar');
    expect(sidebar).toHaveClass('hidden');

    // Click the menu button to show sidebar
    const menuButton = screen.getByLabelText('Toggle sidebar');
    fireEvent.click(menuButton);

    // Sidebar should be visible
    expect(sidebar).not.toHaveClass('hidden');

    // Click the menu button again to hide sidebar
    fireEvent.click(menuButton);

    // Sidebar should be hidden again
    expect(sidebar).toHaveClass('hidden');
  });
});

describe('ProtectedRoute Component', () => {
  test('renders children when authenticated', () => {
    render(
      <BrowserRouter>
        <ProtectedRoute>
          <div data-testid="protected-content">Protected Content</div>
        </ProtectedRoute>
      </BrowserRouter>
    );

    expect(screen.getByTestId('protected-content')).toBeInTheDocument();
  });
});

describe('DebugPanel Component', () => {
  const mockRunTest = jest.fn().mockResolvedValue({
    response: {
      url: 'https://example.com',
      status_code: 200,
      headers: { 'Content-Type': 'text/html' },
      text: '<html><body><h1>Example</h1></body></html>',
      time: 0.1,
      orig_url: 'https://example.com',
    },
    result: { title: 'Example' },
    follows: ['https://example.com/page1', 'https://example.com/page2'],
  });

  const mockFollowUrl = jest.fn().mockResolvedValue({
    response: {
      url: 'https://example.com/page1',
      status_code: 200,
      headers: { 'Content-Type': 'text/html' },
      text: '<html><body><h1>Page 1</h1></body></html>',
      time: 0.1,
      orig_url: 'https://example.com/page1',
    },
    result: { title: 'Page 1' },
    follows: [],
  });

  const mockSaveResult = jest.fn().mockResolvedValue({});

  test('renders debug panel with URL input', () => {
    render(
      <DebugPanel
        projectId={1}
        script="script"
        onRunTest={mockRunTest}
        onFollowUrl={mockFollowUrl}
        onSaveResult={mockSaveResult}
      />
    );

    expect(screen.getByText('デバッグパネル')).toBeInTheDocument();
    expect(screen.getByPlaceholderText('テストするURL')).toBeInTheDocument();
    expect(screen.getByText('実行')).toBeInTheDocument();
  });

  test('runs test when button is clicked', async () => {
    render(
      <DebugPanel
        projectId={1}
        script="script"
        onRunTest={mockRunTest}
        onFollowUrl={mockFollowUrl}
        onSaveResult={mockSaveResult}
      />
    );

    // Enter URL
    const urlInput = screen.getByPlaceholderText('テストするURL');
    fireEvent.change(urlInput, { target: { value: 'https://example.com' } });

    // Click run button
    const runButton = screen.getByText('実行');
    fireEvent.click(runButton);

    // Check if onRunTest was called with the correct URL
    expect(mockRunTest).toHaveBeenCalledWith('https://example.com');
  });
});
