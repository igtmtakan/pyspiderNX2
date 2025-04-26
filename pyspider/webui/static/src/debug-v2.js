/**
 * PySpider Debug v2 - Modern UI
 * 
 * A modern implementation of the PySpider debugger interface
 * using Vue.js 3 and Vuetify 3.
 */

// CSS Selector Helper
class CSSSelectorHelper {
  constructor() {
    this.server = null;
    this.enabled = false;
  }

  init(iframe) {
    if (!iframe || !iframe.contentWindow) {
      console.error('Invalid iframe for CSS selector helper');
      return;
    }

    this.clear();
    
    try {
      this.server = new CSSSelectorHelperServer(iframe.contentWindow);
      this.server.on('selector_helper_click', (path) => {
        app.cssSelector = path;
      });
      this.enabled = true;
    } catch (e) {
      console.error('Failed to initialize CSS selector helper:', e);
    }
  }

  clear() {
    if (this.server) {
      try {
        this.server.destroy();
      } catch (e) {
        console.error('Error destroying CSS selector helper:', e);
      }
    }
    this.server = null;
    this.enabled = false;
  }
}

// CSS Selector Helper Server
class CSSSelectorHelperServer {
  constructor(contentWindow) {
    this.contentWindow = contentWindow;
    this.events = {};
    this.init();
  }

  init() {
    const script = document.createElement('script');
    script.textContent = `
      (function() {
        window.addEventListener('click', function(e) {
          e.preventDefault();
          
          var path = '';
          var element = e.target;
          
          while (element && element.tagName) {
            var selector = element.tagName.toLowerCase();
            
            if (element.id) {
              selector += '#' + element.id;
              path = selector + (path ? ' > ' + path : '');
              break;
            } else {
              var siblings = Array.from(element.parentNode.children).filter(
                child => child.tagName === element.tagName
              );
              
              if (siblings.length > 1) {
                var index = siblings.indexOf(element) + 1;
                selector += ':nth-of-type(' + index + ')';
              }
              
              path = selector + (path ? ' > ' + path : '');
              element = element.parentNode;
            }
          }
          
          window.parent.postMessage({
            type: 'selector_helper_click',
            path: path
          }, '*');
        }, true);
      })();
    `;
    
    try {
      this.contentWindow.document.head.appendChild(script);
      
      window.addEventListener('message', (event) => {
        if (event.data && event.data.type === 'selector_helper_click') {
          this.trigger('selector_helper_click', event.data.path);
        }
      });
    } catch (e) {
      console.error('Failed to inject CSS selector helper script:', e);
    }
  }

  on(event, callback) {
    if (!this.events[event]) {
      this.events[event] = [];
    }
    this.events[event].push(callback);
  }

  trigger(event, data) {
    if (this.events[event]) {
      this.events[event].forEach(callback => callback(data));
    }
  }

  destroy() {
    this.events = {};
    // Remove event listeners if needed
  }
}

// CodeMirror Editors
class Editors {
  constructor() {
    this.taskEditor = null;
    this.pythonEditor = null;
    this.followDetailsEditor = null;
    this.htmlContent = null;
    this.logsContent = null;
  }

  init() {
    // Task Editor (JSON)
    this.taskEditor = CodeMirror(document.getElementById('task-editor'), {
      value: JSON.stringify(JSON.parse(task_content), null, 2),
      mode: 'application/json',
      theme: app.darkMode ? 'material' : 'default',
      lineNumbers: true,
      styleActiveLine: true,
      matchBrackets: true,
      autoCloseBrackets: true,
      tabSize: 2,
      gutters: ['CodeMirror-lint-markers'],
      lint: true
    });

    // Python Editor
    this.pythonEditor = CodeMirror(document.getElementById('python-editor'), {
      value: script_content,
      mode: 'text/x-python',
      theme: app.darkMode ? 'material' : 'default',
      lineNumbers: true,
      styleActiveLine: true,
      matchBrackets: true,
      autoCloseBrackets: true,
      tabSize: 4,
      indentUnit: 4
    });

    // Follow Details Editor (JSON)
    this.followDetailsEditor = CodeMirror(document.getElementById('follow-details'), {
      value: '',
      mode: 'application/json',
      theme: app.darkMode ? 'material' : 'default',
      lineNumbers: true,
      readOnly: true,
      tabSize: 2
    });

    // HTML Content
    this.htmlContent = document.getElementById('html-content');

    // Logs Content
    this.logsContent = document.getElementById('logs-content');

    // Add event listeners
    this.taskEditor.on('change', () => {
      app.taskModified = true;
    });

    this.pythonEditor.on('change', () => {
      app.scriptModified = true;
    });
  }

