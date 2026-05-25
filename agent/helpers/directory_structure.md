# Helper: Directory Structure & Path Resolution

**Auto-load triggers**: "where is", "which directory", "AGENT.md path", "directory structure", "where does this live", "path confusion"
**Lessons count**: 0 entries

---

## Purpose

Detailed orientation for the magpie-agent directory layout and path conventions. Hoisted from AGENT.md in R6 to free always-loaded surface — most sessions don't need the full diagram. AGENT.md keeps the load-bearing distinctions (AGENT.md vs ../AGENT.md vs ../CLAUDE.md, modules/ vs ../modules/); this helper has the rest.

---

## Working directory

The agent's working directory is the "magpie-agent" subdirectory (relative to the MAgPIE project root).

```
/magpie/                          ← Parent: Main MAgPIE project (git repo #1)
├── AGENT.md                      ← DEPLOYED copy (auto-updated, do NOT edit)
├── CLAUDE.md                     ← DEPLOYED copy (auto-updated, do NOT edit) — Claude Code's load target; identical to ../AGENT.md
├── modules/                      ← GAMS modules (actual MAgPIE code)
│   ├── 14_yields/
│   ├── 70_livestock/
│   └── ...
├── main.gms                      ← MAgPIE entry point
├── magpie-agent/                 ← AGENT WORKING DIR (git repo #2)
│   ├── AGENT.md                  ← SOURCE instructions (edit here)
│   ├── README.md                 ← Project overview
│   ├── agent/
│   │   ├── commands/             ← Slash command definitions
│   │   └── helpers/              ← Auto-loading context helpers (incl. this file)
│   ├── modules/                  ← AI documentation (NOT GAMS code — see distinction below)
│   │   ├── module_14.md
│   │   ├── module_70.md
│   │   └── ...
│   ├── core_docs/                ← Architecture docs
│   ├── cross_module/             ← Conservation laws + safety guides
│   ├── reference/                ← GAMS programming reference
│   ├── audit/                    ← Validation rounds, pipeline audits, lessons, plans
│   ├── project/                  ← Project-management files (sync_log, version_pins, frozen v1.0 snapshot)
│   └── scripts/                  ← Validators and helpers
└── magpie-preproc-agent/         ← Optional companion agent for R preprocessing
```

## Path resolution rules

### 1. For AI documentation (module_XX.md, core_docs/*, etc.)

From current dir (the magpie-agent directory): use "modules/module_14.md" ✅
NOT: "magpie-agent/modules/module_14.md" ❌ (double-prefixed)

### 2. For MAgPIE GAMS code (XX_name/realization/*.gms inside parent magpie/modules/)

From current dir: use "../modules/14_yields/managementcalib_aug19/equations.gms" ✅
NOT: "modules/14_yields/..." ❌ (that's the AI-docs path, not GAMS!)

### 3. Important distinctions

| Path | What it is |
|---|---|
| `modules/` in current dir | AI documentation (markdown — 46 modules + `_notes` sidecars) |
| `../modules/` in parent dir | MAgPIE GAMS code |
| `AGENT.md` in current dir | SOURCE (edit this) |
| `../AGENT.md` in parent dir | DEPLOYED copy (auto-copied by session_startup or after edits). Canonical, tool-agnostic name. Cursor / Aider / generic users point their tool at this. |
| `../CLAUDE.md` in parent dir | DEPLOYED copy (auto-copied). Identical content to `../AGENT.md`; exists because Claude Code auto-loads `CLAUDE.md` by convention. |

### 4. Git operations

- For AI docs: commit from the magpie-agent directory.
- For MAgPIE code: commit from parent directory.
- NEVER commit magpie-agent changes to the main MAgPIE repo.

---

## Lessons Learned

<!-- APPEND-ONLY -->
