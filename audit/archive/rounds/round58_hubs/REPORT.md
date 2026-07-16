# R58 — adversarial round on stale hubs

**Status:** IN PROGRESS (started 2026-07-17 00:21 CEST, autonomous overnight)
**Branch:** `r57-rolemap-guard` · **Base:** `664f6f8` · **MAgPIE develop:** `0d7ebeb90`
**Baseline gate at start:** 47 checks / 45 passed / 2 warnings / 0 errors / PASS

## Why this round exists

Mike's ask: find bug surfaces that aren't mechanized, in **hub modules that haven't been tested recently**.

The selection criterion was derived, not assumed. Degree centrality (from the interface-variable role map) cross-cut against audit recency:

| module | degree | last audited |
|---|---|---|
| 32 | 40 | R55 2026-07-16 (just done) |
| **11 costs** | **35** | **R47 2026-06-05** |
| 35 | 30 | R54 2026-07-15 (just done) |
| **70 livestock** | **25** | **R41 2026-06-03** (2 rounds ever) |
| **29 cropland** | **24** | **R24 2026-05-24** (1 round ever) |
| 59 | 23 | R52 2026-06-28 |
| 14 / 52 / 10 / 56 | 22 / 22 / 22 / 17 | R54–R57 (audited 5–18× each) |

**The audit's own attention is survivorship-biased.** R54–R57 went where earlier rounds had already found bugs. M11 — the cost-aggregation hub, 2nd-highest centrality in MAgPIE, consuming 33 interface variables — had not been examined in six weeks. M29 had been examined once, ever. This is the censorship thesis applied to module selection rather than bug classes.

## The experiment

R55 measured **28 confirmed findings / 498 claims = 5.6%** claim-level defect rate on the 3 *most*-audited hubs. R58 runs the same n on 3 *stale* hubs.

- ≈5.6% → corpus is uniformly ~5% defective; recency doesn't matter.
- materially higher → recent clean rounds were an artifact of re-auditing already-clean modules.

**Asymmetry that must travel with the number:** R55 *imposed* its taxonomy (auditors were handed the class to hunt); R58 is open-ended (auditors name their own classes). An open-ended auditor should find ≥ a lens-directed one on the same claims — but lens-direction also focuses attention, so a lower R58 rate is NOT automatically "cleaner". This is not a clean comparison and must never be quoted as one.

## Method (and the design fix over R55)

- **Open-ended taxonomy.** Auditors were given the severity tiers (for comparability) but deliberately NOT the bug-class list. R55's lens files told auditors which class to hunt, so it could only ever resurface already-named classes.
- **The `other` bucket is recorded per-claim.** R55's 60 out-of-taxonomy claims survive as a single integer — the only bottom-up signal the project ever had, and it was discarded.
- **Auditors were barred from the instruments.** No reading `scripts/check_*.py`, no role map, no `--dump-rolemap`. Using the instruments as the frame inherits the blind spots this round exists to find.
- **Adversarial refutation** per finding-bearing module; R55's "refuted-and-survived" bar.

## Results

_(pending)_

## The grade

_(pending — see runplan for the required framing: defect rate WITH denominator; instrument grade as a before/after pair with the retrofit count as denominator; per-guard positive-control status; expiry)_

## Verification log

- [x] Preconditions: lock acquired, R58-idempotence guard passed, remote=mscrawford, branch=r57-rolemap-guard, tree clean, caffeinate alive
- [x] Baseline gate: 0 errors (47 checks, 2 warnings)
- [ ] Phase 1 auditors returned
- [ ] Findings confirmed against develop by direct read
- [ ] Adversarial refutation pass
- [ ] Phase 2 automation (only for classes with ≥2 instances + local anchor)
- [ ] Phase A′ retrofit (n of 9)
- [ ] Phase 3 mutation pass (SELFCHECK_OK first)
- [ ] Phase 4 QA (conditional ≥40%)

## Guardrails honoured

- Nothing pushed.
- No truth number written for the 3 unadjudicated dependent-count findings (`module_56.md:1138/:1150`, `module_17.md:899`) or their `core_docs/Module_Dependencies.md` twins.
- No check flipped to gating.
- Gate held at 0 errors.
