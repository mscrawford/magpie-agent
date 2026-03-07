# Helper: Documentation Maintenance Protocol

**Auto-load triggers**: "maintenance", "keep docs current", "docs outdated", "documentation drift", "update docs", "stale documentation", "doc maintenance"
**Last updated**: 2026-03-07
**Lessons count**: 0 entries

---

## Purpose

This helper defines **how the magpie-agent documentation stays current** as MAgPIE evolves. It provides a structured, three-layer maintenance model, clear cadences, drift detection signals, and recovery procedures. Use this as the authoritative reference whenever documentation freshness, sync, or validation questions arise.

---

## 1. Three-Layer Maintenance Model

Documentation health is maintained through three complementary layers, each catching different classes of problems at different frequencies.

### Layer 1 — Syntactic Validation (automated, every session)

**What it does**: `scripts/validate_consistency.sh` runs 32 structural checks against the documentation.

**What it catches**:
- Broken cross-references and internal links
- Wrong variable/set/equation names (compared to GAMS code)
- Stale counts (e.g., "46 modules" when count has changed)
- Deployment drift (AGENT.md source ≠ deployed copies)
- Missing required sections in module docs

**Cadence**: Run at session start if docs were modified in a previous session. Always run after any documentation edit.

**Command**: `/validate`

**Typical time**: ~2 minutes

**Key principle**: This layer is cheap and fast — never skip it after editing docs.

### Layer 2 — Code Sync (manual, triggered by MAgPIE updates)

**What it does**: The `/sync` command reads MAgPIE commit diffs since the last sync point and updates affected module documentation accordingly.

**How it works**:
1. Reads `project/sync_log.json` for the last sync commit hash
2. Diffs all commits from that point to current HEAD
3. Identifies which modules were changed and how
4. Updates the corresponding `modules/module_XX.md` files
5. Records the new sync point in `sync_log.json`

**What it catches**:
- New equations, variables, or parameters added to modules
- Changed default values or switch names in `config/default.cfg`
- New realizations added to existing modules
- Renamed or removed realizations
- Structural changes to core files

**Cadence**: When session startup shows 🟡 or 🔴 staleness badge (>5 commits behind develop).

**Command**: `/sync`

**Typical time**: 15–30 minutes for 5–10 commits

### Layer 3 — Semantic Validation (periodic, flywheel)

**What it does**: `/validate-semantic` generates expert-level questions about MAgPIE, answers them using only the AI documentation, then audits those answers against the actual GAMS code.

**What it catches**:
- Fabricated or outdated counts (e.g., wrong number of crop types)
- Wrong equation formulations (doc says one thing, code does another)
- Realization confusion (attributes of one realization described under another)
- Missing caveats or limitations not mentioned in docs
- Subtle semantic drift that passes syntactic checks

**How it works**:
1. Generates 5 expert questions spanning different modules and difficulty levels
2. Answers each question using ONLY the AI documentation (no code access)
3. Audits each answer against the actual GAMS source code using 10 parallel agents
4. Scores accuracy (1–10) and categorizes bugs as Critical/Major/Minor
5. Records results in `feedback/validation_rounds.json`

**Cadence**: After major sync events (>20 commits integrated), or approximately quarterly.

**Command**: `/validate-semantic` (full) or `/validate-semantic --modules 14,29,32` (targeted)

**Typical time**: 30–60 minutes per round (5 questions, 10 agents)

---

## 2. Maintenance Cadence

| Activity | Trigger | Cadence | Time | Command |
|---|---|---|---|---|
| Syntactic validation | After any doc edit | Every edit | 2 min | `/validate` |
| Sync freshness check | Session start | Every session | Automatic | *(session_startup)* |
| Code sync | 🟡/🔴 staleness badge | When >5 commits behind | 15–30 min | `/sync` |
| Targeted semantic check | After sync touches >3 modules | After major sync | 20 min | `/validate-semantic --modules 14,29,32` |
| Full semantic round | Quarterly or after major refactor | ~4×/year | 45–60 min | `/validate-semantic` |
| Meta-check | Before releases | Before release | 30 min | Manual inventory |

### Meta-Check Inventory (before releases)

A manual sweep to ensure everything is in order:
1. All module docs exist and are non-empty
2. AGENT.md source matches both deployed copies
3. `sync_log.json` shows 🟢 status
4. Latest semantic validation round has no unresolved Critical bugs
5. All `module_XX_notes.md` warnings have been addressed or acknowledged
6. Helper docs reference correct commands and paths

