<script setup lang="ts">
import { computed, onMounted } from "vue";
import ConnectInaprocForm from "./components/ConnectInaprocForm.vue";
import CollectForm from "./components/CollectForm.vue";
import CollectProgress from "./components/CollectProgress.vue";
import EpurchasingPanel from "./components/EpurchasingPanel.vue";
import PaginationBar from "./components/PaginationBar.vue";
import ProductTable from "./components/ProductTable.vue";
import ResultTable from "./components/ResultTable.vue";
import SearchForm from "./components/SearchForm.vue";
import SessionBadge from "./components/SessionBadge.vue";
import { exportUrl, gatewayExportUrl } from "./api";
import { useInaprocSessionStore } from "./stores/inaprocSession";
import { useTkdnStore } from "./stores/tkdn";

const session = useInaprocSessionStore();
const store = useTkdnStore();

const csvUrl = computed(() =>
  exportUrl("csv", {
    q: store.query,
    brand: store.brand,
    min_value: store.minValue,
    sort: store.sort,
    order: store.order,
  }),
);
const jsonUrl = computed(() =>
  exportUrl("json", {
    q: store.query,
    brand: store.brand,
    min_value: store.minValue,
    sort: store.sort,
    order: store.order,
  }),
);
const productCsvUrl = computed(() =>
  gatewayExportUrl("csv", "produk", { q: store.productQuery }),
);
const productJsonUrl = computed(() =>
  gatewayExportUrl("json", "produk", { q: store.productQuery }),
);

onMounted(async () => {
  await session.load();
  if (!session.configured) {
    return;
  }
  await Promise.all([
    store.search(),
    store.loadGatewayStatus(),
    store.searchEpurchasing(),
  ]);
  if (store.gatewayEnabled) {
    await store.searchProducts();
  }
});

async function changePerPage(value: number) {
  store.perPage = value;
  store.page = 1;
  await store.search();
}
</script>

