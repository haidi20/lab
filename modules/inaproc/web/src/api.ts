import type {
  CollectPreview,
  EpurchasingKind,
  EpurchasingRow,
  GatewayJobState,
  GatewayStatus,
  JobState,
  PageResult,
  ProductRow,
  SessionStatus,
  TkdnRow,
} from "./types";

export class ApiError extends Error {
  constructor(
    message: string,
    public code: string,
    public status: number,
  ) {
    super(message);
  }
}

const userErrorMessages: Record<string, string> = {
  db_unavailable: "Database tidak dapat dihubungi.",
  filter_tidak_valid: "Filter pencarian tidak valid.",
  format_tidak_valid: "Format ekspor tidak valid.",
  kind_tidak_valid: "Jenis data tidak valid.",
  job_aktif: "Masih ada proses yang berjalan.",
  login_failed: "Login INAPROC gagal. Periksa email dan password.",
  nomor_tidak_ditemukan: "Nomor tidak ditemukan di cache.",
  belum_login: "Hubungkan sesi INAPROC terlebih dahulu.",
  request_failed: "Permintaan gagal. Coba lagi.",
  scope_tidak_valid: "Jenis sinkronisasi tidak valid.",
  butuh_interaksi: "INAPROC memerlukan OTP atau captcha. Gunakan login interaktif.",
  kredensial_salah: "Email atau password INAPROC salah.",
  upstream_timeout: "INAPROC terlalu lama merespons. Coba lagi.",
  tidak_ada_job: "Tidak ada proses pengumpulan data yang berjalan.",
  upstream_error: "INAPROC tidak memberikan respons yang valid.",
};

export function userMessage(error: unknown): string {
  if (error instanceof ApiError) {
    if (error.code === "login_failed" && error.message.toLowerCase().includes("not registered")) {
      return "Email INAPROC belum terdaftar.";
    }
    if (userErrorMessages[error.code]) {
      return userErrorMessages[error.code];
    }
  }
  return "Terjadi kesalahan. Coba lagi.";
}

export function jobUserMessage(message: string | null | undefined): string {
  if (!message) return "";
  if (message.startsWith("belum_login")) {
    return userErrorMessages.belum_login;
  }
  if (message.startsWith("butuh_interaksi")) {
    return userErrorMessages.butuh_interaksi;
  }
  return "Terjadi kesalahan saat pengumpulan data.";
}

export function gatewayUserMessage(job: {
  error_code?: string | null;
  error_message?: string | null;
}): string {
  const messages: Record<string, string> = {
    GATEWAY_DISABLED: "API Gateway belum aktif. Atur token terlebih dahulu.",
    INVALID_JSON: "Respons API Gateway tidak valid.",
    SCOPE_TIDAK_VALID: "Jenis sinkronisasi tidak valid.",
    SYNC_FAILED: "Sinkronisasi gagal. Coba lagi.",
    TOKEN_EXPIRED: "Token INAPROC tidak valid atau sudah berakhir.",
    TOKEN_INVALID: "Token INAPROC tidak valid atau sudah berakhir.",
  };
  const code = job.error_code;
  if (code && messages[code]) {
    return messages[code];
  }
  if (code && userErrorMessages[code]) {
    return userErrorMessages[code];
  }
  return "Sinkronisasi gagal. Coba lagi.";
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(path, {
    headers: { "Content-Type": "application/json", ...(init?.headers || {}) },
    ...init,
  });
  if (!response.ok) {
    let code = "request_failed";
    let message = "Permintaan gagal. Coba lagi.";
    try {
      const body = await response.json();
      const errorValue = body?.error;
      if (typeof errorValue === "string") {
        code = errorValue;
        message = typeof body?.message === "string" ? body.message : message;
      } else if (errorValue && typeof errorValue === "object") {
        code = (errorValue as { code?: string }).code ?? code;
        message = (errorValue as { message?: string }).message ?? message;
      }
    } catch {
      // Keep the generic message when the body is not JSON.
    }
    throw new ApiError(message, code, response.status);
  }
  if (response.status === 204) {
    return undefined as T;
  }
  return (await response.json()) as T;
}

