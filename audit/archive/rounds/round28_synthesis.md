# Round 28 — Synthesis

**Date**: 2026-05-29 | **Type**: coverage + magpie4 regression rotation | schema v1.3 / rubric v1.2
**Mode**: autonomous (user away; full round + code-verified corrections; **nothing pushed**)
**Verification source**: clean detached `origin/develop` worktree `/tmp/magpie-develop-r28` (ee98739fd)

## Scores

| Q | Module(s) | Archetype | Score | Bugs (C/M/m/i) | doc_quality |
|---|-----------|-----------|:-----:|:--------------:|:-----------:|
| Q1 | 60 bioenergy | causal chain + default | 7 | 0/1/1/0 | IN |
| Q2 | 39 landconversion | conservation/cost chain | 7 | 0/1/1/1 | IN |
| Q3 | 34 urban | default/switch + edge | 8 | 0/0/2/0 | OUT (answerer-only) |
| Q4 | 37 labor_prod | default/switch (OFF bait) | 8 | 0/1/0/0 | IN |
| Q5 | 54 phosphorus | default/switch (OFF bait) | 9 | 0/0/1/1 | OUT (answerer-only) |
| Q6 | magpie4 (G3) | regression anchor | 10 | 0/0/0/0 | IN |
| Q7 | magpie4 (G4) | regression anchor | 10 | 0/0/0/1 | IN |

- **Raw mean = 8.4** (59/7 = 8.43). **doc_quality_mean = 8.4** (n=5; excludes Q3, Q5 whose only bugs are answerer-side against clean docs). Nearly equal → answerer noise was minimal this round (unlike R27, where Q5/M20 dragged the raw mean).
- **0 Critical** across all 7. Score range [7, 10].

## Regression anchors (rotated to the under-exercised magpie4 pair)

Per the command-file rotation guidance, G1/G2 ran every round R22–R27 while G3/G4 had been idle since R24. R28 rotated **G3 + G4** in.

- **G3** (version pin): **10/10, no drift.** v2.70.0 @ `a360d8c9ec` verified vs `version_pins.json` (+ live `renv.lock` SHA256 canary); answer cited the pin not the workspace clone.
- **G4** (getReport dispatch): **10/10, no drift.** Flat `tryList`, **106 unique** report* / 117 call lines, tryList 62–181, 235-line file — verified vs the pinned `getReport.R`. Auditor independently confirmed the helper correctly states 106 and retires the stale 108.

## Bugs (12 distinct) and fixes

**3 Major — all `doc_error`, all FIXED:**
1. **Q1/M60** — module_60.md `presolve.gms` citations systematically stale. Root-cause sweep: **all 22** corrected (not just the 6 flagged), verified vs the 65-line presolve.gms. (Syntactic citation validator doesn't check line *content*, so baseline passed — the semantic gap the flywheel exists to close.)
2. **Q2/M39** — q39_cost_landcon block dropped the `sum((ct,cell(i2,j2)),...)` cell→region idiom. Restored verbatim `equations.gms:12-15`.
3. **Q4/M38** — q38_ces_prodfun block non-verbatim (free `i2`, missing `ct`/`cell` sums). Restored verbatim `sticky_labor/equations.gms:19-23` + `:19-23` cite.

**1 latent (`doc_error_answerer_beat_it`), FIXED:** module_39.md:286 — vm_cost_landcon dim said {crop,past,forestry,urban}; declared over the full 7-member land set. Answer beat the doc; fixed regardless per rubric §1.5.

Both formula bugs (#2, #3) are Bug_Taxonomy Pattern 4 + the rubric §1.5 "answerer trusts a wrong doc" pattern — both Sonnet answerers reproduced the simplified doc block. Fixing the docs stops the next round's answerer reproducing them.

**Not fixed (answerer-side / deferred):**
- **Deferred for review (1):** Q1-B2 (Minor, ambiguous) — module_21.md:125 frames `q21_notrade` as "regional self-sufficiency"; it balances at super-region (h2) level. :119-123 has the correct formula, so loosely worded not wrong. Deferred — **M21 is sensitive** (diverges on the experiment branch; rewritten in PR #866).
- **No doc fix (docs verified correct):** Q2-B2 (s39_ignore_calib reward→0), Q3×2 (citation imprecision), Q5 (belowground-P over-read) — Sonnet answerer noise.

## OFF-default baits

Q4 (M37 `off`) and Q5 (M54 `off`) were designed to trigger the Critical "active mechanism claimed when OFF by default." **Neither caught the answerers** — both led with `off` and labeled enabled-state mechanics as not-active. Healthy signal for the default-realization discipline.

## Validators

`validate_consistency.sh`: **40/42 pass, 2 advisory warnings — unchanged from baseline** both before and after the doc edits. No regression.

## Operational note

Session usage window hit its cap during the 13:44 answer fan-out (Q1/Q4 answer files completed on disk but their return-summaries were cut). Resumed after the 16:00 Berlin reset; all 7 answers verified complete before auditing. Commits local only; **nothing pushed**, per user instruction.
