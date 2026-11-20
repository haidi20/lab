<script setup lang="ts">
import { useInaprocSessionStore } from "../stores/inaprocSession";

const session = useInaprocSessionStore();
</script>

<template>
  <div class="d-flex align-items-center gap-2">
    <span
      class="badge"
      :class="session.configured ? 'text-bg-success' : 'text-bg-secondary'"
    >
      <i class="bi" :class="session.configured ? 'bi-check-circle' : 'bi-dash-circle'"></i>
      {{ session.configured ? "Sesi INAPROC aktif" : "Sesi INAPROC belum terhubung" }}
    </span>
    <button
      v-if="session.configured"
      class="btn btn-sm btn-outline-secondary"
      type="button"
      title="Putuskan sesi INAPROC"
      :disabled="session.disconnecting"
      @click="session.disconnect()"
    >
      <span v-if="session.disconnecting" class="spinner-border spinner-border-sm" aria-hidden="true"></span>
      <i v-else class="bi bi-plug"></i>
    </button>
  </div>
</template>
