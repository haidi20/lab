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

Skill animasi modul ini mengikuti `ANIMATION_GUIDE.md`: layout berbeda tiap
scene, easing halus, reveal bertahap, parallax ringan, data key, dan transisi
lembut. Palet wajib putih-biru agar hasilnya clean dan soft.

## Menjalankan

```powershell
python -m modules.video_producer
```

Output default:

```text
public/generated_video/kaltim_video_YYYYMMDD.mp4
```

Untuk memilih artikel lain:

```powershell
python -m modules.video_producer --url "https://..."
```

## Parameter

- Durasi target default: `60` detik.
- Resolusi: `720x1280`.
- Frame rate default: `24` fps.
- Voice default: `id-ID-ArdiNeural` (male, Bahasa Indonesia).

## Testing

```powershell
python -m unittest modules.video_producer.tests.test_video_producer -v
```

Test mencakup pembersihan HTML, pembagian scene 30 detik, layout teks vertikal,
argumen ffmpeg, frame 720x1280, dan pengambilan artikel dari MySQL.
