# REA (Reverse Engineer Anything): Cara Pakai

**Repo:** https://github.com/morluto/rea
**Website:** https://rea.tools/
**NPM:** https://www.npmjs.com/package/rea-agents
**Versi saat dokumen dibuat:** 6.8.0
**Lisensi:** MIT

---

## Apa Itu REA

REA adalah MCP server dan CLI untuk reverse engineering. Satu tool yang
menghubungkan coding agent (Claude Code, Codex, Cursor, Gemini CLI, dll)
ke kemampuan analisis binary, aplikasi JavaScript/Electron, .NET, dan
website. Analisis berjalan lokal, hasilnya disertai bukti (evidence) dan
batasannya, bukan sekadar jawaban spekulatif.

Use case utamanya: kamu melihat fitur menarik di sebuah aplikasi, lalu
meminta agent menyelidiki cara kerjanya sampai level binary, menunjukkan
bukti, dan membangun versi serupa untuk projekmu.

## Apakah Ada MCP-nya?

**Ya, REA justru intinya adalah MCP server.** Konfigurasi resminya
(server.json):

- Nama server: `io.github.morluto/rea`
- Paket NPM: `rea-agents`
- Transport: `stdio`
- Perintah server: `npx rea-agents mcp`

## Persyaratan

- Node.js 22.x (>= 22.23.4), 24.x (>= 24.22.1), atau 26.12.1+
- npm
- Linux: butuh `ps` kompatibel procps di PATH untuk beberapa analisis
- Analisis binary native: butuh Hopper, Ghidra, atau IDA (opsional,
  setup bisa meng-install Hopper dengan persetujuan)
- Analisis JavaScript/Electron statis: tidak butuh engine tambahan

## Persiapan Disk (Sudah Diterapkan di Laptop Ini)

Drive C hampir penuh, sehingga seluruh jalur unduhan dan file sementara
dialihkan ke drive E:

- Cache npm: `E:\npm-cache` (via `npm config set cache E:\npm-cache --global`)
- Prefix global npm: `E:\apps\nodejs` (sudah bawaan)
- TMP/TEMP user: `E:\temp` (via Environment Variable user Windows)

Catatan: perubahan TMP/TEMP user baru berlaku penuh untuk aplikasi yang
baru dibuka setelah perubahan; terminal/VS Code yang sudah berjalan
perlu di-restart. TMP/TEMP level system tetap di `C:\WINDOWS\TEMP` dan
sengaja tidak diubah karena dipakai service Windows.

Saat instalasi Hopper/Ghidra (opsional), pilih lokasi di drive E, misal
`E:\apps\hopper` atau `E:\apps\ghidra`.

## Keputusan Setup (Terkunci)

- Agent yang didaftarkan: **Codex CLI saja**, bukan agent lain.
- Cara setup: `npx rea-agents setup --client codex`
- Engine analisis native (Hopper/Ghidra/IDA): skip dulu, install belakangan
  di drive E hanya jika ada kebutuhan analisis binary native.
- Lokasi instalasi engine (jika nanti di-install): `E:\apps\...`

Setelah setup selesai: restart Codex CLI, lalu uji dengan meminta agent
menganalisis satu target kecil sesuai template prompt di bagian
Daftar Pertanyaan Wajib.



## Cara Pakai

### 1. Setup Otomatis (Direkomendasikan)

```bash
npx rea-agents setup
```

Setup akan:

1. Mendeteksi agent yang terpasang (Claude Code, Codex, Cursor, dll).
2. Menawarkan pilihan agent mana yang mau dikonfigurasi.
3. Menambahkan registrasi MCP REA ke konfigurasi agent.
4. Meng-install workflow instructions (skill) REA.
5. Menawarkan instalasi Hopper untuk analisis native (opsional).

Semua perubahan konfigurasi ditampilkan dulu dan butuh persetujuan.
Konfigurasi lama di-backup otomatis. Setelah selesai, restart agent.

### 2. Konfigurasi MCP Manual

Kalau mau mendaftarkan MCP server-nya manual, jalankan:

```bash
npx rea-agents mcp
```

Contoh untuk Codex CLI (`~/.codex/config.toml`):

```toml
[mcp_servers.rea]
command = "npx"
args = ["rea-agents", "mcp"]
```