---

## 3. Drift Detection Signals

Watch for these warning signs that documentation is falling behind the code:

| Signal | Severity | What to do |
|---|---|---|
| Session startup shows 🔴 (>20 commits behind) | High | Run `/sync` immediately before answering code questions |
| Validator fails GAMS variable/equation checks | High | Code changed but docs didn't — update affected module docs |
| User reports incorrect information | High | Record in `module_XX_notes.md`, fix doc, run validator |
| New realizations added without doc updates | Medium | Add realization section to affected `module_XX.md` |
| Module file sizes changed significantly (>20% lines added/removed) | Medium | Review changes and update docs accordingly |
| Semantic validation score drops below 8.0 | Medium | Run targeted validation on weak modules |
| `config/default.cfg` switches renamed or added | Low | Update helper docs (scenario helpers, realization_selection) |
| Cross-module docs reference removed sets/parameters | Low | Update `cross_module/` docs |

### Proactive Monitoring

When answering user questions, watch for these informal signals:
- You find yourself saying "the docs say X but I'm not sure if that's still true"
- A user corrects something you stated from documentation
- You need to go to raw GAMS code because docs feel incomplete
- Module docs mention a realization that doesn't exist in code

Each of these is a documentation gap — record it and fix it.

---

## 4. Maintenance Decision Tree

When MAgPIE code changes are detected, use this tree to determine what documentation needs updating:

```
MAgPIE commit detected
  │
  ├── Changes to modules/XX_name/?
  │   │
  │   ├── equations.gms changed
  │   │   └── UPDATE module_XX.md equations section
  │   │       • Verify equation names, formulations, and descriptions
  │   │       • Check if new equations were added or old ones removed
  │   │
  │   ├── declarations.gms changed
  │   │   └── CHECK variable names still match in module_XX.md
  │   │       • Verify variable/parameter/set declarations
  │   │       • Update "Key Variables" or equivalent section
  │   │
  │   ├── presolve.gms or postsolve.gms changed
  │   │   └── UPDATE module_XX.md bounds/dynamics sections
  │   │       • Check bound-setting logic
  │   │       • Verify temporal dynamics descriptions
  │   │
  │   ├── input.gms changed
  │   │   └── CHECK default values and switch names
  │   │       • Verify s_/c_ switch descriptions and defaults
  │   │       • Update configuration tables in docs
  │   │
  │   ├── New realization added
  │   │   └── ADD realization section to module_XX.md
  │   │       • Document purpose, equations, key differences
  │   │       • Update realization count in module header
  │   │
  │   └── Realization renamed or removed
  │       └── UPDATE all references across docs
  │           • Module doc, cross-module docs, helpers
  │           • Check AGENT.md for any hardcoded references
  │
  ├── Changes to core/sets.gms?
  │   └── UPDATE cross_module/ docs + any module docs using affected sets
  │       • land_balance_conservation.md if land sets changed
  │       • Module docs that reference modified sets
  │
  ├── Changes to config/default.cfg?
  │   └── UPDATE helper docs
  │       • realization_selection.md (default realizations)
  │       • Scenario helpers (scenario_carbon_pricing, etc.)
  │       • Module docs with configuration tables
  │
  └── Changes to main.gms or core/?
      └── UPDATE Core_Architecture.md if structural changes
          • Module loading order
          • Solve sequence
          • Pre/post processing flow
```

### Priority Rules

When multiple docs need updating from a single sync:
1. **Equation changes** — highest priority (directly affects accuracy of technical answers)
2. **New/removed realizations** — high priority (users ask "what options does module X have?")
3. **Variable/parameter changes** — medium priority (affects debugging guidance)
4. **Configuration changes** — medium priority (affects scenario setup advice)
5. **R-script and data-only changes** — low priority (rarely affects AI documentation)

---

## 5. Quality Gates

Documentation is considered **healthy** when all of these conditions are met:

