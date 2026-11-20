<script setup lang="ts">
import { computed } from "vue";

const props = defineProps<{
  page: number;
  pageCount: number;
  total: number;
  perPage: number;
  loading?: boolean;
}>();

const emit = defineEmits<{
  change: [page: number];
  "update:perPage": [value: number];
}>();

const start = computed(() => (props.total === 0 ? 0 : (props.page - 1) * props.perPage + 1));
const end = computed(() => Math.min(props.page * props.perPage, props.total));
</script>

<template>
  <div class="d-flex flex-wrap justify-content-between align-items-center gap-2">
    <div class="small muted">
      Menampilkan {{ start }}-{{ end }} dari {{ total }}
    </div>
    <div class="d-flex align-items-center gap-2">
      <select
        class="form-select form-select-sm"
        :value="perPage"
        style="width: 88px"
        @change="emit('update:perPage', Number(($event.target as HTMLSelectElement).value))"
      >
        <option :value="25">25</option>
        <option :value="50">50</option>
        <option :value="100">100</option>
        <option :value="200">200</option>
      </select>
      <button
        class="btn btn-sm btn-outline-secondary"
        type="button"
        :disabled="page <= 1 || loading"
        title="Halaman sebelumnya"
        @click="emit('change', page - 1)"
      >
        <i class="bi bi-chevron-left"></i>
      </button>
      <span class="small">{{ page }} / {{ pageCount }}</span>
      <button
        class="btn btn-sm btn-outline-secondary"
        type="button"
        :disabled="page >= pageCount || loading"
        title="Halaman berikutnya"
        @click="emit('change', page + 1)"
      >
        <i class="bi bi-chevron-right"></i>
      </button>
    </div>
  </div>
</template>
