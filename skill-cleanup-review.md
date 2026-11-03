# Review Skill Codex — Rekomendasi Hapus

Tanggal: 2026-11-03

## Ringkasan

| Lokasi | Total | Rekomendasi Hapus | Rekomendasi Simpan |
|--------|-------|-------------------|-------------------|
| `C:\Users\nhaid\.codex\skills\` | 819 | ~818 (semua kecuali `.system`) | 0 custom (gitpush sudah ada di lokasi lain) |
| `C:\Users\nhaid\.agents\skills\` | 52 | 33 (accounting workflow yang tidak relevan) | 19 |
| `D:\learns\random\skills\` | 4 | 0 | 4 (semua project-specific) |

## 1. `C:\Users\nhaid\.codex\skills\` — HAPUS SEMUA (818 skill)

Ini adalah **cybersecurity skill pack** yang ter-install massal (pentest, malware analysis, forensics, red team, SIEM, OT security, dll). Tidak ada satu pun yang relevan dengan pekerjaan kamu (Laravel dev, Accurate analysis, skripsi).

### Yang dihapus (818 skill)

Semua folder kecuali `.system`. Contoh kategori:

- Pentesting: `performing-web-application-penetration-test`, `performing-network-penetration-test`, dll
- Malware: `analyzing-malware-*`, `reverse-engineering-malware-*`, `recovering-from-ransomware-*`
- Forensics: `analyzing-disk-image-*`, `analyzing-memory-forensics-*`, `performing-windows-artifact-*`
- Red Team: `building-red-team-*`, `operating-havoc-c2`, `operating-sliver-c2`
- Cloud Security: `auditing-aws-*`, `auditing-azure-*`, `auditing-gcp-*`
- OT/ICS: `performing-ot-*`, `securing-historian-server-*`
- SOC/IR: `building-incident-response-*`, `triaging-security-*`

### Yang disimpan

- `.system/` — skill bawaan Codex (imagegen, skill-creator, dll). JANGAN dihapus.

### Yang dipindah (bukan dihapus)

- `gitpush` → sudah ada di `C:\Users\nhaid\.claude\skills\gitpush` dan `D:\projects\karta_spa\.codex\skills\gitpush`. Aman dihapus dari sini.

### Cara hapus

```powershell
# Hapus semua kecuali .system
Get-ChildItem C:\Users\nhaid\.codex\skills -Directory | Where-Object { $_.Name -ne '.system' } | Remove-Item -Recurse -Force
```

---

## 2. `C:\Users\nhaid\.agents\skills\` — HAPUS 33, SIMPAN 19

### Simpan (19 skill) — relevan dengan pekerjaan kamu

**Accounting inti (12):**
- `chart-of-accounts`
- `journal-entries`
- `bank-reconciliation`
- `subledger-reconciliations`
- `extract-bank-statement`
- `classify-transactions`
- `adjusted-trial-balance`
- `revenue-recognition`
- `year-end-adjustments`
- `tax-computation`
- `capitalise-or-expense`
- `capex`

**React/Frontend (2):**
- `vercel-react-best-practices`
- `vercel-composition-patterns`

**Review/Quality (2):**
- `web-design-guidelines`
- `writing-guidelines`

**Accounting umum (3):**
- `ask-accounting`
- `do-books`
- `record-transactions`

### Hapus (33 skill) — workflow akuntan profesional, tidak relevan

- `auditor-pack`
- `engagement-setup`
- `full-engagement-pipeline`
- `resume-engagement`
- `compilation-report`
- `prepare-notes`
- `prepare-primary-statements`
- `disclosure-checklist`
- `statutory-handoff`
- `quality-review`
- `mpers-technical-review`
- `client-workspace`
- `cold-start-interview`
- `smart-intake`
- `source-documents`
- `management-approval`
- `cross-tie-check`
- `prove`
- `present`
- `extract`
- `classify`
- `post`
- `resume`
- `revenue`
- `preliminary-trial-balance`
- `finalise-accounts`
- `generate-workbook`
- `export-beancount`
- `validate-beancount`
- `open-fava`
- `jurisdiction-scaffold`
- `capital-allowances`
- `skills-qa`

### Cara hapus

```powershell
$skills = @('auditor-pack','engagement-setup','full-engagement-pipeline','resume-engagement','compilation-report','prepare-notes','prepare-primary-statements','disclosure-checklist','statutory-handoff','quality-review','mpers-technical-review','client-workspace','cold-start-interview','smart-intake','source-documents','management-approval','cross-tie-check','prove','present','extract','classify','post','resume','revenue','preliminary-trial-balance','finalise-accounts','generate-workbook','export-beancount','validate-beancount','open-fava','jurisdiction-scaffold','capital-allowances','skills-qa')
foreach ($s in $skills) {
    $p = Join-Path $env:USERPROFILE\.agents\skills $s
    if (Test-Path $p) { Remove-Item -LiteralPath $p -Recurse -Force }
}
```

---

## 3. `D:\learns\random\skills\` — SIMPAN SEMUA (4 skill)

| Skill | Status |
|-------|--------|
| `accurate-human-automation` | **WAJIB** — required by AGENTS.md |
| `emotion-ui-ux` | **WAJIB** — required by AGENTS.md |
| `emilkowalski` | Simpan — animasi/design reference |
| `linkedin-hook-generator` | Simpan — kalau masih dipakai |

---

## Dampak Setelah Hapus

- Sebelum: 875 skill total → Sesudah: ~23 skill
- Context window agent jauh lebih bersih
- Skill yang relevan lebih mudah terpicu otomatis
- Tidak ada perubahan pada fungsionalitas Codex
