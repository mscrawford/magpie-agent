# Bootstrap Command

**Purpose**: Complete first-time setup for a new magpie-agent installation

**When user says**: "/bootstrap", "first time setup", "initialize agent", etc.

---

## Auto-Detection

The agent automatically checks for missing setup on first message:

```bash
# Check if AGENT.md is deployed to parent
ls ../AGENT.md 2>/dev/null
```

If AGENT.md is missing in the parent directory, the agent offers to bootstrap.

---

## Setup Message

```
🔧 First-time setup detected!

I notice this is a fresh magpie-agent installation. I can complete the setup automatically by:
- Copying AGENT.md to the parent MAgPIE directory
- Verifying the documentation structure

Would you like me to complete the setup now?
```

---

## Bootstrap Steps

If user agrees, run these commands:

```bash
# 1. Copy AGENT.md to parent directory (both targets)
cp AGENT.md ../AGENT.md
cp AGENT.md ../CLAUDE.md

# 2. Verify the copy
ls -lh ../AGENT.md

# 3. Verify documentation structure exists
ls -d modules/ core_docs/ cross_module/ reference/ agent/commands/

# 4. Report success
echo "✅ Bootstrap complete!"
```

---

## Confirmation Message

After successful bootstrap:

```
✅ Bootstrap complete!

AGENT.md is now deployed to the parent directory.

🚀 Available Commands:
  /guide              - Complete capabilities guide (start here!)
  /sync               - Sync docs with MAgPIE code changes
  /feedback           - Submit feedback to improve the agent

🎯 You can now use all magpie-agent features!

Try: "/guide" to see everything I can do.
```

---

## Manual Bootstrap

If the user prefers to do it manually:

```bash
# From magpie-agent directory
cp AGENT.md ../AGENT.md && cp AGENT.md ../CLAUDE.md
```

---

## Important Notes

- The agent should only offer bootstrap ONCE per session when first detecting missing files
- Don't repeatedly ask on every message
- Bootstrap copies TO parent directory (`../AGENT.md` AND `../CLAUDE.md`)
- CLAUDE.md is what Claude loads into its system prompt — must stay in sync!
- Source files remain in magpie-agent/

---

## Verification

After bootstrap, verify the setup is correct:

```bash
# Check parent has AGENT.md
test -f ../AGENT.md && echo "✅ AGENT.md deployed" || echo "❌ AGENT.md missing"

# Check command files exist
ls agent/commands/*.md | wc -l
```

Expected: AGENT.md deployed, 6 command files present
