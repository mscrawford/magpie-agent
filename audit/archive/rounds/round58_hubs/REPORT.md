# R58 — adversarial round on stale hubs

**Status:** COMPLETE (2026-07-17, 00:21–01:10 CEST, autonomous overnight)
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

## THE GRADE

Mike asked for "the grade… correctly set in the context of our infrastructure." The honest answer is that **the headline grade cannot answer the question**, and that is the finding.

### 1. R57 has no rubric grade
It was not a Q-round — it asked no questions. It found 2 bugs, both `instrument_defect`. Any number quoted for R57 would be invented.

### 2. The Q-round grade is a low-power instrument — and tonight re-demonstrated it
The Q-grade (9.52, 9.57) is a mean over ~5–7 questions: a sample of ~7 against thousands of claims. It **structurally cannot detect a 5–8% defect rate.**

Tonight's QA round scored **8.375/10** on 4 questions. In the *same corpus*, the depth arm found **46 defects in 595 claims**. Both numbers are correct. They measure different things, and only one of them is a corpus statement. **A QA mean is a smoke test. It may never be quoted as evidence the corpus is clean — that is precisely the 9.52 error.**

### 3. The grades that mean something

| grade | value | what it licenses |
|---|---|---|
| **Claim-level defect rate** (stale hubs) | **46/595 = 7.7%** | the corpus is ~8% defective at depth on these modules |
| same, R55 (most-audited hubs) | 28/498 = 5.6% | **not a clean comparison** — see the method caveat above |
| **Criticals** | **7** (R58) vs **1** (R55) | the more robust signal; Critical triggers were shared by both rounds |
| **QA product smoke test** | **8.375/10** (n=4) | the docs mostly answer correctly; **licenses nothing about corpus cleanliness** |
| G1 regression anchor (M14) | **10/10** | holding |
| G2 regression anchor (`vm_carbon_stock` populators) | **9.5/10**, set exact | holding, no regression |
| **Mutation survival** | **51.2%** (was 54.9%) | **FAILS the <5% bar by 10×.** "0 findings" is still NOT licensed as "clean" |
| **Dead-to-test** | **22.9%** (was 41%) | improved, but see the denominator caveat |
| Retrofit denominator | **9 of 9** named extractors | the number that makes the dead-to-test delta interpretable |

### 4. The number I must not let you misread

**Dead-to-test 41% → 22.9% overstates the improvement.** The denominators differ: 164 → 231 functions, because **I added covered helper functions** (`_write_fixture`, `_scan_only`) which inflate the denominator with things that pass. Absolute dead count: **67 → 53**.

**And mutation survival barely moved: 54.9% → 51.2%, despite retrofitting all 9 extractors.** This is the most important negative result of the night. The two metrics measure different things:
- **dead-to-test** asks "is this function called and asserted at all?" — a neuter probe (`body → raise`) is the crudest possible test.
- **mutation survival** asks "would a one-character change in a predicate be caught?"

My retrofit fixed the first and barely touched the second. `check_consumer_attribution` is now the *worst* checker (74.8% survival) despite being the first one I retrofitted, because its large `scan_*` functions remain uncovered. **The instruments are better, not fixed.** The halt threshold (>20% survival ⇒ "fix the instruments") is still exceeded 2.5×.

### 5. Expiry
This statement expires on the **next `/sync` touching module `.gms` files.** Coverage and scope are properties of a code snapshot (`develop @ 0d7ebeb90`). Both prior "done" claims had no expiry; that, more than any threshold, is what makes this attempt different.

## What was AUTOMATED (Phase 2) — two new checkers, both replay- or live-validated

**Check 38 `check_cfg_gams_wiring`** — **a real MAgPIE bug class**, found by the M70 auditor, confirmed by me. 3 of 312 scalar `cfg$gms$` keys name a GAMS identifier that does not exist. Set them and nothing happens, silently:

| | |
|---|---|
| `config/default.cfg:673` | `s21_trade_bal_damper` (0.65) |
| `config/default.cfg:1590` | `s52_plantation_threshold` (8) |
| `config/default.cfg:2197` | `s70_feed_subst_functional_form` (1) → real name `s70_subst_functional_form` |

The M70 one means the **sigmoid feed-substitution fader is unreachable from the config surface.** Nothing else can catch this: `check_config` validates a run's cfg against `default.cfg` itself (wrong in both ⇒ consistent ⇒ passes); `manipulateConfig` is a regex substitution with no existence check; GAMS never sees the key, so no compile error is possible. **These are parent-repo bugs — NOT fixed here. They need Mike.**

**Check 39 `check_fenced_identifiers`** — closes the gap that let the M29 Critical live. Replay-validated against the real pre-fix doc. **It immediately found 2 more real phantoms in `module_17.md`** (`vm_demand`, `vm_import` in a dependency diagram, with module attributions, neither existing anywhere) — in a module this round never audited. Found by mechanization, not by an auditor, which is the point. FP rate measured down from 32/32 → 2 real / 1 suppressible before shipping.

Both advisory. **Neither wired to gating — Mike's call.**

## What was FIXED, and what was deliberately NOT

**Fixed (9):** all **7 Criticals** (M11 ×3, M29 ×2, M70 ×2) + the 2 `module_17.md` diagram phantoms. Each independently re-verified against develop with positive controls before editing.

**NOT fixed (39):** the surviving Major/Minor findings are documented in the per-module audit + refute files and left for review. Fixing 39 doc claims autonomously overnight exceeds "as you deem fit" for a corpus Mike has to trust. They are listed, evidenced, and ready.

**NOT touched (guardrail):** the 3 unadjudicated dependent-count findings and their `Module_Dependencies.md` twins. No truth number written.

## Verification log

- [x] Preconditions: lock acquired, R58-idempotence guard passed, remote=mscrawford, branch=r57-rolemap-guard, tree clean, caffeinate alive
- [x] Baseline gate: 0 errors (47 checks, 2 warnings)
- [x] Phase 1: 3 auditors returned (595 claims, open-ended taxonomy, barred from the instruments)
- [x] Findings confirmed against develop by direct read (with positive controls)
- [x] Adversarial refutation: 3 refuters; 1 of 47 fully refuted, 2 findings got stronger
- [x] Phase 2: 2 new checkers (Check 38, Check 39), both with real-bug positive controls
- [x] Phase A′ retrofit: **9 of 9** — complete, not truncated
- [x] Phase 3: `SELFCHECK_OK` confirmed BEFORE any mutation number was trusted
- [x] Phase 4 QA: ran (window was ~75% remaining, well above the 40% gate)
- [x] Gate held at 0 errors throughout; battery PASS at 27 scripts

## Guardrails honoured

- Nothing pushed.
- No truth number written for the 3 unadjudicated dependent-count findings (`module_56.md:1138/:1150`, `module_17.md:899`) or their `core_docs/Module_Dependencies.md` twins.
- No check flipped to gating.
- Gate held at 0 errors.
