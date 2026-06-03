# G3 Answer: magpie4 source-of-truth version and determination

**Question**: Which version of magpie4 does this agent's source-of-truth clone reflect, and how was that version determined?

---

## Version

The agent's source-of-truth clone reflects **magpie4 v2.70.0** at commit SHA `a360d8c9ec1ee7af6c9287791e8b182bf391d355`.

- Clone location: `.cache/sources/magpie4/` (gitignored; managed by `scripts/sync_magpie4_clone.py`)
- Pin recorded: `project/version_pins.json` (lines 7-12), captured 2026-05-25
- Resolution method: `"sha"` — the clone was checked out at the exact `RemoteSha` from `renv.lock`

🟡 (documented — read from `project/version_pins.json` and `agent/helpers/magpie4_reference.md` this session)

---

## How the version was determined

### Upstream authority: `../input/renv.lock`

The authoritative source is `../input/renv.lock` → `Packages.magpie4`, fields `Version` and `RemoteSha`. These are set by MAgPIE's own R environment lock (managed by `renv`) and represent exactly what version of magpie4 was in use when that lock file was last generated.

From the live `../input/renv.lock` (verified this session):

```
Version:    2.70.0
RemoteSha:  a360d8c9ec1ee7af6c9287791e8b182bf391d355
RemoteRef:  HEAD
```

(`../input/renv.lock`, `Packages.magpie4` fields)

### Sync mechanism

`scripts/sync_magpie4_clone.py` reads `renv.lock`, extracts `Version` and `RemoteSha`, and clones/checks-out the magpie4 GitHub repository at that exact SHA. It tries three resolution strategies in order:

1. **`sha`** (preferred) — checkout at the exact `RemoteSha`. Used in this case.
2. **`tag`** — if the SHA is not reachable on GitHub, fall back to the `v<Version>` tag.
3. **`head`** — if both fail, use HEAD of the default branch (lowest fidelity; flagged in the `resolution` field).

After cloning, it writes `project/version_pins.json` recording the version, SHA, clone path, and the SHA256 of the `renv.lock` file it read from — this SHA256 is the freshness canary.

(`agent/helpers/magpie4_reference.md` lines 24-28; `project/version_pins.json` lines 11-12, 19-22)

### Current pin status

The live `../input/renv.lock` SHA256 (`de41e0ce9239aabab001102277e85fa576fb3e8e5c84b9d27c2a461e123731ba`) matches the `lock_file_sha256` recorded in `project/version_pins.json` (line 5). The pin is **current** as of 2026-06-03.

---

## Why the workspace clone is intentionally NOT source-of-truth

`~/Documents/Work/Workspace/magpie4/` tracks the GitHub remote's HEAD. As of 2026-05-24 it was at **v2.75.1** — five minor versions ahead of the renv-pinned v2.70.0.

The renv pin records what the user's actual MAgPIE runs were using when `renv.lock` was committed. Answering questions about `report.mif` variables or `getReport` dispatch from a newer HEAD would produce answers that describe code the user never ran. Line numbers, function signatures, and even function existence can differ between versions. The workspace clone is therefore treated as a drift-prone convenience copy, not an authoritative source.

(`agent/helpers/magpie4_reference.md` lines 17, 257-258 — "Common Pitfalls" §1)

---

## Files read

| File | Lines / fields cited | Purpose |
|---|---|---|
| `project/version_pins.json` | Lines 1-25 (full file) | Version, SHA, resolution method, captured_at, lock_file_sha256 |
| `agent/helpers/magpie4_reference.md` | Lines 14-28 ("Three rules", "Version pinning" section); lines 257-258 ("Common Pitfalls" §1) | Pin verification procedure; workspace-clone drift warning |
| `../input/renv.lock` | `Packages.magpie4.Version`, `Packages.magpie4.RemoteSha`, `Packages.magpie4.RemoteRef` | Upstream authoritative source; confirmed SHA256 match live this session |

---

**Source statement**: All factual claims are 🟡 documented — read from the three files listed above during this session. No version number was taken from memory or training data. The SHA256 match between `version_pins.json` and the live `../input/renv.lock` was verified programmatically this session (match = True).
