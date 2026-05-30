# Anchor G3: magpie4 version in agent source-of-truth clone

## Answer

The agent's source-of-truth clone reflects **magpie4 v2.70.0**, at git SHA **a360d8c9ec1ee7af6c9287791e8b182bf391d355**.

The version was determined by reading `../input/renv.lock` — specifically the `Packages.magpie4.Version` and `Packages.magpie4.RemoteSha` fields. The sync script (`scripts/sync_magpie4_clone.py`) extracts both values from `renv.lock` and tries to resolve the clone in priority order: exact SHA first, then version tag (`v<Version>`), then HEAD as a last-resort fallback. The `resolution` field in `project/version_pins.json` records which strategy succeeded. For this pin, `"resolution": "sha"` — meaning the clone was checked out at the exact `RemoteSha` from `renv.lock`.

The pin snapshot was captured on 2026-05-25. The `lock_file_sha256` value (`de41e0ce9239aabab001102277e85fa576fb3e8e5c84b9d27c2a461e123731ba`) serves as a freshness canary: if it differs from the current SHA256 of `../input/renv.lock`, the cache is stale and the sync script must be re-run.

The workspace-level clone at `~/Documents/Work/Workspace/magpie4/` is NOT the source of truth; as of 2026-05-24 it was at HEAD (v2.75.1), five minor versions ahead of the renv pin. All source reads must use `.cache/sources/magpie4/`.

## Files read

- `agent/helpers/magpie4_reference.md` — authoritative helper; defines the three rules for magpie4 questions, explains the version-pinning mechanism, documents `"head"` as a caveat-triggering fallback, and notes the workspace clone divergence
- `project/version_pins.json` — machine-readable pin snapshot; records version `"2.70.0"`, sha `"a360d8c9ec1ee7af6c9287791e8b182bf391d355"`, resolution `"sha"`, and the lock-file SHA256 used as a freshness canary
