# Git Workflow for CLAUDE.md

**When updating the CLAUDE.md file, follow this workflow:**

## Critical Rules

1. **ALWAYS work on the file in the magpie-agent directory** (`/path/to/magpie/magpie-agent/CLAUDE.md`)
2. **After editing, copy it to the main MAgPIE directory**:
   ```bash
   cp magpie-agent/CLAUDE.md CLAUDE.md
   ```
3. **Commit and push from the magpie-agent repository ONLY**:
   ```bash
   cd magpie-agent
   git add CLAUDE.md
   git commit -m "Update CLAUDE.md with [description]"
   git push
   ```
4. **DO NOT commit CLAUDE.md from the main MAgPIE repository**
   - The main MAgPIE repository should NOT track changes to CLAUDE.md
   - All version control for CLAUDE.md happens in the magpie-agent subrepository

## Why This Workflow?

- The magpie-agent repository is the source of truth for all AI documentation
- This keeps documentation changes separate from MAgPIE model code changes
- The main CLAUDE.md is just a convenience copy for the AI to read from the project root

## Full Paths

- **Source of truth**: `/Users/turnip/Documents/Work/Workspace/magpie/magpie-agent/CLAUDE.md`
- **Convenience copy**: `/Users/turnip/Documents/Work/Workspace/magpie/CLAUDE.md`

Always edit the source of truth, then copy to the convenience location.
