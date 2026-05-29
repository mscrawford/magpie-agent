# R28 Q6 / regression G3: Which version of magpie4 does this agent's source-of-truth clone reflect, and how was that version determined?

## Answer

The agent's source-of-truth clone of magpie4 reflects **version 2.70.0** at commit SHA **a360d8c9ec1ee7af6c9287791e8b182bf391d355**.

### How the version was determined

The version is pinned via a two-step authority chain:

1. **Authoritative upstream source**: `../input/renv.lock` (the MAgPIE project's R environment lockfile). The lockfile's `Packages.magpie4` entry records the `Version` and `RemoteSha` fields that the project actually runs against. This is the definitive upstream authority — it is what MAgPIE users run when they `renv::restore()`.

2. **Pin snapshot**: `project/version_pins.json` records the result of resolving the lockfile at the time the sync script last ran. The relevant fields:

   ```json
   {
     "captured_at": "2026-05-25",
     "lock_file": "/Users/turnip/Documents/Work/Workspace/magpie/input/renv.lock",
     "lock_file_sha256": "de41e0ce9239aabab001102277e85fa576fb3e8e5c84b9d27c2a461e123731ba",
     "packages": {
       "magpie4": {
         "version": "2.70.0",
         "sha": "a360d8c9ec1ee7af6c9287791e8b182bf391d355",
         "source_dir": "/Users/turnip/Documents/Work/Workspace/magpie/magpie-agent/.cache/sources/magpie4",
         "resolution": "sha"
       }
     }
   }
   ```

   The `resolution: "sha"` field indicates the clone was checked out at the **exact `RemoteSha`** from `renv.lock` — the strongest of the three resolution strategies the sync script attempts (SHA > version tag > HEAD).

### Resolution strategy hierarchy

`project/version_pins.json` documents three possible resolution values (in priority order):

| Value | Meaning |
|-------|---------|
| `"sha"` | Checked out at the exact `RemoteSha` from `renv.lock` (most precise) |
| `"tag"` | `RemoteSha` unavailable on GitHub; fell back to `v<version>` tag |
| `"head"` | Both SHA and tag unavailable; using HEAD of default branch (may not match what users run — flag to user) |

For this pin, `"sha"` resolution was achieved, meaning the clone is bit-for-bit identical to what the `renv.lock` specifies.

### Freshness verification

Before answering any magpie4 question, the agent should verify the pin is still aligned with the current `renv.lock`:

```bash
python3 scripts/sync_magpie4_clone.py --check
# Returns 0 if SHA matches local HEAD, 1 otherwise
```

The pin was captured **2026-05-25**. The `lock_file_sha256` (`de41e0ce...`) is the integrity check — if `../input/renv.lock` has changed since that date, the pin is stale and `sync_magpie4_clone.py` should be re-run.

### Why this matters (regression anchor G3)

This versioning discipline exists because `~/Documents/Work/Workspace/magpie4/` (the user's HEAD checkout) is currently **5 minor versions ahead** of the renv pin (per 2026-05-24 note in `magpie4_reference.md`). Reading from HEAD would silently answer questions about a version the user is not running. The pinned clone at `.cache/sources/magpie4/` is the only authoritative source for magpie4 function behavior in this agent.

---

## Files read

- `project/version_pins.json` — primary source for version, SHA, resolution method, and capture date
- `agent/helpers/magpie4_reference.md` — confirms the authority chain (`renv.lock` → `version_pins.json` → `.cache/sources/magpie4/`) and documents the resolution strategy table and freshness-check protocol

## Epistemic hierarchy

🟡 **Documented** — read from agent state files (`project/version_pins.json`, `agent/helpers/magpie4_reference.md`) this session. The version and SHA are as recorded in the pin snapshot captured 2026-05-25; freshness relative to the current `renv.lock` was not verified this session.
