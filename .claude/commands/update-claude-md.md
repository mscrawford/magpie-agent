# Git Workflow for AI Documentation

**When updating CLAUDE.md, slash commands, or any AI documentation, follow this workflow:**

## Critical Rules

1. **ALL AI documentation lives in magpie-agent directory**
   - CLAUDE.md: `magpie-agent/CLAUDE.md`
   - Slash commands: `magpie-agent/.claude/commands/`
   - All other docs: `magpie-agent/` subdirectories

2. **After editing CLAUDE.md, copy it to the main MAgPIE directory** (convenience only):
   ```bash
   cp magpie-agent/CLAUDE.md CLAUDE.md
   ```

3. **Commit and push from the magpie-agent repository ONLY**:
   ```bash
   cd magpie-agent
   git add CLAUDE.md .claude/ [or other files]
   git commit -m "Update [description]"
   git push
   ```

4. **NEVER commit AI documentation from the main MAgPIE repository**
   - The main MAgPIE repository should NOT track CLAUDE.md, .claude/, or magpie-agent/
   - All version control for AI documentation happens in the magpie-agent subrepository
   - No branches, no commits in main MAgPIE for AI docs

## Why This Workflow?

- The magpie-agent repository is the source of truth for all AI documentation
- This keeps documentation changes separate from MAgPIE model code changes
- The main CLAUDE.md is just a convenience copy for the AI to read from the project root

## Full Paths

- **Source of truth**: `/Users/turnip/Documents/Work/Workspace/magpie/magpie-agent/CLAUDE.md`
- **Convenience copy**: `/Users/turnip/Documents/Work/Workspace/magpie/CLAUDE.md`

Always edit the source of truth, then copy to the convenience location.

---

## 🚨 MANDATORY CHECK Before ANY Git Operation

**Before running `git add`, `git commit`, or `git push`, ALWAYS ask:**

### 1. What repository am I in?
```bash
pwd  # Check current directory
```
**Should see:** `/Users/turnip/Documents/Work/Workspace/magpie/magpie-agent`

### 2. Is this AI documentation?
- CLAUDE.md → YES
- .claude/commands/ → YES
- core_docs/, modules/, reference/, cross_module/ → YES
- MAgPIE model code (*.gms, etc.) → NO

### 3. Decision Tree

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

### 🚩 Red Flags - STOP if you see:

- `git add CLAUDE.md` from `/Users/turnip/Documents/Work/Workspace/magpie` (should be from magpie-agent)
- `git add .claude/` from main MAgPIE directory (should be from magpie-agent)
- Any attempt to commit AI docs from main MAgPIE repo
- `pwd` shows you're in wrong directory

### ✅ Correct Workflow Template

```bash
# 1. Check where you are
pwd
# Should see: /Users/turnip/Documents/Work/Workspace/magpie/magpie-agent

# 2. If not in magpie-agent, navigate there FIRST
cd /Users/turnip/Documents/Work/Workspace/magpie/magpie-agent

# 3. Now commit AI documentation
git add [files]
git commit -m "message"
git push
```

## Common Mistake

**DON'T create files in main MAgPIE directory then commit them!**

❌ WRONG:
```bash
# Create file in wrong location
touch /Users/turnip/Documents/Work/Workspace/magpie/.claude/commands/foo.md
cd /Users/turnip/Documents/Work/Workspace/magpie
git add .claude/  # WRONG REPO!
```

✅ CORRECT:
```bash
# Create file in correct location
touch /Users/turnip/Documents/Work/Workspace/magpie/magpie-agent/.claude/commands/foo.md
cd /Users/turnip/Documents/Work/Workspace/magpie/magpie-agent
git add .claude/  # CORRECT REPO!
```
