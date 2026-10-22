# Video Producer

Modul ini membuat video vertikal pembahasan lengkap dari 3 artikel Kaltim yang sudah
tersimpan di tabel `news_articles`. Alurnya:

1. Ambil artikel dari MySQL.
2. Ambil isi lengkap halaman artikel.
3. Susun 7 scene: pengantar dan pembahasan detail untuk tiap berita,
   lalu kesimpulan dampak dan tindak lanjut.
3. Generate narasi suara cowok Indonesia dengan Edge TTS.
4. Render animasi lokal dengan Pillow.
5. Encoding dan concat video dengan ffmpeg dari `imageio-ffmpeg`.

Modul ini juga menampung generator video AI **Kling AI** sebagai bagian dari pipeline.

Skill animasi modul ini mengikuti `ANIMATION_GUIDE.md`: layout berbeda tiap
scene, easing halus, reveal bertahap, parallax ringan, data key, dan transisi
lembut. Palet wajib putih-biru agar hasilnya clean dan soft.

## Menjalankan

```powershell
python -m modules.ui_animation
```

Output default:

```text
public/generated_video/kaltim_video_YYYYMMDD.mp4
```

Untuk memilih artikel lain:

```powershell
python -m modules.ui_animation --url "https://..."
```

## Parameter

- Durasi target default: `60` detik.
- Resolusi: `720x1280`.
- Frame rate default: `24` fps.
- Voice default: `id-ID-ArdiNeural` (male, Bahasa Indonesia).

## Testing

```powershell
python -m unittest modules.ui_animation.tests.test_video_producer -v
```

Test mencakup pembersihan HTML, pembagian scene 30 detik, layout teks vertikal,
argumen ffmpeg, frame 720x1280, dan pengambilan artikel dari MySQL.

## Generator Kling AI

```python
from modules.ui_animation import KlingBackend, VideoGenerator, VideoRequest

generator = VideoGenerator(backend=KlingBackend(), api_key="KLING_API_KEY")
task = generator.submit(
    VideoRequest(prompt="Kucing oren bermain di taman", mode="std", duration="5")
)
result = generator.wait_for_result(task.task_id)
print(result.video_url)
```

Gunakan `FakeKlingBackend` untuk pengujian tanpa API asli. Parameter `VideoRequest`:

| Parameter | Nilai | Keterangan |
|---|---|---|
| `prompt` | teks | Deskripsi video yang diinginkan |
| `mode` | `std` / `pro` | Lebih cepat/murah atau kualitas lebih tinggi |
| `duration` | `5` / `10` | Durasi dalam detik |
| `aspect_ratio` | `9:16` / `16:9` / `1:1` | `9:16` untuk TikTok |
| `negative_prompt` | teks opsional | Hal yang perlu dihindari |

Simpan `KLING_API_KEY` di `.env` dan jangan commit kredensial asli.
