# Anchor G3: magpie4 Source-of-Truth Clone — Version & Provenance

**Question:** Which version of magpie4 does this agent's source-of-truth clone reflect, and how was that version determined?

**Sources used (doc-only, no GAMS code read):**
- `agent/helpers/magpie4_reference.md`
- `project/version_pins.json`

---

## Answer

### Version

The source-of-truth clone (`.cache/sources/magpie4/`) reflects **magpie4 v2.70.0**, at commit SHA `a360d8c9ec1ee7af6c9287791e8b182bf391d355` (short form `a360d8c9ec`, the form used in the helper's own citation examples).

- `project/version_pins.json`, the `packages.magpie4` object:
  `"version": "2.70.0"`, `"sha": "a360d8c9ec1ee7af6c9287791e8b182bf391d355"`, `"source_dir": "<magpie-agent>/.cache/sources/magpie4"`, `"resolution": "sha"` (version_pins.json:8-11).
- `agent/helpers/magpie4_reference.md` cites the same pin: "Cite with full version-pinned path: e.g. `.cache/sources/magpie4/R/reportEmissions.R:23` plus the pin (`v2.70.0 @ a360d8c9ec`)." (magpie4_reference.md:18), and inside the `getReport.R` excerpt: "`# .cache/sources/magpie4/R/getReport.R: getReport() spans L56-235; tryList dispatch block L62-182 (v2.70.0 @ a360d8c9ec)`" (magpie4_reference.md:45).

### How the version was determined

Per `agent/helpers/magpie4_reference.md` § "Version pinning" (magpie4_reference.md:22-36):

1. **Authoritative upstream source**: "`../input/renv.lock` → `Packages.magpie4` → `Version` + `RemoteSha`" (magpie4_reference.md:24) — the parent MAgPIE repo's renv lockfile is the ground truth for which magpie4 version/commit the pinned R environment uses.
2. **Resolution mechanism**: `scripts/sync_magpie4_clone.py` "tries three resolution strategies in order: exact SHA → version tag (`v<Version>`) → HEAD with caveat. The `resolution` field in `version_pins.json` records which one was used. If it's `\"head\"`, your reads may not match what the user is running — flag this to the user." (magpie4_reference.md:28)
3. **Result for this clone**: `"resolution": "sha"` (version_pins.json:11) — the exact `RemoteSha` from `renv.lock` was found and checked out directly. This is the strongest of the three strategies; no fallback to a version tag or to HEAD-with-caveat was needed. (Contrast: `_documentation.resolution_values.sha` in the same file glosses this as "Checked out at the exact RemoteSha from renv.lock." — version_pins.json:21.)
4. **Snapshot artifact**: the resolved state is captured into `project/version_pins.json`, which also records `"captured_at": "2026-05-25"` (version_pins.json:3), the source `"lock_file"` path `<magpie-root>/input/renv.lock` (version_pins.json:4), and a `"lock_file_sha256"` hash of that renv.lock (version_pins.json:5) used as a staleness canary. Per the helper: "Run `python3 scripts/sync_magpie4_clone.py --check` — it compares the stored `lock_file_sha256` in `project/version_pins.json` against the live `../input/renv.lock` hash (plus the clone HEAD vs the pinned SHA) and reports `pin canary: OK` or `STALE`. If STALE, re-run without `--check` to refresh the pin + clone." (magpie4_reference.md:16)
5. **Where the clone lives / is read from**: `.cache/sources/magpie4/` — "gitignored under `.cache/`; managed by `scripts/sync_magpie4_clone.py`" (magpie4_reference.md:25) — matching the `source_dir` field in version_pins.json.
6. **Why this mechanism exists at all**: "magpie4 v2.70.0 exports several hundred functions, and `getReport.R` alone calls ~106 unique `report*` functions. Curation would be a treadmill. Instead, we keep a **version-pinned local clone** and the helper teaches you to **grep + read source on demand**." (magpie4_reference.md:12)

### Contrast noted in the docs (NOT the source-of-truth clone)

The helper explicitly warns against a second, unpinned clone that must not be confused with the source-of-truth one: "Read from `.cache/sources/magpie4/` (the SHA-pinned clone), NEVER from `~/Documents/Work/Workspace/magpie4/` (HEAD; drifts ahead of the renv pin — currently 5 minor versions ahead per 2026-05-24)." (magpie4_reference.md:17). Common Pitfalls #1 repeats this with a version number: "`~/Documents/Work/Workspace/magpie4/` is at HEAD (currently v2.75.1, ahead of the renv pin v2.70.0). Lines, variable definitions, and even function names can differ. ALWAYS use `.cache/sources/magpie4/` unless the user explicitly asked about HEAD." (magpie4_reference.md:257).

---

## Verification badges

- 🟡 Documented — version, SHA, and resolution method read from `project/version_pins.json` and `agent/helpers/magpie4_reference.md` this session.
- No live freshness check was run (`python3 scripts/sync_magpie4_clone.py --check`) — per this session's no-tools/no-recompute constraint, no command was executed and no command output is reported. The values above are cited verbatim from the two files as found; whether the pin is still aligned with the live `../input/renv.lock` at the time of this answer is **not verified**. `version_pins.json` is itself gitignored, machine-local, regenerated data — "Refreshed by scripts/sync_magpie4_clone.py... Gitignored — regenerate locally." (version_pins.json:19) — captured at 2026-05-25, which is not the current session date, so its currency is unconfirmed rather than assumed.
- No raw GAMS code and no `.gms` files were read in this session.