Contoh untuk Claude Desktop (`claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "rea": {
      "command": "npx",
      "args": ["rea-agents", "mcp"]
    }
  }
}
```

Variabel environment opsional:

- `REA_MCP_INPUT_SCHEMA_PROFILE=full` - schema input lengkap (default compact)
- `REA_MCP_OUTPUT_SCHEMA_PROFILE=compact|off` - batasi schema output
- `REA_MCP_MAX_RESPONSE_BYTES` - batas ukuran response
- `REA_MCP_TOOL_FAMILIES` - pilih keluarga tool yang dimuat

### 3. Pakai via Agent

Setelah setup, cukup minta agent secara natural:

```text
Understand how search works in the Notes app, show me the evidence,
and build a similar feature for my project.
```

Agent akan memanggil tool REA via MCP, menyelidiki target, lalu
melaporkan temuan beserta buktinya.

### 4. Pakai via CLI (Tanpa Agent)

Tool yang sama juga bisa dipakai langsung dari terminal:

```bash
# Analisis aplikasi JavaScript/Electron (ASAR atau folder hasil ekstraksi)
npx -y rea-agents@latest analyze-javascript-application /absolute/path/to/app --json
```

## Target yang Bisa Dianalisis

## Daftar Pertanyaan Wajib Sebelum Analisa

Sebelum meminta REA/agent menganalisis target, WAJIB menyiapkan jawaban
untuk daftar pertanyaan berikut. Daftar ini menjadi patokan agar analisa
tidak melebar, hasilnya bisa diverifikasi, dan output akhirnya jelas.

### 1. Identifikasi Target

1. Apa nama target dan fungsinya? (contoh: aplikasi Notes, game Unity, website X)
2. Di mana path/lokasi target? (path absolut: binary, ASAR, APK, URL)
3. Versi berapa target yang dianalisis? (versi app berpengaruh pada struktur kode)
4. Platform apa? (Windows, macOS, Linux, Android, web)
5. Apakah target legal untuk dianalisis? (milik sendiri, lisensi mengizinkan, atau tujuan edukasi/interop yang sah)

### 2. Ruang Lingkup Fitur

6. Fitur spesifik mana yang mau dipahami? (satu fitur per analisa, bukan seluruh app)
7. Apa trigger fitur tersebut? (klik tombol, event timer, perintah keyboard, deep link)
8. Apa input yang diterima fitur? (teks, file, gesture, data sensor)
9. Apa output/side effect yang dihasilkan? (UI berubah, file tersimpan, network request terkirim)
10. Apakah fitur butuh state tertentu? (login, cache, konfigurasi, device capability)

### 3. Kebutuhan Bukti

11. Bukti apa yang wajib ditunjukkan? (nama fungsi, potongan kode, assembly offset, network payload, file path)
12. Apakah kesimpulan bisa diverifikasi ulang? (agent wajib menyertakan lokasi bukti, bukan hanya kesimpulan)
13. Apa yang TIDAK diketahui dari analisa? (REA wajib melaporkan batasan, jangan menebak)
14. Apakah ada asumsi yang dipakai? (setiap asumsi WAJIB ditandai eksplisit)

### 4. Target Replikasi

15. Fitur serupa mau dibangun di stack apa? (Laravel+Vue, Electron, Flutter, dst)
16. Apa batasan projek tujuan? (versi framework, pattern arsitektur, aturan AGENTS.md)
17. Apakah butuh 1:1 dengan aslinya, atau hanya prinsip kerjanya? (hindari menyalin UI/asset berhak cipta)
18. Apa definisi selesai untuk fitur replikanya? (test apa yang harus lulus)

### 5. Verifikasi Akhir

19. Bagaimana cara membuktikan replikasi berjalan? (test manual, automated test, screenshot, log)
20. Apa kriteria gagal yang perlu diwaspadai? (performance, edge case, dependency yang tidak ada di stack tujuan)

### Template Prompt Analisa

Gabungan pertanyaan di atas menghasilkan prompt siap pakai:

```text
Target: [nama app + versi + path absolut]
Fitur yang dianalisis: [satu fitur spesifik]
Trigger: [bagaimana fitur dijalankan]
Input: [data yang masuk]
Output yang diharapkan: [hasil/side effect]
Bukti wajib: [fungsi/offset/payload yang harus ditunjukkan]
Laporkan juga: batasan analisa dan asumsi yang dipakai
Tujuan akhir: [replikasi di stack X dengan definisi selesai Y]
```

Contoh terisi:

```text
Target: Notes app macOS 15, path /System/Applications/Notes.app
Fitur yang dianalisis: pencarian catatan (search)
Trigger: user mengetik di kolom search
Input: string query
Output: daftar catatan yang cocok terurut relevansi
Bukti wajib: fungsi query, index yang dipakai, format ranking
Laporkan juga: bagian yang tidak bisa dianalisis tanpa runtime
Tujuan akhir: fitur search serupa di projek Laravel+Vue, selesai jika
test pencarian dan ranking lulus
```

Aturan disiplin saat analisa berjalan:

- Satu sesi analisa = satu fitur. Jangan campur beberapa fitur.
- Setiap klaim dari agent WAJIB punya bukti yang bisa ditunjuk lokasinya.
- Kalau bukti tidak cukup, agent WAJIB bilang tidak tahu, bukan menebak.
- Replikasi menulis ulang prinsip kerja, bukan menyalin asset/kode berhak cipta.

| Target | Butuh Engine Tambahan? |
|--------|------------------------|
| Aplikasi desktop ter-install | Tidak (inspeksi built-in) |
| Binary native (pseudocode, assembly, symbols) | Hopper / Ghidra / IDA |
| Aplikasi JavaScript / Electron / ASAR | Tidak |
| .NET assembly | Tidak |
| Website | Tidak |
| Go binary (versi compiler, modules) | Tidak |
| GPU code objects (CUDA/HIP/PTX) | Tidak |
| Model AI (GGUF / safetensors metadata) | Tidak |
| Unity IL2CPP metadata (v24, 27, 29, 31, 39) | Tidak |
| Godot PCK (format 2, 3, 4) | Tidak |
| Rust binary (cargo-auditable) | Tidak |
| PE certificates dan imports | Tidak |
| ELF notes, kernel modules | Tidak |
| Apple IPS crash report | Tidak |
| Erlang BEAM | Tidak |
| WASM | WABT 1.0.42 |
| EVM bytecode | Linux x64 |
| SQLite database | Tidak |
| Android (APK, JADX) | JADX + bridge |

## Catatan Keamanan

- Analisis berjalan **lokal**, bukan di cloud.
- Ambil REA hanya dari repo resmi `morluto/rea`, website `rea.tools`,
  atau paket NPM `rea-agents`. Repo dengan nama mirip bukan sumber resmi.
- Setup memiliki mekanisme backup dan recovery untuk konfigurasi agent:
  snapshot `.rea.backup` dibuat sebelum perubahan.

## Referensi

- Panduan lengkap: https://rea.tools/guides/
- Katalog tool MCP: `docs/mcp-contracts.md` di repo
- Instalasi detail: `docs/installation.md` di repo
- Discord komunitas: https://discord.gg/GkcryMnJDM

