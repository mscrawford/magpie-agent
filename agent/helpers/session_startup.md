# Helper: Session Startup Context

**Auto-load triggers**: ALWAYS — load at every session start (not keyword-triggered)
**Last updated**: 2026-03-06
**Lessons count**: 0 entries

---

## Purpose

This helper gives the agent **situational awareness** about the user's MAgPIE environment. Run these checks silently at session start. Store findings internally and surface only when relevant to the user's question.

## Startup Checklist

Run these checks at the beginning of every session. Report a brief status line to the user in your greeting.

### 0. Pull Latest Agent & MAgPIE Code

**Do this silently before anything else:**

```bash
# Determine working directory (could be magpie/ or magpie-agent/)
# Use absolute paths to avoid cd breaking relative references
if [ -f "AGENT.md" ] && [ -d "agent/helpers" ]; then
  AGENT_DIR="$(pwd)"
  MAGPIE_DIR="$(cd .. && pwd)"
elif [ -d "magpie-agent" ]; then
  AGENT_DIR="$(cd magpie-agent && pwd)"
  MAGPIE_DIR="$(pwd)"
else
  echo "Warning: Cannot determine magpie-agent location"
fi

# Pull latest magpie-agent (teammates may have pushed improvements)
cd "$AGENT_DIR" && git pull --rebase origin main 2>/dev/null
# Re-deploy AGENT.md to both targets (CLAUDE.md is what Claude loads!)
cp "$AGENT_DIR/AGENT.md" "$MAGPIE_DIR/AGENT.md" 2>/dev/null
cp "$AGENT_DIR/AGENT.md" "$MAGPIE_DIR/CLAUDE.md" 2>/dev/null
# Fetch latest MAgPIE develop (so we can detect new commits)
cd "$MAGPIE_DIR" && git fetch origin develop --quiet 2>/dev/null
```

**Why**: Team members push corrections, new helpers, and lessons learned to magpie-agent. Without this step, you'd be working with stale documentation. The MAgPIE fetch (not pull) lets us count new commits without changing the user's working tree.

**Note**: The script handles both possible working directories (magpie/ or magpie-agent/) since the AI tool may start in either location.

### 1. MAgPIE Version & Branch

**Note**: Steps 1-5 assume the agent's working directory is `magpie-agent/` (as stated in AGENT.md). All `../` paths point to the parent MAgPIE directory.

```bash
# From magpie-agent/ directory:
cat ../CITATION.cff | grep "^version:" | head -1
git -C .. rev-parse --abbrev-ref HEAD
git -C .. --no-pager log --oneline -1
```

**What to look for:**
- Version number (e.g., `4.13.0-dev`)
- Branch name (`develop` = active development, `master` = release)
- Recent commit message (gives context on what's being worked on)

### 2. Documentation Sync Freshness

```bash
# Last sync point (from magpie-agent)
LAST_SYNC=$(python3 -c "import json; d=json.load(open('project/sync_log.json')); print(d['sync_status']['last_sync_commit'])" 2>/dev/null)
echo "Last sync commit: ${LAST_SYNC}"
# Commits since last sync (use the dynamic value, NOT a hardcoded hash)
git -C .. --no-pager log --oneline ${LAST_SYNC}..HEAD 2>/dev/null | wc -l
```

**Staleness assessment:**
| Commits behind | Days since sync | Badge | Action |
|---------------|----------------|-------|--------|
| 0-5 | <14 days | 🟢 Current | None needed |
| 6-20 | 14-30 days | 🟡 Aging | Mention to user, suggest `/sync` |
| 21+ | >30 days | 🔴 Stale | Warn user, recommend sync before trusting docs |

**Report format:** `📊 Docs synced: [badge] (X commits behind, last sync YYYY-MM-DD)`

### Step 2b: Semantic Validation Freshness

Check when the last semantic validation round was run:

```bash
# From magpie-agent directory (do NOT cd)
python3 -c "
import json, datetime
with open('feedback/validation_rounds.json') as f:
    data = json.load(f)
rounds = data.get('rounds', [])
if rounds:
    last = rounds[-1]
    last_date = last.get('date', 'unknown')
    last_score = last.get('mean_score', 'N/A')
    last_bugs = last.get('total_bugs', 0)
    critical = last.get('critical_bugs', 0)
    print(f'Last validation: {last_date} (R{len(rounds)})')
    print(f'Score: {last_score}/10, Bugs: {last_bugs} ({critical} critical)')
    # Check if overdue (>90 days)
    try:
        d = datetime.datetime.strptime(last_date, '%Y-%m-%d')
        days = (datetime.datetime.now() - d).days
        print(f'Days since: {days}')
        if days > 90: print('STATUS: OVERDUE')
        elif days > 60: print('STATUS: DUE_SOON')
        else: print('STATUS: OK')
    except: print('STATUS: UNKNOWN')
else:
    print('No validation rounds found')
    print('STATUS: NEVER_RUN')
"
```

**Reporting**:
- If STATUS=OK: Include in one-liner: `Semantic: 🟢 R13 (8.6/10)`
- If STATUS=DUE_SOON: `Semantic: 🟡 last validated [N] days ago`
- If STATUS=OVERDUE: `Semantic: 🔴 overdue ([N] days) — suggest /validate-semantic`
- If last round had Critical bugs: Always warn regardless of date

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

### Step 6: Maintenance Status Summary

Combine all checks into a maintenance health assessment:

| Check | Status | Action if Yellow/Red |
|-------|--------|---------------------|
| Code sync | 🟢/🟡/🔴 | Run `/sync` |
| Syntactic validator | ✅/❌ | Run `/validate` |
| Semantic validation | 🟢/🟡/🔴 | Run `/validate-semantic` |
| AGENT.md deployment | ✅/❌ | `cp AGENT.md ../AGENT.md && cp AGENT.md ../CLAUDE.md` |

**Surface in greeting ONLY if any check is 🟡 or 🔴**:
```
⚠️ Maintenance: [list yellow/red items]
```

If all green, just show the one-liner — don't clutter the greeting.

---

## How to Report

In your session greeting, include a brief status line:

```
📊 MAgPIE 4.13.0-dev on develop | Docs: 🟢 synced (0 commits behind) | Semantic: 🟢 R13 (8.6/10) | Runs: 2 recent
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
