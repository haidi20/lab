# INAPROC TKDN Search

Read-only search tool for INAPROC TKDN data and the official INAPROC API
Gateway. The backend stores results in MySQL only as a cache. It never sends
INSERT, UPDATE, or DELETE requests to INAPROC.

## Layout

```text
modules/inaproc/
├── api/   # FastAPI backend, CLI, tests, and smoke script
├── web/   # Vue 3 + TypeScript frontend
└── documents/
```

## Requirements

- Python 3.10+
- MySQL 8.x
- Node.js 20+
- Playwright Chromium (`python -m playwright install chromium`)

## Environment

Copy the relevant keys from the root `.env.example` into `.env`:

```env
INAPROC_MYSQL_HOST=127.0.0.1
INAPROC_MYSQL_PORT=3306
INAPROC_MYSQL_USER=root
INAPROC_MYSQL_PASSWORD=
INAPROC_MYSQL_DATABASE=inaproc
INAPROC_MYSQL_CONNECT_TIMEOUT=10
INAPROC_API_BASE_URL=https://data.inaproc.id
INAPROC_API_TOKEN=
INAPROC_API_TIMEOUT=30
INAPROC_API_MAX_RETRIES=3
INAPROC_API_ENABLED=false
```

`INAPROC_MYSQL_DATABASE` is required. It does not fall back to `MYSQL_DATABASE`.

Create the database once:

```sql
CREATE DATABASE IF NOT EXISTS inaproc
  CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

## Backend

```powershell
python -m uvicorn modules.inaproc.api.app:create_app --factory --reload --port 8000
```

The API creates its tables on startup. If MySQL is unavailable, endpoints return
`503 db_unavailable`.
All API errors use `{"error": "<code>", "message": "<message>"}`.
Collect jobs expose `done = found + empty + errors` and skip cache hits separately.

Gateway sync runs as a background job:

```text
POST /api/gateway/sync/{scope}         -> 202 {"job": {...}}
GET  /api/gateway/sync/{scope}/status  -> current job state
GET  /api/gateway/status               -> counts + last run, never the token
```

Scopes: `penyedia`, `produk`, `kategori`, `paket`, `transaksi`, `program`.
Starting the same scope while it is running returns `409 job_aktif`; different
scopes may run in parallel. Unknown scopes return `422`.

Read-only query and export endpoints:

```text
GET /api/gateway/produk        q, kode_penyedia, kategori, page, per_page, sort, order
GET /api/gateway/epurchasing   kind=paket|transaksi, q, tahun, kode_klpd, kd_produk, kode_penyedia
GET /api/gateway/export        kind=produk|paket|transaksi, format=csv|json + same filters
```

`GET /api/gateway/status` reports `produk_count`, `paket_count`,
`transaksi_count`, `scopes`, and `last_run`. All responses are served from the
MySQL cache; the Gateway is only called by an explicit sync.

## INAPROC session

Connect the provider account from the web UI. The backend stores the session in
`modules/inaproc/storageState.json`, which is gitignored. For OTP/captcha use:

```powershell
python -m modules.inaproc login
```

This is not an application login. It only opens an INAPROC provider session.

## CLI

```powershell
python -m modules.inaproc probe --nomor 11469/SJ-IND.8/E-TKDN/7/2025
python -m modules.inaproc collect --nomor 11469/SJ-IND.8/E-TKDN/7/2025 --start 1000 --end 1100
python -m modules.inaproc gateway-status
```

`gateway-status` never prints the token.

## Frontend

```powershell
cd modules/inaproc/web
npm install
npm run dev
```

Vite serves on `http://127.0.0.1:5173` and proxies `/api` to
`http://127.0.0.1:8000`. Override the backend target with
`VITE_API_PROXY_TARGET` when the API runs on another port:

```powershell
$env:VITE_API_PROXY_TARGET="http://127.0.0.1:8010"
npm run dev -- --port 5174 --strictPort
```

Use `http://localhost:5174` rather than `127.0.0.1` when a different local app
owns the default port.

The UI shows only the connection form until an INAPROC provider session exists.
Search, gateway, and e-purchasing panels are gated by `session.configured`.

Production build:

```powershell
npm run build
```

## Tests

```powershell
python -m unittest discover -s modules/inaproc/api/tests -t .
cd modules/inaproc/web
npm test -- --run
npm run build
```

UI smoke test (expects the API and Vite dev server to be running):

```powershell
python modules/inaproc/api/scripts/ui_smoke.py
```

## Data rules

- TKDN comes from `https://penyedia.inaproc.id/products/tkdn` through Playwright.
- Catalog and procurement data come from the official API Gateway, GET only.
- The Gateway token stays on the backend and is never returned to the frontend.
- `source_url` is rendered as a normal link opened by the user's browser.
- Search results are answered from MySQL first. Scraping or Gateway sync runs only
  when the cache has no final result or the user explicitly asks for a refresh.
- Product and e-purchasing searches never call the Gateway. Sync writes only to
  `inaproc_*` cache tables in MySQL.
