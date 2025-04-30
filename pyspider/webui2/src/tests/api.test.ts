import axios from 'axios';
import MockAdapter from 'axios-mock-adapter';
import { projectsApi } from '../api';
import { tasksApi } from '../api';
import { resultsApi } from '../api';
import { authApi } from '../api';

// Create a mock for axios
const mock = new MockAdapter(axios);

describe('API Client Tests', () => {
  afterEach(() => {
    // Reset the mock after each test
    mock.reset();
  });

  // Auth API Tests
  describe('Auth API', () => {
    test('login should return user and tokens', async () => {
      const mockResponse = {
        user: { id: 1, username: 'admin', role: 'admin' },
        access_token: 'access_token',
        refresh_token: 'refresh_token',
      };

      mock.onPost('/api/auth/login').reply(200, mockResponse);

      const result = await authApi.login({ username: 'admin', password: 'admin' });
      expect(result).toEqual(mockResponse);
    });

    test('getCurrentUser should return user data', async () => {
      const mockUser = { id: 1, username: 'admin', role: 'admin' };
      mock.onGet('/api/auth/me').reply(200, mockUser);

      const result = await authApi.getCurrentUser();
      expect(result).toEqual(mockUser);
    });
  });

  // Projects API Tests
  describe('Projects API', () => {
    test('getProjects should return projects list', async () => {
      const mockProjects = [
        { id: 1, name: 'Project 1', status: 'RUNNING' },
        { id: 2, name: 'Project 2', status: 'STOPPED' },
      ];

      mock.onGet('/api/projects').reply(200, mockProjects);

      const result = await projectsApi.getProjects();
      expect(result).toEqual(mockProjects);
    });

    test('getProject should return project details', async () => {
      const mockProject = { id: 1, name: 'Project 1', status: 'RUNNING' };
      mock.onGet('/api/projects/1').reply(200, mockProject);

      const result = await projectsApi.getProject(1);
      expect(result).toEqual(mockProject);
    });

    test('createProject should create and return new project', async () => {
      const newProject = { name: 'New Project', script: 'script', status: 'STOPPED' };
      const mockResponse = { id: 3, ...newProject };

      mock.onPost('/api/projects').reply(201, mockResponse);

      const result = await projectsApi.createProject(newProject);
      expect(result).toEqual(mockResponse);
    });

    test('updateProject should update and return project', async () => {
      const updatedProject = { name: 'Updated Project', script: 'updated script' };
      const mockResponse = { id: 1, ...updatedProject, status: 'RUNNING' };

      mock.onPut('/api/projects/1').reply(200, mockResponse);

      const result = await projectsApi.updateProject(1, updatedProject);
      expect(result).toEqual(mockResponse);
    });

    test('deleteProject should return success', async () => {
      mock.onDelete('/api/projects/1').reply(204);

      const result = await projectsApi.deleteProject(1);
      expect(result).toBe(true);
    });

    test('startProject should return success', async () => {
      mock.onPost('/api/projects/1/start').reply(200, { success: true });

      const result = await projectsApi.startProject(1);
      expect(result.success).toBe(true);
    });

    test('pauseProject should return success', async () => {
      mock.onPost('/api/projects/1/pause').reply(200, { success: true });

      const result = await projectsApi.pauseProject(1);
      expect(result.success).toBe(true);
    });

    test('stopProject should return success', async () => {
      mock.onPost('/api/projects/1/stop').reply(200, { success: true });

      const result = await projectsApi.stopProject(1);
      expect(result.success).toBe(true);
    });
  });

  // Tasks API Tests
  describe('Tasks API', () => {
    test('getTasks should return tasks list', async () => {
      const mockTasks = [
        { id: 1, url: 'https://example.com/1', status: 'SUCCESS' },
        { id: 2, url: 'https://example.com/2', status: 'FAILED' },
      ];

      mock.onGet('/api/tasks').reply(200, mockTasks);

      const result = await tasksApi.getTasks();
      expect(result).toEqual(mockTasks);
    });

    test('getTask should return task details', async () => {
      const mockTask = { id: 1, url: 'https://example.com/1', status: 'SUCCESS' };
      mock.onGet('/api/tasks/1').reply(200, mockTask);

      const result = await tasksApi.getTask(1);
      expect(result).toEqual(mockTask);
    });

    test('updateTaskStatus should update task status', async () => {
      const mockResponse = { id: 1, status: 'PENDING' };
      mock.onPut('/api/tasks/1/status').reply(200, mockResponse);

      const result = await tasksApi.updateTaskStatus(1, 'PENDING');
      expect(result).toEqual(mockResponse);
    });

    test('deleteTask should return success', async () => {
      mock.onDelete('/api/tasks/1').reply(204);

      const result = await tasksApi.deleteTask(1);
      expect(result).toBe(true);
    });
  });

  // Results API Tests
  describe('Results API', () => {
    test('getResults should return results list', async () => {
      const mockResults = [
        { id: 1, task_id: 1, data: { title: 'Result 1' } },
        { id: 2, task_id: 2, data: { title: 'Result 2' } },
      ];

      mock.onGet('/api/results').reply(200, mockResults);

      const result = await resultsApi.getResults();
      expect(result).toEqual(mockResults);
    });

    test('getResult should return result details', async () => {
      const mockResult = { id: 1, task_id: 1, data: { title: 'Result 1' } };
      mock.onGet('/api/results/1').reply(200, mockResult);

      const result = await resultsApi.getResult(1);
      expect(result).toEqual(mockResult);
    });

    test('deleteResult should return success', async () => {
      mock.onDelete('/api/results/1').reply(204);

      const result = await resultsApi.deleteResult(1);
      expect(result).toBe(true);
    });
  });
});
