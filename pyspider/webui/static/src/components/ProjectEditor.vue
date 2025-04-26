<template>
  <v-container fluid>
    <v-row>
      <v-col cols="12">
        <v-card>
          <v-toolbar>
            <v-toolbar-title>{{ project.name }}</v-toolbar-title>
            <v-spacer></v-spacer>
            <v-btn-group>
              <v-btn
                :color="project.status === 'RUNNING' ? 'error' : 'success'"
                @click="toggleStatus"
              >
                {{ project.status === 'RUNNING' ? 'Stop' : 'Start' }}
              </v-btn>
              <v-btn color="primary" @click="saveProject">
                Save
              </v-btn>
            </v-btn-group>
          </v-toolbar>

          <v-card-text>
            <v-row>
              <v-col cols="12" md="8">
                <code-editor
                  v-model:value="project.script"
                  language="python"
                  title="Script Editor"
                  @save="saveProject"
                  @run="runProject"
                />
              </v-col>
              <v-col cols="12" md="4">
                <v-card>
                  <v-card-title>Project Settings</v-card-title>
                  <v-card-text>
                    <v-text-field
                      v-model="project.name"
                      label="Project Name"
                      :readonly="!isNewProject"
                    />
                    <v-text-field
                      v-model="project.group"
                      label="Group"
                    />
                    <v-select
                      v-model="project.status"
                      :items="['RUNNING', 'STOPPED', 'DEBUG']"
                      label="Status"
                    />
                    <v-text-field
                      v-model.number="project.rate"
                      label="Rate (requests/second)"
                      type="number"
                    />
                    <v-text-field
                      v-model.number="project.burst"
                      label="Burst"
                      type="number"
                    />
                  </v-card-text>
                </v-card>

                <v-card class="mt-4">
                  <v-card-title>Results</v-card-title>
                  <v-card-text>
                    <code-editor
                      v-if="results"
                      v-model:value="results"
                      language="json"
                      title="Run Results"
                      :read-only="true"
                    />
                  </v-card-text>
                </v-card>
              </v-col>
            </v-row>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>
  </v-container>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { useProjectStore } from '../stores/project';
import CodeEditor from './CodeEditor.vue';

const props = defineProps({
  projectId: {
    type: String,
    required: true
  }
});

const store = useProjectStore();
const project = ref({
  name: '',
  group: '',
  status: 'STOPPED',
  script: '',
  rate: 1,
  burst: 10
});
const results = ref('');
const isNewProject = ref(false);

onMounted(async () => {
  if (props.projectId === 'new') {
    isNewProject.value = true;
  } else {
    const loadedProject = await store.getProject(props.projectId);
    project.value = { ...loadedProject };
  }
});

const saveProject = async () => {
  try {
    if (isNewProject.value) {
      await store.createProject(project.value);
    } else {
      await store.updateProject(project.value);
    }
  } catch (error) {
    console.error('Failed to save project:', error);
  }
};

const runProject = async () => {
  try {
    const result = await store.runProject(project.value.name);
    results.value = JSON.stringify(result, null, 2);
  } catch (error) {
    console.error('Failed to run project:', error);
  }
};

const toggleStatus = async () => {
  project.value.status = project.value.status === 'RUNNING' ? 'STOPPED' : 'RUNNING';
  await saveProject();
};
</script>