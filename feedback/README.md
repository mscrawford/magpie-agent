# Feedback System for MAgPIE Agent

This directory supports continuous improvement of the MAgPIE AI agent through user feedback and automated learning.

## How Feedback Works

### Automatic Learning (Primary)

The agent records corrections and lessons **during sessions**:
- When you correct the agent → saved to `modules/module_XX_notes.md`
- When the agent discovers something → saved to helper Lessons Learned
- System-wide insights → saved to `global/agent_lessons.md`

These are committed at session end (with your permission) and immediately available to future sessions.

### Formal Feedback Submission (Optional)

For structured feedback that needs maintainer review:

1. Create a file in `pending/` following this naming: `YYYYMMDD_TYPE_MODULE.md`
2. Use a template from `templates/` (correction, warning, lesson_learned, missing, global)
3. Commit and push to magpie-agent repo
4. Maintainer reviews and integrates into documentation

Type `/feedback` for detailed instructions.

---

## Directory Structure

```
feedback/
├── pending/        ← Feedback awaiting review
├── integrated/     ← Archive of processed feedback
├── global/         ← System-wide lessons (agent_lessons.md)
├── templates/      ← Submission templates
├── archive/        ← Archived infrastructure (scripts, guides)
└── README.md       ← You are here
```

## Feedback Types

| Type | Use when | Goes to |
|------|----------|---------|
| **Correction** | Documentation has errors | `module_XX.md` (core doc fix) |
| **Warning** | You found a common mistake | `module_XX_notes.md` |
| **Lesson** | You figured something out | `module_XX_notes.md` or helper Lessons |
| **Missing** | Documentation has gaps | `module_XX.md` (add section) |
| **Global** | Agent behavior improvement | `global/agent_lessons.md` |

## Key Files

- `global/agent_lessons.md` — System-wide lessons the agent has learned
- `pending/README.md` — Detailed guide for the pending feedback workflow
- `templates/*.md` — Ready-to-fill feedback templates

## Integration

Maintainers review `pending/` periodically:
1. Read pending feedback files
2. Validate against current code
3. Route to appropriate docs (module_XX.md or module_XX_notes.md)
4. Move processed files to `integrated/`
5. Commit

For the archived formal integration pipeline (scripts, guides), see `archive/`.
