<template>
  <v-container fluid>
    <v-card>
      <v-card-title class="d-flex align-center">
        Projects Dashboard
        <v-spacer></v-spacer>
        <v-btn
          color="primary"
          prepend-icon="mdi-plus"
          :to="'/projects/new'"
        >
          New Project
        </v-btn>
      </v-card-title>

      <v-card-text>
        <v-data-table
          :headers="headers"
          :items="projects"
          :loading="loading"
          :group-by="['group']"
          item-value="name"
        >
          <!-- プロジェクト名 -->
          <template v-slot:item.name="{ item }">
            <v-btn
              variant="text"
              :to="`/projects/${item.raw.name}`"
              class="text-none"
            >
              {{ item.raw.name }}
            </v-btn>
          </template>

          <!-- ステータス -->
          <template v-slot:item.status="{ item }">
            <v-chip
              :color="getStatusColor(item.raw.status)"
              :text="item.raw.status"
              size="small"
            />
          </template>

          <!-- プログレス -->
          <template v-slot:item.progress="{ item }">
            <div class="progress-container">
              <div v-for="type in ['5m', '1h', '1d', 'all']" :key="type" class="progress-row">
                <span class="progress-label">{{ type }}:</span>
                <v-progress-linear
                  :model-value="getProgressValue(item.raw.progress?.[type])"
                  :color="getProgressColor(item.raw.progress?.[type])"
                  height="20"
                >
                  <template v-slot:default="{ value }">
                    <span class="progress-text">
                      {{ getProgressText(item.raw.progress?.[type]) }}
                    </span>
                  </template>
                </v-progress-linear>
              </div>
            </div>
          </template>

          <!-- アクション -->
          <template v-slot:item.actions="{ item }">
            <v-btn-group>
              <v-btn
                icon="mdi-play"
                size="small"
                :color="item.raw.status === 'RUNNING' ? 'error' : 'success'"
                @click="toggleProjectStatus(item.raw)"
                :loading="loadingProjects[item.raw.name]"
              >
                <v-icon>{{ item.raw.status === 'RUNNING' ? 'mdi-stop' : 'mdi-play' }}</v-icon>
              </v-btn>
              <v-btn
                icon="mdi-pencil"
                size="small"
                color="primary"
                :to="`/projects/${item.raw.name}`"
              />
              <v-btn
                icon="mdi-delete"
                size="small"
                color="error"
                @click="confirmDelete(item.raw)"
              />
            </v-btn-group>
          </template>
        </v-data-table>
      </v-card-text>
    </v-card>

    <!-- 削除確認ダイアログ -->
    <v-dialog v-model="deleteDialog" max-width="400">
      <v-card>
        <v-card-title>Confirm Delete</v-card-title>
        <v-card-text>
          Are you sure you want to delete project "{{ projectToDelete?.name }}"?
        </v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn color="grey" @click="deleteDialog = false">Cancel</v-btn>
          <v-btn color="error" @click="deleteProject">Delete</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </v-container>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue';
import { useProjectStore } from '../stores/project';
import { storeToRefs } from 'pinia';

const store = useProjectStore();
const { projects, loading } = storeToRefs(store);
const loadingProjects = ref({});
const deleteDialog = ref(false);
const projectToDelete = ref(null);

const headers = [
  { title: 'Name', key: 'name', sortable: true },
  { title: 'Group', key: 'group', sortable: true },
  { title: 'Status', key: 'status', sortable: true },
  { title: 'Rate', key: 'rate', sortable: true },
  { title: 'Progress', key: 'progress', sortable: false },
  { title: 'Actions', key: 'actions', sortable: false, align: 'end' }
];

// ステータスに応じた色を返す
const getStatusColor = (status) => {
  switch (status) {
    case 'RUNNING': return 'success';
    case 'STOPPED': return 'error';
    case 'DEBUG': return 'warning';
    default: return 'grey';
  }
};

// プログレスバーの値を計算
const getProgressValue = (progress) => {
  if (!progress) return 0;
  const total = progress.pending + progress.success + progress.retry + progress.failed;
  return total > 0 ? (progress.success / total) * 100 : 0;
};

// プログレスバーの色を決定
const getProgressColor = (progress) => {
  if (!progress) return 'grey';
  const value = getProgressValue(progress);
  if (value >= 80) return 'success';
  if (value >= 50) return 'warning';
  return 'error';
};

// プログレスバーのテキストを生成
const getProgressText = (progress) => {
  if (!progress) return 'No data';
  return `${progress.success}/${progress.pending + progress.success + progress.retry + progress.failed}`;
};

// プロジェクトの状態を切り替え
const toggleProjectStatus = async (project) => {
  loadingProjects.value[project.name] = true;
  try {
    const newStatus = project.status === 'RUNNING' ? 'STOPPED' : 'RUNNING';
    await store.updateProject({
      ...project,
      status: newStatus
    });
  } finally {
    loadingProjects.value[project.name] = false;
  }
};

// 削除確認ダイアログを表示
const confirmDelete = (project) => {
  projectToDelete.value = project;
  deleteDialog.value = true;
};

// プロジェクトを削除
const deleteProject = async () => {
  if (!projectToDelete.value) return;
  try {
    await store.deleteProject(projectToDelete.value.name);
    deleteDialog.value = false;
    projectToDelete.value = null;
  } catch (error) {
    console.error('Failed to delete project:', error);
  }
};

onMounted(() => {
  store.fetchProjects();
});
</script>

<style scoped>
.progress-container {
  width: 100%;
  padding: 4px 0;
}

.progress-row {
  display: flex;
  align-items: center;
  margin: 4px 0;
}

.progress-label {
  min-width: 40px;
  margin-right: 8px;
  font-size: 0.8rem;
  color: rgba(0, 0, 0, 0.6);
}

.progress-text {
  font-size: 0.8rem;
  white-space: nowrap;
}

:deep(.v-progress-linear) {
  border-radius: 4px;
}
</style>
