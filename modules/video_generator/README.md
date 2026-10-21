# Modul Video Generator (Kling AI)

Modul untuk generate video AI via **Kling AI** (keputusan tool 2026-10-21,
tercatat juga di AGENTS.md klinik-git). Output video siap masuk pipeline
upload TikTok (draft/private via jalur resmi, publish manual oleh user).

## Cara Pakai

```python
from modules.video_generator import FakeKlingBackend, KlingBackend, VideoGenerator, VideoRequest

generator = VideoGenerator(backend=KlingBackend(), api_key="KLING_API_KEY")
task = generator.submit(VideoRequest(prompt="Kucing oren bermain di taman", mode="std", duration="5"))
result = generator.wait_for_result(task.task_id)
print(result.video_url)  # URL video siap diunduh
```

Untuk testing tanpa API asli, pakai `FakeKlingBackend()`.

## Parameter VideoRequest

| Parameter | Nilai | Keterangan |
|---|---|---|
| `prompt` | teks | Deskripsi video yang diinginkan |
| `mode` | `std` / `pro` | std lebih cepat & murah, pro kualitas lebih tinggi |
| `duration` | `5` / `10` | Durasi detik |
| `aspect_ratio` | `9:16` / `16:9` / `1:1` | 9:16 untuk TikTok |
| `negative_prompt` | teks (opsional) | Hal yang dihindari (blur, distorsi, dll) |

## Setup API Key

1. Daftar di https://klingai.com (atau platform partner resmi)
2. Ambil API key dari dashboard
3. Simpan di `.env`: `KLING_API_KEY=...` (jangan commit)

## Status Pipeline

```
VideoGenerator.submit() -> task_id
VideoGenerator.wait_for_result(task_id) -> VideoResult(status, video_url)
status: submitted -> processing -> completed | failed
```

## Integrasi Pipeline TikTok

```
Kling AI (modul ini) -> video_url
  -> unduh mp4
  -> upload draft via Postiz / Content Posting API
  -> user publish manual dari app TikTok
```

Aturan pipeline tercatat di AGENTS.md klinik-git (section Konten Video).
