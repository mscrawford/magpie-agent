# magpie4 lean scaffolding — execution plan

**Created**: 2026-05-24
**Origin**: queued initiative #3 in `~/.claude/projects/.../memory/project_magpie_agent_initiatives.md` (HIGH PRIORITY)
**Estimated effort**: 1–1.5 hours wall-clock, ~70–100K tokens
**Tier chosen**: Mid (renv-pinned SHA-anchored clone + sync script + helper doc; not full preproc-parity)

---

## Goal

Enable the magpie-agent to answer questions about magpie4 (the R post-processing package consuming `fulldata.gdx`) by directing the agent to grep version-correct source on demand — NOT by curating function-level docs.

## Non-goals (scope guards)

- **No curated function docs.** magpie4 has 309 exports; `getReport` alone fans out to 108 `report*` callees. Curation would be an endless treadmill.
- **No coverage of `magpiesets`, `gdx2`, or other postproc R packages.** Deferred until magpie4 lean scaffolding is proven; the same mechanism extends trivially if needed.
- **No magpie4 inclusion in core_docs/** — it's not an architectural concept of MAgPIE itself.
- **No live source reads against `~/Documents/Work/Workspace/magpie4/`** (HEAD) — that clone drifts from the renv-pinned version. The user's runs use version 2.70.0 per `magpie/input/renv.lock`; the workspace clone is at 2.75.1 (5 minor versions ahead).

## Load-bearing facts (confirmed 2026-05-24)

- `magpie/input/renv.lock` pins **magpie4 @ 2.70.0** (Source: "Repository", date 2026-03-13). The renv.lock entry needs to be parsed to extract the version; SHA may need a separate lookup via `git ls-remote --tags pik-piam/magpie4 v2.70.0`.
- Local clone at `~/Documents/Work/Workspace/magpie4/` is at **2.75.1** — DO NOT use for version-correct reads.
- `getReport.R` calls **108 unique `report*` functions** via an `if/else if (any(grepl(...)))` dispatch pattern. Each `reportX` corresponds to an IAMC variable subtree.
- `scripts/output/rds_report.R:37` (in MAgPIE proper) is what invokes `magpie4::getReport(gdx)`.
- Direct namespace-qualified usage in `scripts/output/`: only 9 calls (`magpie4::land` 4×, `magpie4::tau` 2×, `magpie4::croparea` 2×, `magpie4::production` 1×, plus 5 singletons). Most calls are bare-name under `library(magpie4)`.

## Architecture

```
magpie-agent/
├── project/
│   └── version_pins.json          ← {magpie4: {version, sha, source_dir}} (single-package mini of preproc's)
├── .cache/sources/
│   └── magpie4/                   ← SHA-pinned clone, never edited (read-only by convention)
├── scripts/
│   └── sync_magpie4_clone.sh      ← reads renv.lock, clones at pin, writes version_pins.json
└── agent/helpers/
    └── magpie4_reference.md       ← the helper itself (path pointer + grep convention + auto-load)
```

`.cache/sources/` and `project/version_pins.json` should be `.gitignore`-d (they're derivable from `magpie/input/renv.lock`). Only `scripts/sync_magpie4_clone.sh` and `magpie4_reference.md` are committed.

---

## Phases

### Phase 1 — Version-pinning infrastructure (~30 min, ~30K tokens)

**Build**: `scripts/sync_magpie4_clone.sh`

Steps:
1. Parse `magpie/input/renv.lock` for the `"magpie4"` object → extract `Version`, `Source`, optionally `RemoteRef` / `RemoteSha`.
2. If renv.lock has a SHA, use it. Otherwise, resolve `v<Version>` against `git ls-remote --tags git@github.com:pik-piam/magpie4` → get the commit SHA.
3. If `magpie-agent/.cache/sources/magpie4/.git/HEAD` doesn't exist → `git clone git@github.com:pik-piam/magpie4 .cache/sources/magpie4 && cd .cache/sources/magpie4 && git checkout <SHA>`.
4. If clone exists but HEAD doesn't match the pinned SHA → `git fetch && git checkout <SHA>` (or warn the user if working tree is dirty).
5. Write/update `project/version_pins.json` with `{magpie4: {version, sha, source_dir, renv_lock_hash, captured_at}}`.
6. Idempotent: if already at pinned SHA and version_pins.json is current, no-op with status message.

**Acceptance**:
- `bash scripts/sync_magpie4_clone.sh` → exits 0 with message "magpie4 @ 2.70.0 (SHA xxx) cached at .cache/sources/magpie4/"
- Second invocation: "already in sync" no-op.
- `.cache/sources/magpie4/DESCRIPTION` shows `Version: 2.70.0`.
- `git -C .cache/sources/magpie4 status` is clean.

**Risk**: renv.lock "Repository" source may not include a SHA. **Mitigation**: tag-based clone (`git checkout v2.70.0` after `git fetch --tags`). If neither SHA nor tag resolves, warn and fall back to `git checkout main` with a loud caveat in the script output AND in `version_pins.json` (a `resolution: "fallback_HEAD"` field).

### Phase 2 — getReport call-graph + thematic grouping (~30 min, ~30K tokens)

**Goal**: Extract the structure of `getReport.R`'s dispatch so the helper can teach the agent how to find the right `report*` function.

Steps:
1. Read `.cache/sources/magpie4/R/getReport.R` from the pinned clone (NOT from the workspace clone).
2. Identify the dispatch pattern: `if (any(grepl("...", control)))` blocks pointing at one or more `report*` calls.
3. Group `report*` callees into thematic blocks based on the dispatch (likely: Land, Costs, Emissions, Demand, Water, Nitrogen, Carbon, Biodiversity, Agriculture, etc.).
4. For each thematic block, extract 3–5 example function names + 1-line roxygen `@title` for each. Read the roxygen via `head -20 .cache/sources/magpie4/R/<reportX>.R`.
5. DO NOT enumerate all 108 — that's the curation trap. Just enough examples per theme that the agent can pattern-match and the user can browse.

**Output**: thematic-block draft for the helper doc. Likely ~10 blocks × 4 example functions = ~40 named entry points, plus the grep convention for finding the other ~70.

**Risk**: Dispatch parsing may not yield clean themes. **Mitigation**: fall back to alphabetical grouping (still bounded; less pedagogically clean but works).

### Phase 3 — Write `agent/helpers/magpie4_reference.md` (~20 min, ~15K tokens)

**Structure** (target ~250 lines):

```markdown
# Helper: magpie4 reference (R post-processing package)

**Auto-load triggers**: "magpie4", "getReport", "magpie4::", "reportX function", "what magpie4 function...", "report.mif variable definition"
**Last updated**: 2026-05-24
**Lessons count**: 0 entries

---

## Why this exists

magpie4 is the R package consuming `fulldata.gdx` and producing `report.mif`.
It has 309 exported functions. We DO NOT curate function-level docs (treadmill).
Instead, this helper directs the agent to read SHA-pinned source on demand.

## Version pinning

**Authoritative source**: `magpie/input/renv.lock` → magpie4 entry.
**Current pin**: see `project/version_pins.json` (regenerated by
`scripts/sync_magpie4_clone.sh`).
**Cached clone**: `.cache/sources/magpie4/` (gitignored; managed by sync script).

**Before answering ANY magpie4 question**:
1. Check `project/version_pins.json` is current (not older than `input/renv.lock` mtime).
2. If stale or missing → run `bash scripts/sync_magpie4_clone.sh`.
3. Read `.cache/sources/magpie4/`, NEVER the workspace clone (`~/Documents/Work/Workspace/magpie4/`) which drifts ahead of the renv pin.

## Central entry point: getReport

`magpie4::getReport(gdx, ...)` is the canonical IAMC-format report generator.
It dispatches to ~108 `report*` functions based on the `control` argument.
[Show getReport's dispatch skeleton in 15-20 lines.]

## Thematic function index

[10 thematic blocks. Each block: name, ~4 example reportX functions with 1-line title, grep recipe for finding others in that theme.]

## Reading source on demand

For ANY magpie4 function the user asks about:

1. Confirm version-pinned clone is current.
2. Locate the function file: `ls .cache/sources/magpie4/R/<funcname>.R`.
3. Read the file. Pay attention to:
   - roxygen `@title`, `@description`, `@param`, `@return`
   - the function body (often just a wrapper around `setNames(...)`)
   - which other magpie4 functions it calls
4. Cite as `magpie4::<funcname>` and the file path under `.cache/sources/magpie4/R/`.

## Working with report.mif variables

[Recipe: IAMC variable name → grep .cache/sources/magpie4/R/getReport.R → identify reportX dispatch → read reportX.R.]

## Common questions

[5-7 worked examples spanning the thematic blocks.]

## Lessons Learned

(empty — append per usage)
```

### Phase 4 — AGENT.md integration (~15 min, ~10K tokens)

**Steps**:
1. Add auto-load row to AGENT.md's "Auto-load rules (keyword-triggered)" table:
   - **Triggers**: `magpie4`, `getReport`, `magpie4::`, `report.mif variable`, `which magpie4 function`, `postsolve report`
2. Update `agent/helpers/interpreting_outputs.md` to cross-reference magpie4_reference.md (one-line "for function-level magpie4 questions, see magpie4_reference.md") rather than duplicating function lookups.
3. Add `.cache/sources/` and `project/version_pins.json` to `.gitignore`.

**Trigger overlap check**: `interpreting_outputs.md` covers output PIPELINE (filenames, timing, IAMC convention). `magpie4_reference.md` covers magpie4 FUNCTIONS specifically. Triggers should NOT both fire on the same question — interpreting_outputs uses pipeline keywords (`fulldata.gdx`, `report.mif`, `postsolve`); magpie4_reference uses function-discovery keywords. Verify with a few cross-pollinated test phrases.

### Phase 5 — Smoke test (~10 min, ~10K tokens)

Via subagent (`magpie-helper` type):

> "Which magpie4 function reports regional N₂O emissions, and what does it return? Cite the file path."

Expected behavior:
1. Agent loads `magpie4_reference.md` (auto-trigger on "magpie4 function")
2. Agent checks `version_pins.json` → confirms current
3. Agent greps `.cache/sources/magpie4/R/getReport.R` for "N2O" or "Nitrogen"
4. Agent identifies likely candidate (probably `reportEmissions` or `reportNitrogen`)
5. Agent reads `.cache/sources/magpie4/R/<candidate>.R`
6. Agent cites the file with version-pinned path

**Failure modes to watch**:
- Agent reads workspace clone instead of `.cache/sources/` (would be version-wrong)
- Agent enumerates many functions instead of grepping (treadmill)
- Auto-load fails to fire (trigger keywords too narrow)

### Phase 6 — Commit + verify (~10 min, ~5K tokens)

- `bash scripts/validate_consistency.sh` → expect 40/40 + allowlist clean
- Commit: `infra: magpie4 lean scaffolding (renv-pinned, source-read-on-demand)`
- Push to mscrawford/magpie-agent main

---

## What this plan deliberately does NOT include

- A `check_magpie4_freshness.py` validator that warns if version_pins.json is stale relative to renv.lock — **deferred** (could be added in a second pass if the staleness recurs in practice).
- Auto-sync on every session-startup — **deferred** (would slow session startup by ~5s; better as on-demand via the AGENT.md trigger or a new `/sync-magpie4` command).
- Curated function docs for the top-N entry points — **explicitly rejected** (the whole design philosophy of this initiative).
- Coverage of `magpiesets`, `gdx2`, `quitte` — **deferred** until magpie4 scaffolding has been used in 2-3 real sessions and the pattern is validated.

---

## Cross-references

- Memory: `~/.claude/projects/.../memory/project_magpie_agent_initiatives.md` (initiative #3)
- Architectural philosophy: `~/.claude/memory/feedback_synthetic_interventions.md` (one mechanism, not N patches)
- Template: this is an application of the preproc-agent's "lean scaffolding for live source reads" pattern, applied inside magpie-agent rather than preproc-agent. See preproc-agent's `project/version_pins.json` and `scripts/bootstrap_clones.R` for the more-elaborate version of the same pattern.

## When to execute

User has scheduled for a future session ("we'll execute it in a bit"). Phases are sequential; estimated total wall-clock ~1–1.5 hr. Can be split: Phase 1 alone gives a reusable sync script; Phases 2–5 can run in a subsequent session if needed.
