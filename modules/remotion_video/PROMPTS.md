# Template Prompt Peningkatan Animasi Remotion

Gunakan file ini sebagai template prompt saat ingin meningkatkan kualitas animasi `KaltimRoundup`.

## Prompt Cepat

```text
Tingkatkan animasi KaltimRoundup:
- Buat judul masuk dengan spring yang lebih cepat dan elastis, lalu tenang dengan gerakan melayang halus.
- Tambahkan sorotan kata per kata secara bertahap dan sinkron dengan durasi scene.
- Buat chip topik muncul dengan sedikit efek overshoot dan denyut cahaya berkelanjutan.
- Tambahkan latar parallax halus dengan arah gerakan berbeda untuk setiap layout.
- Gunakan easing antar scene yang lebih kuat, tetapi tetap halus dan mudah dibaca.
- Pertahankan sistem desain gelap Kaltim dan font Poppins.
- Perbaiki hierarki visual: judul paling menonjol, chip topik kedua, caption ketiga.
- Hindari gerakan lambat, datar, dan berulang.
```

## Prompt Teknis

```text
Rapikan ulang motion KaltimRoundup dengan token animasi yang dapat dipakai ulang:
- springIn, settleFloat, pulse, driftX, dan sceneExit.
- Gunakan spring() dan interpolate() dari Remotion secara konsisten.
- Tambahkan gerakan kamera dan warna aksen berbeda untuk setiap layout.
- Tambahkan sorotan caption yang mengikuti progres durasi scene.
- Render satu frame preview untuk setiap layout sebelum render final.
```

## Prompt Mengikuti Referensi Motion

```text
Buat KaltimRoundup lebih mendekati public/ssstik.io_1793164540873.mp4:
- Gunakan judul besar dengan reveal cepat.
- Tampilkan chip interaktif satu per satu.
- Sorot kata narasi dengan timing ritmis.
- Buat latar lebih bersih, kontras lebih kuat, dan aksen lebih dinamis.
- Pastikan hasil tetap sesuai standar motion dan desain repository.
```

## Prompt Berdasarkan Durasi

Sebutkan durasi target di awal prompt, lalu minta pacing animasi disesuaikan dengan durasi tersebut. Durasi yang sama dengan `durationSeconds` pada plan akan dikonversi menjadi `durationInFrames` di `props.json`, jadi prompt cukup menyebut detik.

### Template Umum

```text
Tingkatkan animasi KaltimRoundup untuk video {durasi} detik:
- Pastikan semua entrance dan exit scene masuk dalam durasi target.
- Sesuaikan kecepatan animasi: durasi pendek butuh gerakan lebih cepat dan tegas; durasi panjang butuh pacing lebih tenang.
- Sinkronkan sorotan caption dan kemunculan chip dengan durasi scene, bukan dengan detik tetap.
- Pertahankan tiga detik pertama sebagai hook yang kuat.
- Pertahankan sistem desain gelap Kaltim, font Poppins, dan token motion Remotion.
- Render satu frame preview untuk setiap layout sebelum render final.
```

### Contoh 15 Detik

```text
Tingkatkan animasi KaltimRoundup untuk video 15 detik:
- Gunakan gerakan cepat dan tegas dengan jeda minimal antar elemen.
- Tampilkan judul dalam waktu kurang dari 1 detik.
- Tampilkan chip topik dalam 2 detik pertama.
- Sorot kata caption dengan transisi cepat dan ritmis.
- Buat keluaran scene singkat dan bersih.
```

### Contoh 30 Detik

```text
Tingkatkan animasi KaltimRoundup untuk video 30 detik:
- Seimbangkan kecepatan dan keterbacaan agar setiap scene punya ruang napas.
- Bagi kemunculan judul, chip, dan caption secara bertahap dalam 3 detik pertama.
- Tambahkan parallax latar yang halus dan berkelanjutan.
- Sinkronkan sorotan kata caption dengan durasi scene.
```

### Contoh 60 Detik

```text
Tingkatkan animasi KaltimRoundup untuk video 60 detik:
- Gunakan pacing sedang dengan hierarki visual yang jelas di setiap scene.
- Berikan warna aksen dan arah gerakan berbeda untuk setiap layout.
- Tambahkan drift kamera lambat dan gerakan kartu yang halus sepanjang video.
- Tampilkan hook hanya pada 3 detik pertama.
- Buat sorotan caption mengikuti progres scene agar tidak terasa terburu-buru.
```

### Contoh 180 Detik

```text
Tingkatkan animasi KaltimRoundup untuk video 180 detik:
- Gunakan pacing tenang dan sinematik agar penonton tidak lelah secara visual.
- Tambahkan variasi antar scene: arah latar, warna aksen, dan motif gerakan yang berbeda.
- Beri waktu reveal lebih panjang untuk setiap poin pembahasan dengan settle yang halus.
- Tambahkan penanda progres berkala agar penonton tetap paham posisi berita.
- Buat transisi halus tetapi tidak berulang dan membosankan.
```

## Catatan

- Sumber animasi utama: `remotion/src/KaltimRoundup.tsx`.
- Prompt boleh mengubah desain dan motion, tetapi hasil final tetap harus dirender dengan Remotion.
- Untuk efek kompleks, pertimbangkan `@remotion/three`, Lottie, atau custom shader setelah kebutuhan visual jelas.
