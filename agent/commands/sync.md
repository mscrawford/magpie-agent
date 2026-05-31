# Sync Command

**Purpose**: Check for MAgPIE code changes and update documentation accordingly

**When user says**: "/sync", "sync with develop", "check for updates", etc.

---

## Overview

This command performs a **deep sync** between MAgPIE code and agent documentation. Unlike the automatic freshness check at session start (which only counts new commits), this command reads each commit's diff and updates module documentation accordingly.

> 📋 This command is Layer 2 of the [maintenance protocol](../helpers/maintenance_protocol.md). 
> Layer 1 = `/validate` (syntactic). Layer 3 = `/validate-semantic` (semantic accuracy).

## Workflow

### Step 1: Check Current Sync Status

```bash
# Read the sync log
cat project/sync_log.json
```

Report:
- Last sync date and commit
- Any pending updates
- Modules that may be stale

### Step 2: Fetch Latest Commits from MAgPIE

```bash
# From magpie-agent/, fetch CANONICAL MAgPIE develop (magpiemodel/magpie) BY URL
# into a stable ref, then show recent commits. By URL (not a remote name) so this
# works whether the local clone calls canonical 'origin' (direct clone) or
# 'upstream' (fork clone). Read-only: writes one ref, never a branch/working tree.
git -C .. fetch https://github.com/magpiemodel/magpie.git develop:refs/magpie-canonical-develop --force
git -C .. log refs/magpie-canonical-develop --oneline -20 --date=short --format="%h %ad %s"
```

Compare against `sync_status.last_sync_commit` in sync_log.json.

> ⚠️ **Verify against canonical `magpiemodel/magpie` develop (`refs/magpie-canonical-develop`), never the working tree OR the local fork's `origin/develop`.** The agent's docs track the canonical `develop` branch. The surrounding MAgPIE checkout is often on a feature or experiment branch that lags or diverges from develop — AND in a fork-based setup `origin/develop` is the *fork's* develop, which can itself lag canonical. Three consequences:
> - **Read every reference GAMS file via `git -C .. show refs/magpie-canonical-develop:<path>`**, not `../modules/...` directly. A working-tree file may be a stale or divergent version, and reconciling docs against it syncs to the wrong branch. (This generalizes Rule 4 below from citations to *all* reads.)
> - **Size the sweep from canonical develop, filtered to module GAMS**, so feature/analysis-branch noise does not distort the workload:
>   ```bash
>   LAST=$(python3 -c "import json;print(json.load(open('project/sync_log.json'))['sync_status']['last_sync_commit'])")
>   git -C .. log --oneline ${LAST}..refs/magpie-canonical-develop -- 'modules/**/*.gms'   # doc-relevant commits only
>   ```
> - **`/validate` (`validate_consistency.sh`) greps the working tree**, so a clean run proves only internal + working-tree consistency; it CANNOT detect doc-vs-develop drift. Closing that drift is the job of this sync (which reads canonical develop) and the develop-targeted `/validate-semantic` audit, not the syntactic validator.

### Step 3: Identify Changes Requiring Documentation Updates

For each new commit since last sync:

**Check if it affects GAMS modules:**
```bash
git -C .. show <commit> --stat | grep -E "\.gms$"
```

**Categorize the change:**

| Change Type | Doc Update Needed? |
|-------------|-------------------|
| New/modified equations (*.gms) | ✅ YES |
| Changed parameters or domains | ✅ YES |
| New interface variables | ✅ YES |
| Modified module dependencies | ✅ YES |
| R preprocessing scripts (*.R) | ❌ NO |
| Configuration files (*.cfg, *.csv) | ❌ NO |
| Input data version bumps | ❌ NO |
| Changelog updates | ❌ NO |
| Comments-only changes | ❌ NO |

### Step 4: Review Each Relevant Commit

For commits that affect GAMS modules:

```bash
# See what changed (from magpie-agent/)
git -C .. show <commit> -- modules/<module_name>/*.gms
```

**Questions to answer:**
1. Does this change an equation formula?
2. Does this add/remove/modify parameters?
3. Does this change interface variables (vm_*, im_*, pm_*)?
4. Does this affect module dependencies?

### Step 5: Update Documentation

If documentation updates are needed:

1. **Read the current module doc**: `modules/module_XX.md`
2. **Compare with the develop code, read via git** (NOT the working tree -- see the ⚠️ box under Step 2): `git -C .. show refs/magpie-canonical-develop:modules/XX_name/realization/file.gms`
3. **Update the relevant sections**:
   - Equations (if formula changed)
   - Parameters (if added/removed/modified)
   - Interface variables (if changed)
   - Add a note about the update with commit reference

**🔑 Three rules learned from R20 (2026-04-20) semantic validation:**

**Rule 1 — GREP ALL CONSUMERS for new interface parameters.**
When a commit introduces a new `im_`, `pm_`, `fm_`, or `sm_` parameter (or a new `_uncalib` variant, etc.), the driving commit usually documents ONE consumer. Other modules may already consume it or will in the same PR. Before writing the doc, grep the entire codebase:
```bash
grep -rn "<new_parameter_name>" ../modules/ ../core/ --include="*.gms"
```
Enumerate EVERY consumer in the doc. R20-Q1-B1 (Major bug) was caused by documenting only M29 as a consumer of `pm_carbon_density_*_ac_uncalib` when M32 also used them for afforestation and NDC.

**Rule 2 — GREP FOR OLD NAMES after any rename.**
When a variable/scalar/parameter is renamed (e.g., `pm_timber_yield` → `im_growing_stock`), the old name persists in many doc sections that aren't being directly edited — interface tables, modification checklists, testing sections, cross-module references. After updating the "primary" section, grep every affected doc file for the old name:
```bash
grep -rn "<old_name>" modules/module_*.md
```
Update ALL occurrences, then verify with `python3 scripts/check_gams_variables.py`. R20 post-pull had 10 stale references across 5 files because the first-pass doc update missed them.

