<script setup lang="ts">
import { useTkdnStore } from "../stores/tkdn";

const store = useTkdnStore();

function valueText(value: number | null): string {
  return value === null || value === undefined ? "-" : value.toFixed(2);
}

async function copyNumber(number: string): Promise<void> {
  try {
    await navigator.clipboard.writeText(number);
  } catch {
    // The number remains selectable for manual copy.
  }
}

function copyTitle(number: string): string {
  return "Salin " + number;
}

function portalUrl(number: string): string {
  return "https://penyedia.inaproc.id/products/tkdn?keyword=" + encodeURIComponent(number);
}

function sourceBadge(): string {
  return store.resultSource;
}
</script>

<template>
  <div class="table-responsive">
    <table class="table table-sm table-hover align-middle mb-0" :class="{ 'opacity-50': store.searching }">
      <thead>
        <tr>
          <th>Nomor SPT</th>
          <th>Jenis Produk</th>
          <th>Merek</th>
          <th>Tipe</th>
          <th>Uraian Produk</th>
          <th>Standard</th>
          <th class="text-end">Nilai</th>
          <th class="text-end">Sumber</th>
          <th class="text-end">Aksi</th>
        </tr>
      </thead>
      <tbody>
        <tr v-if="!store.rows.length">
          <td colspan="9" class="text-center py-4">
            <div v-if="store.searching" class="muted">Mencari data...</div>
            <div v-else-if="store.notice" class="alert alert-info mb-0 py-2">
              Cache untuk nomor ini kosong. Tidak ada scraping ulang.
            </div>
            <div v-else class="alert alert-warning mb-0 py-2">
              Tidak ada hasil untuk filter ini.
            </div>
          </td>
        </tr>
        <tr v-for="row in store.rows" :key="`${row.number}-${row.brand}-${row.type}-${row.description}`">
          <td class="mono">
            <button
              class="btn btn-link btn-sm p-0 text-start"
              type="button"
              :title="copyTitle(row.number)"
              @click="copyNumber(row.number)"
            >
              {{ row.number }}
            </button>
          </td>
          <td>{{ row.product_type || "-" }}</td>
          <td class="fw-semibold">{{ row.brand || "-" }}</td>
          <td>{{ row.type || "-" }}</td>
          <td>{{ row.description || "-" }}</td>
          <td>{{ row.standard || "-" }}</td>
          <td class="text-end">{{ valueText(row.value) }}</td>
          <td class="text-end"><span class="badge text-bg-primary">{{ sourceBadge() }}</span></td>
          <td class="text-end">
            <a
              class="btn btn-sm btn-outline-success me-1"
              :href="portalUrl(row.number)"
              target="_blank"
              rel="noopener noreferrer"
              title="Buka nomor ini di portal INAPROC"
            >
              <i class="bi bi-box-arrow-up-right"></i>
            </a>
            <button
              class="btn btn-sm btn-outline-secondary"
              type="button"
              title="Ambil ulang nomor ini dari INAPROC"
              :disabled="store.refreshingNumber === row.number"
              @click="store.refreshNumber(row.number)"
            >
              <span
                v-if="store.refreshingNumber === row.number"
                class="spinner-border spinner-border-sm"
                aria-hidden="true"
              ></span>
              <i v-else class="bi bi-arrow-repeat"></i>
            </button>
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>