function query(params: Record<string, string | number | null | undefined>): string {
  const search = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value !== null && value !== undefined && value !== "") {
      search.set(key, String(value));
    }
  });
  const text = search.toString();
  return text ? `?${text}` : "";
}

export const api = {
  session: () => request<SessionStatus>("/api/session"),
  login: (email: string, password: string) =>
    request<{ connected: boolean; configured: boolean }>("/api/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    }),
  logout: () => request<{ configured: boolean }>("/api/logout", { method: "POST" }),

  searchTkdn: (params: {
    q?: string;
    brand?: string;
    min_value?: number | null;
    page: number;
    per_page: number;
    sort: string;
    order: string;
  }) => request<PageResult<TkdnRow>>(`/api/search${query(params)}`),

  lookup: (number: string, force = false) =>
    request<{ source: string; status: string; items: TkdnRow[] }>("/api/lookup", {
      method: "POST",
      body: JSON.stringify({ number, force }),
    }),

  preview: (template: string, start: number, end: number, delayMin = 1, delayMax = 3) =>
    request<CollectPreview>("/api/collect/preview", {
      method: "POST",
      body: JSON.stringify({ template, start, end, delay_min: delayMin, delay_max: delayMax }),
    }),

  collect: (
    template: string,
    start: number,
    end: number,
    options: { delayMin?: number; delayMax?: number; force?: boolean } = {},
  ) =>
    request<{ accepted: boolean; job: JobState }>("/api/collect", {
      method: "POST",
      body: JSON.stringify({
        template,
        start,
        end,
        delay_min: options.delayMin ?? 1,
        delay_max: options.delayMax ?? 3,
        force: options.force ?? false,
      }),
    }),

  cancelCollect: () =>
    request<{ cancelling: boolean }>("/api/collect/cancel", { method: "POST" }),

  status: () => request<JobState>("/api/status"),

  refresh: (number: string) =>
    request<{ source: string; status: string; items: TkdnRow[] }>("/api/refresh", {
      method: "POST",
      body: JSON.stringify({ number }),
    }),

  gatewayStatus: () => request<GatewayStatus>("/api/gateway/status"),

  searchProducts: (params: {
    q?: string;
    kode_penyedia?: string;
    kategori?: string;
    page: number;
    per_page: number;
    sort: string;
    order: string;
  }) => request<PageResult<ProductRow>>(`/api/gateway/produk${query(params)}`),

  searchEpurchasing: (params: {
    kind: EpurchasingKind;
    q?: string;
    tahun?: number | null;
    kode_klpd?: string;
    kd_produk?: string;
    kode_penyedia?: string;
    page: number;
    per_page: number;
    sort: string;
    order: string;
  }) =>
    request<PageResult<EpurchasingRow> & { kind: EpurchasingKind }>(
      `/api/gateway/epurchasing${query(params)}`,
    ),

  syncGateway: (scope: string, force = false) =>
    request<{ job: GatewayJobState }>(`/api/gateway/sync/${scope}`, {
      method: "POST",
      body: JSON.stringify({ force, params: {} }),
    }),

  syncStatus: (scope: string) =>
    request<GatewayJobState>(`/api/gateway/sync/${scope}/status`),
};

export function exportUrl(format: "csv" | "json", params: {
  q?: string;
  brand?: string;
  min_value?: number | null;
  sort?: string;
  order?: string;
}): string {
  return `/api/export${query({ format, ...params })}`;
}

export function gatewayExportUrl(
  format: "csv" | "json",
  kind: "produk" | "paket" | "transaksi",
  params: Record<string, string | number | null | undefined> = {},
): string {
  return `/api/gateway/export${query({ format, kind, ...params })}`;
}
