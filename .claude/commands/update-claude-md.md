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
