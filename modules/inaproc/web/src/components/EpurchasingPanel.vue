<script setup lang="ts">
import { computed } from "vue";
import PaginationBar from "./PaginationBar.vue";
import { useTkdnStore } from "../stores/tkdn";
import type { EpurchasingKind, EpurchasingRow } from "../types";
import { gatewayExportUrl } from "../api";

const store = useTkdnStore();

const kindOptions: { value: EpurchasingKind; label: string }[] = [
  { value: "paket", label: "Paket" },
  { value: "transaksi", label: "Transaksi" },
];

const sortOptions = computed(() =>
  store.epKind === "paket"
    ? [
        { value: "nama_paket", label: "Nama paket" },
        { value: "tahun", label: "Tahun" },
        { value: "total_nilai", label: "Nilai" },
        { value: "kode_klpd", label: "KLPD" },
      ]
    : [
        { value: "tahun", label: "Tahun" },
        { value: "nama_produk", label: "Produk" },
        { value: "jumlah", label: "Jumlah" },
        { value: "total", label: "Total" },
      ],
);

const exportParams = computed(() => ({
  q: store.epQuery,
  tahun: store.epTahun,
  kode_klpd: store.epKind === "paket" ? store.epKodeKlpd : "",
  kd_produk: store.epKind === "transaksi" ? store.epKdProduk : "",
  kode_penyedia: store.epKind === "transaksi" ? store.epKodePenyedia : "",
}));
const csvUrl = computed(() => gatewayExportUrl("csv", store.epKind, exportParams.value));
const jsonUrl = computed(() => gatewayExportUrl("json", store.epKind, exportParams.value));

function money(value: number | null): string {
  return value === null || value === undefined
    ? "-"
    : new Intl.NumberFormat("id-ID").format(value);
}

function text(value: string | null | undefined): string {
  return value ? value : "-";
}

function keyOf(row: EpurchasingRow, index: number): string {
  return store.epKind === "paket" ? row.kode_paket ?? `paket-${index}` : row.order_id ?? `order-${index}`;
}

async function applySort() {
  store.epPage = 1;
  await store.searchEpurchasing();
}
</script>

