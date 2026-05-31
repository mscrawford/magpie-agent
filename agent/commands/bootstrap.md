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

## Prerequisite — download MAgPIE input data (recommended)

The agent answers some questions from the model's **actual input data**, and the
steps below pin to it. Running `download_data` in the parent magpie root populates
`input/` and `modules/*/input/` with the `.cs3`/`.mz` files **and writes
`input/renv.lock`** — which Step 4 (`sync_magpie4_clone.py`) and the companion
preproc-agent read to pin package versions to the exact data revision. Without it,
those steps fall back to the bundled `project/version_pins.json` snapshot (may lag)
and input-data values aren't legible.

```bash
# from the parent magpie/ root (NOT magpie-agent/):
cd .. && Rscript scripts/start/download_data.R && cd magpie-agent
```

Requires R with `gms`/`magclass` and access to the MAgPIE data repositories
(`cfg$repositories`). On the PIK cluster this is fast — the `intern`/mirror paths
in `/p/projects/rd3mod/R/.Rprofile` resolve to local filesystem copies. For a public
off-cluster clone the data may be unavailable; skip it and the agent still works for
GAMS-code questions (only input-data legibility and exact version pinning are lost).

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

# 4. Populate the SHA-pinned magpie4 R-package clone for report.mif / IAMC
#    variable questions. Reads magpie/input/renv.lock for the pinned version,
#    clones if missing, no-op if already current. ~30s on first run.
python3 scripts/sync_magpie4_clone.py

# 5. Report success
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

🎯 You can now use all magpie-agent features!

Try: "/guide" to see everything I can do.
```

---

## Manual Bootstrap

If the user prefers to do it manually:

```bash
# From magpie-agent directory
cp AGENT.md ../AGENT.md && cp AGENT.md ../CLAUDE.md
python3 scripts/sync_magpie4_clone.py
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

Expected: AGENT.md deployed, 10 command files present
