# 🤖 magpie-agent

**MAgPIE AI Documentation System**

Comprehensive, AI-optimized documentation for the MAgPIE land-use model. Works with any AI assistant (Claude Code, Cursor, Copilot, etc.).

**Latest release:** v1.1.0 (2026-06-05) - see [CHANGELOG.md](CHANGELOG.md). The semantic-validation flywheel has matured to 47 rounds (recent rounds 9.3-9.6 / 10, periphery stabilized) and the docs are current with MAgPIE `develop`.

For current state of the project, see `audit/validation_rounds.json`, `audit/pipeline_audit_rounds.json`, `audit/BACKLOG.md` (open work) / `audit/get_under_control_plan.md` (R24 campaign), and the git commit log. (Historical v1.0 snapshot at `project/archive/CURRENT_STATE.v1.0_frozen_2026-03-07.json`.)

---

## 📦 Setup

### 1. Clone magpie-agent into your MAgPIE directory

```bash
cd /path/to/your/magpie/
git clone git@github.com:mscrawford/magpie-agent.git magpie-agent
```

### 2. Deploy AGENT.md to MAgPIE root

Your AI assistant needs `AGENT.md` in the working directory (the MAgPIE root). The file is tool-agnostic; the deployment step is to put a copy where your tool will find it:

```bash
cd /path/to/your/magpie/
cp magpie-agent/AGENT.md AGENT.md          # canonical, tool-agnostic
cp magpie-agent/AGENT.md CLAUDE.md         # Claude Code auto-loads CLAUDE.md
# cp magpie-agent/AGENT.md .cursorrules    # Cursor convention (if using Cursor)
# cp magpie-agent/AGENT.md CONVENTIONS.md  # Aider convention (if using Aider)
```

Same content, different filenames per tool's auto-load convention. If your tool doesn't auto-load any project file, point it at `AGENT.md` manually. Subsequent updates flow through `magpie-agent/agent/helpers/session_startup.md` which keeps `../AGENT.md` and `../CLAUDE.md` in sync; if you use a third filename, you'll need to add the copy manually after agent updates.

### 3. Add agent infrastructure to parent `.gitignore`

magpie-agent lives inside the MAgPIE working tree as a local install, not part of MAgPIE itself. Add these lines to your parent magpie/`.gitignore` so they aren't accidentally committed to upstream:

```
AGENT.md
CLAUDE.md
/magpie-agent/
.claude/
validation_report_*.txt
.cache/
```

### 4. Verify Setup

```bash
ls -la AGENT.md           # in MAgPIE root
ls -la magpie-agent/      # full documentation repo
bash magpie-agent/scripts/validate_consistency.sh   # should pass
```

---

## 📁 Repository Structure

```
magpie-agent/
├── README.md                  ← This file (project overview)
├── AGENT.md                   ← AI agent instructions (the SSOT for agent behavior)
│
├── agent/
│   ├── commands/              ← Slash command definitions (see AGENT.md "Available Commands")
│   └── helpers/               ← Auto-loading context helpers (see AGENT.md "Auto-Loading Context Helpers")
│
├── modules/                   ← Per-module documentation (46 files + _notes sidecars)
├── cross_module/              ← Conservation laws + safety guides + dependency resolution
├── core_docs/                 ← Architecture, dependencies, query patterns, response guidelines
├── reference/                 ← GAMS programming reference + verification protocol
│
├── audit/                     ← Internal iteration artifacts (validation rounds, pipeline audits, lessons, plans)
├── project/                   ← Project-management files (sync_log, version_pins, frozen v1.0 snapshot)
├── scripts/                   ← Validators and helpers
└── ...
```

