# Update Command

**Purpose**: Full update pipeline — pull latest agent, sync with MAgPIE develop, then run semantic freshness validation on affected modules.

**When user says**: "/update", "update magpie and the agent", "update everything", "pull and sync", "update the agent", "update magpie", etc.

---

## Overview

This command chains three operations into one seamless pipeline:

1. **Pull** latest magpie-agent (get teammate improvements)
2. **Sync** documentation with MAgPIE develop (detect code changes, update docs)
3. **Semantic freshness** on affected modules (verify updated docs are accurate)

Unlike session startup (which only fetches and counts commits), this command actively updates documentation and validates it.

> 📋 This command runs all three layers of the [maintenance protocol](../helpers/maintenance_protocol.md) in sequence.

## Workflow

### Phase 1: Pull Latest Agent

```bash
# From magpie-agent directory
git pull --rebase origin main
```

Report what changed:
```
📥 Agent updated: [N] new commits pulled
   - [commit summaries]
```

If no new commits:
```
✅ Agent already up to date
```

After pulling, re-deploy AGENT.md:
```bash
cp AGENT.md ../AGENT.md && cp AGENT.md ../CLAUDE.md
```

### Phase 2: Sync with MAgPIE Develop

**Execute the full `/sync` workflow** (read and follow `agent/commands/sync.md`, Steps 1–7).

This will:
- Fetch MAgPIE develop branch
- Diff commits since last sync
- Identify affected modules
- Update module documentation
- Update sync_log.json

**Track which modules were updated** — you'll need this list for Phase 3.

### Phase 3: Semantic Freshness Validation

**This phase runs automatically after sync completes** — do NOT ask the user whether to run it.

**If sync updated any module docs:**

1. Collect the list of module numbers whose docs were modified in Phase 2
2. Run a targeted semantic validation round on those modules:
   - Generate 1-2 cross-module questions that exercise the updated modules
   - Answer using only the AI documentation (as a Sonnet-class agent would)
   - Audit the answers against the actual GAMS source code
   - Report accuracy scores

3. Report results:
```
🔍 Semantic freshness check on updated modules [list]:
   Score: [X]/10
   Issues found: [N] ([details if any])
   
   [If issues found]: Fixed [N] issues in module docs. Run `/validate` to confirm.
   [If clean]: ✅ Updated docs are semantically accurate.
```

4. If bugs are found during the semantic check, fix them immediately and note what was fixed.

**If sync found no changes (no modules updated):**
```
✅ No documentation changes — semantic check not needed.
```

**If only minor changes (comments, formatting, no equation/logic changes):**
```
✅ Changes were cosmetic — semantic check not needed.
```

---

## Output Summary

At the end, provide a consolidated status:

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🔄 Update Complete
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Agent:    [up to date / N commits pulled]
Sync:     [up to date / N modules updated]
Semantic: [skipped / N modules checked, score X/10]
Validator: [32/32 ✅ / X/32 ⚠️]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

## Lessons Learned

*(append-only — add entries from real sessions)*
