export interface TkdnRow {
  number: string;
  product_type: string | null;
  brand: string | null;
  type: string | null;
  description: string | null;
  standard: string | null;
  value: number | null;
  hs: string | null;
}

export interface ProductRow {
  kd_produk: string;
  kode_penyedia: string | null;
  nama_produk: string | null;
  kategori: string | null;
  brand: string | null;
  harga: number | null;
  satuan: string | null;
  source_url: string | null;
}

export type EpurchasingKind = "paket" | "transaksi";
export interface EpurchasingRow {
  source_url: string | null;
  kode_paket?: string;
  nama_paket?: string | null;
  tahun?: number | null;
  kode_klpd?: string | null;
  total_nilai?: number | null;
  order_id?: string;
  kd_produk?: string | null;
  kode_penyedia?: string | null;
  nama_produk?: string | null;
  jumlah?: number | null;
  total?: number | null;
}

export interface PageResult<T> {
  items: T[];
  page: number;
  per_page: number;
  total: number;
}

export interface SessionStatus {
  configured: boolean;
  valid?: boolean | null;
  checked_at?: string;
  cookies?: number;
  origins?: number;
}

export interface GatewayStatus {
  enabled: boolean;
  scopes: string[];
  produk_count: number;
  paket_count?: number;
  transaksi_count?: number;
  last_run: Record<string, unknown> | null;
}

export interface GatewayJobState {
  scope: string;
  status: string;
  items?: number;
  pages?: number;
  error_code?: string | null;
  error_message?: string | null;
  created_at?: string;
  started_at?: string;
  finished_at?: string;
}

export interface JobState {
  job_id?: string | null;
  status: string;
  total: number;
  done: number;
  processed?: number;
  error?: number;
  found: number;
  empty: number;
  errors: number;
  skipped: number;
  progress: number;
  start: number | null;
  end: number | null;
  template: string | null;
  last_error: string | null;
  current: string | null;
  current_number?: string | null;
  started_at?: string | null;
  finished_at?: string | null;
}

export interface CollectPreview {
  total: number;
  sudah_ada: number;
  akan_diproses: number;
  estimasi_menit: number;
  chunks: number;
}
