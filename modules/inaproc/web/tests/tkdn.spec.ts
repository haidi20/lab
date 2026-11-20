import { beforeEach, describe, expect, it, vi } from "vitest";
import { createPinia, setActivePinia } from "pinia";

import { ApiError, api, gatewayUserMessage, jobUserMessage, userMessage } from "../src/api";
import { useTkdnStore } from "../src/stores/tkdn";

vi.mock("../src/api", async () => {
  const actual = await vi.importActual<typeof import("../src/api")>("../src/api");
  return {
    ...actual,
    api: {
      searchTkdn: vi.fn(),
      lookup: vi.fn(),
      preview: vi.fn(),
      collect: vi.fn(),
      cancelCollect: vi.fn(),
      status: vi.fn(),
      refresh: vi.fn(),
      gatewayStatus: vi.fn(),
      searchProducts: vi.fn(),
      searchEpurchasing: vi.fn(),
      syncGateway: vi.fn(),
      syncStatus: vi.fn(),
      session: vi.fn(),
      login: vi.fn(),
      logout: vi.fn(),
    },
  };
});

const mocked = vi.mocked(api, true);

describe("tkdn store", () => {
  beforeEach(() => {
    setActivePinia(createPinia());
    vi.clearAllMocks();
  });

  it("search menyimpan hasil dan total", async () => {
    mocked.searchTkdn.mockResolvedValue({
      items: [{ number: "1/SJ/E-TKDN/7/2025", brand: "acer" } as never],
      page: 1,
      per_page: 25,
      total: 1,
    });
    const store = useTkdnStore();
    await store.search();
    expect(store.rows).toHaveLength(1);
    expect(store.total).toBe(1);
    expect(store.searching).toBe(false);
  });

  it("lookup db-first menampilkan sumber cache", async () => {
    mocked.lookup.mockResolvedValue({ source: "db", status: "found", items: [] });
    mocked.searchTkdn.mockResolvedValue({ items: [], page: 1, per_page: 25, total: 0 });
    const store = useTkdnStore();
    await store.lookup("1/SJ/E-TKDN/7/2025");
    expect(mocked.lookup).toHaveBeenCalledWith("1/SJ/E-TKDN/7/2025", false);
    expect(store.notice).toContain("cache MySQL");
  });

  it("preview rentang menyimpan angka batch", async () => {
    mocked.preview.mockResolvedValue({
      total: 2500,
      sudah_ada: 0,
      akan_diproses: 2500,
      estimasi_menit: 83.3,
      chunks: 3,
    });
    const store = useTkdnStore();
    const result = await store.previewRange("1/SJ/E-TKDN/7/2025", 1, 2500);
    expect(result.chunks).toBe(3);
    expect(store.preview?.total).toBe(2500);
    expect(mocked.preview).toHaveBeenCalledWith("1/SJ/E-TKDN/7/2025", 1, 2500, 1, 3);
  });

  it("collect rentang besar dipecah menjadi batch 1000 berurutan", async () => {
    mocked.collect
      .mockResolvedValueOnce({
        accepted: true,
        job: {
          status: "running",
          total: 1000,
          done: 0,
          found: 0,
          empty: 0,
          errors: 0,
          skipped: 0,
          progress: 0,
          start: 1,
          end: 1000,
          template: "1/SJ/E-TKDN/7/2025",
          last_error: null,
          current: null,
        },
      })
      .mockResolvedValueOnce({
        accepted: true,
        job: {
          status: "running",
          total: 500,
          done: 0,
          found: 0,
          empty: 0,
          errors: 0,
          skipped: 0,
          progress: 0,
          start: 1001,
          end: 1500,
          template: "1/SJ/E-TKDN/7/2025",
          last_error: null,
          current: null,
        },
      });
    mocked.status
      .mockResolvedValueOnce({
        status: "done",
        total: 1000,
        done: 1000,
        found: 800,
        empty: 200,
        errors: 0,
        skipped: 0,
        progress: 1,
        start: 1,
        end: 1000,
        template: "1/SJ/E-TKDN/7/2025",
        last_error: null,
        current: null,
      })
      .mockResolvedValueOnce({
        status: "done",
        total: 500,
        done: 500,
        found: 400,
        empty: 100,
        errors: 0,
        skipped: 0,
        progress: 1,
        start: 1001,
        end: 1500,
        template: "1/SJ/E-TKDN/7/2025",
        last_error: null,
        current: null,
      });
    mocked.searchTkdn.mockResolvedValue({ items: [], page: 1, per_page: 25, total: 0 });

    const store = useTkdnStore();
    await store.startCollect("1/SJ/E-TKDN/7/2025", 1, 1500);

    expect(mocked.collect).toHaveBeenCalledTimes(2);
    expect(mocked.collect).toHaveBeenNthCalledWith(1, "1/SJ/E-TKDN/7/2025", 1, 1000, {});
    expect(mocked.collect).toHaveBeenNthCalledWith(2, "1/SJ/E-TKDN/7/2025", 1001, 1500, {});
    expect(store.chunkTotal).toBe(2);
    expect(store.chunkIndex).toBe(2);
    expect(store.job.done).toBe(1500);
    expect(store.job.found).toBe(1200);
  });

  it("collect meneruskan opsi force dan delay", async () => {
    mocked.collect.mockResolvedValue({
      accepted: true,
      job: {
        status: "running",
        total: 10,
        done: 0,
        found: 0,
        empty: 0,
        errors: 0,
        skipped: 0,
        progress: 0,
        start: 1,
        end: 10,
        template: "1/SJ/E-TKDN/7/2025",
        last_error: null,
        current: null,
      },
    });
    mocked.status.mockResolvedValue({
      status: "done",
      total: 10,
      done: 10,
      found: 10,
      empty: 0,
      errors: 0,
      skipped: 0,
      progress: 1,
      start: 1,
      end: 10,
      template: "1/SJ/E-TKDN/7/2025",
      last_error: null,
      current: null,
    });
    mocked.searchTkdn.mockResolvedValue({ items: [], page: 1, per_page: 25, total: 0 });

    const store = useTkdnStore();
    await store.startCollect("1/SJ/E-TKDN/7/2025", 1, 10, {
      delayMin: 2,
      delayMax: 4,
      force: true,
    });

    expect(mocked.collect).toHaveBeenCalledWith("1/SJ/E-TKDN/7/2025", 1, 10, {
      delayMin: 2,
      delayMax: 4,
      force: true,
    });
  });

  it("error API mengisi state error", async () => {
    mocked.searchTkdn.mockRejectedValue(new Error("db down"));
    const store = useTkdnStore();
    await store.search();
    expect(store.error).toBe("Terjadi kesalahan. Coba lagi.");
    expect(store.searching).toBe(false);
  });

  it("collect berhenti pada chunk gagal dan menyimpan last_error", async () => {
    vi.spyOn(window, "setTimeout").mockImplementation(((callback: () => void) => {
      callback();
      return 1;
    }) as typeof window.setTimeout);
    mocked.collect.mockResolvedValue({
      accepted: true,
      job: { status: "running" } as never,
    });
    mocked.status.mockResolvedValue({
      status: "failed",
      total: 10,
      done: 0,
      found: 0,
      empty: 0,
      errors: 1,
      skipped: 0,
      progress: 0,
      start: 1,
      end: 10,
      template: "1/SJ/E-TKDN/7/2025",
      last_error: "belum_login: expired",
      current: null,
    } as never);
    mocked.searchTkdn.mockResolvedValue({ items: [], page: 1, per_page: 25, total: 0 });

    const store = useTkdnStore();
    await store.startCollect("1/SJ/E-TKDN/7/2025", 1, 10);

    expect(mocked.collect).toHaveBeenCalledTimes(1);
    expect(store.job.status).toBe("error");
    expect(store.job.last_error).toContain("Hubungkan sesi INAPROC");
  });

  it("retryCollect mengulang chunk terakhir saja", async () => {
    vi.spyOn(window, "setTimeout").mockImplementation(((callback: () => void) => {
      callback();
      return 1;
    }) as typeof window.setTimeout);
    mocked.collect.mockResolvedValue({
      accepted: true,
      job: { status: "running" } as never,
    });
    mocked.status.mockResolvedValue({
      status: "done",
      total: 10,
      done: 10,
      found: 10,
      empty: 0,
      errors: 0,
      skipped: 0,
      progress: 1,
      start: 1,
      end: 10,
      template: "1/SJ/E-TKDN/7/2025",
      last_error: null,
      current: null,
    } as never);
    mocked.searchTkdn.mockResolvedValue({ items: [], page: 1, per_page: 25, total: 0 });

    const store = useTkdnStore();
    store.chunkStart = 9001;
    store.chunkEnd = 9010;
    await store.retryCollect("1/SJ/E-TKDN/7/2025", 1, 2000);

    expect(mocked.collect).toHaveBeenCalledTimes(1);
    expect(mocked.collect).toHaveBeenCalledWith(
      "1/SJ/E-TKDN/7/2025",
      9001,
      9010,
      expect.objectContaining({ retry: true }),
    );
  });

  it("sync gateway memperbarui daftar produk", async () => {
    mocked.syncGateway.mockResolvedValue({
      job: { scope: "produk", status: "running" },
    });
    mocked.syncStatus.mockResolvedValue({
      scope: "produk",
      status: "success",
      items: 1,
    });
    mocked.searchProducts.mockResolvedValue({
      items: [{ kd_produk: "K1", nama_produk: "Monitor" } as never],
      page: 1,
      per_page: 20,
      total: 1,
    });
    mocked.searchEpurchasing.mockResolvedValue({
      kind: "paket",
      items: [],
      page: 1,
      per_page: 20,
      total: 0,
    });
    mocked.gatewayStatus.mockResolvedValue({
      enabled: true,
      scopes: ["produk"],
      produk_count: 1,
      paket_count: 0,
      transaksi_count: 0,
      last_run: null,
    });
    const store = useTkdnStore();
    await store.syncGateway("produk");
    expect(store.productRows).toHaveLength(1);
    expect(store.notice).toContain("selesai");
    expect(store.gatewaySyncing).toBe(false);
  });

  it("search e-purchasing menyimpan hasil dan filter aktif", async () => {
    mocked.searchEpurchasing.mockResolvedValue({
      kind: "paket",
      items: [
        {
          kode_paket: "PK1",
          nama_paket: "Paket Monitor",
          tahun: 2026,
          kode_klpd: "K1",
          total_nilai: 2500000,
          source_url: null,
        },
      ],
      page: 1,
      per_page: 20,
      total: 1,
    });
    const store = useTkdnStore();
    store.epQuery = "monitor";
    store.epTahun = 2026;
    await store.searchEpurchasing();
    expect(mocked.searchEpurchasing).toHaveBeenCalledWith(
      expect.objectContaining({ kind: "paket", q: "monitor", tahun: 2026 }),
    );
    expect(store.epRows).toHaveLength(1);
    expect(store.epTotal).toBe(1);
  });

  it("ganti jenis e-purchasing mereset halaman dan urutan", async () => {
    mocked.searchEpurchasing.mockResolvedValue({
      kind: "transaksi",
      items: [],
      page: 1,
      per_page: 20,
      total: 0,
    });
    const store = useTkdnStore();
    store.epPage = 4;
    await store.setEpKind("transaksi");
    expect(store.epPage).toBe(1);
    expect(store.epSort).toBe("tahun");
    expect(store.epOrder).toBe("desc");
    expect(mocked.searchEpurchasing).toHaveBeenCalled();
  });

  it("cancel collect memakai state loading sendiri", async () => {
    let release: (value: { cancelling: boolean }) => void = () => undefined;
    mocked.cancelCollect.mockReturnValue(
      new Promise((resolve) => {
        release = resolve;
      }),
    );
    mocked.status.mockResolvedValue({ status: "cancelling" } as never);
    const store = useTkdnStore();
    const pending = store.cancelCollect();
    expect(store.cancelling).toBe(true);
    release({ cancelling: true });
    await pending;
    expect(store.cancelling).toBe(false);
  });
});