  updateTheme(darkMode) {
    const theme = darkMode ? 'material' : 'default';
    
    if (this.taskEditor) {
      this.taskEditor.setOption('theme', theme);
    }
    
    if (this.pythonEditor) {
      this.pythonEditor.setOption('theme', theme);
    }
    
    if (this.followDetailsEditor) {
      this.followDetailsEditor.setOption('theme', theme);
    }
  }

  formatTask() {
    try {
      const taskJson = this.taskEditor.getValue();
      const task = JSON.parse(taskJson);
      const formatted = JSON.stringify(task, null, 2);
      this.taskEditor.setValue(formatted);
    } catch (e) {
      app.showError('Invalid JSON: ' + e.message);
    }
  }

  getTaskValue() {
    try {
      return JSON.parse(this.taskEditor.getValue());
    } catch (e) {
      app.showError('Invalid JSON: ' + e.message);
      return null;
    }
  }

  setTaskValue(task) {
    this.taskEditor.setValue(JSON.stringify(task, null, 2));
  }

  getScriptValue() {
    return this.pythonEditor.getValue();
  }

  setFollowDetails(follow) {
    this.followDetailsEditor.setValue(JSON.stringify(follow, null, 2));
  }

  setHtmlContent(html) {
    if (!html) {
      this.htmlContent.innerHTML = '<div class="pa-4">No HTML content available</div>';
      return;
    }

    // Format HTML with syntax highlighting
    let htmlFormatted = '';
    CodeMirror.runMode(html, 'text/html', (text, style) => {
      if (style) {
        htmlFormatted += `<span class="cm-${style}">${this.escapeHtml(text)}</span>`;
      } else {
        htmlFormatted += this.escapeHtml(text);
      }
    });

    this.htmlContent.innerHTML = `<pre class="cm-s-${app.darkMode ? 'material' : 'default'} pa-2">${htmlFormatted}</pre>`;
  }

  setLogsContent(logs) {
    if (!logs) {
      this.logsContent.innerHTML = '<div>No logs available</div>';
      return;
    }

    this.logsContent.innerHTML = `<pre>${this.escapeHtml(logs)}</pre>`;
  }

  escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
  }
}

