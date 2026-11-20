import { defineStore } from "pinia";
import { api, gatewayUserMessage, jobUserMessage, userMessage } from "../api";
import type {
  CollectPreview,
  EpurchasingKind,
  EpurchasingRow,
  GatewayJobState,
  JobState,
  PageResult,
  ProductRow,
  TkdnRow,
} from "../types";

const sleep = (ms: number) => new Promise((resolve) => window.setTimeout(resolve, ms));

export function splitCollectRanges(start: number, end: number, size = 1000) {
  const ranges: Array<[number, number]> = [];
  for (let first = start; first <= end; first += size) {
    ranges.push([first, Math.min(first + size - 1, end)]);
  }
  return ranges;
}

const idleJob = (): JobState => ({
  job_id: null,
  status: "idle",
  total: 0,
  done: 0,
  processed: 0,
  error: 0,
  found: 0,
  empty: 0,
  errors: 0,
  skipped: 0,
  progress: 0,
  start: null,
  end: null,
  template: null,
  last_error: null,
  current: null,
  current_number: null,
  started_at: null,
  finished_at: null,
});

export const useTkdnStore = defineStore("tkdn", {
  state: () => ({
    query: "",
    brand: "",
    minValue: null as number | null,
    sort: "number",
    order: "asc",
    page: 1,
    perPage: 25,
    total: 0,
    rows: [] as TkdnRow[],
    resultSource: "Database" as "Database" | "Portal TKDN" | "API Gateway",
    searching: false,
    lookingUp: false,
    refreshingNumber: "" as string,
    job: idleJob(),
    preview: null as CollectPreview | null,
    previewing: false,
    collecting: false,
    chunkTotal: 0,
    chunkIndex: 0,
    chunkStart: null as number | null,
    chunkEnd: null as number | null,
    polling: false,
    error: "",
    notice: "",
    productQuery: "",
    productRows: [] as ProductRow[],
    productTotal: 0,
    productPage: 1,
    productPerPage: 20,
    productSort: "nama_produk",
    productOrder: "asc",
    productSearching: false,
    gatewayEnabled: false,
    gatewaySyncing: false,
    gatewayJob: null as GatewayJobState | null,
    paketCount: 0,
    transaksiCount: 0,
    epKind: "paket" as EpurchasingKind,
    epQuery: "",
    epTahun: null as number | null,
    epKodeKlpd: "",
    epKdProduk: "",
    epKodePenyedia: "",
    epRows: [] as EpurchasingRow[],
    epTotal: 0,
    epPage: 1,
    epPerPage: 20,
    epSort: "nama_paket",
    epOrder: "asc",
    epSearching: false,
    cancelling: false,
  }),
  getters: {
    pageCount(state): number {
      return Math.max(1, Math.ceil(state.total / state.perPage));
    },
    productPageCount(state): number {
      return Math.max(1, Math.ceil(state.productTotal / state.productPerPage));
    },
    epPageCount(state): number {
      return Math.max(1, Math.ceil(state.epTotal / state.epPerPage));
    },
    collectRunning(state): boolean {
      return ["running", "cancelling"].includes(state.job.status);
    },
  },
  actions: {
    applyPage(result: PageResult<TkdnRow>) {
      this.rows = result.items;
      this.total = result.total;
      this.page = result.page;
      this.perPage = result.per_page;
    },
    async search() {
      this.searching = true;
      this.error = "";
      try {
        const result = await api.searchTkdn({
          q: this.query,
          brand: this.brand,
          min_value: this.minValue,
          page: this.page,
          per_page: this.perPage,
          sort: this.sort,
          order: this.order,
        });
        this.applyPage(result);
        this.resultSource = "Database";
      } catch (error) {
        this.error = userMessage(error);
      } finally {
        this.searching = false;
      }
    },
    async goToPage(page: number) {
      this.page = Math.min(Math.max(1, page), this.pageCount);
      await this.search();
    },
    async lookup(number: string, force = false) {
      this.lookingUp = true;
      this.error = "";
      this.notice = "";
      try {
        const result = await api.lookup(number, force);
        this.resultSource = result.source === "db" ? "Database" : "Portal TKDN";
        this.notice =
          result.source === "db"
            ? "Hasil diambil dari cache MySQL."
            : "Hasil diambil dari INAPROC lalu disimpan ke MySQL.";
        await this.search();
        return result;
      } catch (error) {
        this.error = userMessage(error);
        throw error;
      } finally {
        this.lookingUp = false;
      }
    },
    async previewRange(
      template: string,
      start: number,
      end: number,
      delayMin = 1,
      delayMax = 3,
    ) {
      this.previewing = true;
      this.error = "";
      try {
        this.preview = await api.preview(template, start, end, delayMin, delayMax);
        return this.preview;
      } catch (error) {
        this.error = userMessage(error);
        throw error;
      } finally {
        this.previewing = false;
      }
    },
    async startCollect(
      template: string,
      start: number,
      end: number,
      options: {
        delayMin?: number;
        delayMax?: number;
        force?: boolean;
        retry?: boolean;
      } = {},
    ) {
      this.collecting = true;
      this.error = "";
      const ranges = options.retry && this.chunkStart !== null && this.chunkEnd !== null
        ? [[this.chunkStart, this.chunkEnd] as [number, number]]
        : splitCollectRanges(start, end);
      this.chunkTotal = ranges.length;
      this.chunkIndex = 0;
      const aggregate: JobState = {
        job_id: null,
        status: "running",
        total: 0,
        done: 0,
        processed: 0,
        error: 0,
        found: 0,
        empty: 0,
        errors: 0,
        skipped: 0,
        progress: 0,
        start,
        end,
        template,
        last_error: null,
        current: null,
        current_number: null,
        started_at: null,
        finished_at: null,
      };
      try {
        for (const [chunkStart, chunkEnd] of ranges) {
          this.chunkIndex += 1;
          this.chunkStart = chunkStart;
          this.chunkEnd = chunkEnd;
          const result = await api.collect(template, chunkStart, chunkEnd, options);
          this.job = result.job;
          const final = await this.pollUntilDone();
          aggregate.total += final.total;
          aggregate.done += final.done;
          aggregate.found += final.found;
          aggregate.empty += final.empty;
          aggregate.errors += final.errors;
          aggregate.skipped += final.skipped;
          aggregate.status = final.status;
          aggregate.job_id = final.job_id ?? aggregate.job_id;
          aggregate.last_error = final.last_error ? jobUserMessage(final.last_error) : aggregate.last_error;
          if (["cancelled", "stopped", "failed"].includes(final.status)) {
            break;
          }
        }
        if (aggregate.errors > 0) {
          aggregate.status = "error";
        }
        aggregate.progress = aggregate.total
          ? Math.round((aggregate.done / aggregate.total) * 10000) / 10000
          : 0;
        this.job = aggregate;
        await this.search();
        return { accepted: true, job: aggregate };
      } catch (error) {
        this.error = userMessage(error);
        throw error;
      } finally {
        this.collecting = false;
      }
    },
    async cancelCollect() {
      this.cancelling = true;
      this.error = "";
      try {
        await api.cancelCollect();
        await this.refreshStatus();
      } catch (error) {
        this.error = userMessage(error);
      } finally {
        this.cancelling = false;
      }
    },
    async retryCollect(
      template: string,
      start: number,
      end: number,
      options: { delayMin?: number; delayMax?: number; force?: boolean } = {},
    ) {
      return this.startCollect(template, start, end, { ...options, retry: true });
    },
    async refreshStatus() {
      this.job = await api.status();
    },
    async pollUntilDone(): Promise<JobState> {
      this.polling = true;
      try {
        while (true) {
          await sleep(2000);
          this.job = await api.status();
          if (!["running", "cancelling"].includes(this.job.status)) {
            return this.job;
          }
        }
      } finally {
        this.polling = false;
      }
    },
    async refreshNumber(number: string) {
      this.refreshingNumber = number;
      this.error = "";
      try {
        await api.refresh(number);
        this.resultSource = "Portal TKDN";
        this.notice = "Data nomor ini sudah diambil ulang.";
        await this.search();
      } catch (error) {
        this.error = userMessage(error);
      } finally {
        this.refreshingNumber = "";
      }
    },
    async loadGatewayStatus() {
      try {
        const status = await api.gatewayStatus();
        this.gatewayEnabled = status.enabled;
        this.paketCount = status.paket_count ?? 0;
        this.transaksiCount = status.transaksi_count ?? 0;
      } catch (error) {
        this.error = userMessage(error);
      }
    },
    async syncGateway(scope = "produk") {
      this.gatewaySyncing = true;
      this.error = "";
      this.notice = "";
      try {
        const { job } = await api.syncGateway(scope, true);
        this.gatewayJob = job;
        let current = job;
        while (["queued", "running"].includes(current.status)) {
          await sleep(1500);
          current = await api.syncStatus(scope);
          this.gatewayJob = current;
        }
        if (current.status === "failed") {
          this.error = gatewayUserMessage(current);
          return;
        }
        this.notice =
          current.status === "skipped"
            ? "Data sudah ada di cache MySQL."
            : `Sinkronisasi ${scope} selesai: ${current.items ?? 0} baris.`;
        await Promise.all([this.searchProducts(), this.searchEpurchasing(), this.loadGatewayStatus()]);
      } catch (error) {
        this.error = userMessage(error);
      } finally {
        this.gatewaySyncing = false;
      }
    },
    async searchProducts() {
      this.productSearching = true;
      this.error = "";
      try {
        const result = await api.searchProducts({
          q: this.productQuery,
          page: this.productPage,
          per_page: this.productPerPage,
          sort: this.productSort,
          order: this.productOrder,
        });
        this.productRows = result.items;
        this.productTotal = result.total;
        this.productPage = result.page;
        this.productPerPage = result.per_page;
      } catch (error) {
        this.error = userMessage(error);
      } finally {
        this.productSearching = false;
      }
    },
    async searchProductsFromFirstPage() {
      this.productPage = 1;
      await this.searchProducts();
    },
    async goToProductPage(page: number) {
      this.productPage = Math.min(Math.max(1, page), this.productPageCount);
      await this.searchProducts();
    },
    async changeProductPerPage(value: number) {
      this.productPerPage = value;
      this.productPage = 1;
      await this.searchProducts();
    },
    async setProductSort(sort: string, order: string) {
      this.productSort = sort;
      this.productOrder = order;
      this.productPage = 1;
      await this.searchProducts();
    },
    async searchEpurchasing() {
      this.epSearching = true;
      this.error = "";
      try {
        const result = await api.searchEpurchasing({
          kind: this.epKind,
          q: this.epQuery,
          tahun: this.epTahun,
          kode_klpd: this.epKodeKlpd,
          kd_produk: this.epKdProduk,
          kode_penyedia: this.epKodePenyedia,
          page: this.epPage,
          per_page: this.epPerPage,
          sort: this.epSort,
          order: this.epOrder,
        });
        this.epRows = result.items;
        this.epTotal = result.total;
        this.epPage = result.page;
        this.epPerPage = result.per_page;
      } catch (error) {
        this.error = userMessage(error);
      } finally {
        this.epSearching = false;
      }
    },
    async setEpKind(kind: EpurchasingKind) {
      if (this.epKind === kind) {
        return;
      }
      this.epKind = kind;
      this.epPage = 1;
      this.epSort = kind === "paket" ? "nama_paket" : "tahun";
      this.epOrder = kind === "paket" ? "asc" : "desc";
      await this.searchEpurchasing();
    },
    async goToEpPage(page: number) {
      this.epPage = Math.min(Math.max(1, page), this.epPageCount);
      await this.searchEpurchasing();
    },
    async changeEpPerPage(value: number) {
      this.epPerPage = value;
      this.epPage = 1;
      await this.searchEpurchasing();
    },
  },
});
