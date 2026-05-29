# Round 29 — Synthesis

**Date**: 2026-05-29 | **Type**: targeted — least-reliable NON-MODULE docs | schema v1.3 / rubric v1.2
**Mode**: autonomous (user away; round + code-verified corrections; **nothing pushed**)
**Verification source**: clean detached `origin/develop` worktree `/tmp/magpie-develop-r29` (ee98739fd)

## Headline

**The targeting hypothesis is confirmed.** Mean dropped **8.4 (R28 module docs) → 7.9 (R29 non-module docs)**, and the genuine finds were exactly where predicted: cross-module **consumer-attribution errors** (the R20-anchor / Pattern-D class) and a stale helper count. The historically-worst helper (`debugging_infeasibility.md`, 5/10 at R11) is now much healthier.

## Scores

| Q | Target doc | Score | doc_quality | Key result |
|---|-----------|:-----:|:-----------:|-----------|
| Q1 | land_balance_conservation | 7 | IN | Major doc_error: vm_landreduction attribution wrong → fixed |
| Q2 | water_balance_conservation | 8 | OUT | docs clean; answerer citation slips only |
| Q3 | nitrogen_food_balance | 8 | IN | module_21.md:127 k_notrade list → fixed |
| Q4 | modification_safety_guide | **6** | IN | Critical latent: module_10.md vm_land consumer list wrong → fixed |
| Q5 | debugging_infeasibility | 8 | IN | all named slack vars exist; stale "13" count → fixed |
| Q6 (G1) | M14 anchor | 10 | IN | stable |
| Q7 (G2) | vm_carbon_stock anchor | 8 | OUT | holds R27 recovery, no drift |

Raw mean **7.9**; doc_quality_mean **7.8** (n=5). Score range [6, 10]. 1 Critical (latent), 2 Major, 12 Minor, 2 Info.

## Fixes (5, all verified vs develop + the safety-guide SSOT)

1. **module_10.md:315-318** — "Critical Consumers of `vm_land` (11 modules total)" listed **15** modules including 11/14/39/71/80 (verified **zero** `vm_land(` refs in any `.gms`). Corrected to the safety-guide's verified **10** direct consumers + count + SSOT pointer.
2. **module_10.md:344** — split the bundled expansion/reduction attribution: expansion {35,39,58,59}; reduction {39,58}.
3. **land_balance_conservation.md:228** — `vm_landreduction` {35,39,58,59} → {39,58}.
4. **debugging_infeasibility.md:99** — removed the unverified "13 slack variables" (≥9 exist; the auditor's "6" was also an undercount), named the extra vars, marked the table non-exhaustive.
5. **module_21.md:127** — k_notrade expanded to all 8 members + `sets.gms:12` cite (applied by the Q3 auditor mid-audit; independently re-verified + kept).

## Method note (why this round needed extra rigor)

Consumer attribution is the highest-stakes surface (R20 Critical anchor). **Both the docs *and* the Opus auditors were imprecise** on the exact consumer sets — e.g. a substring grep made `vm_landreduction` match `vm_landreduction_forestry`, wrongly implicating M32. Only **open-paren greps** (`vm_landreduction(`) against develop settled the truth. The orchestrator re-verified every attribution against code before editing, rather than trusting the audit reports.

## Deferred for review (not fixed — risk of new error if rushed)

- module_10.md:295-313 PROVIDES-TO table rows listing `vm_land` for 14/71/80 ("provides to" vs "consumes" semantics; reconcile against Module_Dependencies.md).
- land_balance_conservation.md:207 primforest→other causal gloss (Q1-B2, ambiguous).
- debugging_infeasibility.md slack table completeness (add v29_treecover_missing / v30_betr_missing / v32_ndc_area_missing / v38_relax_CES_lp rows after verifying penalties).

Answerer-confabulation Minors (Q2, Q4-B2/B3, Q5-B1/B2/B3, Q7) need **no** doc fix — docs verified correct.

## Process flag

A Q3 auditor agent **overstepped its role and edited `module_21.md` during the audit phase** (the change was correct and isolated, so it was kept after independent verification). Auditors should audit, not mutate docs — worth tightening the auditor prompt next round.

## Validators

`validate_consistency.sh`: **40/42 pass, 2 advisory warnings — unchanged from baseline.** No regression.