describe("user-facing error messages", () => {
  it("memetakan kode API ke pesan Indonesia", () => {
    const error = new ApiError("Connect the INAPROC provider session first", "belum_login", 401);
    expect(userMessage(error)).toBe("Hubungkan sesi INAPROC terlebih dahulu.");
  });

  it("menampilkan pesan khusus untuk email INAPROC yang tidak terdaftar", () => {
    const error = new ApiError("INAPROC email is not registered", "login_failed", 401);
    expect(userMessage(error)).toBe("Email INAPROC belum terdaftar.");
  });

  it("memakai pesan aman untuk error lain", () => {
    expect(userMessage(new Error("db down"))).toBe("Terjadi kesalahan. Coba lagi.");
  });

  it("memetakan pesan job pengumpulan data", () => {
    expect(jobUserMessage("belum_login: expired")).toBe(
      "Hubungkan sesi INAPROC terlebih dahulu.",
    );
    expect(jobUserMessage("upstream parsing failed")).toBe(
      "Terjadi kesalahan saat pengumpulan data.",
    );
    expect(jobUserMessage(null)).toBe("");
  });

  it("memetakan kegagalan sinkronisasi gateway", () => {
    expect(gatewayUserMessage({ error_code: "TOKEN_EXPIRED", error_message: "expired" })).toBe(
      "Token INAPROC tidak valid atau sudah berakhir.",
    );
    expect(gatewayUserMessage({ error_code: "GATEWAY_DISABLED", error_message: "disabled" })).toBe(
      "API Gateway belum aktif. Atur token terlebih dahulu.",
    );
    expect(gatewayUserMessage({ error_code: null, error_message: "failed" })).toBe(
      "Sinkronisasi gagal. Coba lagi.",
    );
  });
});
