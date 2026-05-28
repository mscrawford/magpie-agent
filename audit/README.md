# Audit / iteration artifacts for the MAgPIE agent

This directory holds the **internal iteration artifacts** for the agent — the open-work backlog, validation rounds, pipeline audits, plans, rubrics, ledgers, and the agent-side write paths for lessons learned. There is no longer an external user-submission inbox (the `/feedback` command and `pending/` were removed in commit `327116c` on 2026-05-24; see `archive/plans/agent_simplification_plan.md` for the rationale).

> This directory was previously named `feedback/`; it was renamed to `audit/` in commit `1c7df77` on 2026-05-24 to match its actual contents. The artifacts inside are unchanged from before the rename.

## How the agent records lessons

The agent appends directly to these files during sessions:

- **Module-specific lessons / warnings / corrections** → `modules/module_XX_notes.md` (in the magpie-agent repo, not here)
- **Helper improvements** → `agent/helpers/*.md` under each helper's `## Lessons Learned` section
- **System-wide lessons** → `global/agent_lessons.md` in this directory

Sessions end with the agent showing a learning summary and (with the user's permission) committing those appends.

## Directory contents

```
audit/
├── BACKLOG.md                        ← Single source of truth for OPEN work (active / deferred / won't-fix)
├── get_under_control_plan.md         ← R24 bomb-rate campaign (Phases 0-3 done; kept for the R26 charter)
├── validation_rounds.json            ← Semantic-flywheel round log (schema v1.2) — LIVING
├── pipeline_audit_rounds.json        ← Structural-audit round log — LIVING
├── flywheel_rubric.md                ← Canonical scoring spec for /validate-semantic
├── probe_dedup_ledger.json           ← Names off-limits for fresh probes
├── advisory_allowlist.json           ← Allowlisted advisory findings for validate_consistency.sh
├── renames.json                      ← Tracked historical renames (for validate_consistency.sh)
├── global/                           ← System-wide agent lessons (agent_lessons.md)
├── integrated/                       ← Archived agent-recorded lessons (history)
├── templates/                        ← Templates referenced by validators/auditors
├── archive/                          ← Frozen history; validators skip everything under here
│   ├── plans/                        ← Completed / superseded plans (next_session, R3 exec, feedback removal, magpie4 scaffolding, Pattern-D2)
│   ├── rounds/                       ← Per-round artifacts: round{N}_* + pipeline_audit_round{N}*.md
│   └── (loose files)                 ← Legacy /feedback infrastructure (scripts, design docs)
└── README.md                         ← You are here
```

**New round artifacts go in `archive/rounds/`, not the top level.** The living records are the two `*_rounds.json` logs; per-round markdown (design, answers, audits, synthesis, reports) is frozen history. This keeps the `audit/` top level all-living and keeps citation-heavy round files out of the validators' scan path. Open work is tracked in `BACKLOG.md` — superseded plans move to `archive/plans/`.

## Key files

- `BACKLOG.md` — single source of truth for open work; read this first when picking up maintenance
- `global/agent_lessons.md` — system-wide lessons the agent has learned, appended over many sessions
- `validation_rounds.json` — persistent record of every `/validate-semantic` round (severity tiers + audit format in `flywheel_rubric.md`); each round must include at least one regression question from the top-level `regression_questions` array
- `flywheel_rubric.md` — canonical scoring spec (severity tiers, mechanical checks, bug classes, anchor examples); referenced by `/validate-semantic` and the Opus auditor
- `pipeline_audit_rounds.json` (living log) + `archive/rounds/pipeline_audit_roundN.md` (per-round reports) — `/pipeline-audit` structural audits of the agent's own machinery
- `probe_dedup_ledger.json` — tracks names already in agent rule text / past rounds; new probes that hit these names risk testing recognition rather than capability (run `scripts/probe_dedup_check.py`)
- `advisory_allowlist.json` / `renames.json` — registries consumed by `scripts/validate_consistency.sh` and its Python checkers

## Where lesson categories go

| Category | File | When |
|---|---|---|
| Correction to a module fact | `modules/module_XX.md` (direct edit) | Agent edits the doc, records the change |
| Warning about a module pitfall | `modules/module_XX_notes.md` | Append-only |
| Helper-specific lesson | `agent/helpers/<helper>.md` `## Lessons Learned` | Append-only |
| System-wide pattern | `audit/global/agent_lessons.md` | Append-only |
| Documentation gap that turned into a usable fix | `modules/module_XX.md` + entry in agent_lessons.md | Edit + append |

For the archived formal-integration pipeline (scripts, guides), see `archive/`.
