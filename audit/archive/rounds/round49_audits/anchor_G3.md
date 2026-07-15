# Audit Report: G3 (magpie4 source-of-truth / version-pin discipline)

**Round**: 49 (calibration anchor, regression question, added rubric v1.1)
**Auditor**: Opus 4.8
**Date**: 2026-06-06
**Rubric**: flywheel_rubric.md v1.2, §6 G3

---

## Overall Verdict: ACCURATE
## Accuracy Score: 10/10
## drift_observed: false

---

## Files read (audit verification)

- `project/version_pins.json` (authoritative pin snapshot) — read directly to compute expected version/SHA at audit time (per rubric §6 G3: "do not hardcode it here").
- `../input/renv.lock` (upstream authoritative source; absolute: `<magpie-root>/input/renv.lock`) — magpie4 entry at lines 4437-4470.
- `agent/helpers/magpie4_reference.md` (the helper the agent must auto-load).
- `scripts/sync_magpie4_clone.py` (the resolution mechanism the answer describes).
- `.cache/sources/magpie4/` (the SHA-pinned clone) — git HEAD + DESCRIPTION.
- `~/Documents/Work/Workspace/magpie4/DESCRIPTION` (the drift-prone workspace clone) — live version cross-check.

---

## Verified Claims (all correct)

| Claim in answer | Evidence | Verdict |
|---|---|---|
| Version **2.70.0** | `version_pins.json:8` (`"version": "2.70.0"`); `renv.lock:4439`; pinned clone DESCRIPTION `Version: 2.70.0` | ✓ |
| SHA `a360d8c9ec1ee7af6c9287791e8b182bf391d355` | `version_pins.json:9`; pinned clone `git rev-parse HEAD` returns this EXACT 40-char SHA | ✓ |
| resolution = `"sha"` (exact RemoteSha checkout) | `version_pins.json:11` | ✓ |
| Stored at `.cache/sources/magpie4/` | `version_pins.json:10`; directory exists, is a git repo at that SHA | ✓ |
| Pin captured **2026-05-25** | `version_pins.json:3` (`"captured_at": "2026-05-25"`) | ✓ |
| Read `project/version_pins.json`, NOT workspace clone | answer cites version_pins.json + helper; does not source-of-truth the workspace clone | ✓ (core discipline) |
| Upstream authoritative source = `../input/renv.lock` `Packages.magpie4` (Version + RemoteSha) | sync script `sync_magpie4_clone.py:174-175` reads `rec["Version"]` and `rec.get("RemoteSha")`; matches rubric §6 G3 expected summary verbatim | ✓ |
| Workspace clone NOT source-of-truth; drifts ahead | `magpie4_reference.md:17,257` | ✓ |
| 3 resolution strategies SHA→tag→HEAD, in order | `sync_magpie4_clone.py:128-154` (`checkout_pinned`) | ✓ |
| `resolution` field records which strategy succeeded | `sync_magpie4_clone.py:105,245`; `version_pins.json:11` | ✓ |
| `lock_file_sha256` canary enables `--check` staleness detection | `sync_magpie4_clone.py:99,193-204` (canary block, pipeline-audit R8 I4) | ✓ |
| Workspace clone "v2.75.1, 5 minor versions ahead as of 2026-05-24" | sourced verbatim from `magpie4_reference.md:257` ("currently v2.75.1, ahead of the renv pin v2.70.0") and :17 ("5 minor versions ahead per 2026-05-24") — documented value, correctly attributed, NOT fabricated | ✓ |
| Citations use full relative paths | both cited files use full relative paths | ✓ |

The claimed version, SHA (full 40-char, superset of the 10-char prefix requirement), and resolution field all MATCH version_pins.json. No fabrication.

---

## Bugs Found

**None.**

---

## Investigated-but-not-a-bug (recorded for transparency + future-round signal)

### Upstream renv.lock magpie4 entry no longer carries `RemoteSha` (infrastructure drift, NOT an answer bug)

