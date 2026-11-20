<script setup lang="ts">
import { useInaprocSessionStore } from "../stores/inaprocSession";
import { useTkdnStore } from "../stores/tkdn";

const store = useTkdnStore();
const session = useInaprocSessionStore();
</script>

<template>
  <div v-if="store.job.status !== 'idle'" class="vstack gap-2">
    <div class="d-flex justify-content-between small">
      <span class="fw-semibold text-capitalize">
        {{ store.job.status }}
        <span v-if="store.chunkTotal > 1" class="muted fw-normal">
          (chunk {{ store.chunkIndex }}/{{ store.chunkTotal }})
        </span>
      </span>
      <span class="muted">{{ store.job.done }} / {{ store.job.total }}</span>
    </div>
    <div class="progress" role="progressbar" :aria-valuenow="store.job.progress * 100" aria-valuemin="0" aria-valuemax="100">
      <div class="progress-bar bg-success" :style="{ width: `${store.job.progress * 100}%` }"></div>
    </div>
    <div class="d-flex flex-wrap gap-3 small muted">
      <span>Ditemukan: {{ store.job.found }}</span>
      <span>Kosong: {{ store.job.empty }}</span>
      <span>Error: {{ store.job.errors }}</span>
      <span>Skip: {{ store.job.skipped }}</span>
    </div>
    <div v-if="store.job.current" class="mono small">{{ store.job.current }}</div>
    <div v-if="store.job.status === 'failed'" class="alert alert-danger py-2 small mb-0">
      <div>Gagal: {{ store.job.last_error || "Proses collect gagal." }}</div>
      <button
        class="btn btn-sm btn-outline-danger mt-2"
        type="button"
        :disabled="store.collecting"
        @click="store.retryCollect(store.job.template || '', store.job.start || 1, store.job.end || 1)"
      >
        Coba lagi
      </button>
    </div>
    <div v-else-if="store.job.last_error" class="alert alert-warning py-2 small mb-0">
      {{ store.job.last_error }}
    </div>
    <div v-if="store.job.status === 'failed' && store.job.last_error?.startsWith('belum_login')" class="alert alert-info py-2 small mb-0">
      Sesi INAPROC perlu dihubungkan ulang.
      <button class="btn btn-sm btn-outline-primary ms-2" type="button" @click="session.load()">
        Buka form koneksi
      </button>
    </div>
    <button
      v-if="store.collectRunning"
      class="btn btn-sm btn-outline-danger align-self-start"
      type="button"
      :disabled="store.cancelling"
      @click="store.cancelCollect()"
    >
      <span v-if="store.cancelling" class="spinner-border spinner-border-sm me-1" aria-hidden="true"></span>
      <i v-else class="bi bi-stop-circle me-1"></i>
      {{ store.cancelling ? "Membatalkan..." : "Batal" }}
    </button>
  </div>
</template>