| Gate | Criteria | How to check |
|---|---|---|
| ✅ Validator | 32/32 checks pass | `/validate` |
| ✅ Sync | 🟢 badge (≤5 commits behind, <14 days) | Session startup check |
| ✅ Semantic | Latest round mean ≥8.0/10 with 0 Critical bugs | `feedback/validation_rounds.json` |
| ✅ Coverage | All modules have `module_XX.md` docs | `/validate` (includes coverage check) |
| ✅ AGENT.md | All 3 copies synced (source, `../AGENT.md`, `../CLAUDE.md`) | `/validate` (includes deployment check) |

### Minimum Acceptable State

For day-to-day use, the **minimum** is:
- Validator passes (no broken references)
- Sync badge is 🟢 or 🟡 (not 🔴)
- No unresolved Critical bugs from semantic validation

### Target State

For confident, high-quality answers:
- All quality gates green
- Semantic validation score ≥9.0/10
- All `module_XX_notes.md` warnings addressed
- Helpers tested against recent model runs

---

## 6. Recovery Procedures

### Validator Fails

**Fix errors in priority order:**
1. **Code truth errors** (variable/equation name mismatches) — fix immediately, these cause wrong answers
2. **Module doc errors** (broken links, stale counts) — fix before answering related questions
3. **Cross-module doc errors** — fix during dedicated maintenance
4. **Core doc errors** — fix when Core_Architecture.md is referenced

```bash
# Run validator and capture failures
cd /path/to/magpie-agent
bash scripts/validate_consistency.sh 2>&1 | grep "FAIL"
# Fix each failure, then re-run to confirm
```

### Sync Way Behind (>50 commits)

When documentation is severely stale:

1. **Don't try to sync everything at once** — focus on high-impact changes
2. **Prioritize equation and declaration changes** — these affect answer accuracy most
3. **Skip R-script and data-only commits** — these rarely affect AI documentation
4. **Use targeted sync**: Focus on modules that were actually modified

```bash
# See which modules were touched in the commit range
git -C .. --no-pager diff --stat <last_sync_commit>..HEAD -- modules/ | head -30
# Focus on modules with .gms changes (not just data)
git -C .. --no-pager diff --name-only <last_sync_commit>..HEAD -- 'modules/*/realization/*.gms'
```

5. **After sync, run `/validate`** to catch any remaining inconsistencies
6. **Run targeted semantic validation** on the most-changed modules

### Semantic Score Drops Below 7.0

1. **Identify weak modules** from the validation round results
2. **Run targeted validation**: `/validate-semantic --modules <weak_module_numbers>`
3. **Fix Critical bugs first**, then Major, then Minor
4. **Re-run semantic validation** to confirm improvement
5. **If score doesn't improve**, the module doc may need a full rewrite from GAMS code

### User Reports Error

1. **Record immediately** in `modules/module_XX_notes.md` with date and description
2. **Fix the documentation** — verify against GAMS code before correcting
3. **Run `/validate`** to ensure fix doesn't break other references
4. **Commit with descriptive message**: `fix: correct [description] in module_XX.md`
5. **If error pattern suggests systemic issue**, run semantic validation on related modules

### AGENT.md Out of Sync

```bash
# From magpie-agent/ directory:
cp AGENT.md ../AGENT.md && cp AGENT.md ../CLAUDE.md
# Verify
diff AGENT.md ../AGENT.md  # should show no differences
diff AGENT.md ../CLAUDE.md  # should show no differences
```

---

## Module Cross-References

| Topic | Read |
|---|---|
| Session startup & freshness checks | `agent/helpers/session_startup.md` |
| Sync command details | `agent/commands/sync.md` |
| Validation command details | `agent/commands/validate.md` |
| Semantic validation command | `agent/commands/validate-semantic.md` (if exists) |
| Sync state tracking | `project/sync_log.json` |
| Validation results | `feedback/validation_rounds.json` |
| Module documentation | `modules/module_XX.md` |
| User feedback & notes | `modules/module_XX_notes.md` |

---

## Related Helpers & Docs

- **Session startup** → `agent/helpers/session_startup.md` (freshness checks, staleness badges)
- **Modification safety** → `agent/helpers/modification_impact_analysis.md` (impact of code changes)
- **Core architecture** → `core_docs/Core_Architecture.md` (model structure reference)
- **Module dependencies** → `core_docs/Module_Dependencies.md` (cross-module relationships)

---

## Lessons Learned
<!-- APPEND-ONLY: Add new entries at the bottom. Never remove old ones. -->
<!-- Format: - YYYY-MM-DD: [lesson] (source: [user feedback | session experience]) -->
