import { defineStore } from 'pinia';
import axios from 'axios';

export const useProjectStore = defineStore('project', {
  state: () => ({
    projects: [],
    loading: false,
    error: null,
    progressData: {},
    refreshInterval: null
  }),

  actions: {
    async fetchProjects() {
      this.loading = true;
      try {
        // プロジェクト基本情報を取得
        const [projectsResponse, progressResponse] = await Promise.all([
          axios.get('/api/projects'),
          axios.get('/api/projects/progress')
        ]);

        // プロジェクト情報とプログレス情報を結合
        this.projects = projectsResponse.data.map(project => ({
          ...project,
          progress: progressResponse.data[project.name] || {
            '5m': { pending: 0, success: 0, retry: 0, failed: 0 },
            '1h': { pending: 0, success: 0, retry: 0, failed: 0 },
            '1d': { pending: 0, success: 0, retry: 0, failed: 0 },
            'all': { pending: 0, success: 0, retry: 0, failed: 0 }
          }
        }));
      } catch (error) {
        this.error = error.message;
      } finally {
        this.loading = false;
      }
    },

    // 定期的な更新を開始
    startProgressRefresh() {
      if (this.refreshInterval) return;
      this.refreshInterval = setInterval(() => {
        this.fetchProgress();
      }, 5000); // 5秒ごとに更新
    },

    // 定期的な更新を停止
    stopProgressRefresh() {
      if (this.refreshInterval) {
        clearInterval(this.refreshInterval);
        this.refreshInterval = null;
      }
    },

    // プログレス情報のみを更新
    async fetchProgress() {
      try {
        const response = await axios.get('/api/projects/progress');
        this.projects = this.projects.map(project => ({
          ...project,
          progress: response.data[project.name] || project.progress
        }));
      } catch (error) {
        console.error('Failed to fetch progress:', error);
      }
    },

    async getProject(name) {
      try {
        const response = await axios.get(`/api/projects/${name}`);
        return response.data;
      } catch (error) {
        this.error = error.message;
        throw error;
      }
    },

    async createProject(project) {
      try {
        const response = await axios.post('/api/projects', project);
        await this.fetchProjects();
        return response.data;
      } catch (error) {
        this.error = error.message;
        throw error;
      }
    },

    async updateProject(project) {
      try {
        const response = await axios.put(`/api/projects/${project.name}`, project);
        await this.fetchProjects();
        return response.data;
      } catch (error) {
        this.error = error.message;
        throw error;
      }
    },

    async deleteProject(name) {
      try {
        await axios.delete(`/api/projects/${name}`);
        await this.fetchProjects();
      } catch (error) {
        this.error = error.message;
        throw error;
      }
    },

    async runProject(name) {
      try {
        const response = await axios.post(`/api/projects/${name}/run`);
        return response.data;
      } catch (error) {
        this.error = error.message;
        throw error;
      }
    }
  }
});
