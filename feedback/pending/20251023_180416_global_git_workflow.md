# Feedback: Git Workflow Critical Error

**Type:** Global (Agent Behavior)
**Priority:** HIGH
**Date:** 2025-10-23
**Submitted by:** Claude (AI Agent)

## What Went Wrong

I committed AI documentation files (.claude/commands/) to the **main MAgPIE repository** instead of the **magpie-agent repository**. This directly violated the documented workflow in `/update-claude-md`.

## The Mistake

**What I did:**
```bash
cd /Users/turnip/Documents/Work/Workspace/magpie  # WRONG REPO
git add .claude/commands/
git commit -m "Add slash commands..."
git push  # Failed, but I was about to push to main MAgPIE!
```

**What I should have done:**
```bash
cd /Users/turnip/Documents/Work/Workspace/magpie/magpie-agent  # CORRECT REPO
git add .claude/commands/
git commit -m "Add slash commands..."
git push
```

## Why This Matters

1. **Main MAgPIE repo should NEVER track AI documentation**
   - No CLAUDE.md
   - No .claude/commands/
   - No magpie-agent/ subdirectory
   - No branches or commits for AI docs

2. **magpie-agent is the sole source of truth**
   - All AI documentation lives here
   - All commits happen here
   - All version control happens here

3. **Separation of concerns**
   - Main MAgPIE = model code
   - magpie-agent = AI documentation
   - Never mix them

## Root Cause

**I followed a pattern without thinking:**
- I created files in `/Users/turnip/Documents/Work/Workspace/magpie/.claude/commands/`
- My muscle memory said "commit what you just created"
- I didn't stop to think: "Wait, where should this actually live?"

**I had JUST written the instructions** for the correct workflow but didn't follow my own documentation!

## How to Avoid This in the Future

### 🚨 MANDATORY CHECK Before ANY Git Operation

**Before running `git add`, `git commit`, or `git push`, ask:**

1. **What repository am I in?**
   ```bash
   pwd  # Check current directory
   ```

2. **Is this AI documentation?**
   - If YES → Must be in `magpie-agent/` repository
   - If NO → Can be in main MAgPIE repository

3. **Where should this file live?**
   - CLAUDE.md → `magpie-agent/CLAUDE.md` (commit from magpie-agent)
   - .claude/commands/ → `magpie-agent/.claude/commands/` (commit from magpie-agent)
   - core_docs/, modules/, reference/, cross_module/ → `magpie-agent/` (commit from magpie-agent)
   - MAgPIE model code (*.gms, etc.) → main MAgPIE repository

### Decision Tree

```
About to run git add/commit/push...
  │
  ├─ Is this AI documentation (CLAUDE.md, .claude/, docs/)?
  │  │
  │  ├─ YES → Check: Am I in magpie-agent/ directory?
  │  │  │
  │  │  ├─ YES → ✅ PROCEED
  │  │  └─ NO  → 🛑 STOP! cd to magpie-agent/ first
  │  │
  │  └─ NO → Check: Am I modifying MAgPIE model code?
  │     │
  │     ├─ YES → ✅ PROCEED (but only if authorized)
  │     └─ NO  → ❓ Ask user where this should be committed
```

### Red Flags

🚩 **STOP if you see:**
- `git add CLAUDE.md` from `/Users/turnip/Documents/Work/Workspace/magpie` (should be from magpie-agent)
- `git add .claude/` from main MAgPIE directory (should be from magpie-agent)
- Any attempt to commit AI docs from main MAgPIE repo

### Correct Workflow Template

```bash
# 1. Check where you are
pwd
# Should see: /Users/turnip/Documents/Work/Workspace/magpie/magpie-agent

# 2. If not in magpie-agent, navigate there
cd /Users/turnip/Documents/Work/Workspace/magpie/magpie-agent

# 3. Now commit AI documentation
git add [files]
git commit -m "message"
git push
```

## Action Items

- [x] Undid the incorrect commit to main MAgPIE
- [x] Moved .claude/commands/ to magpie-agent/.claude/commands/
- [x] Committed from magpie-agent repository
- [x] Updated `/update-claude-md` to clarify ALL AI docs live in magpie-agent
- [x] Created this feedback file

## Verification

**Main MAgPIE repo status:**
```
On branch develop
Untracked files:
  CLAUDE.md           ← Correct (should be untracked)
  magpie-agent/       ← Correct (should be untracked)
nothing added to commit
```
✅ Clean - no AI documentation staged or committed

**magpie-agent repo status:**
```
On branch main
Your branch is up to date with 'origin/main'
```
✅ All AI documentation properly committed and pushed

## For Future AI Agents

**Before ANY git operation, read `/update-claude-md` first!**

It exists for exactly this reason. Don't make the same mistake I did by violating the workflow that I literally just documented.

## Lesson Learned

**Having documentation isn't enough - you have to actually use it BEFORE acting, not after making a mistake.**

The `/update-claude-md` command is there for a reason. Use it proactively, not reactively.
