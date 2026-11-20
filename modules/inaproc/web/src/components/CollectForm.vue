<script setup lang="ts">
import { reactive, ref } from "vue";
import { userMessage } from "../api";
import { useTkdnStore } from "../stores/tkdn";

const store = useTkdnStore();
const form = reactive({
  template: "11469/SJ-IND.8/E-TKDN/7/2025",
  start: 1,
  end: 100,
  month: 7,
  year: 2025,
  delayMin: 1,
  delayMax: 3,
  force: false,
  useAdjacentMonth: false,
});
const previewError = ref("");

async function preview() {
  previewError.value = "";
  try {
    await store.previewRange(
      form.template.trim(),
      Number(form.start),
      Number(form.end),
      Number(form.delayMin),
      Number(form.delayMax),
    );
  } catch (error) {
    previewError.value = userMessage(error);
  }
}

async function start() {
  previewError.value = "";
  try {
    await store.startCollect(form.template.trim(), Number(form.start), Number(form.end), {
      delayMin: Number(form.delayMin),
      delayMax: Number(form.delayMax),
      force: form.force,
    });
  } catch (error) {
    previewError.value = userMessage(error);
  }
}
</script>

<template>
  <form class="row g-2" @submit.prevent="preview">
    <div class="col-12">
      <label class="form-label small fw-semibold" for="collect-template">Nomor contoh</label>
      <input
        id="collect-template"
        v-model="form.template"
        class="form-control mono"
        required
      />
    </div>
    <div class="col-6">
      <label class="form-label small fw-semibold" for="collect-month">Bulan</label>
      <select id="collect-month" v-model.number="form.month" class="form-select">
        <option v-for="month in 12" :key="month" :value="month">{{ month }}</option>
      </select>
    </div>
    <div class="col-6">
      <label class="form-label small fw-semibold" for="collect-year">Tahun</label>
      <input id="collect-year" v-model.number="form.year" type="number" min="2000" class="form-control" />
    </div>
    <div class="col-6">
      <label class="form-label small fw-semibold" for="collect-start">Dari</label>
      <input id="collect-start" v-model.number="form.start" type="number" min="1" class="form-control" required />
    </div>
    <div class="col-6">
      <label class="form-label small fw-semibold" for="collect-end">Sampai</label>
      <input id="collect-end" v-model.number="form.end" type="number" min="1" class="form-control" required />
    </div>
    <div class="col-6">
      <label class="form-label small fw-semibold" for="collect-delay-min">Delay min (detik)</label>
      <input
        id="collect-delay-min"
        v-model.number="form.delayMin"
        type="number"
        min="0.1"
        max="30"
        step="0.1"
        class="form-control"
        required
      />
    </div>
    <div class="col-6">
      <label class="form-label small fw-semibold" for="collect-delay-max">Delay max (detik)</label>
      <input
        id="collect-delay-max"
        v-model.number="form.delayMax"
        type="number"
        min="0.1"
        max="30"
        step="0.1"
        class="form-control"
        required
      />
    </div>
    <div class="col-12">
      <div class="form-check">
        <input id="collect-force" v-model="form.force" class="form-check-input" type="checkbox" />
        <label class="form-check-label small" for="collect-force">
          Proses ulang nomor yang sudah ada di cache
        </label>
      </div>
      <div class="form-check">
        <input id="collect-adjacent" v-model="form.useAdjacentMonth" class="form-check-input" type="checkbox" />
        <label class="form-check-label small" for="collect-adjacent">
          Coba bulan sebelumnya/berikutnya jika tidak ditemukan
        </label>
      </div>
    </div>
    <div v-if="store.preview" class="col-12">
      <div class="d-flex flex-wrap gap-3 small muted border rounded px-3 py-2">
        <span>Total: <strong>{{ store.preview.total }}</strong></span>
        <span>Sudah ada: <strong>{{ store.preview.sudah_ada }}</strong></span>
        <span>Akan diproses: <strong>{{ store.preview.akan_diproses }}</strong></span>
        <span>Estimasi: <strong>{{ store.preview.estimasi_menit }} menit</strong></span>
        <span>Dijalankan dalam <strong>{{ store.preview.chunks }}</strong> chunk</span>
      </div>
    </div>
    <div class="col-12 d-flex gap-2">
      <button class="btn btn-outline-success flex-grow-1" type="submit" :disabled="store.previewing">
        <span v-if="store.previewing" class="spinner-border spinner-border-sm me-2" aria-hidden="true"></span>
        <i v-else class="bi bi-calculator me-2"></i>
        Cek Rentang
      </button>
      <button
        class="btn btn-success flex-grow-1"
        type="button"
        :disabled="store.collecting || store.collectRunning"
        @click="start"
      >
        <span v-if="store.collecting" class="spinner-border spinner-border-sm me-2" aria-hidden="true"></span>
        <i v-else class="bi bi-play-fill me-2"></i>
        Mulai
      </button>
    </div>
    <p v-if="previewError" class="col-12 text-danger small mb-0">{{ previewError }}</p>
  </form>
</template>
