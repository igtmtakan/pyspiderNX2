<script setup>
import { RouterView } from 'vue-router';
import { onMounted, onUnmounted } from 'vue';
import { useProjectStore } from './stores/project';

const store = useProjectStore();

onMounted(() => {
  store.startProgressRefresh();
});

onUnmounted(() => {
  store.stopProgressRefresh();
});
</script>

<template>
  <v-app>
    <v-main>
      <RouterView />
    </v-main>
  </v-app>
</template>