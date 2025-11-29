# Sync Command

**Purpose**: Check for MAgPIE code changes and update documentation accordingly

**When user says**: "run command: sync", "sync with develop", "check for updates", etc.

---

## Overview

This command helps keep the agent documentation synchronized with the MAgPIE codebase. It reviews recent commits to the develop branch and identifies which changes require documentation updates.

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
# Navigate to MAgPIE repo and get recent commits
cd ..
git fetch origin develop
git log origin/develop --oneline -20 --date=short --format="%h %ad %s"
```

Compare against `sync_status.last_sync_commit` in sync_log.json.

### Step 3: Identify Changes Requiring Documentation Updates

For each new commit since last sync:

**Check if it affects GAMS modules:**
```bash
git show <commit> --stat | grep -E "\.gms$"
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
# See what changed
git show <commit> -- modules/<module_name>/*.gms
```

**Questions to answer:**
1. Does this change an equation formula?
2. Does this add/remove/modify parameters?
3. Does this change interface variables (vm_*, im_*, pm_*)?
4. Does this affect module dependencies?

### Step 5: Update Documentation

If documentation updates are needed:

1. **Read the current module doc**: `modules/module_XX.md`
2. **Compare with actual code**: `../modules/XX_name/realization/*.gms`
3. **Update the relevant sections**:
   - Equations (if formula changed)
   - Parameters (if added/removed/modified)
   - Interface variables (if changed)
   - Add a note about the update with commit reference

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

### Step 7: Report Results

Present a summary:

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✨ Sync Complete!
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📅 Previous sync: 2025-11-29 (commit 3e0478c83)
📅 Current sync: 2025-MM-DD (commit <new_hash>)

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

---

## Quick Sync (No Changes)

If no new commits since last sync:

```
✅ Documentation is up to date!

Last sync: 2025-11-29 (commit 3e0478c83)
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
