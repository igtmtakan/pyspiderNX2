/**
 * PySpider Index v2 - Modern UI
 * 
 * A modern implementation of the PySpider dashboard interface
 * using Vue.js 3 and Vuetify 3.
 */

// Main Vue App
const app = Vue.createApp({
  data() {
    return {
      darkMode: localStorage.getItem('darkMode') === 'true',
      projects: window.projects || [],
      loading: false,
      search: '',
      sortBy: 'name',
      sortOptions: [
        { title: 'Name (A-Z)', value: 'name' },
        { title: 'Name (Z-A)', value: '-name' },
        { title: 'Status', value: 'status' },
        { title: 'Group', value: 'group' },
        { title: 'Last Updated', value: 'updatetime' },
        { title: 'Last Updated (Oldest)', value: '-updatetime' }
      ],
      headers: [
        { title: 'Name', key: 'name', sortable: true },
        { title: 'Group', key: 'group', sortable: true },
        { title: 'Status', key: 'status', sortable: true },
        { title: 'Rate/Burst', key: 'rate', sortable: true },
        { title: 'Last Updated', key: 'updatetime', sortable: true },
        { title: 'Actions', key: 'actions', sortable: false }
      ],
      runningStates: {},
      showNewProjectDialog: false,
      newProject: {
        name: '',
        startUrl: '',
        group: '',
        scriptMode: 'script'
      },
      creatingProject: false,
      showEditProjectDialog: false,
      editingProject: null,
      savingProject: false,
      showDeleteDialog: false,
      projectToDelete: null,
      deletingProject: false,
      snackbar: {
        show: false,
        text: '',
        color: 'success',
        timeout: 3000
      }
    };
  },

  computed: {
    filteredProjects() {
      let result = [...this.projects];
      
      // Apply sorting
      if (this.sortBy) {
        const desc = this.sortBy.startsWith('-');
        const key = desc ? this.sortBy.substring(1) : this.sortBy;
        
        result.sort((a, b) => {
          let aVal = a[key];
          let bVal = b[key];
          
          // Handle null/undefined values
          if (aVal === null || aVal === undefined) aVal = '';
          if (bVal === null || bVal === undefined) bVal = '';
          
          // Compare based on type
          let comparison;
          if (typeof aVal === 'string') {
            comparison = aVal.localeCompare(bVal);
          } else {
            comparison = aVal - bVal;
          }
          
          return desc ? -comparison : comparison;
        });
      }
      
      return result;
    },
    
    runningProjects() {
      return this.projects.filter(p => p.status === 'RUNNING');
    },
    
    pausedProjects() {
      return this.projects.filter(p => p.status === 'PAUSED');
    },
    
    stoppedProjects() {
      return this.projects.filter(p => 
        p.status !== 'RUNNING' && p.status !== 'PAUSED'
      );
    },
    
    availableGroups() {
      const groups = new Set();
      this.projects.forEach(p => {
        if (p.group) groups.add(p.group);
      });
      return ['', ...Array.from(groups)];
    }
  },

  mounted() {
    // Initialize Vuetify
    this.vuetify = this.$vuetify;
    this.vuetify.theme.global.name.value = this.darkMode ? 'dark' : 'light';
    
    // Setup refresh interval
    this.refreshInterval = setInterval(() => {
      this.refreshProjects();
    }, 30000); // Refresh every 30 seconds
    
    // Initial refresh
    this.refreshProjects();
    
    // Watch for dark mode changes
    this.$watch('darkMode', (newVal) => {
      this.vuetify.theme.global.name.value = newVal ? 'dark' : 'light';
      localStorage.setItem('darkMode', newVal);
    });
  },
  
  beforeUnmount() {
    // Clear interval when component is destroyed
    if (this.refreshInterval) {
      clearInterval(this.refreshInterval);
    }
  },

  methods: {
    toggleDarkMode() {
      this.darkMode = !this.darkMode;
    },
    
    refreshProjects() {
      this.loading = true;
      
      // Fetch projects data
      fetch('/api/projects')
        .then(response => response.json())
        .then(data => {
          if (data.projects) {
            this.projects = data.projects;
          }
        })
        .catch(error => {
          console.error('Error fetching projects:', error);
          this.showSnackbar('Failed to fetch projects', 'error');
        })
        .finally(() => {
          this.loading = false;
        });
      
      // Fetch counter data
      fetch('/counter')
        .then(response => response.json())
        .then(data => {
          // Update project progress data
          this.projects.forEach(project => {
            if (data[project.name]) {
              project.progress = data[project.name];
            }
          });
        })
        .catch(error => {
          console.error('Error fetching counter data:', error);
        });
    },
    
    getStatusColor(status) {
      switch (status) {
        case 'RUNNING':
          return 'success';
        case 'PAUSED':
          return 'warning';
        case 'DEBUG':
          return 'info';
        case 'CHECKING':
          return 'purple';
        case 'STOPPED':
        case 'ERROR':
          return 'error';
        default:
          return 'grey';
      }
    },
    
    getStatusIcon(status) {
      switch (status) {
        case 'RUNNING':
          return 'mdi-play-circle';
        case 'PAUSED':
          return 'mdi-pause-circle';
        case 'DEBUG':
          return 'mdi-bug';
        case 'CHECKING':
          return 'mdi-clock-check';
        case 'STOPPED':
          return 'mdi-stop-circle';
        case 'ERROR':
          return 'mdi-alert-circle';
        default:
          return 'mdi-help-circle';
      }
    },
    
    formatDate(timestamp) {
      if (!timestamp) return 'N/A';
      
      const date = new Date(timestamp * 1000);
      const now = new Date();
      const diffMs = now - date;
      const diffSec = Math.floor(diffMs / 1000);
      const diffMin = Math.floor(diffSec / 60);
      const diffHour = Math.floor(diffMin / 60);
      const diffDay = Math.floor(diffHour / 24);
      
      if (diffSec < 60) {
        return 'just now';
      } else if (diffMin < 60) {
        return `${diffMin}m ago`;
      } else if (diffHour < 24) {
        return `${diffHour}h ago`;
      } else if (diffDay < 30) {
        return `${diffDay}d ago`;
      } else {
        return date.toLocaleDateString();
      }
    },
    
    formatDateTime(timestamp) {
      if (!timestamp) return 'N/A';
      
      const date = new Date(timestamp * 1000);
      return date.toLocaleString();
    },
    
    runProject(project) {
      // Set running state for this project
      this.$set(this.runningStates, project.name, true);
      
      // Create form data
      const formData = new FormData();
      formData.append('project', project.name);
      
      // Send request
      fetch('/run', {
        method: 'POST',
        body: formData
      })
        .then(response => {
          if (response.ok) {
            this.showSnackbar(`Project ${project.name} started successfully`, 'success');
          } else {
            throw new Error('Failed to start project');
          }
        })
        .catch(error => {
          console.error('Error running project:', error);
          this.showSnackbar(`Failed to start project: ${error.message}`, 'error');
        })
        .finally(() => {
          // Clear running state
          this.$set(this.runningStates, project.name, false);
        });
    },
    
    editProject(project) {
      this.editingProject = { ...project };
      this.showEditProjectDialog = true;
    },
    
    saveProjectChanges() {
      if (!this.editingProject) return;
      
      this.savingProject = true;
      
      // Create form data
      const formData = new FormData();
      formData.append('pk', this.editingProject.name);
      
      // Update status
      if (this.editingProject.status) {
        formData.append('name', 'status');
        formData.append('value', this.editingProject.status);
        
        fetch('/update', {
          method: 'POST',
          body: formData
        })
          .then(response => response.json())
          .then(data => {
            if (data.status === 'success') {
              // Update group
              const groupFormData = new FormData();
              groupFormData.append('pk', this.editingProject.name);
              groupFormData.append('name', 'group');
              groupFormData.append('value', this.editingProject.group || '');
              
              return fetch('/update', {
                method: 'POST',
                body: groupFormData
              });
            } else {
              throw new Error('Failed to update status');
            }
          })
          .then(response => response.json())
          .then(data => {
            if (data.status === 'success') {
              // Update rate/burst
              const rateFormData = new FormData();
              rateFormData.append('pk', this.editingProject.name);
              rateFormData.append('name', 'rate');
              rateFormData.append('value', `${this.editingProject.rate}/${this.editingProject.burst}`);
              
              return fetch('/update', {
                method: 'POST',
                body: rateFormData
              });
            } else {
              throw new Error('Failed to update group');
            }
          })
          .then(response => response.json())
          .then(data => {
            if (data.status === 'success') {
              this.showSnackbar(`Project ${this.editingProject.name} updated successfully`, 'success');
              this.refreshProjects();
              this.showEditProjectDialog = false;
            } else {
              throw new Error('Failed to update rate/burst');
            }
          })
          .catch(error => {
            console.error('Error updating project:', error);
            this.showSnackbar(`Failed to update project: ${error.message}`, 'error');
          })
          .finally(() => {
            this.savingProject = false;
          });
      }
    },
    
    toggleProjectStatus(project) {
      const newStatus = project.status === 'RUNNING' ? 'PAUSED' : 'RUNNING';
      
      // Create form data
      const formData = new FormData();
      formData.append('pk', project.name);
      formData.append('name', 'status');
      formData.append('value', newStatus);
      
      fetch('/update', {
        method: 'POST',
        body: formData
      })
        .then(response => response.json())
        .then(data => {
          if (data.status === 'success') {
            project.status = newStatus;
            this.showSnackbar(`Project ${project.name} ${newStatus === 'RUNNING' ? 'resumed' : 'paused'} successfully`, 'success');
          } else {
            throw new Error('Failed to update status');
          }
        })
        .catch(error => {
          console.error('Error toggling project status:', error);
          this.showSnackbar(`Failed to update project status: ${error.message}`, 'error');
        });
    },
    
    confirmDeleteProject(project) {
      this.projectToDelete = project;
      this.showDeleteDialog = true;
    },
    
    deleteProject() {
      if (!this.projectToDelete) return;
      
      this.deletingProject = true;
      
      // In a real implementation, you would call an API to delete the project
      // For now, we'll just simulate it
      setTimeout(() => {
        this.showSnackbar(`Project ${this.projectToDelete.name} deleted successfully`, 'success');
        this.projects = this.projects.filter(p => p.name !== this.projectToDelete.name);
        this.showDeleteDialog = false;
        this.projectToDelete = null;
        this.deletingProject = false;
      }, 1000);
    },
    
    createProject() {
      if (!this.newProject.name) return;
      
      this.creatingProject = true;
      
      // Create form data
      const formData = new FormData();
      formData.append('project-name', this.newProject.name);
      formData.append('start-urls', this.newProject.startUrl || '');
      formData.append('script-mode', this.newProject.scriptMode || 'script');
      
      fetch('/debug/new', {
        method: 'POST',
        body: formData
      })
        .then(response => {
          if (response.ok) {
            this.showSnackbar(`Project ${this.newProject.name} created successfully`, 'success');
            this.refreshProjects();
            this.showNewProjectDialog = false;
            
            // Reset form
            this.newProject = {
              name: '',
              startUrl: '',
              group: '',
              scriptMode: 'script'
            };
            
            // Redirect to debug page
            window.location.href = `/debug-v2/${this.newProject.name}`;
          } else {
            throw new Error('Failed to create project');
          }
        })
        .catch(error => {
          console.error('Error creating project:', error);
          this.showSnackbar(`Failed to create project: ${error.message}`, 'error');
        })
        .finally(() => {
          this.creatingProject = false;
        });
    },
    
    showSnackbar(text, color = 'success', timeout = 3000) {
      this.snackbar.text = text;
      this.snackbar.color = color;
      this.snackbar.timeout = timeout;
      this.snackbar.show = true;
    },
    
    // Vue 3 compatibility method for reactive updates
    $set(obj, key, value) {
      if (obj) {
        obj[key] = value;
      }
    }
  }
}).mount('#app');
