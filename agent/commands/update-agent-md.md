# Update Agent MD Command

**Purpose**: Git workflow for AI documentation updates

**When user says**: "run command: update-agent-md", "how do I update AGENT.md", "git workflow for docs", etc.

---

## Critical Rules

1. **ALL AI documentation lives in magpie-agent directory**
   - AGENT.md: `magpie-agent/AGENT.md`
   - Commands: `magpie-agent/agent/commands/`
   - All other docs: `magpie-agent/` subdirectories

2. **After editing AGENT.md, copy it to the main MAgPIE directory** (convenience only):
   ```bash
   cp AGENT.md ../AGENT.md
   ```

3. **Commit and push from the magpie-agent repository ONLY**:
   ```bash
   cd magpie-agent
   git add AGENT.md agent/ [or other files]
   git commit -m "Update [description]"
   git push
   ```

4. **NEVER commit AI documentation from the main MAgPIE repository**
   - The main MAgPIE repository should NOT track AGENT.md or magpie-agent/
   - All version control for AI documentation happens in the magpie-agent subrepository
   - No branches, no commits in main MAgPIE for AI docs

## Why This Workflow?

- The magpie-agent repository is the source of truth for all AI documentation
- This keeps documentation changes separate from MAgPIE model code changes
- The main AGENT.md is just a convenience copy for the AI to read from the project root

## Full Paths

- **Source of truth**: `magpie-agent/AGENT.md`
- **Convenience copy**: `../AGENT.md` (in parent MAgPIE directory)

Always edit the source of truth, then copy to the convenience location.

---

## 🚨 MANDATORY CHECK Before ANY Git Operation

**Before running `git add`, `git commit`, or `git push`, ALWAYS ask:**

### 1. What repository am I in?
```bash
pwd  # Check current directory
```
**Should see:** `.../magpie/magpie-agent`

### 2. Is this AI documentation?
- AGENT.md → YES
- agent/commands/ → YES
- core_docs/, modules/, reference/, cross_module/ → YES
- MAgPIE model code (*.gms, etc.) → NO

### 3. Decision Tree

```
About to run git add/commit/push...
  │
  ├─ Is this AI documentation (AGENT.md, agent/, docs/)?
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

- `git add AGENT.md` from the main magpie directory (should be from magpie-agent)
- `git add agent/` from main MAgPIE directory (should be from magpie-agent)
- Any attempt to commit AI docs from main MAgPIE repo
- `pwd` shows you're in wrong directory

### ✅ Correct Workflow Template

```bash
# 1. Check where you are
pwd
# Should see: .../magpie/magpie-agent

# 2. If not in magpie-agent, navigate there FIRST
cd magpie-agent  # or full path

# 3. Now commit AI documentation
git add [files]
git commit -m "message"
git push

# 4. Copy to parent for convenience
cp AGENT.md ../AGENT.md
```

## Common Mistake

**DON'T create files in main MAgPIE directory then commit them!**

❌ WRONG:
```bash
# Create file in wrong location
touch ../agent/commands/foo.md
cd ..
git add agent/  # WRONG REPO!
```

✅ CORRECT:
```bash
# Create file in correct location
touch agent/commands/foo.md
git add agent/  # CORRECT REPO!
```