// Main Vue App
const app = Vue.createApp({
  data() {
    return {
      darkMode: localStorage.getItem('darkMode') === 'true',
      activeTab: 'web',
      showCssHelper: false,
      cssSelector: '',
      follows: [],
      messages: [],
      logs: '',
      isRunning: false,
      isSaving: false,
      taskHistory: [],
      taskHistoryIndex: 0,
      taskModified: false,
      scriptModified: false,
      followDialog: false,
      selectedFollow: null,
      selectedFollowIndex: -1,
      fetchResult: null,
      errorMessage: null
    };
  },

  mounted() {
    // Initialize Vuetify
    this.vuetify = this.$vuetify;
    this.vuetify.theme.global.name.value = this.darkMode ? 'dark' : 'light';

    // Initialize editors
    this.editors = new Editors();
    this.editors.init();

    // Initialize CSS selector helper
    this.selectorHelper = new CSSSelectorHelper();

    // Initialize task history
    this.taskHistory.push(this.editors.taskEditor.getValue());
    this.taskHistoryIndex = 0;

    // Watch for CSS helper changes
    this.$watch('showCssHelper', (newVal) => {
      if (newVal) {
        this.$nextTick(() => {
          const iframe = document.querySelector('#iframe-box iframe');
          if (iframe) {
            this.selectorHelper.init(iframe);
          }
        });
      } else {
        this.selectorHelper.clear();
      }
    });

    // Watch for dark mode changes
    this.$watch('darkMode', (newVal) => {
      this.vuetify.theme.global.name.value = newVal ? 'dark' : 'light';
      this.editors.updateTheme(newVal);
      localStorage.setItem('darkMode', newVal);
    });
  },

  methods: {
    toggleDarkMode() {
      this.darkMode = !this.darkMode;
    },

    runTask() {
      const task = this.editors.getTaskValue();
      if (!task) return;

      // Add to history if modified
      if (this.taskModified) {
        const currentValue = this.editors.taskEditor.getValue();
        // Remove any forward history
        this.taskHistory = this.taskHistory.slice(0, this.taskHistoryIndex + 1);
        this.taskHistory.push(currentValue);
        this.taskHistoryIndex = this.taskHistory.length - 1;
        this.taskModified = false;
      }

      this.isRunning = true;
      this.follows = [];
      this.messages = [];
      this.logs = '';
      this.fetchResult = null;
      this.errorMessage = null;

      // Clear iframe
      document.getElementById('iframe-box').innerHTML = '';
      
      // Clear HTML content
      this.editors.setHtmlContent('');

      const script = this.editors.getScriptValue();
      const formData = new FormData();
      formData.append('task', JSON.stringify(task));
      formData.append('script', script);

      fetch(window.location.pathname + '/run', {
        method: 'POST',
        body: formData
      })
      .then(response => response.json())
      .then(data => {
        this.handleRunResult(data);
      })
      .catch(error => {
        console.error('Error running task:', error);
        this.errorMessage = 'Failed to run task: ' + error.message;
      })
      .finally(() => {
        this.isRunning = false;
      });
    },

    handleRunResult(data) {
      // Set logs
      this.logs = data.logs || '';
      this.editors.setLogsContent(this.logs);

      // Set follows
      this.follows = data.follows || [];

      // Set messages
      this.messages = data.messages || [];

      // Set fetch result
      this.fetchResult = data.fetch_result || null;

      // Handle HTML content
      if (this.fetchResult && this.fetchResult.content) {
        this.editors.setHtmlContent(this.fetchResult.content);
      }

      // Handle iframe content
      if (this.fetchResult) {
        const iframeBox = document.getElementById('iframe-box');
        iframeBox.innerHTML = '';

        if (this.fetchResult.content) {
          const iframe = document.createElement('iframe');
          iframe.style.width = '100%';
          iframe.style.height = '100%';
          iframe.style.border = 'none';
          iframeBox.appendChild(iframe);

          const doc = iframe.contentWindow.document;
          doc.open();
          doc.write(this.fetchResult.content);
          doc.close();

          // If CSS selector helper is enabled, initialize it
          if (this.showCssHelper) {
            this.selectorHelper.init(iframe);
          }
        }
      }

      // Switch to appropriate tab based on result
      if (this.fetchResult && this.fetchResult.content) {
        this.activeTab = 'web';
      } else if (this.follows.length > 0) {
        this.activeTab = 'follows';
      } else if (this.messages.length > 0) {
        this.activeTab = 'messages';
      } else {
        this.activeTab = 'logs';
      }
    },

    saveScript() {
      const script = this.editors.getScriptValue();
      this.isSaving = true;

      const formData = new FormData();
      formData.append('script', script);

      fetch(window.location.pathname + '/save', {
        method: 'POST',
        body: formData
      })
      .then(response => {
        if (response.ok) {
          this.showSuccess('Script saved successfully');
          this.scriptModified = false;
        } else {
          return response.text().then(text => {
            throw new Error(text || 'Failed to save script');
          });
        }
      })
      .catch(error => {
        console.error('Error saving script:', error);
        this.showError('Failed to save script: ' + error.message);
      })
      .finally(() => {
        this.isSaving = false;
      });
    },

    undoTask() {
      if (this.taskHistoryIndex > 0) {
        this.taskHistoryIndex--;
        this.editors.taskEditor.setValue(this.taskHistory[this.taskHistoryIndex]);
        this.taskModified = false;
      }
    },

    redoTask() {
      if (this.taskHistoryIndex < this.taskHistory.length - 1) {
        this.taskHistoryIndex++;
        this.editors.taskEditor.setValue(this.taskHistory[this.taskHistoryIndex]);
        this.taskModified = false;
      }
    },

    formatTask() {
      this.editors.formatTask();
    },

    copyCssSelector() {
      if (!this.cssSelector) return;
      
      navigator.clipboard.writeText(this.cssSelector)
        .then(() => {
          this.showSuccess('CSS selector copied to clipboard');
        })
        .catch(err => {
          console.error('Failed to copy CSS selector:', err);
          this.showError('Failed to copy CSS selector');
        });
    },

    addToEditor() {
      if (!this.cssSelector) return;
      
      const script = this.editors.getScriptValue();
      const newScript = script + '\n\n# CSS Selector: ' + this.cssSelector;
      this.editors.pythonEditor.setValue(newScript);
      this.scriptModified = true;
    },

    showFollowDetails(follow, index) {
      this.selectedFollow = follow;
      this.selectedFollowIndex = index;
      this.editors.setFollowDetails(follow);
      this.followDialog = true;
    },

    runFollow(follow) {
      this.editors.setTaskValue(follow);
      this.taskModified = true;
      this.runTask();
    },

    runSelectedFollow() {
      if (this.selectedFollow) {
        this.runFollow(this.selectedFollow);
        this.followDialog = false;
      }
    },

    showSuccess(message) {
      // Implement toast or notification
      alert(message);
    },

    showError(message) {
      // Implement toast or notification
      alert('Error: ' + message);
    }
  }
}).mount('#app');