**Scope: the agent spans three layers of the MAgPIE pipeline and routes across them.**
- **Core (the GAMS model):** the 46 modules, conservation laws, architecture, and GAMS reference (`modules/`, `cross_module/`, `core_docs/`, `reference/`). The agent's primary domain.
- **Downstream (R reporting):** `agent/helpers/magpie4_reference.md` (in this repo) routes `report.mif` / IAMC-variable / `getReport` questions to the version-pinned `magpie4` source (`project/version_pins.json` + `.cache/sources/magpie4/`).
- **Upstream (R preprocessing):** the companion `PREPROC_AGENT.md` (deployed at the MAgPIE root alongside `AGENT.md`; see AGENT.md's preprocessing-agent and twin-agent sections) routes `madrat`/`mrcommons`/`mrmagpie`/... input-provenance questions ("where does this input file come from?").

---

## ⚠️ Code Truth Principle

When analyzing MAgPIE, describe ONLY what is actually implemented in the code.

- ✅ Describe actual equations, parameters, and module implementations
- ❌ Don't add ecological/economic reality, suggest improvements, or describe ideal features
- 📖 See `reference/Code_Truth_Principles.md` (full discussion) and `AGENT.md` Step 1d for the 20 anti-confabulation MANDATEs

---

## 💬 For AI Agents Answering MAgPIE Questions

Follow `AGENT.md` — it contains the full workflow:

1. Check AI documentation first (`modules/module_XX.md`, `core_docs/*`, etc.)
2. Cite `file:line` for every factual claim
3. Use exact variable names (`vm_land(j,land)`, not "the land variable")
4. Distinguish what code DOES vs what it does NOT
5. State limitations explicitly
6. Verify in raw GAMS code for high-stakes claims

Doc-vs-code accuracy is mechanically guarded by `scripts/validate_consistency.sh` (run it; the summary prints the live check count). Semantic accuracy is probed by the flywheel rounds in `audit/validation_rounds.json`.

---

## 🛠️ For Documentation-Project Maintainers

(Skip this section if you're a MAgPIE user.)

Open work is tracked in one place:

- `audit/BACKLOG.md` — single source of truth for open work (active / deferred / won't-fix)
- `audit/get_under_control_plan.md` — R24 bomb-rate campaign (Phases 0-3 done; R26/R27 complete; archive-ready)
- `audit/validation_rounds.json` — semantic-flywheel round log
- `audit/pipeline_audit_rounds.json` — structural pipeline audit log
- `audit/global/agent_lessons.md` — system-wide lessons
- `audit/archive/` — completed plans (`plans/`) and per-round artifacts (`rounds/`)

`git log --oneline -20` shows recent direction.

### Capturing lessons during sessions

The agent records lessons directly:
- **Module-specific corrections** → `modules/module_XX_notes.md`
- **Helper-specific corrections** → `agent/helpers/XX.md` `## Lessons Learned`
- **System-wide lessons** → `audit/global/agent_lessons.md`

There is no external user-submission inbox; the `/feedback` command was removed 2026-05-24.

### Common commands

```bash
# Count documented modules
ls -1 modules/module_*.md | wc -l

# Verify equation count for module XX
grep "^[ ]*qXX_" ../modules/XX_*/*/declarations.gms | wc -l

# Run the consistency validator
bash scripts/validate_consistency.sh

# Sync with MAgPIE develop
# (see agent/commands/sync.md)
```

---

## ✓ Quality Checklist for Module Docs

Before publishing a module doc edit, verify:

- [ ] Cited `file:line` for every factual claim (full-path form)
- [ ] Used exact variable names (`vm_land(j,land)`, not "the land variable")
- [ ] Verified feature exists (grep'd or read the file)
- [ ] Described CODE behavior only (not ecological/economic theory)
- [ ] Labeled examples (made-up numbers vs. actual input data)
- [ ] Checked arithmetic (if providing calculations)
- [ ] Listed dependencies (if suggesting modifications)
- [ ] Stated limitations (what code does NOT do)
- [ ] No vague language ("the model handles..." → specific equation)
- [ ] Ran `bash scripts/validate_consistency.sh` (must pass)

If you can't check all boxes, the response needs more verification.

---

## 📚 Visualization & Data Files

### Dependency Graphs (snapshot)

`reference/dependency_analysis/` contains an Oct-2025 dependency snapshot:
- `core_dependencies.dot`, `full_dependencies.dot`, etc.
- `dependency_report.txt`, `dependency_analysis.json`
- `EXECUTIVE_SUMMARY.md`

Regenerate PNGs: `cd reference/dependency_analysis && dot -Tpng core_dependencies.dot -o core_dependencies.png`

Note: the snapshot is from 2025-10-10; MAgPIE has churned since (renames in PR #869 etc.). For current dependencies, prefer `core_docs/Module_Dependencies.md` or recompute via grep.

---

## 📞 What to Do When Stuck

| Problem | Solution |
|---|---|
| Can't find equation | `grep "^[ ]*qXX_" ../modules/XX_*/*/declarations.gms` |
| Unknown interface variable | Check `core_docs/Module_Dependencies.md` for producer |
| Need to understand agent workflow | Read `AGENT.md` |
| Tool usage / path issues | Check `core_docs/Tool_Usage_Patterns.md` |
| Module docs look stale | Check `audit/validation_rounds.json` for recent findings; run `bash scripts/validate_consistency.sh` |
| report.mif / IAMC variable / model output | Check `agent/helpers/magpie4_reference.md` (version-pinned magpie4 reporting layer) |
| Input data / where an input file comes from | Route to `PREPROC_AGENT.md` (R preprocessing companion) |

---

## 🌟 Project Goal

Make it effortless for any AI assistant to understand and reason about MAgPIE: 100% Code Truth, complete module coverage, mechanically-verified citations, AI-optimized structure.

**Purpose**: Enable any AI to effectively work with MAgPIE without prior knowledge.
**Principle**: Code Truth — describe only what IS implemented in the code.
