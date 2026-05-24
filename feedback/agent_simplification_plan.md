# Agent simplification: drop /feedback machinery + rename `feedback/` → `audit/`

**Created**: 2026-05-24
**Origin**: User decisions on 2026-05-24:
  1. "Colleagues don't use the feedback mechanism... I don't want the capability. I'd prefer to continue iterating with our system, rather than having external PRs to integrate."
  2. "I'd like to eventually rename it though. I like audit."

**Estimated effort**: 1–1.5 hours wall-clock, ~60–80K tokens (Phase A ~30 min + Phase B ~45 min)
**Tier**: Single sweep, two clean commits

---

## Goal

Reduce the agent's surface to match its actual use pattern:
- Drop the **external user-feedback collection** capability (`/feedback` command + `feedback/pending/` submission inbox + the "submit feedback" prompt path).
- Rename the directory `feedback/` → `audit/` to reflect its actual contents (validation rounds, pipeline audits, plans, rubrics, registries — all internal iteration artifacts, not user-submitted feedback).

This is **not** a scope reduction of iteration capability. The agent will continue to:
- Run semantic-validation flywheel rounds (now `/validate-semantic` → results land in `audit/validation_rounds.json`)
- Run multi-lens pipeline audits (`/pipeline-audit` → `audit/pipeline_audit_rounds.json`)
- Append systemic lessons to `audit/global/agent_lessons.md` when corrections surface during normal sessions (the agent-side write path stays; only the external-user-submission path goes away)
- Maintain ledgers/registries (`audit/renames.json`, `audit/probe_dedup_ledger.json`, `audit/advisory_allowlist.json`)
- Use the same workflow we've been using

## Motivation

1. **Empirical**: zero formal feedback submissions exist in `feedback/pending/` (only a README). Colleagues don't engage with the formal submission flow.
2. **Workflow fit**: the working pattern has been *agent-and-user iteration*, not external-PR review of feedback submissions. Every doc fix in R3, R22, R23, and pipeline-audit rounds came from the agent-user loop, not from `/feedback`-submitted entries.
3. **Naming accuracy**: `feedback/` was named for the user-submission flow. With that gone, the directory's contents (rounds, rubrics, plans, audits) are categorically *audit artifacts*. The user's "audit" preference matches the actual contents.

## Non-goals

- **Don't** remove the internal write-path to `audit/global/agent_lessons.md`. The agent still records systemic lessons during sessions; only the formal user-submission inbox is removed.
- **Don't** rename `feedback/` in any external systems (e.g., colleagues' personal forks, the magpie-preproc-agent repo). The rename is local to magpie-agent.
- **Don't** restructure `audit/` internals during this pass. Just rename the top-level directory; sub-structure stays as-is.

---

## Phase A: Remove `/feedback` machinery (~30 min, ~30K tokens)

### Files to delete

- `agent/commands/feedback.md` (77 lines — the slash-command spec)
- `feedback/pending/` (subdirectory + its README; empty of submissions)

### Files to edit

| File | Change |
|------|--------|
| `AGENT.md` | Remove "🔄 User Feedback System" section (~30 lines, around line ~750). Remove `/feedback` row from the Command-System table. Remove "/feedback is also available" line from the greeting template. |
| `agent/commands/guide.md` | Remove `/feedback` mention from the user-facing command list. |
| `agent/commands/bootstrap.md` | Remove first-time-user reference to `/feedback`. |
| `core_docs/Tool_Usage_Patterns.md` | Remove the "submit /feedback" suggestion (1 occurrence). |
| `core_docs/Response_Guidelines.md` | Remove the "remind user about /feedback" guidance (3 occurrences). |
| `agent/commands/validate-semantic.md` + `agent/commands/pipeline-audit.md` | Audit for any "/feedback" mention (likely none; these reference `feedback/` as a path, not the command — that's Phase B's job). |

### Acceptance

- `grep -r "/feedback\b" --include="*.md" .` returns no hits.
- `grep -r "submit feedback\|formal feedback\|User Feedback System" --include="*.md" .` returns no hits.
- Validator stays 40/40 + advisory allowlist clean.

### Commit

Single commit: `simplify: remove /feedback command + external-submission machinery`

---

## Phase B: Rename `feedback/` → `audit/` (~45 min, ~40K tokens)

### Why a separate phase

Phase A removes a chunk of the surface (deletes `agent/commands/feedback.md`, `feedback/pending/`, edits ~6 doc files). Doing Phase A first means Phase B's rename doesn't have to update files that no longer exist. Two clean commits beat one tangled one.

### Inventory (counted 2026-05-24, pre-Phase-A)

- **43 files** outside `feedback/` reference `feedback/` as a path
- **100+ individual references** when including archives, scripts, JSON registries
- Memory hits (in `~/.claude/`):
  - `~/.claude/memory/rename_ledger_defensive_infra.md` (mentions `feedback/renames.json`)
  - `~/.claude/projects/.../memory/template_verifier_mandate_flywheel.md` (mentions validation_rounds.json + flywheel_rubric in feedback/)
  - NOT `feedback_run_gates_after_last_edit.md` — that's a memory-TYPE prefix, not a path reference

### Steps

1. **Move the directory** (preserves git history for each file):
   ```
   git mv feedback audit
   ```

2. **Sed-replace path-form references** across docs/scripts/JSON:
   ```
   # macOS sed needs '' after -i
   find . -type f \( -name "*.md" -o -name "*.py" -o -name "*.sh" -o -name "*.json" \) \
     -not -path "./.git/*" -not -path "./.cache/*" \
     -exec sed -i '' 's|feedback/|audit/|g' {} +
   ```

   This is safe because the search pattern `feedback/` (with trailing slash) is unambiguously path-form. The word "feedback" without slash (in prose like "if you receive feedback from hooks") is left alone.

