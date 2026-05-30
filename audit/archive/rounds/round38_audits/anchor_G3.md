# Audit Report: G3 (magpie4 source-of-truth / version-pin discipline)

**Round**: R38 (calibration anchor, added rubric v1.1)
**Auditor**: Opus 4.8
**Date**: 2026-05-30

### Overall Verdict: ACCURATE
### Accuracy Score: 10/10
### drift_observed: false

---

## Ground-truth verification (authoritative sources, read this session)

| Source | What it says | File:line |
|---|---|---|
| `../input/renv.lock` Packages.magpie4 | `Version = 2.70.0`, `RemoteSha = a360d8c9ec1ee7af6c9287791e8b182bf391d355` (verified via `python3 json` read of `Packages.magpie4`) | `/Users/turnip/Documents/Work/Workspace/magpie/input/renv.lock` |
| `project/version_pins.json` | `version=2.70.0`, `sha=a360d8c9ec1ee7af6c9287791e8b182bf391d355`, `resolution="sha"`, `captured_at=2026-05-25`, `lock_file_sha256=de41e0ce...31ba` | version_pins.json:7-12, :3, :5 |
| `shasum -a 256 ../input/renv.lock` | `de41e0ce9239aabab001102277e85fa576fb3e8e5c84b9d27c2a461e123731ba` — matches the canary in version_pins.json EXACTLY → pin is current | (live command) |
| Cached clone HEAD | `git -C .cache/sources/magpie4 rev-parse HEAD` → `a360d8c9ec1ee7af6c9287791e8b182bf391d355` — matches pin exactly | (live command) |
| `scripts/sync_magpie4_clone.py` | Three-strategy resolution SHA → tag(`v<version>`) → HEAD; `resolution="sha"` documented as "Checked out at the exact RemoteSha" | sync_magpie4_clone.py:128-154, :116 |
| Workspace clone `~/Documents/Work/Workspace/magpie4/` | EXISTS, ahead of cached clone (345 commits past v2.53.1 vs cached 313) → empirically confirms drift-ahead claim | (live command) |

The auditor read `project/version_pins.json` directly to compute the expected version/SHA at audit time (per §6 G3 mandate — not hardcoded). Pin advances when the user pulls upstream MAgPIE; as of R38 it remains v2.70.0 @ a360d8c9ec.

---

## Verified Claims (all correct)

- **Version 2.70.0, SHA a360d8c9ec...** — matches renv.lock RemoteSha, version_pins.json, AND the cached clone's actual HEAD. Triple-confirmed.
- **Authoritative source = `../input/renv.lock`, fields `Packages.magpie4.Version` + `Packages.magpie4.RemoteSha`** — exact field names correct; both fields present in the lock.
- **Three-strategy resolution (exact SHA → version tag → HEAD)** — confirmed at sync_magpie4_clone.py:128-154. `checkout_pinned` tries SHA (line 131), then `v{version}` tag (line 138), then HEAD only with `--allow-head-fallback` (line 144+).
- **`resolution="sha"` ⇒ exact-RemoteSha checkout** — confirmed (version_pins.json:116 documentation string + script line 131-132). Correct interpretation.
- **SHA256 canary `de41e0ce...` as freshness sentinel** — matches the live `shasum` exactly; the answer's description of its purpose (stale-cache detection) matches magpie4_reference.md:16,258.
- **Pin captured 2026-05-25** — version_pins.json:3 confirms.
- **Workspace clone (`~/Documents/Work/Workspace/magpie4/`) explicitly NOT source-of-truth, drifts ahead; v2.75.1 as of 2026-05-24** — directionally confirmed empirically (workspace 345 > cached 313 commits past v2.53.1); the v2.75.1 label is correctly sourced from magpie4_reference.md:17,257, not fabricated.
- **Files read: `agent/helpers/magpie4_reference.md` + `project/version_pins.json`** — exactly the two correct primary sources. The answer read version_pins.json (the mandated SoT), NOT the workspace clone.

## Critical-confabulation checklist (from expected summary) — all AVOIDED

- ❌ Wrong version → answer is correct (2.70.0).
- ❌ Citing workspace clone as SoT → answer explicitly names version_pins.json as the pin and flags the workspace clone as non-SoT.
- ❌ Fabricating a SHA → SHA matches authoritative renv.lock RemoteSha exactly.

## Mechanical checks

- M1 (file:line): N/A for an R-package/version-pin question; the answer cites the correct files by path. Pass-equivalent.
- M5 (confidence tier matches depth): answer's claims are all sourced from files it names. Pass.
- M6 (closing source statement): present ("Files read: ..."). Pass.
- No GAMS variable/equation/realization claims → M2/M3 N/A.

## Bugs Found

None.

## Missing Nuances

Trivial/non-load-bearing: the answer doesn't mention the `--check` alignment verb or that the clone uses a `blob:none --no-checkout` partial clone, but neither is required by the question (which asks version + how-determined). The answer's added detail (resolution strategies, canary) is accurate and strengthens it.

## Summary

A model G3 response. Source-of-truth discipline is intact: the answer read `project/version_pins.json` (not the drift-prone workspace clone), reported the correct version (2.70.0) and SHA (a360d8c9ec...) — both triple-verified against renv.lock RemoteSha and the cached clone's actual HEAD — and correctly identified `../input/renv.lock` (`Packages.magpie4.Version`/`RemoteSha`) as the upstream authority. All three named critical confabulations avoided. The auditor also confirmed the answer's optional elaborations (three-strategy resolution, `resolution="sha"` semantics, SHA256 canary, workspace-clone drift) are each correct. Score 10/10, no drift. The anchor is stable; nothing near it appears broken this round.
