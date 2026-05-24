# Audit / iteration artifacts for the MAgPIE agent

This directory holds the **internal iteration artifacts** for the agent — validation rounds, pipeline audits, plans, rubrics, ledgers, and the agent-side write paths for lessons learned. There is no longer an external user-submission inbox (the `/feedback` command and `pending/` were removed; see the `agent_simplification_plan.md` in this directory for the rationale).

> The directory will be renamed `audit/` in a follow-up commit (Phase B of the simplification plan). After that rename, the *artifacts* described here are unchanged — only the directory name.

## How the agent records lessons

The agent appends directly to these files during sessions:

- **Module-specific lessons / warnings / corrections** → `modules/module_XX_notes.md` (in the magpie-agent repo, not here)
- **Helper improvements** → `agent/helpers/*.md` under each helper's `## Lessons Learned` section
- **System-wide lessons** → `global/agent_lessons.md` in this directory

Sessions end with the agent showing a learning summary and (with the user's permission) committing those appends.

## Directory contents

```
audit/
├── global/                          ← System-wide agent lessons (agent_lessons.md)
├── integrated/                      ← Archived agent-recorded lessons (history)
├── templates/                       ← Templates referenced by validators/auditors
├── archive/                         ← Historical infrastructure (older scripts, design docs)
├── validation_rounds.json           ← Semantic-flywheel round log (schema v1.1)
├── flywheel_rubric.md               ← Canonical scoring spec for /validate-semantic
├── pipeline_audit_rounds.json       ← Structural-audit round log
├── pipeline_audit_roundN.md         ← Per-round detailed findings reports
├── probe_dedup_ledger.json          ← Names off-limits for fresh probes
├── advisory_allowlist.json          ← Allowlisted advisory findings for validate_consistency.sh
├── renames.json                     ← Tracked historical renames (for validate_consistency.sh)
├── agent_simplification_plan.md     ← Plan for /feedback removal + audit/ → audit/ rename
├── magpie4_scaffolding_plan.md      ← Plan for the magpie4 lean scaffolding initiative
├── round*.md                        ← Per-round design/answer/report markdown for flywheel rounds
└── README.md                        ← You are here
```

## Key files

- `global/agent_lessons.md` — system-wide lessons the agent has learned, appended over many sessions
- `validation_rounds.json` — persistent record of every `/validate-semantic` round (severity tiers + audit format in `flywheel_rubric.md`); each round must include at least one regression question from the top-level `regression_questions` array
- `flywheel_rubric.md` — canonical scoring spec (severity tiers, mechanical checks, bug classes, anchor examples); referenced by `/validate-semantic` and the Opus auditor
- `pipeline_audit_rounds.json` + `pipeline_audit_roundN.md` — `/pipeline-audit` structural audits of the agent's own machinery
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
