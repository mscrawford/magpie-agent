# Audit Report: G3 (magpie4 source-of-truth / version-pin discipline)

## Overall Verdict: ACCURATE
## Accuracy Score: 10/10
## drift_observed: false

Calibration anchor G3 (v1.1 regression question). Tests source-of-truth discipline
for the two-clone setup: SHA-pinned `.cache/sources/magpie4/` (read this) vs the
drift-prone workspace clone at `~/Documents/Work/Workspace/magpie4/` (do NOT cite).

---

## Verified Claims (correct)

1. **Version v2.70.0, SHA `a360d8c9ec1ee7af6c9287791e8b182bf391d355`.**
   - `project/version_pins.json:8-9` → `"version": "2.70.0"`, `"sha": "a360d8c9ec1ee7af6c9287791e8b182bf391d355"`. EXACT match. No fabricated SHA.

2. **Reads `project/version_pins.json` as the cached pin (NOT the workspace clone).**
   - Answer explicitly reads `version_pins.json` and names the workspace clone only to warn it is NOT source-of-truth. Satisfies the core discipline the anchor exists to test.

3. **Upstream authoritative source = `../input/renv.lock`, `Packages.magpie4` (`Version` + `RemoteSha`).**
   - Verified live: `input/renv.lock` `Packages.magpie4.Version` = `2.70.0`, `RemoteSha` = `a360d8c9ec1ee7af6c9287791e8b182bf391d355`. Both fields match the pin and the answer's claim.

4. **Cached clone genuinely at the pinned SHA.**
   - `git -C .cache/sources/magpie4 rev-parse HEAD` = `a360d8c9ec1ee7af6c9287791e8b182bf391d355`; DESCRIPTION `Version: 2.70.0`. Consistent with `"resolution": "sha"`.

5. **Workspace clone drifts ahead (v2.75.1 as of 2026-05-24, five minor versions ahead).**
   - Verified: `~/Documents/Work/Workspace/magpie4/DESCRIPTION` = `Version: 2.75.1` (HEAD `69b5d644...`). Helper `agent/helpers/magpie4_reference.md:17,257` independently states "currently v2.75.1 ... 5 minor versions ahead per 2026-05-24". Answer's framing matches.

6. **Sync-script 3-strategy resolution (SHA → tag → HEAD).**
   - `scripts/sync_magpie4_clone.py:128-154` `checkout_pinned()`: SHA checkout returns `"sha"` (131-132); tag fallback returns `"tag"` (137-139); HEAD fallback returns `"head"` (151-154, refused unless `--allow-head-fallback`). Answer's description is faithful, including the caveat flag on HEAD.

7. **Freshness canary `lock_file_sha256`.**
   - `version_pins.json:5` = `de41e0ce9239aabab001102277e85fa576fb3e8e5c84b9d27c2a461e123731ba`; live `shasum -a 256 input/renv.lock` = same. Pin is NOT stale. Canary mechanism correctly described (written at sync_magpie4_clone.py:94,99).

8. **Gloss: `"resolution": "sha"` "meaning the SHA was available on GitHub."**
   - Substantively correct. `checkout_pinned` returns `"sha"` only when `git checkout <sha>` succeeds (requires SHA fetchable); the no-op path (sync_magpie4_clone.py:194-198) also writes `"sha"` when the clone is already at the pinned SHA. Either way the clone is at the exact RemoteSha — the answer's point. Not a confabulation.

## Mechanical checks
- M1 (file:line): N/A for this meta/process question; full relative paths given per MANDATE 16. Pass-equivalent.
- M4/M5 (epistemic badges): Answer omits explicit 🟢/🟡 badges, but every claim is source-grounded with the file named. This is an Informational-tier style nit at most; not scored as a bug (consistent with prior G3 rounds treating the process answer as exempt from module-style badges).
- M6 (closing source statement): "Files read" block lists `project/version_pins.json` + `agent/helpers/magpie4_reference.md`. Both verified to exist and contain the cited content. Pass.

## Bugs Found
None.

## Missing Nuances
- Minor: the answer cites `magpie4_reference.md` rather than `../input/renv.lock` directly as a "file read"; however it correctly NAMES `renv.lock` as the upstream authoritative source with the exact fields, which is what the rubric requires. Not a defect — the renv.lock content is correctly reported.
- The answer could have noted `RemoteRepo: None` in renv.lock (the magpie4 entry has `Source: Repository`, no RemoteRepo), but this is immaterial to the version-determination question.

## Summary
Fully accurate on every load-bearing element: correct version + SHA from `version_pins.json`,
correct upstream source (`renv.lock` `Packages.magpie4` Version+RemoteSha), correct
workspace-clone-is-NOT-source-of-truth discipline (and the v2.75.1 divergence verified live),
faithful sync-script 3-strategy description, correct freshness canary. No Critical-class
confabulation (no wrong version, no workspace-as-SoT, no fabricated SHA). Score 10/10,
no drift. Anchor stable.