3. **Review residual "feedback" mentions** in prose:
   - `grep -rni "feedback" --include="*.md" .` — review remaining occurrences
   - Update where they refer to the (now-renamed) directory specifically. Most prose uses of "feedback" should now read "audit" (e.g., "feedback flow" → "audit flow"). Leave alone where "feedback" means the general concept (hook feedback, user feedback during conversation, etc.).
   - Target: ~10–20 manual edits after the sed pass

4. **Update memory files**:
   - `~/.claude/memory/rename_ledger_defensive_infra.md` — `feedback/renames.json` → `audit/renames.json`
   - `~/.claude/projects/.../memory/template_verifier_mandate_flywheel.md` — `feedback/...` paths → `audit/...`

5. **Validator + check linkage**:
   - `bash scripts/validate_consistency.sh` — must hold 40/40
   - `python3 scripts/check_param_defaults.py` — must read `audit/advisory_allowlist.json` (sed will have rewritten the constant)
   - `python3 scripts/check_multi_section_consistency.py` — same
   - `python3 scripts/check_renames.py` — must read `audit/renames.json`
   - `python3 scripts/probe_dedup_check.py` — must read `audit/probe_dedup_ledger.json`
   - `python3 scripts/refresh_aggregate_counts.py` — must read `audit/validation_rounds.json`

6. **Update validate_consistency.sh internals**:
   - `REPORT_DIR=".cache/validation_reports"` doesn't reference `feedback/` (already gitignored under .cache/), no change needed
   - But the script reads/greps from `feedback/` in places — sed handles those
   - Check for any heredoc / quoted paths the sed missed

### Acceptance

- `git ls-files | xargs grep -l "feedback/" | grep -v "feedback" | head` returns empty
- Validator + all 5 Python checkers run cleanly against `audit/`
- `ls feedback/ 2>&1` returns "No such file or directory"
- `ls audit/` shows all the migrated contents

### Commit

Single commit: `rename: feedback/ → audit/ (matches actual contents — rounds, rubrics, plans, ledgers)`

Likely 50+ files changed; a big diff but mostly mechanical path rewrites.

---

## Ordering rationale

A then B, because:
- A deletes files (`agent/commands/feedback.md`, `feedback/pending/`); if B ran first, A would have to operate on `audit/pending/` and `agent/commands/feedback.md` (weird mix).
- A doesn't touch any path references (it only deletes the user-feedback machinery surface); B can do its sed cleanly knowing all remaining `feedback/` references are legitimate paths.
- Each commit stands alone: A is reviewable as "we dropped the formal feedback inbox"; B is reviewable as "we renamed the directory".

## Risks

1. **Sed catches false positives.** Some prose uses "feedback/..." metaphorically. Mitigation: pre-sed grep to inspect all matches, do a one-pass review of high-density files after sed.
2. **Scripts hardcode old path.** `check_param_defaults.py` has `os.path.join(AGENT_DIR, "feedback", "advisory_allowlist.json")` — the sed pattern matches "feedback/" only, not "feedback" alone. **Need to verify** the Python path constructions before/after.

   *Pre-flight check*: grep for `"feedback"` (quoted, no slash) in `.py` and `.sh` files. Hits are likely path components that need manual fixing.

3. **Memory in `~/.claude/` won't auto-update** with the repo rename. Manual edits required as listed in step 4.
4. **External callers may break**: e.g., if the user has shell aliases, bash history with `cd feedback/`, or git hooks referencing `feedback/`. Out of scope to fix; just flag.
5. **Sync log might cite old paths**: `project/sync_log.json` and similar config files may have path references. The sed catches them.

## Verification at the end

- `bash scripts/validate_consistency.sh`: 40/40 passed, 3 advisory allowlisted, 0 warnings.
- `ls audit/`: shows validation_rounds.json, flywheel_rubric.md, renames.json, probe_dedup_ledger.json, advisory_allowlist.json, magpie4_scaffolding_plan.md, agent_simplification_plan.md, round*.md, pipeline_audit_round*.md, global/agent_lessons.md, archive/, etc.
- `grep -r "feedback/" --include="*.md" --include="*.py" --include="*.sh" --include="*.json" . | grep -v ".cache"`: zero hits (or only legitimate non-path prose).
- All five Python checkers run cleanly.
- Manual: ask the agent a question that loads a helper; verify it cites paths as `audit/...` correctly.

---

## What stays the same

- **The internal iteration loop**: agent observes during sessions → appends corrections to module notes / agent_lessons.md → user runs validators / flywheel / pipeline-audit → bug fixes commit. All this continues unchanged, just under `audit/` paths.
- **The flywheel architecture**: regression questions, anti-confabulation MANDATEs, validator suite, allowlist convention — unchanged.
- **Cross-agent boundaries**: magpie-preproc-agent has its own `feedback/` directory (under its own repo). We're NOT renaming that. The two agents stay independent.

## Cross-references

- Queued initiative memory: `~/.claude/projects/.../memory/project_magpie_agent_initiatives.md` (add this plan as initiative #4 after execution, OR fold into #3 if executed in the same session as magpie4 scaffolding)
- Sibling plan: `audit/magpie4_scaffolding_plan.md` (will already use the `audit/` path after this rename lands)
- Validator: `scripts/validate_consistency.sh` (must not break)

## When to execute

Both phases can run in one session. Phase A is the smaller half; B is the more mechanical-but-large half. Useful to pair with another agent-improvement session (e.g., when executing magpie4 scaffolding — the two together would be ~3 hours but produce a much cleaner agent state).
