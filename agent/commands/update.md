# Update Command

**Purpose**: Pull latest changes from magpie-agent repository and re-deploy AGENT.md

**When user says**: "run command: update", "update the docs", "pull latest", etc.

---

## What This Does

1. **Checks current repository status** - Verifies we're in the magpie-agent directory
2. **Pulls latest changes** - Fetches and merges from origin/main
3. **Handles conflicts** - Provides guidance if merge conflicts occur
4. **Re-deploys AGENT.md** - Copies updated AGENT.md to parent magpie directory
5. **Verifies deployment** - Confirms files are in sync

## When to Use This

- **Start of session** - Get the latest documentation updates
- **After someone else updates docs** - Sync with team changes
- **Before answering questions** - Ensure you have current information
- **Testing new features** - Pull newly added commands or documentation

## Execution

Please execute the following steps:

### Step 1: Verify Location and Git Status

```bash
# Show current directory
pwd

# Show git status
git status

# Show current branch
git branch
```

### Step 2: Check for Uncommitted Changes

If there are uncommitted changes, ask the user:
- "You have uncommitted changes. Would you like to stash them, commit them, or cancel the update?"

Handle based on user response:
- **Stash**: `git stash push -m "Auto-stash before update $(date +%Y%m%d_%H%M%S)"`
- **Commit**: Guide user through commit process
- **Cancel**: Exit update process

### Step 3: Pull Latest Changes

```bash
# Pull from origin/main
git pull origin main --no-edit
```

**If pull succeeds:**
- ✅ Proceed to Step 4

**If merge conflicts occur:**
- ❌ Report conflicted files: `git status --short | grep "^UU\|^AA\|^DD"`
- Provide conflict resolution instructions:
  ```
  Merge conflicts detected in:
  [list files]

  To resolve:
  1. Edit the conflicted files
  2. Remove conflict markers (<<<<<<, =======, >>>>>>>)
  3. Run: git add <resolved-files>
  4. Run: git commit
  5. Re-run update command
  ```
- Exit and wait for user to resolve

**If stashed changes exist:**
- Restore them: `git stash pop`
- If conflicts during restore, provide guidance

### Step 4: Re-deploy AGENT.md

```bash
# Copy AGENT.md to parent magpie directory
cp AGENT.md ../AGENT.md

# Verify the copy
ls -lh ../AGENT.md
```

### Step 5: Report Status

Show a summary:

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✨ Update Complete!
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📦 Repository: magpie-agent
🔄 Branch: main
✅ Pulled latest changes from origin/main

📝 Files updated:
   - AGENT.md
   - [list other changed files from git pull]

📋 Deployed to parent directory:
   - AGENT.md → ../AGENT.md

🎯 Status: Ready to use latest documentation

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

## Safety Checks

Before executing, verify:
- [ ] We're in the magpie-agent directory (pwd shows `.../magpie/magpie-agent`)
- [ ] The parent directory exists (`../` is the magpie directory)
- [ ] Git repository is valid (`git rev-parse --git-dir` succeeds)
- [ ] On main branch (or ask user if on different branch)

## Error Handling

### Error: Not in magpie-agent directory
```
❌ Error: Not in magpie-agent directory
Current: [show pwd]
Expected: .../magpie/magpie-agent

Please navigate to magpie-agent directory first.
```

### Error: Not a git repository
```
❌ Error: Not in a git repository
Expected to be in magpie-agent repository.
```

### Error: Network issues
```
❌ Error: Cannot connect to remote repository
Please check your internet connection and try again.
```

### Error: Permission issues
```
❌ Error: Cannot write to parent directory
Check file permissions for the parent magpie directory.
```

## Notes

- **Non-destructive**: This command only pulls and copies files, never modifies existing work
- **Conflict handling**: Provides clear guidance for manual resolution
- **Stash support**: Safely handles uncommitted changes
- **Verification**: Always confirms successful deployment

---

**Remember**: This updates the documentation, not the MAgPIE model code itself. Use this to stay in sync with the latest agent improvements!
