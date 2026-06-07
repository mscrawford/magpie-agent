# Anchor G3: magpie4 version reflected by the agent's source-of-truth clone

## Answer

The agent's source-of-truth clone reflects **magpie4 v2.70.0**, at commit SHA `a360d8c9ec1ee7af6c9287791e8b182bf391d355`.

The clone lives at `.cache/sources/magpie4/` (gitignored; managed by `scripts/sync_magpie4_clone.py`).

## How the version was determined

The version is pinned to the **parent project's `../input/renv.lock`** file. Specifically:

- `renv.lock` → `Packages.magpie4` → `Version` (`2.70.0`) and `RemoteSha` (`a360d8c9ec1ee7af6c9287791e8b182bf391d355`) are the authoritative source.
- The sync script (`scripts/sync_magpie4_clone.py`) reads those two fields and attempts resolution in three strategies in order: (1) exact SHA checkout, (2) version tag `v<Version>`, (3) HEAD with caveat.
- The `resolution` field in `project/version_pins.json` records which strategy succeeded. For this snapshot it is `"sha"`, meaning the clone was checked out at the exact `RemoteSha` from `renv.lock`.
- A canary hash (`lock_file_sha256`) of the live `../input/renv.lock` is stored so that the check command (`python3 scripts/sync_magpie4_clone.py --check`) can detect if the lock file has been updated since the last sync.

The pin snapshot was captured on **2026-05-25**.

`magpie4_reference.md` also notes that the workspace clone at `~/Documents/Work/Workspace/magpie4/` is currently at HEAD (v2.75.1 as of 2026-05-24), which is **5 minor versions ahead** of the pinned clone and must NOT be used for answering questions — only `.cache/sources/magpie4/` is authoritative.

## Files read

- `agent/helpers/magpie4_reference.md` — version-pinning methodology, three rules, and the HEAD-vs-cache warning
- `project/version_pins.json` — the actual pinned version (`2.70.0`), SHA (`a360d8c9ec`), resolution strategy (`sha`), and capture date (`2026-05-25`)