The CURRENT `../input/renv.lock` magpie4 entry (lines 4437-4470) is a **`"Source": "Repository"`** entry with **NO `RemoteSha`** field (only `Version: 2.70.0`). `RemoteSha` appears 31× in the lock file for OTHER packages, but not for magpie4. Verified two ways: `awk` slice of the block + `rg 'RemoteSha'` line list (magpie4's block range contains none).

Why this is NOT a bug in the audited answer:
1. **The answer describes the SCRIPT correctly.** `sync_magpie4_clone.py:175` literally does `sha = rec.get("RemoteSha", "")`. The answer's statement that the script "reads `Packages.magpie4.Version` and `Packages.magpie4.RemoteSha`" is an accurate description of the code.
2. **The rubric's own G3 expected summary names `RemoteSha`** (flywheel_rubric.md:201; validation_rounds.json regression entry). The answer matches the expected anchor summary exactly.
3. **The pin predates the drift.** version_pins.json was captured 2026-05-25 with `resolution: "sha"` and a real 40-char SHA that matches the clone HEAD — proving the renv.lock DID carry a magpie4 RemoteSha at pin time. The upstream entry was later regenerated as a Repository-source entry (a360d8c is no longer in the lock as a field).
4. Penalizing the answer for upstream source drift that postdates the captured pin would be incorrect — the question asks what the pin reflects and how it was determined, and the answer reports the pin faithfully.

**Latent infrastructure note (NOT scored against the answer; for maintainers):** if `sync_magpie4_clone.py` were re-run against the current renv.lock, it would `sys.exit("magpie4 entry ... has no RemoteSha. Cannot pin.")` (line 176-177). The pin is therefore currently "frozen" at the 2026-05-25 snapshot and cannot be regenerated by the SHA path until upstream restores a RemoteSha (or the script gains a Repository-source/version-tag fallback for the no-RemoteSha case). This does not affect G3 scoring but is worth a maintainer ticket. Also minor doc staleness: helper says workspace clone is v2.75.1; live is now v2.76.1 — the answer correctly reproduced the documented (stale) value with attribution, so no answer penalty.

---

## Mechanical checks

G3 is a meta/infrastructure question (no GAMS module), so M1-M6 (module file:line, realization, GAMS prefixes, etc.) are largely N/A by design. Applicable analogues:
- File citations present and correct (version_pins.json + magpie4_reference.md): PASS
- Source-of-truth discipline (read pin, not workspace clone): PASS
- No fabricated version/SHA/resolution: PASS

---

## Missing Nuances

Minor, non-scoring. The answer could have noted that the upstream renv.lock magpie4 entry is currently a Repository-source entry without a live RemoteSha (so the SHA in version_pins.json is the cached resolution rather than a field readable from today's renv.lock). But the question asks what the pin reflects and how it was *determined* (the script's read-RemoteSha-then-resolve mechanism), which the answer describes correctly and which matches the rubric's expected summary. Omitting an upstream-drift caveat that postdates the pin is not a defect.

---

## Summary

Textbook-correct G3 answer. Reads `project/version_pins.json` (the authoritative pin), reports version 2.70.0 + full SHA a360d8c9ec1ee7af6c9287791e8b182bf391d355 + resolution "sha", all matching the file exactly. Correctly identifies the upstream authoritative source as `../input/renv.lock` `Packages.magpie4`, correctly flags the workspace clone as NOT source-of-truth, describes the sync script's 3-strategy resolution + canary mechanism accurately, and cites both files with full relative paths. No confabulation, no fabricated SHA, no workspace-clone-as-truth error — the three Critical-severity traps the anchor guards against are all avoided.

Score: **10/10**. drift_observed: **false** — the anchor is stable; nothing near it broke this round. (The upstream renv.lock RemoteSha drift is an infrastructure/source-state change, not a regression in the anchor's expected answer, and is recorded above for a maintainer follow-up rather than as anchor drift.)