<template>
  <div class="container-fluid app-shell py-4">
    <header class="d-flex flex-wrap justify-content-between align-items-center gap-3 mb-4">
      <div class="d-flex align-items-center gap-3">
        <div class="brand-mark">IN</div>
        <div>
          <h1 class="h4 mb-0">Pencarian TKDN INAPROC</h1>
          <div class="small muted">Cache MySQL, sesi INAPROC sekali, ekspor CSV/JSON.</div>
        </div>
      </div>
      <SessionBadge />
    </header>

    <div v-if="store.error" class="alert alert-danger d-flex justify-content-between align-items-center">
      <span>{{ store.error }}</span>
      <button class="btn-close" type="button" aria-label="Tutup" @click="store.error = ''"></button>
    </div>
    <div v-if="store.notice" class="alert alert-success d-flex justify-content-between align-items-center">
      <span>{{ store.notice }}</span>
      <button class="btn-close" type="button" aria-label="Tutup" @click="store.notice = ''"></button>
    </div>

    <section v-if="!session.configured" class="panel p-3 mb-4">
      <h2 class="h6 mb-1">Koneksi Penyedia INAPROC</h2>
      <p class="small muted mb-3">
        Bukan login aplikasi. Kredensial dipakai backend untuk membuka sesi penyedia INAPROC
        dan menyimpan <span class="mono">storageState.json</span>.
      </p>
      <ConnectInaprocForm />
    </section>

    <div v-if="session.configured" class="row g-4">
      <div class="col-12 col-xl-9">
        <section class="panel p-3 mb-4">
          <SearchForm />
        </section>

        <section class="panel mb-4">
          <div class="d-flex flex-wrap justify-content-between align-items-center gap-2 px-3 pt-3">
            <div>
              <h2 class="h6 mb-0">Hasil TKDN</h2>
              <div class="small muted">Pencarian tabel tidak memanggil INAPROC.</div>
            </div>
            <div class="btn-group">
              <a class="btn btn-sm btn-outline-secondary" :href="csvUrl" title="Ekspor CSV">
                <i class="bi bi-filetype-csv me-1"></i>
                CSV
              </a>
              <a class="btn btn-sm btn-outline-secondary" :href="jsonUrl" title="Ekspor JSON">
                <i class="bi bi-filetype-json me-1"></i>
                JSON
              </a>
            </div>
          </div>
          <ResultTable class="mt-3" />
          <div class="border-top p-3">
            <PaginationBar
              :page="store.page"
              :page-count="store.pageCount"
              :total="store.total"
              :per-page="store.perPage"
              :loading="store.searching"
              @change="store.goToPage"
              @update:per-page="changePerPage"
            />
          </div>
        </section>

        <section class="panel p-3">
          <div class="d-flex flex-wrap justify-content-between align-items-center gap-2 mb-3">
            <div>
              <h2 class="h6 mb-0">Katalog INAPROC</h2>
              <div class="small muted">Data API Gateway resmi, read-only.</div>
            </div>
            <div class="d-flex align-items-center gap-2">
              <span class="badge" :class="store.gatewayEnabled ? 'text-bg-success' : 'text-bg-secondary'">
                {{ store.gatewayEnabled ? "Gateway aktif" : "Gateway nonaktif" }}
              </span>
              <div class="btn-group">
                <a class="btn btn-sm btn-outline-secondary" :href="productCsvUrl" title="Ekspor katalog CSV">
                  <i class="bi bi-filetype-csv me-1"></i>
                  CSV
                </a>
                <a class="btn btn-sm btn-outline-secondary" :href="productJsonUrl" title="Ekspor katalog JSON">
                  <i class="bi bi-filetype-json me-1"></i>
                  JSON
                </a>
              </div>
            </div>
          </div>
          <div v-if="!store.gatewayEnabled" class="alert alert-info py-2 small mb-3">
            Token API Gateway belum aktif atau belum disetujui LKPP. Token dapat diatur lewat
            <span class="mono">INAPROC_API_TOKEN</span>. Fitur TKDN tetap memakai sesi penyedia.
          </div>
          <form class="row g-2 align-items-end mb-3" @submit.prevent="store.searchProductsFromFirstPage()">
            <div class="col-12 col-md-5">
              <label class="form-label small fw-semibold" for="product-query">Cari katalog</label>
              <input
                id="product-query"
                v-model="store.productQuery"
                class="form-control"
                placeholder="Nama produk, merek, penyedia"
              />
            </div>
            <div class="col-6 col-md-2">
              <label class="form-label small fw-semibold" for="product-sort">Urut</label>
              <select
                id="product-sort"
                class="form-select"
                :value="store.productSort"
                @change="store.setProductSort(($event.target as HTMLSelectElement).value, store.productOrder)"
              >
                <option value="nama_produk">Produk</option>
                <option value="brand">Merek</option>
                <option value="kategori">Kategori</option>
                <option value="harga">Harga</option>
              </select>
            </div>
            <div class="col-6 col-md-2">
              <label class="form-label small fw-semibold" for="product-order">Arah</label>
              <select
                id="product-order"
                class="form-select"
                :value="store.productOrder"
                @change="store.setProductSort(store.productSort, ($event.target as HTMLSelectElement).value)"
              >
                <option value="asc">Naik</option>
                <option value="desc">Turun</option>
              </select>
            </div>
            <div class="col-12 col-md-3 d-flex gap-2">
              <button class="btn btn-outline-success flex-grow-1" type="submit" :disabled="store.productSearching">
                <span v-if="store.productSearching" class="spinner-border spinner-border-sm me-2" aria-hidden="true"></span>
                <i v-else class="bi bi-search me-2"></i>
                Cari
              </button>
              <button
                class="btn btn-success"
                type="button"
                :disabled="!store.gatewayEnabled || store.gatewaySyncing"
                @click="store.syncGateway('produk')"
              >
                <span v-if="store.gatewaySyncing" class="spinner-border spinner-border-sm me-2" aria-hidden="true"></span>
                <i v-else class="bi bi-cloud-arrow-down me-2"></i>
                Sync
              </button>
            </div>
          </form>
          <ProductTable />
          <div class="border-top mt-3 pt-3">
            <PaginationBar
              :page="store.productPage"
              :page-count="store.productPageCount"
              :total="store.productTotal"
              :per-page="store.productPerPage"
              :loading="store.productSearching"
              @change="store.goToProductPage"
              @update:per-page="store.changeProductPerPage"
            />
          </div>
        </section>

        <EpurchasingPanel />
      </div>

      <div class="col-12 col-xl-3">
        <section class="panel p-3 mb-4">
          <h2 class="h6 mb-3">Ambil Rentang</h2>
          <CollectForm />
        </section>
        <section class="panel p-3">
          <h2 class="h6 mb-3">Progres Collect</h2>
          <CollectProgress />
          <p v-if="store.job.status === 'idle'" class="small muted mb-0">
            Belum ada job collect yang berjalan.
          </p>
        </section>
      </div>
    </div>
  </div>
</template>
