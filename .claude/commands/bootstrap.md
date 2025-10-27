---
description: First-time setup for magpie-agent installation
---

# Bootstrap: First-Time Setup

**Purpose**: Complete initial setup for a new magpie-agent installation.

## Auto-Detection

The agent automatically checks for missing setup on first message:

```bash
# Check if slash commands are deployed
ls ../.claude/commands/ 2>/dev/null
```

If commands directory is missing or empty, the agent offers to bootstrap.

---

## Setup Message

```
🔧 First-time setup detected!

I notice this is a fresh magpie-agent installation. I can complete the setup automatically by copying:
- Slash commands (/guide, /update, /feedback, /integrate-feedback, /update-claude-md)
- AI documentation (already copied - you're reading CLAUDE.md)

Would you like me to complete the setup now? (I'll copy the commands to the parent directory)
```

---

## Bootstrap Steps

If user agrees, run these commands:

```bash
# 1. Create .claude directory in parent if needed
mkdir -p ../.claude

# 2. Copy slash commands
cp -r .claude/commands ../.claude/

# 3. Copy settings if they don't exist in parent
if [ ! -f ../.claude/settings.local.json ]; then
  echo '{
  "permissions": {
    "allow": [
      "Bash(chmod:*)",
      "Bash(scripts/integrate_feedback.sh:*)",
      "Bash(git add:*)",
      "Bash(git commit:*)",
      "Bash(git push:*)",
      "Bash(git restore:*)",
      "Bash(cat:*)",
      "Bash(cp:*)"
    ],
    "deny": [],
    "ask": []
  }
}' > ../.claude/settings.local.json
fi

# 4. Verify
ls -lh ../.claude/commands/
```

---

## Confirmation Message

After successful bootstrap:

```
✅ Bootstrap complete!

Slash commands are now available:
  /guide              - Complete capabilities guide
  /update             - Pull latest docs and sync files
  /feedback           - User feedback system
  /integrate-feedback - Process pending feedback (maintainers)
  /update-claude-md   - Git workflow instructions

🎯 You can now use all magpie-agent features!

Try: /guide to see everything I can do.
```

---

## Manual Bootstrap

If the user prefers to do it manually:

```bash
# From magpie-agent directory
cp -r .claude/commands ../.claude/
```

---

## Important Notes

- The agent should only offer bootstrap ONCE per session when first detecting missing files
- Don't repeatedly ask on every message
- Bootstrap copies TO parent directory (../.claude/)
- Source files remain in magpie-agent/.claude/
