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

(Validator's Check 23 will fail if AGENT.md drifts from its deployed copies.)

---

## Cross-references

- User's global `session-close` skill — the primary trigger; this helper is the fallback.
- `agent/helpers/maintenance_protocol.md` §5 Class-level rules — captures patterns worth recording globally.
- `AGENT.md` "Internal iteration loop" section — the agent-side write paths (notes / Lessons Learned / agent_lessons.md).

## Lessons Learned

<!-- APPEND-ONLY: Add new entries at the bottom. Never remove old ones. -->
<!-- Format: - YYYY-MM-DD: [lesson] (source: [user feedback | session experience]) -->
