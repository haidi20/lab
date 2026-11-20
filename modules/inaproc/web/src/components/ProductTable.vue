<script setup lang="ts">
import { useTkdnStore } from "../stores/tkdn";

const store = useTkdnStore();
</script>

<template>
  <div class="table-responsive">
    <table class="table table-hover align-middle mb-0">
      <thead>
        <tr>
          <th>Produk</th>
          <th>Merek</th>
          <th>Kategori</th>
          <th class="text-end">Harga</th>
          <th>Penyedia</th>
          <th class="text-end">Sumber</th>
          <th class="text-end">Detail</th>
        </tr>
      </thead>
      <tbody>
        <tr v-if="!store.productRows.length">
          <td colspan="7" class="text-center py-4 muted">
            {{ store.productSearching ? "Mencari katalog..." : "Belum ada produk tersinkron di cache." }}
          </td>
        </tr>
        <tr v-for="row in store.productRows" :key="row.kd_produk">
          <td class="fw-semibold">{{ row.nama_produk || "-" }}</td>
          <td>{{ row.brand || "-" }}</td>
          <td>{{ row.kategori || "-" }}</td>
          <td class="text-end">
            {{ row.harga === null ? "-" : new Intl.NumberFormat("id-ID").format(row.harga) }}
          </td>
          <td class="mono">{{ row.kode_penyedia || "-" }}</td>
          <td class="text-end"><span class="badge text-bg-info">API Gateway</span></td>
          <td class="text-end">
            <a
              v-if="row.source_url"
              class="btn btn-sm btn-outline-success"
              :href="row.source_url"
              target="_blank"
              rel="noopener noreferrer"
            >
              Detail INAPROC
            </a>
            <span v-else class="muted small">-</span>
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>
