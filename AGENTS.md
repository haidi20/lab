# Project Rules

## Testing

- Use Test-Driven Development (TDD) for every feature, bug fix, and task in this repository.
- Before writing implementation code, add or update a failing test that describes the expected behavior.
- Run the relevant tests first and confirm they fail for the expected reason.
- Implement the smallest useful change needed to make the tests pass.
- Run `python -m unittest` before finishing a task.
- Refactor only while keeping tests green.
- Do not add implementation-only changes without test coverage unless the change is documentation, configuration, or generated files.

## Modules

- Keep each feature inside its own module under `modules/`.
- Expose a module through its `__init__.py`.
- Place module-specific tests inside the module under a `tests/` folder, for example `modules/<module_name>/tests/test_<feature>.py`.

## UI/UX Animation Standard: Emotion

- **Emotion adalah standar WAJIB untuk semua styling dan animasi UI/UX**
  di repositori ini. Gunakan `@emotion/css` untuk HTML statis dan
  `@emotion/react` untuk React.
- Standar ini WAJIB dipakai bersama skill
  `skills/emotion-ui-ux/SKILL.md`.
- Agent TIDAK BOLEH memakai blok `<style>` lama, file CSS global manual,
  inline `style`, atau framework styling lain untuk UI tanpa keputusan
  baru dari user.
- Animasi UI WAJIB memakai `css`, `keyframes`, dan/atau `injectGlobal`
  dari Emotion, tetap mudah dibaca, dan menghormati
  `prefers-reduced-motion`.
- Untuk UI/UX, animasi, kehalusan gerak, dan interaktivitas, WAJIB
  mengikuti `public/ssstik.io_1793164540873.mp4` sebagai acuan motion
  100%. Jangan mengganti gaya, timing, easing, atau feedback interaktif
  tanpa keputusan baru dari user.
