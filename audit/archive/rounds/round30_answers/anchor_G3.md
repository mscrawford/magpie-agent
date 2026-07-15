# G3: magpie4 version reflected by the agent's source-of-truth clone

## Answer

The agent's source-of-truth clone reflects **magpie4 v2.70.0**, checked out at exact commit SHA `a360d8c9ec1ee7af6c9287791e8b182bf391d355`.

## How the version was determined

The version is determined by reading `../input/renv.lock` (the parent MAgPIE project's R environment lockfile). Specifically:

- `renv.lock` → `Packages.magpie4` → `Version` (gives `2.70.0`) and `RemoteSha` (gives `a360d8c9ec...`)
- The sync script `scripts/sync_magpie4_clone.py` reads those two fields and attempts three resolution strategies in order: exact SHA checkout → version tag (`v<Version>`) → HEAD with caveat
- The `resolution` field in `project/version_pins.json` records which strategy succeeded; for this pin it is `"sha"`, meaning the clone was checked out at the exact `RemoteSha` from `renv.lock`

The clone lives at `.cache/sources/magpie4/` (gitignored). A snapshot of the pin state is stored in `project/version_pins.json`, captured on 2026-05-25, keyed against `lock_file_sha256: de41e0ce9239aabab001102277e85fa576fb3e8e5c84b9d27c2a461e123731ba` so freshness can be detected when `renv.lock` changes.

## Freshness check

Before answering any magpie4 question, the agent is instructed to compare `project/version_pins.json`'s `lock_file_sha256` against the actual SHA256 of `../input/renv.lock`. If they differ, `scripts/sync_magpie4_clone.py` must be re-run. If `resolution` were `"head"` rather than `"sha"`, the agent would flag to the user that the clone may not match the pinned version.

## Files cited

- `<magpie-agent>/project/version_pins.json` — authoritative pin snapshot (schema_version 1, captured 2026-05-25)
- `<magpie-agent>/agent/helpers/magpie4_reference.md` — documents the pinning protocol and three-rule freshness check (lines 1-29)
