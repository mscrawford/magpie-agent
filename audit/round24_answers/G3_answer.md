# R24-G3 Sonnet answer (magpie4 version-pin discipline)

## magpie4 version-pin discipline (R24 G3)

### Which version does the source-of-truth clone reflect?

The agent's source-of-truth clone is **magpie4 v2.70.0**, checked out at commit SHA **`a360d8c9ec1ee7af6c9287791e8b182bf391d355`**.

The clone lives at:

```
/Users/turnip/Documents/Work/Workspace/magpie/magpie-agent/.cache/sources/magpie4/
```

### How was that version determined?

The version is determined from `../input/renv.lock` — the R environment lockfile that MAgPIE itself uses to reproduce its R dependency environment. The relevant entry is:

```
renv.lock → Packages → magpie4 → Version: "2.70.0"
                                → RemoteSha: "a360d8c9ec1ee7af6c9287791e8b182bf391d355"
```

This lockfile is the authoritative source of truth because it records exactly which magpie4 commit was used when the MAgPIE model run was configured. Any R post-processing (via `magpie4::getReport()` and the individual `report*` functions) should be interpreted against the same code revision that was locked in at model-run time.

### The sync script and resolution chain

The sync script `scripts/sync_magpie4_clone.py` resolves the clone to the correct state by trying three strategies in order:

1. **Exact SHA** (`resolution = "sha"`) — checks out the exact `RemoteSha` from `renv.lock`. This is the current case and the highest-fidelity match.
2. **Version tag** (`resolution = "tag"`) — falls back to the `v<Version>` git tag if the SHA is not directly available on the remote.
3. **HEAD** (`resolution = "head"`) — last resort; uses the default branch HEAD with an explicit caveat to the user that the code may not match what the user is running.

The `resolution` field in `project/version_pins.json` records which strategy was used. The current value is `"sha"` — the strongest guarantee.

### The pin snapshot file

`project/version_pins.json` (gitignored; regenerated locally by the sync script) records:

| Field | Value |
|---|---|
| `captured_at` | 2026-05-24 |
| `lock_file` | `/Users/turnip/Documents/Work/Workspace/magpie/input/renv.lock` |
| `lock_file_sha256` | `de41e0ce9239aabab001102277e85fa576fb3e8e5c84b9d27c2a461e123731ba` |
| `packages.magpie4.version` | `2.70.0` |
| `packages.magpie4.sha` | `a360d8c9ec1ee7af6c9287791e8b182bf391d355` |
| `packages.magpie4.resolution` | `sha` |

The `lock_file_sha256` is the canary: before any session that reads from the clone, the agent hashes the live `renv.lock` and compares it to the stored SHA256. If they differ, the parent lockfile has been updated (e.g., by a recent `git pull`) and the clone must be re-synced before it can be trusted. The verification command is:

```bash
python3 /Users/turnip/Documents/Work/Workspace/magpie/magpie-agent/scripts/sync_magpie4_clone.py --check
# exit 0 = pin is aligned; exit 1 = stale, re-sync needed
```

### Why not read from the workspace clone?

The workspace clone at `/Users/turnip/Documents/Work/Workspace/magpie4/` tracks HEAD. Per `agent/helpers/magpie4_reference.md`, as of 2026-05-24 it is at v2.75.1 — five minor versions ahead of the renv-pinned v2.70.0. Function signatures, `getReport.R` dispatch order, and IAMC variable name constructions can all change across minor versions. Reading from that clone would produce citations that do not match what the model actually used.

---

**Sources**:

- 🟢 `project/version_pins.json` — read this session; pin snapshot confirming v2.70.0 @ `a360d8c9ec`
- 🟢 `/Users/turnip/Documents/Work/Workspace/magpie/input/renv.lock` → `Packages.magpie4` — read this session; authoritative source of `Version` and `RemoteSha`
- 🟡 `agent/helpers/magpie4_reference.md` — read this session; version-pinning methodology and three-resolution-strategy description
