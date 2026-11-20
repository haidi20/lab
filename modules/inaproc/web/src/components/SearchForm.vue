<script setup lang="ts">
import { onBeforeUnmount, ref, watch } from "vue";
import { useTkdnStore } from "../stores/tkdn";

const store = useTkdnStore();
const lookupNumber = ref("");
let debounceTimer: number | undefined;

watch(
  () => [store.query, store.brand, store.minValue],
  () => {
    if (debounceTimer !== undefined) {
      window.clearTimeout(debounceTimer);
    }
    debounceTimer = window.setTimeout(() => {
      store.page = 1;
      void store.search();
    }, 300);
  },
);

onBeforeUnmount(() => {
  if (debounceTimer !== undefined) {
    window.clearTimeout(debounceTimer);
  }
});

async function applySort() {
  store.page = 1;
  await store.search();
}

async function submitSearch() {
  store.page = 1;
  await store.search();
}

async function lookup() {
  if (!lookupNumber.value.trim()) {
    return;
  }
  try {
    await store.lookup(lookupNumber.value.trim());
  } catch {
    // Error is shown by the shared alert.
  }
}
</script>

<template>
  <div class="row g-3">
    <div class="col-12 col-lg-7">
      <form class="row g-2" @submit.prevent="submitSearch">
        <div class="col-12 col-md-5">
          <label class="form-label small fw-semibold" for="tkdn-query">Cari di cache</label>
          <input
            id="tkdn-query"
            v-model="store.query"
            class="form-control"
            placeholder="Merek, tipe, uraian, nomor SPT"
          />
        </div>
        <div class="col-6 col-md-3">
          <label class="form-label small fw-semibold" for="tkdn-brand">Merek</label>
          <input id="tkdn-brand" v-model="store.brand" class="form-control" placeholder="acer" />
        </div>
        <div class="col-6 col-md-2">
          <label class="form-label small fw-semibold" for="tkdn-min">Nilai min</label>
          <input
            id="tkdn-min"
            v-model.number="store.minValue"
            type="number"
            min="0"
            step="0.01"
            class="form-control"
          />
        </div>
        <div class="col-12 col-md-2 d-flex align-items-end">
          <button class="btn btn-success w-100" type="submit" :disabled="store.searching">
            <span v-if="store.searching" class="spinner-border spinner-border-sm me-2" aria-hidden="true"></span>
            <i v-else class="bi bi-search me-2"></i>
            Cari
          </button>
        </div>
        <div class="col-6 col-md-3">
          <label class="form-label small fw-semibold" for="tkdn-sort">Urut</label>
          <select id="tkdn-sort" v-model="store.sort" class="form-select" @change="applySort">
            <option value="number">Nomor SPT</option>
            <option value="brand">Merek</option>
            <option value="value">Nilai</option>
            <option value="product_type">Jenis produk</option>
          </select>
        </div>
        <div class="col-6 col-md-2">
          <label class="form-label small fw-semibold" for="tkdn-order">Arah</label>
          <select id="tkdn-order" v-model="store.order" class="form-select" @change="applySort">
            <option value="asc">Naik</option>
            <option value="desc">Turun</option>
          </select>
        </div>
      </form>
    </div>
    <div class="col-12 col-lg-5">
      <form class="row g-2" @submit.prevent="lookup">
        <div class="col-12 col-sm-8">
          <label class="form-label small fw-semibold" for="tkdn-number">Ambil satu nomor SPT</label>
          <input
            id="tkdn-number"
            v-model="lookupNumber"
            class="form-control mono"
            placeholder="11469/SJ-IND.8/E-TKDN/7/2025"
          />
        </div>
        <div class="col-12 col-sm-4 d-flex align-items-end">
          <button class="btn btn-outline-success w-100" type="submit" :disabled="store.lookingUp">
            <span v-if="store.lookingUp" class="spinner-border spinner-border-sm me-2" aria-hidden="true"></span>
            <i v-else class="bi bi-cloud-download me-2"></i>
            Ambil
          </button>
        </div>
      </form>
    </div>
  </div>
</template>