<template>
  <section class="panel p-3 mt-4">
    <div class="d-flex flex-wrap justify-content-between align-items-center gap-2 mb-3">
      <div>
        <h2 class="h6 mb-0">E-Purchasing INAPROC</h2>
        <div class="small muted">Paket dan realisasi dari API Gateway resmi, read-only.</div>
      </div>
      <div class="d-flex flex-wrap align-items-center gap-2">
        <div class="btn-group btn-group-sm" role="group" aria-label="Jenis data e-purchasing">
          <button
            v-for="option in kindOptions"
            :key="option.value"
            class="btn"
            :class="store.epKind === option.value ? 'btn-success' : 'btn-outline-success'"
            type="button"
            :disabled="store.epSearching"
            @click="store.setEpKind(option.value)"
          >
            {{ option.label }}
          </button>
        </div>
        <div class="btn-group btn-group-sm">
          <a class="btn btn-outline-secondary" :href="csvUrl" title="Ekspor e-purchasing CSV">
            <i class="bi bi-filetype-csv me-1"></i>
            CSV
          </a>
          <a class="btn btn-outline-secondary" :href="jsonUrl" title="Ekspor e-purchasing JSON">
            <i class="bi bi-filetype-json me-1"></i>
            JSON
          </a>
        </div>
        <button
          class="btn btn-sm btn-success"
          type="button"
          :disabled="!store.gatewayEnabled || store.gatewaySyncing"
          @click="store.syncGateway(store.epKind)"
        >
          <span v-if="store.gatewaySyncing" class="spinner-border spinner-border-sm me-2" aria-hidden="true"></span>
          <i v-else class="bi bi-cloud-arrow-down me-2"></i>
          Sync
        </button>
      </div>
    </div>

    <form class="row g-2 align-items-end mb-3" @submit.prevent="store.goToEpPage(1)">
      <div class="col-12 col-md-4">
        <label class="form-label small fw-semibold" for="ep-query">
          {{ store.epKind === "paket" ? "Cari paket / KLPD" : "Cari produk / order" }}
        </label>
        <input
          id="ep-query"
          v-model="store.epQuery"
          class="form-control"
          :placeholder="store.epKind === 'paket' ? 'Paket monitor' : 'Monitor 24'"
        />
      </div>
      <div class="col-6 col-md-2">
        <label class="form-label small fw-semibold" for="ep-tahun">Tahun</label>
        <input
          id="ep-tahun"
          v-model.number="store.epTahun"
          type="number"
          min="2000"
          max="2100"
          class="form-control"
          placeholder="2026"
        />
      </div>
      <div v-if="store.epKind === 'paket'" class="col-6 col-md-3">
        <label class="form-label small fw-semibold" for="ep-klpd">Kode KLPD</label>
        <input id="ep-klpd" v-model="store.epKodeKlpd" class="form-control mono" placeholder="K1" />
      </div>
      <template v-else>
        <div class="col-6 col-md-2">
          <label class="form-label small fw-semibold" for="ep-produk">Kode produk</label>
          <input id="ep-produk" v-model="store.epKdProduk" class="form-control mono" placeholder="K1" />
        </div>
        <div class="col-6 col-md-1">
          <label class="form-label small fw-semibold" for="ep-penyedia">Penyedia</label>
          <input id="ep-penyedia" v-model="store.epKodePenyedia" class="form-control mono" placeholder="P1" />
        </div>
      </template>
      <div class="col-6 col-md-2">
        <label class="form-label small fw-semibold" for="ep-sort">Urut</label>
        <select id="ep-sort" v-model="store.epSort" class="form-select" @change="applySort">
          <option v-for="option in sortOptions" :key="option.value" :value="option.value">
            {{ option.label }}
          </option>
        </select>
      </div>
      <div class="col-6 col-md-1">
        <label class="form-label small fw-semibold" for="ep-order">Arah</label>
        <select id="ep-order" v-model="store.epOrder" class="form-select" @change="applySort">
          <option value="asc">Naik</option>
          <option value="desc">Turun</option>
        </select>
      </div>
      <div class="col-12 col-md-2">
        <button class="btn btn-outline-success w-100" type="submit" :disabled="store.epSearching">
          <span v-if="store.epSearching" class="spinner-border spinner-border-sm me-2" aria-hidden="true"></span>
          <i v-else class="bi bi-search me-2"></i>
          Cari
        </button>
      </div>
    </form>

    <div class="table-responsive">
      <table class="table table-hover align-middle mb-0">
        <thead v-if="store.epKind === 'paket'">
          <tr>
            <th>Kode paket</th>
            <th>Nama paket</th>
            <th>Tahun</th>
            <th>KLPD</th>
            <th class="text-end">Nilai</th>
            <th class="text-end">Detail</th>
          </tr>
        </thead>
        <thead v-else>
          <tr>
            <th>Order</th>
            <th>Produk</th>
            <th>Kode produk</th>
            <th>Tahun</th>
            <th class="text-end">Jumlah</th>
            <th class="text-end">Total</th>
            <th class="text-end">Detail</th>
          </tr>
        </thead>
        <tbody v-if="store.epKind === 'paket'">
          <tr v-if="!store.epRows.length">
            <td colspan="6" class="text-center py-4 muted">
              {{ store.epSearching ? "Mencari paket..." : "Belum ada paket e-purchasing di cache." }}
            </td>
          </tr>
          <tr v-for="(row, index) in store.epRows" :key="keyOf(row, index)">
            <td class="mono">{{ text(row.kode_paket) }}</td>
            <td class="fw-semibold">{{ text(row.nama_paket) }}</td>
            <td>{{ row.tahun ?? "-" }}</td>
            <td class="mono">{{ text(row.kode_klpd) }}</td>
            <td class="text-end">{{ money(row.total_nilai ?? null) }}</td>
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
        <tbody v-else>
          <tr v-if="!store.epRows.length">
            <td colspan="7" class="text-center py-4 muted">
              {{ store.epSearching ? "Mencari transaksi..." : "Belum ada transaksi e-purchasing di cache." }}
            </td>
          </tr>
          <tr v-for="(row, index) in store.epRows" :key="keyOf(row, index)">
            <td class="mono">{{ text(row.order_id) }}</td>
            <td class="fw-semibold">{{ text(row.nama_produk) }}</td>
            <td class="mono">{{ text(row.kd_produk) }}</td>
            <td>{{ row.tahun ?? "-" }}</td>
            <td class="text-end">{{ money(row.jumlah ?? null) }}</td>
            <td class="text-end">{{ money(row.total ?? null) }}</td>
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

    <div class="border-top mt-3 pt-3">
      <PaginationBar
        :page="store.epPage"
        :page-count="store.epPageCount"
        :total="store.epTotal"
        :per-page="store.epPerPage"
        :loading="store.epSearching"
        @change="store.goToEpPage"
        @update:per-page="store.changeEpPerPage"
      />
    </div>
  </section>
</template>
