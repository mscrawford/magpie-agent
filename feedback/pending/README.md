# Pending Feedback

This directory holds user-submitted feedback **awaiting maintainer review**.

## Naming Convention

Files follow: `YYYYMMDD_HHMMSS_TYPE_TARGET.md`

Examples:
- `20251015_143020_correction_module_70.md`
- `20251022_093000_warning_module_10.md`
- `20251101_160045_lesson_global.md`

## How to Submit

1. Copy a template from `../templates/`
2. Fill in all sections
3. Save here with the naming convention above
4. Commit and push

Or just tell the agent during a session — corrections and lessons are recorded automatically.

## For Maintainers

To integrate pending feedback:

1. Read each file in this directory
2. Validate claims against current GAMS code
3. Route corrections → `modules/module_XX.md` (fix the doc)
4. Route warnings/lessons → `modules/module_XX_notes.md` (user experience)
5. Move processed file to `../integrated/`
6. Commit with descriptive message

## See Also

- `../README.md` — Feedback system overview
- `../templates/` — Feedback submission templates
- `/feedback` command — Interactive feedback guide
