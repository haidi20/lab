# Animation Skill

Skill ini dipakai untuk semua video informatif di modul `video_producer`.

## Prinsip

1. **Smooth motion**: semua gerakan memakai `ease_out_cubic`, bukan linear.
2. **Stagger reveal**: judul, poin, metrik, dan langkah muncul bergantian.
3. **Non-monotonic layout**: tiap scene punya layout berbeda:
   headline, metrics, process, conclusion.
4. **Informasi dulu**: angka penting ditampilkan sebagai data key, bukan
   hanya teks panjang.
5. **Visual hierarchy**: heading kecil, judul besar, isi terbaca, footer
   tidak mengganggu.
6. **Soft white-blue system**: background putih kebiruan, kartu putih,
   aksen biru, teks gelap.
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
