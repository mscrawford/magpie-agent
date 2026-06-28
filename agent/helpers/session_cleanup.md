# Helper: Session Cleanup (end-of-session checklist)

**Auto-load triggers**: "goodbye", "wrapping up", "done for now", "close session", "session over", "ending session", "commit learnings"
**Lessons count**: 0 entries

---

## Purpose

End-of-session checklist for committing accumulated learning back to the magpie-agent repo. Hoisted from AGENT.md in R6 to free always-loaded surface (the section was ~55 lines of end-of-session-only content loading on every session).

**Canonical source**: the user's global `session-close` skill is the primary end-of-session mechanism (it triggers automatically when the user says they're wrapping up). This helper is the fallback walkthrough for situations where the skill isn't loaded, AND it surfaces the magpie-agent-specific learning-capture conventions.

---

## 1. Show Learning Summary to User

If any learning occurred during the session, show:

```
🧠 Session learnings:
  • [Recorded correction about X → Y]
  • [Added warning to module_58_notes.md about peatland infeasibility]
  • [Discovered new pattern: ...]

These will be saved to the magpie-agent repository so future sessions benefit.
Want me to commit and push? (You can review the changes first if you prefer.)
```

If no learning occurred, skip this — don't show an empty summary.

## 2. Commit Accumulated Learning

Check if you made any of these during the session:
- Appended entries to any helper's `## Lessons Learned` section
- Created or updated a `modules/module_XX_notes.md` file
- Discovered and recorded a user correction
- Updated `audit/global/agent_lessons.md`

If YES → show the user what changed, then **pull, commit, and push** to the magpie-agent repo:

```bash
cd magpie-agent/
git pull --rebase origin main   # ← CRITICAL: merge teammates' changes first
git add -A
git commit -m "learn: session learnings — [brief description]

Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>"
git push origin main
```

**Ask the user before pushing** — they may want to review the changes first.

**If `git pull --rebase` creates a merge conflict**: show the user the conflicting file(s) and ask how to resolve. For append-only files (notes, lessons), the resolution is almost always "keep both entries."

## 2a. Pre-push secret / PII gate (REQUIRED before every push)

This repo is **PUBLIC** (so is the preproc-agent repo, and the parent's `magpiemodel/magpie` upstream) — committed content, including history, is world-readable. **Before `git push`**, scan the staged diff for secrets and local paths:

```bash
git diff --cached -U0 | grep -nE '\-\-\-\-\-BEGIN[A-Z ]*PRIVATE KEY|sk-ant-[A-Za-z0-9_-]{16,}|gh[posru]_[A-Za-z0-9]{30,}|github_pat_|AKIA[0-9A-Z]{16}|xox[baprs]-|AIza[0-9A-Za-z_-]{30,}|/Users/[A-Za-z0-9._-]+|/home/[A-Za-z0-9._-]+|(password|api[_-]?key|secret|access[_-]?token)\s*[:=]' \
  && echo "⚠️  REVIEW the matches above — do NOT push secrets or local absolute paths" \
  || echo "✅ pre-push scan clean"
```

- Any **secret/credential** match → stop, remove it, and if it was ever committed treat it as compromised (rotate the credential; a force-push/history-rewrite does not un-leak a pushed secret).
- Any **`/Users/...` or `/home/...`** match → replace with `<magpie-root>`, `~`, or a relative path before committing (keeps the public history free of local layout). For frozen archive logs, this is advisory.
- This gate is a safety net, not a substitute for not writing secrets in the first place.

## 3. Flag Documentation Gaps

If during the session you noticed:
- A helper was loaded but **lacked critical information** → note what was missing in the helper's Lessons Learned
- A user question had **no matching helper** and would have benefited from one → mention it: "💡 This workflow could benefit from a dedicated helper. Want me to create one?"
- Module documentation was **wrong or outdated** → update the `modules/module_XX_notes.md` with a warning

## 4. Deploy AGENT.md (if changed)

If you modified AGENT.md itself during the session:

```bash
cp AGENT.md ../AGENT.md && cp AGENT.md ../CLAUDE.md
```

(Validator's Check 10 will fail if AGENT.md drifts from its deployed copies.)

---

## Cross-references

- User's global `session-close` skill — the primary trigger; this helper is the fallback.
- `agent/helpers/maintenance_protocol.md` §5 Class-level rules — captures patterns worth recording globally.
- `AGENT.md` "Internal iteration loop" section — the agent-side write paths (notes / Lessons Learned / agent_lessons.md).

## Lessons Learned

<!-- APPEND-ONLY: Add new entries at the bottom. Never remove old ones. -->
<!-- Format: - YYYY-MM-DD: [lesson] (source: [user feedback | session experience]) -->
