---
name: emotion-ui-ux
description: Use when creating, changing, reviewing, or testing any UI/UX styling or animation in this repository. Enforces Emotion as the standard styling and animation layer.
---

# Emotion UI/UX Skill

## When To Use

Gunakan skill ini setiap kali pekerjaan menyentuh:

- halaman HTML, form, dashboard, captive portal, atau komponen web;
- styling, layout visual, hover/focus/active state;
- entrance, stagger, transition, ambient motion, atau micro-interaction;
- review atau refactor UI yang masih memakai CSS lama.

## Non-Negotiable Rules

1. **Emotion adalah standar.** Gunakan `@emotion/css` untuk HTML statis
   dan `@emotion/react` untuk React.
2. **JANGAN gunakan blok `<style>`**, file CSS global manual, inline
   `style`, atau styling framework lain tanpa keputusan baru dari user.
3. Untuk halaman captive portal/offline, simpan runtime Emotion di
   `public/vendor/emotion-css.umd.min.js` dan sertakan lisensi
   `public/vendor/EMOTION_LICENSE`.
4. Untuk runtime UMD, destructure API resmi:
   `const { css, keyframes, injectGlobal } = window.emotion;`
5. Global reset dan `prefers-reduced-motion` boleh memakai
   `injectGlobal`. Styling komponen WAJIB memakai `css`.
6. Jangan mengakses variabel style sebelum seluruh objek style selesai
   dibuat.
7. Gunakan `transform`, `opacity`, `filter`, `box-shadow`, atau
   `background-position` untuk animasi. Hindari animasi `width`,
   `height`, `top`, `left`, `margin`, atau `padding`.
8. Setiap animasi WAJIB punya tujuan UX: orientasi, hierarchy, feedback,
   continuity, atau focus.

## Standard Pattern

```js
const { css, keyframes, injectGlobal } = window.emotion;

const cardEntrance = keyframes`
  from {
    opacity: 0;
    transform: translateY(34px) scale(.97);
  }
  to {
    opacity: 1;
    transform: translateY(0) scale(1);
  }
`;

injectGlobal`
  @media (prefers-reduced-motion: reduce) {
    *,
    *::before,
    *::after {
      animation-duration: .01ms !important;
      animation-iteration-count: 1 !important;
      transition-duration: .01ms !important;
    }
  }
`;

const card = css`
  animation: ${cardEntrance} .52s cubic-bezier(.23, 1, .32, 1) both;
`;
```

## Motion Tokens

- **Entrance:** `180–520ms`.
- **Interaction:** `120–220ms`.
- **Stagger:** `60–80ms` per item.
- **Primary easing:** `cubic-bezier(.23, 1, .32, 1)`.
- **Ambient motion:** maksimal `30s`, gerak halus, dan jangan mengganggu
  keterbacaan.
- **State change:** gunakan transition singkat, bukan animasi panjang.

## Accessibility And Quality

- Semua elemen interaktif WAJIB punya `:focus-visible` yang jelas.
- Wajib hormati `prefers-reduced-motion`.
- Jangan gunakan animasi berkedip lebih dari 3 kali per detik.
- Jangan hilangkan indikator focus hanya demi tampilan bersih.
- Pastikan kontras teks tetap memenuhi standar aksesibilitas.
- Animasi tidak boleh menyebabkan horizontal scroll atau layout shift.

## Required Validation

- Jalankan test terkait dengan `python -m unittest`.
- Untuk HTML statis dengan JavaScript baru, jalankan `node --check`
  pada script yang diekstrak atau script terpisah.
- Test kontrak minimal harus memastikan halaman memakai Emotion dan
  tidak mengandung blok `<style>` lama.

## Review Checklist

- [ ] Tidak ada `<style>` lama.
- [ ] Semua styling UI memakai Emotion.
- [ ] Runtime lokal tersedia untuk halaman offline/captive portal.
- [ ] Ada entrance dan stagger yang jelas.
- [ ] Ada state hover, focus, active, atau disabled yang halus.
- [ ] `prefers-reduced-motion` dihormati.
- [ ] Tidak ada animasi properti layout yang mahal.
