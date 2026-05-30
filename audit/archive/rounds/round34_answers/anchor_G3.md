# Anchor G3 — magpie4 version and how it was determined

## Question

Which version of magpie4 does this agent's source-of-truth clone reflect, and how was that version determined?

## Answer

**Version**: magpie4 **v2.70.0**, commit SHA `a360d8c9ec1ee7af6c9287791e8b182bf391d355`.

**Clone location**: `.cache/sources/magpie4/` inside the `magpie-agent/` directory (gitignored).

**How the version was determined**:

The version is pinned from the project's `../input/renv.lock` file (the MAgPIE input-side lockfile). The sync script `scripts/sync_magpie4_clone.py` reads that lockfile and attempts three resolution strategies in order:

1. **SHA** (used here) — checks out the exact `RemoteSha` field from `renv.lock`. This is the strategy recorded for v2.70.0, meaning the SHA was available on GitHub.
2. **tag** — fallback if RemoteSha is unavailable on GitHub; uses the `v<Version>` tag.
3. **head** — last resort if both SHA and tag are unavailable; uses HEAD of the default branch, which may not match the pinned version.

The `resolution` field in `project/version_pins.json` records which strategy succeeded. For the current pin it is `"sha"`, meaning the clone is at exactly the SHA recorded in `renv.lock`.

A freshness canary is maintained: `version_pins.json` stores the `lock_file_sha256` of `../input/renv.lock` at sync time (`de41e0ce9239aabab001102277e85fa576fb3e8e5c84b9d27c2a461e123731ba`). If that SHA256 differs from the live `input/renv.lock`, the pin is stale and the sync script must be re-run.

**Note on workspace clone divergence**: `~/Documents/Work/Workspace/magpie4/` is at HEAD (v2.75.1 as of 2026-05-24, five minor versions ahead of the pin). The agent is explicitly instructed to read ONLY from `.cache/sources/magpie4/`, never from the workspace clone.

## Files read

- `project/version_pins.json` (captured 2026-05-25; contains the version, SHA, resolution strategy, lock file path and SHA256)
- `agent/helpers/magpie4_reference.md` (version pinning section and Common Pitfalls section, which cross-references the workspace-vs-cache divergence)
