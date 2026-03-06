# Helper: Session Startup Context

**Auto-load triggers**: ALWAYS — load at every session start (not keyword-triggered)
**Last updated**: 2026-03-06
**Lessons count**: 0 entries

---

## Purpose

This helper gives the agent **situational awareness** about the user's MAgPIE environment. Run these checks silently at session start. Store findings internally and surface only when relevant to the user's question.

## Startup Checklist

Run these checks at the beginning of every session. Report a brief status line to the user in your greeting.

### 1. MAgPIE Version & Branch

```bash
# Check version
cat ../CITATION.cff | grep "^version:" | head -1
# Check branch
cd .. && git rev-parse --abbrev-ref HEAD
# Check current commit
cd .. && git --no-pager log --oneline -1
```

**What to look for:**
- Version number (e.g., `4.13.0-dev`)
- Branch name (`develop` = active development, `master` = release)
- Recent commit message (gives context on what's being worked on)

### 2. Documentation Sync Freshness

```bash
# Last sync point (from magpie-agent)
python3 -c "import json; d=json.load(open('project/sync_log.json')); s=d['sync_status']; print(f'Last sync: {s[\"last_sync_date\"]} at commit {s[\"last_sync_commit\"]}')"
# Commits since last sync
cd .. && git --no-pager log --oneline ce6e1a89a..HEAD | wc -l
```

**Staleness assessment:**
| Commits behind | Days since sync | Badge | Action |
|---------------|----------------|-------|--------|
| 0-5 | <14 days | 🟢 Current | None needed |
| 6-20 | 14-30 days | 🟡 Aging | Mention to user, suggest `/sync` |
| 21+ | >30 days | 🔴 Stale | Warn user, recommend sync before trusting docs |

**Report format:** `📊 Docs synced: [badge] (X commits behind, last sync YYYY-MM-DD)`

### 3. Recent Model Runs

```bash
# Check for recent output directories
ls -dt ../output/*/ 2>/dev/null | head -3
```

**What to report:**
- If `output/` has recent runs → note them (title, approximate date)
- If empty → note "No recent runs detected"
- If a run appears to have failed → flag it proactively

### 4. R Environment

```bash
# Check if renv is configured
[ -f ../renv.lock ] && echo "renv: configured" || echo "renv: not found"
# Key package versions
python3 -c "
import json
with open('../renv.lock') as f:
    d = json.load(f)
for pkg in ['magpie4', 'gms', 'magclass', 'madrat']:
    if pkg in d.get('Packages', {}):
        print(f'  {pkg}: {d[\"Packages\"][pkg][\"Version\"]}')
" 2>/dev/null
```

### 5. Current Configuration

```bash
# Check key scenario settings from config/default.cfg
grep -E "^cfg\$gms\$c56_pollutant_prices|^cfg\$gms\$c15_food_scenario|^cfg\$gms\$c21_trade_liberalization" ../config/default.cfg 2>/dev/null | head -5
```

---

## How to Report

In your session greeting, include a brief status line:

```
📊 MAgPIE 4.13.0-dev on develop | Docs: 🟢 synced (0 commits behind) | Runs: 2 recent
```

If there are issues, add specific notes:
```
⚠️ Documentation is 🔴 15 commits behind code — consider running /sync
⚠️ Most recent run (output/SSP2_carbon/) appears to have failed (modelstat ≠ 2)
```

---

## When to Surface Findings

- **Always**: Version, branch, sync status (one-liner in greeting)
- **If user asks about results**: Mention detected runs
- **If user asks about a module**: Check if that module's docs were updated since last verification
- **If docs are stale**: Warn before answering code-specific questions

---

## Lessons Learned
<!-- APPEND-ONLY: Add new entries at the bottom. Never remove old ones. -->
<!-- Format: - YYYY-MM-DD: [lesson] (source: [user feedback | session experience]) -->
