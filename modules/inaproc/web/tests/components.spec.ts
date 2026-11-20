import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { flushPromises, mount } from "@vue/test-utils";
import { createPinia, setActivePinia } from "pinia";

import { ApiError, api, gatewayUserMessage, jobUserMessage, userMessage } from "../src/api";
import App from "../src/App.vue";
import CollectProgress from "../src/components/CollectProgress.vue";
import SearchForm from "../src/components/SearchForm.vue";
import { useTkdnStore } from "../src/stores/tkdn";

vi.mock("../src/api", async () => {
  const actual = await vi.importActual<typeof import("../src/api")>("../src/api");
  return {
    ...actual,
    api: {
      session: vi.fn(),
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
      login: vi.fn(),
      logout: vi.fn(),
    },
  };
});

const mocked = vi.mocked(api, true);

describe("frontend behavior", () => {
  beforeEach(() => {
    setActivePinia(createPinia());
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("App hanya menampilkan form koneksi saat sesi belum ada", async () => {
    mocked.session.mockResolvedValue({
      configured: false,
      valid: null,
      checked_at: "2026-01-01T00:00:00+00:00",
    });
    const wrapper = mount(App);
    await flushPromises();

    expect(wrapper.text()).toContain("Koneksi Penyedia INAPROC");
    expect(wrapper.text()).not.toContain("Hasil TKDN");
    expect(mocked.searchTkdn).not.toHaveBeenCalled();
    expect(mocked.gatewayStatus).not.toHaveBeenCalled();
  });

  it("SearchForm menunda pencarian keyword 300ms dan menonaktifkan tombol saat loading", async () => {
    vi.spyOn(window, "setTimeout").mockImplementation(((callback: () => void) => {
      callback();
      return 1;
    }) as typeof window.setTimeout);
    const store = useTkdnStore();
    const search = vi.spyOn(store, "search").mockResolvedValue(undefined);

    const wrapper = mount(SearchForm);
    store.query = "acer";
    await wrapper.vm.$nextTick();

    expect(search).toHaveBeenCalled();
    store.searching = true;
    await wrapper.vm.$nextTick();
    const submit = wrapper.find("button[type=submit]");
    expect(submit.attributes("disabled")).toBeDefined();
  });

  it("CollectProgress menampilkan retry dan form koneksi saat sesi habis", async () => {
    const store = useTkdnStore();
    const retry = vi.spyOn(store, "retryCollect").mockResolvedValue({
      accepted: true,
      job: store.job,
    });
    store.job = {
      job_id: "j1",
      status: "failed",
      total: 10,
      done: 0,
      processed: 0,
      error: 1,
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
      current_number: null,
      started_at: null,
      finished_at: null,
    };

    const wrapper = mount(CollectProgress);
    await wrapper.vm.$nextTick();

    expect(wrapper.text()).toContain("Coba lagi");
    expect(wrapper.text()).toContain("Sesi INAPROC perlu dihubungkan ulang");
    const retryButton = wrapper.findAll("button").find((button) => button.text() === "Coba lagi");
    await retryButton!.trigger("click");
    expect(retry).toHaveBeenCalled();
  });
});

describe("frontend error helpers", () => {
  it("menjaga pesan error lama tetap kompatibel", () => {
    expect(userMessage(new ApiError("connect first", "belum_login", 401))).toBe(
      "Hubungkan sesi INAPROC terlebih dahulu.",
    );
    expect(jobUserMessage("butuh_interaksi: otp")).toContain("OTP");
    expect(gatewayUserMessage({ error_code: "SYNC_FAILED" })).toBe(
      "Sinkronisasi gagal. Coba lagi.",
    );
  });
});
