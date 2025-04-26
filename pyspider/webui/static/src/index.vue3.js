import { createApp } from 'vue';
import { createPinia } from 'pinia';
import { createVuetify } from 'vuetify';
import { useProjectStore } from './stores/project';
import ProjectList from './components/ProjectList.vue';
import '@mdi/font/css/materialdesignicons.css';
import 'vuetify/styles';

// Vuetifyの設定
const vuetify = createVuetify({
  theme: {
    defaultTheme: 'light'
  }
});

// メインアプリケーション
const app = createApp({
  template: `
    <v-app>
      <v-main>
        <project-list></project-list>
      </v-main>
    </v-app>
  `,
  components: {
    ProjectList
  },
  
  setup() {
    const store = useProjectStore();
    
    // 初期データの設定
    if (window.projects) {
      store.projects = window.projects;
    }
    
    // 定期的な更新
    setInterval(() => {
      store.fetchProjects();
    }, 5000);
    
    return {
      store
    };
  }
});

// プラグインの設定
const pinia = createPinia();
app.use(pinia);
app.use(vuetify);

// アプリケーションのマウント
app.mount('#app');