**Rule 3 — USE ITALICS (not backticks) for deprecated names in historical context.**
The GAMS variable checker matches backtick-wrapped names. When writing "formerly named X" or "previously called X" sentences for deprecated parameters, wrap the deprecated name in `*italics*` rather than `` `backticks` `` so the checker only flags genuinely-orphaned current-tense references. Example:
- ❌ Renamed from `pm_timber_yield` (flags forever since the name no longer exists in GAMS)
- ✅ Renamed from *pm_timber_yield* (clear historical reference, not flagged)

**Rule 4 — CITE LINES FROM THE FINAL MERGED CODE, not intermediate diffs.**
Line numbers in citations should come from reading canonical develop (`refs/magpie-canonical-develop`, or whatever the sync target is) AFTER the pull, not from reading diff output during triage. R20 had 13 line-drift bugs because citations were drafted against diff output. Workflow:
1. Finish all code merging first (pull/fast-forward complete)
2. THEN read the final files to extract citations
3. Run `scripts/check_gams_citations.sh` before committing — it compares doc citations against actual file line counts

**Rule 5 — USE FULL RELATIVE PATHS in file:line citations to avoid ambiguity.**
The citation checker resolves a bare filename to the module's **default realization** (read from `config/default.cfg`); only when no default can be determined does it fall back to walk-order first-match. So a bare `preloop.gms:NN` is checked against the *default-compiled* realization — if you actually mean a NON-default realization (e.g. `detail_apr24/preloop.gms` when the default is `simple_apr24`), the bare cite is measured against the wrong file and will mis-flag. Always write citations as `modules/XX_name/realization_dir/file.gms:NN`, not just `file.gms:NN` or `realization_dir/file.gms:NN`.

### Step 5b: Verify Default Realizations

If any commit changed `config/default.cfg` (realization assignments), run Check 18:

```bash
python3 scripts/check_default_realizations.py
```

This cross-references "(default)" labels in module docs against `config/default.cfg` and flags mismatches. If a default realization changed in code, update the corresponding `modules/module_XX.md` header.

### Step 6: Update Sync Log

After reviewing/updating, update `project/sync_log.json`:

```json
{
  "sync_status": {
    "last_sync_date": "YYYY-MM-DD",
    "last_sync_commit": "<commit_hash>",
    "last_sync_commit_date": "YYYY-MM-DD",
    "last_sync_commit_message": "<message>",
    "synced_by": "AI agent",
    "magpie_branch": "develop"
  }
}
```

Add entry to `recent_syncs` array with details of what was reviewed.

### Step 6b: Assess Change Impact

For each updated module doc, classify the change:

| Change Type | Impact | Semantic Re-validation? |
|-------------|--------|------------------------|
| New/changed equations | High | Yes — equation formulations may be wrong |
| New realization added | High | Yes — realization descriptions needed |
| Variable renamed/added | Medium | Yes if interface variable (vm_, pm_) |
| Parameter default changed | Medium | Check if helpers reference old default |
| Input file changed only | Low | No — docs reference logic, not data |
| Comment/formatting only | None | No |

Track changes in sync_log.json with a new field:
```json
{
  "modules_updated": ["14", "29"],
  "change_impact": "high",
  "semantic_validation_recommended": true,
  "semantic_validation_done": false
}
```

### Step 7: Report Results

Present a summary:

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✨ Sync Complete!
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📅 Previous sync: <date> (commit <hash>)
📅 Current sync: <date> (commit <hash>)

📝 Commits reviewed: X
   - Y commits with GAMS changes
   - Z documentation updates made

📋 Modules updated:
   - module_32.md: Updated equation q32_cost_establishment

📋 No update needed:
   - Config changes only: 3 commits
   - R scripts only: 1 commit

🎯 Status: Documentation is current with develop branch
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

### Step 8: Recommend Semantic Validation

After sync completes, check if semantic validation is warranted:

**Triggers for recommendation**:
- 3+ module docs were updated during this sync
- Any equation formulations were changed
- New realizations were added
- Config defaults changed that affect helper docs

**If triggered**, report to user:
```
📋 Sync updated [N] module docs. Recommend running targeted semantic validation:
   /validate-semantic --modules [list of updated module numbers]
   
   This will verify the updated docs still produce accurate answers (~15 min).
```

**If NOT triggered** (minor changes only):
```
✅ Sync complete. Changes were minor — semantic re-validation not needed.
```

---

## Quick Sync (No Changes)

If no new commits since last sync:

```
✅ Documentation is up to date!

Last sync: <date> (commit <hash>)
No new commits on develop branch since last sync.
```

---

## Handling Large Gaps

If many commits since last sync (>20):

1. Focus on **merge commits** first (they summarize feature branches)
2. Look for commits with "equation", "fix", "module" in message
3. Prioritize high-impact modules (10, 11, 17, 56 - high centrality)
4. Consider running full module verification for heavily changed modules

---

## Commit Message Patterns to Watch

**High priority** (likely needs doc update):
- "fix equation", "bugfix", "formula"
- "add parameter", "new variable"
- "module XX" (any module reference)

**Medium priority** (check the diff):
- "update", "modify", "change"
- "refactor"

**Low priority** (usually no doc update):
- "changelog", "version", "release"
- "config", "scenario"
- "input data", "calibration"
- "R script", "preprocessing"

---

## Related Files

- `project/sync_log.json` - Sync tracking data
- `modules/module_XX.md` - Module documentation to update
- `core_docs/Module_Dependencies.md` - If dependencies change

---

**Remember**: The goal is to keep documentation accurate. When in doubt, check the code!
