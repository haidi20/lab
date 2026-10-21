# Animation Skill

Skill ini dipakai untuk semua video informatif di modul `video_producer`.

## Emotion Motion Graphic (Video Only)

Gaya utama video adalah **Emotion Motion Graphic**, bukan slide statis:

1. **Spatial camera**: kamera bergerak kontinu dengan rotasi halus.
2. **Parallax depth**: background, stage, dan konten bergerak di depth
   berbeda.
3. **Kinetic stage**: grid perspektif, sweep cahaya, bar ritmis, dan orbit
   memberi kesan panggung event.
4. **Readable motion**: entrance tetap cepat, stagger pendek, dan teks
   tidak boleh bergerak berlebihan sampai sulit dibaca.
5. **Continuous life**: tidak ada frame yang benar-benar diam seperti PPT.

Untuk UI/UX web, jangan memakai pipeline video atau CSS lama. Gunakan
**Emotion** sebagai styling dan animation layer sesuai skill
`skills/emotion-ui-ux/SKILL.md`.

## Prinsip

1. **Smooth motion**: semua gerakan memakai `ease_out_cubic`, bukan linear.
2. **Stagger reveal**: judul, poin, metrik, dan langkah muncul bergantian.
3. **Non-monotonic layout**: tiap scene punya layout berbeda:
   headline, metrics, process, conclusion.
4. **Informasi dulu**: angka penting ditampilkan sebagai data key, bukan
   hanya teks panjang.
5. **Visual hierarchy**: heading kecil, judul besar, isi terbaca, footer
   tidak mengganggu.
6. **Remotion UI system**: background `#F8FAFC`, kartu putih, border
   hitam tebal, aksen biru `#3578E5`/`#0B84F3`, teks hitam, dan subtitle
   abu. Jangan kembali ke kartu tanpa outline atau tampilan slide lama.
7. **Continuous life**: background bergerak pelan dengan parallax dan wave.
8. **Scene transition**: fade masuk/keluar singkat agar tidak terasa PPT.
9. **Narration sync**: durasi 30 detik dibagi empat scene dan audio dipad
   sampai batas scene.

## Checklist sebelum render

- Ada angka atau fakta utama di scene 2.
- Ada langkah/aksi di scene 3.
- Kesimpulan scene 4 menjawab masalah di scene 1.
- Tidak ada dua frame berturut-turut yang identik.
- Palet tetap putih-biru dan bersih.
