<template>
  <div class="code-editor">
    <v-card>
      <v-card-title class="d-flex justify-space-between align-center">
        {{ title }}
        <v-btn-group v-if="!readOnly">
          <v-btn icon="mdi-content-save" @click="save" :disabled="!modified">Save</v-btn>
          <v-btn icon="mdi-play" @click="run" :loading="running">Run</v-btn>
        </v-btn-group>
      </v-card-title>
      <v-card-text>
        <div ref="editor" class="editor-container"></div>
      </v-card-text>
    </v-card>
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue';
import { EditorView, basicSetup } from 'codemirror';
import { python } from '@codemirror/lang-python';
import { json } from '@codemirror/lang-json';
import { javascript } from '@codemirror/lang-javascript';
import { html } from '@codemirror/lang-html';

const props = defineProps({
  value: {
    type: String,
    default: ''
  },
  language: {
    type: String,
    default: 'python'
  },
  title: {
    type: String,
    default: 'Code Editor'
  },
  readOnly: {
    type: Boolean,
    default: false
  }
});

const emit = defineEmits(['update:value', 'save', 'run']);

const editor = ref(null);
const modified = ref(false);
const running = ref(false);
let editorView = null;

const getLanguageExtension = () => {
  switch (props.language) {
    case 'python': return python();
    case 'json': return json();
    case 'javascript': return javascript();
    case 'html': return html();
    default: return python();
  }
};

onMounted(() => {
  editorView = new EditorView({
    doc: props.value,
    extensions: [
      basicSetup,
      getLanguageExtension(),
      EditorView.updateListener.of(update => {
        if (update.docChanged) {
          modified.value = true;
          emit('update:value', update.state.doc.toString());
        }
      }),
      EditorView.theme({
        '&': { height: '400px' },
        '.cm-scroller': { overflow: 'auto' }
      })
    ],
    parent: editor.value
  });
});

const save = async () => {
  try {
    await emit('save', editorView.state.doc.toString());
    modified.value = false;
  } catch (error) {
    console.error('Save failed:', error);
  }
};

const run = async () => {
  running.value = true;
  try {
    await emit('run', editorView.state.doc.toString());
  } catch (error) {
    console.error('Run failed:', error);
  } finally {
    running.value = false;
  }
};
</script>

<style scoped>
.code-editor {
  height: 100%;
}
.editor-container {
  height: 400px;
  border: 1px solid #ccc;
  border-radius: 4px;
}
</style>