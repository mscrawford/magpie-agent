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

## ⚠️ CORRECTION: the selection numbers in the section above were WRONG

**Raised by the M11 auditor (O4), confirmed by independent re-derivation. The table above is left intact and is superseded by this one.**

I computed degree centrality from the role map's own `--dump-rolemap` output. That map lists a module's own declared variable in its `read_by` set, so **every module double-counted its self-references** and I never checked the convention. Independent scan (own tokenizer, own comment-stripper, nothing imported from the instruments):

| | as briefed | corrected (self-refs excluded) |
|---|---|---|
| **M11** | degree 35, rank **#2**, reads 33 | degree **33**, rank **#1**, produces 1 (`vm_cost_glo`), reads **32** |
| M32 | degree 40, rank #1 | degree 29, rank #2 |
| **M29** | degree 24 | degree **19**, rank #4 |
| **M70** | degree 25 | degree **16**, rank **#8** |

**Root cause, stated plainly: I used the instrument to select the targets and inherited its counting convention unexamined — the exact error this round exists to catch, committed while designing the round.** The auditors were explicitly barred from the instruments' frame; I did not hold myself to the same rule. It surfaced only because an independent auditor tried to reproduce the number and could not.

**What survives:** the selection. M11 is *more* central than briefed (#1, not #2) and had gone 6 weeks unexamined — the round's core claim holds and is strengthened. M29 (#4) is a fair target.
**What does not:** M70 at rank #8 is a materially weaker "hub" than the degree-25 figure I briefed. Its inclusion was justified by an inflated number. It is still a stale, reasonably-central production module, but it was not the #3-tier target it was sold as.

**Do not quote the original table.** Any downstream use of "M11 has degree 35 / consumes 33" is wrong.

## Results

**Denominators and findings (Phase 1, open-ended taxonomy, auditors barred from the instruments' frame):**

| module | claims_evaluated | Critical | Major | Minor | total |
|---|---|---|---|---|---|
| M11 costs | 241 | 4 | 7 | 3 | 14 |
| M29 cropland | 168 | 2 | 13 | 4 | 19 |
| M70 livestock | 186 | 1 | 7 | 5 | 14 (+1 Info) |
| **TOTAL (raw)** | **595** | **7** | **27** | **12** | **47** |

### After the adversarial refutation pass (this is the comparable number)

Each module's findings were attacked by an independent refuter told to *refute*, not agree. R55's 28 were post-refutation survivors, so only post-refutation numbers may be compared to it.

| module | claims | raw | **survivors** | Critical | Major | Minor | Info |
|---|---|---|---|---|---|---|---|
| M11 | 241 | 14 | 14 (3 downgraded) | 3 | 7 | 4 | 0 |
| M29 | 168 | 19 | 19 (1 partial) | 2 | 12 | 5 | 0 |
| M70 | 186 | 14 | **13** (1 refuted, 4 partial, 1 escalated) | 2 | 5 | 5 | 1 |
| **TOTAL** | **595** | 47 | **46** | **7** | **24** | **14** | **1** |

**Only 1 of 47 was fully refuted.** Two findings got *stronger* under attack (M29-F8: the doc's carbon trade-off is INVERTED, not merely unsupported — plantation `k` strictly exceeds natveg's in `f52_growth_par.csv`, so plantation carbon is >= natveg at every age class; M11-F6: the bioenergy subsidy is 6.5 at defaults and applied as a price floor, so `vm_bioenergy_utility` is strictly negative and the doc's prescribed `stopifnot(all(emission_costs >= 0))` fires on a correct default run).

## THE RATE — with its denominator, and its caveat

| | R55 (2026-07-16) | R58 (tonight) |
|---|---|---|
| targets | the 3 **most**-audited hubs (M10/M32/M52) | 3 **stale** hubs (M11/M29/M70) |
| claims evaluated | 498 | **595** |
| confirmed findings | 28 | **46** |
| **claim-level defect rate** | **5.6%** | **7.7%** |
| **Criticals** | **1** | **7** |

**The stale hubs are worse — but the comparison is NOT clean, and must never be quoted as if it were.** R55 *imposed* its taxonomy (auditors were handed the class to hunt); R58 was open-ended (auditors named their own classes). An open-ended auditor should find >= a lens-directed one on the same claims, so **an unknown share of the 5.6% -> 7.7% delta is method, not corpus.** The Critical ratio (1 -> 7) is the more robust signal, because Critical is defined by reader-harm triggers that both rounds shared.

**What this does NOT license:** "recency predicts defects" as a causal claim. n=3 per arm, no randomisation, different instruments. What it does license: the stale hubs are **not** clean, and the hypothesis that the recent clean rounds were an artifact of re-auditing already-audited modules **survives its first real test**.

### The structural signal — both auditors converged on it independently

Neither was told what the other found. Both reported that **the machine-checkable surface is clean and the defects have migrated to the layers checkers cannot parse**:

- **M11 (O9):** all 32 variable names, 32 citations, 27 module attributions, both formulas and all GDX symbols are correct. *Every* defect sits in prose summaries, in descriptions attached to correct identifiers, or in testing prescriptions.
- **M29 (O6):** all 16 formulas, all ~20 defaults, and 11/11 spot-checked cross-module citations are correct. The failures are (a) presolve bounds, (b) macro semantics, (c) interface *sets* vs *rows*, (d) the doc's self-description. (a) and (b) share a property: **one indirection away from the file the doc cites**. (c) exists only at the aggregate level and cannot be found by checking rows.

M29's auditor states the consequence directly: an audit reading `equations.gms` + `declarations.gms` + `input.gms` and scoring per-claim would find **zero of the Criticals** and would be justified in writing the clean-bill banner. **This is a mechanism for how "9.52 = solved" happened** — not a restatement of it.

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
