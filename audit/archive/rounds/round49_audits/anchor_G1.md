# Audit Report: G1 (Module 14 yields — default realization + equations)

**Round**: 49 (calibration anchor, regression)
**Auditor**: Opus 4.8
**Date**: 2026-06-06

## Overall Verdict: ACCURATE
## Accuracy Score: 9/10

---

## Ground truth (verified this session against /tmp/magpie_develop_ro)

- **Default realization**: `managementcalib_aug19`
  - `config/default.cfg:354` → `cfg$gms$yields <- "managementcalib_aug19"          # def = managementcalib_aug19`
  - Only two dirs exist: `modules/14_yields/input/` and `modules/14_yields/managementcalib_aug19/` (the latter is the sole realization).
- **Equations in `modules/14_yields/managementcalib_aug19/equations.gms`**: exactly 2.
  - `q14_yield_crop(j2,kcr,w)` — defined at line 14 (body 15-16).
  - `q14_yield_past(j2,w)` — defined at line 35 (body 36-39).
  - `grep 'q14_'` on equations.gms returns ONLY those two definition lines (lines 14, 35).
  - declarations.gms confirms the same two equations (lines 30-31) plus their `oq14_*` reporting twins (lines 37-38, which are output-parameter declarations, not equations).
- **`q14_yieldcalib`**: does NOT exist anywhere in `modules/14_yields/` (rg exit=1; positive control — `q14_yield_crop`/`q14_yield_past` DO match, proving the search works). Matches the R22 correction.

Positive control passed (sibling tokens `q14_yield_crop`/`q14_yield_past` found where expected); absence of `q14_yieldcalib` cross-checked by two independent reads (full `cat -n` of equations.gms + `rg` over the whole module dir).

---

## Verified Claims (correct)

- **Default realization `managementcalib_aug19`**: CORRECT (`config/default.cfg:354`). The answer sources it from the doc header rather than default.cfg, but the value is right and matches default.cfg.
- **Exactly 2 equations**: CORRECT — count is right (Pattern 6 hardcoded-count check passes).
- **Equation names `q14_yield_crop`, `q14_yield_past`**: CORRECT, exact match to code (no confabulation; `q14_yieldcalib` correctly absent).
- **`q14_yield_crop` mechanism**: CORRECT. "Scales `i14_yields_calib` by `vm_tau(j2,"crop")` / `fm_tau1995(h2)`" matches equations.gms:15-16 exactly. `vm_yld(j2,kcr,w)` LHS correct.
- **`q14_yield_past` mechanism**: CORRECT. Management factor `pm_past_mngmnt_factor`, spillover via `s14_yld_past_switch`, and crucially **`pcm_tau` (previous time step, not current)** all match equations.gms:37-39 exactly. The pcm_tau vs vm_tau distinction is subtle and the answer got it right.
- **All variable names valid**: `i14_yields_calib`, `vm_tau`, `fm_tau1995`, `vm_yld`, `pm_past_mngmnt_factor`, `pcm_tau`, `s14_yld_past_switch` — all confirmed in code. M3 pass.

---

## Bugs Found

### G1-B1 (citation range imprecision — pasture equation)
- **Severity**: Minor (tie-breaker pulled down from Major; tier_uncertainty: true)
- **Class**: 10 (stale/imprecise file:line citation)
- **Trigger matched**: §1 Minor — "Off-by-few line citation where adjacent lines say similar things."
- **Claim in answer**: "`q14_yield_past` (`equations.gms:24-39`)"
- **Reality in code**: the equation is defined at line 35 (body 35-39). Lines 24-33 are `*'` doc comments *describing* this very equation (management factor, spillover). The cited start (24) over-extends 11 lines into the preceding comment block; the end (39) is exact.
- **File evidence**: `modules/14_yields/managementcalib_aug19/equations.gms:24-39` — line 24 is `*' In the case of pasture yields...`, line 35 is `q14_yield_past(j2,w) ..`.
- **Why Minor not Major**: the §1 Major citation-drift trigger requires the cited content to "say something materially different" or mislead a careful reader. Here the over-extended lines are the equation's OWN documentation (same topic), the equation IS within the range, and the end line is exact. A reader lands on a comment that describes the cited equation — not different content. Downgraded per tie-breaker.

### G1-B2 (citation range imprecision — crop equation)
- **Severity**: Informational
- **Class**: 10
- **Trigger matched**: §1 Informational (range slightly loose; no reader harm).
- **Claim in answer**: "`q14_yield_crop` (`equations.gms:14-20`)"
- **Reality in code**: equation header at line 14 (exact start), body ends line 16. Lines 18-20 are `*'` comments describing the crop calc. Range end over-extends 4 lines into the equation's own documentation. Start is exact.
- **File evidence**: `equations.gms:14` = `q14_yield_crop(j2,kcr,w) ..`; lines 18-20 = doc comments. 0 weight.

---

## Mechanical checks (NOT bugs — §2 indicators, 0 score weight)

| Check | Result | Note |
|-------|--------|------|
| M1 file:line present | PASS | two `equations.gms:NN-NN` citations |
| M2 active realization stated | PASS | `managementcalib_aug19` named as default |
| M3 variable prefixes valid | PASS | all vm_/pm_/i14_/fm_/s14_/pcm_ valid |
| M4 epistemic badges present | **FAIL** | no 🟢/🟡/🟠 anywhere → §1 Informational, 0 weight |
| M5 tier matches depth | N/A | no tiers present (M4 fail) |
| M6 closing source statement | **FAIL** | ends with "Answer written to ..." not "Verified against modules/14_yields/.../equations.gms" → §1 Informational, 0 weight |

M4/M6 failures are real but map to Informational (§1 "Missing or malformed closing block") which carries 0 weight in the score formula. They are recorded as quality indicators, consistent with §2 ("Failures are NOT bugs"). For a calibration anchor these are stable, low-stakes style gaps.

---

## Score computation

raw_severity_weighted = 4·0 (Critical) + 2·0 (Major) + 1·1 (Minor: B1) + 0·1 (Informational: B2) = 1
score_0_10 = max(0, 10 − 1) = **9**

---

## drift_observed: FALSE

The answer matches the expected ground-truth summary in every load-bearing way:
- Default realization `managementcalib_aug19` ✓
- Exactly 2 equations ✓
- `q14_yield_crop` + `q14_yield_past` ✓ (and `q14_yieldcalib` correctly NOT listed — the R22 correction held)
- Mechanisms accurate, all variable names valid, pcm_tau-vs-vm_tau distinction correct.

The only deviations are line-range imprecision (citations over-extend into the equations' own doc comments) and missing epistemic-footer/badges (0-weight style). None of these depart from the expected summary's substance. Nothing near this anchor appears broken.

## Missing nuances (non-scoring)
- Could note that `oq14_yield_crop`/`oq14_yield_past` exist as reporting *output parameters* (declarations.gms:37-38) but are not equations — the answer correctly excluded them, so no nuance gap, just a completeness FYI.
- The default value is sourced from the module doc header rather than `config/default.cfg:354`; value is correct but reading default.cfg directly would be the rubric-preferred provenance (calibration intent (a)).

## Summary
Substantively correct calibration anchor: right default realization, right equation count, right equation names, accurate mechanisms including the subtle `pcm_tau` (previous-timestep) detail, no confabulated identifiers, `q14_yieldcalib` correctly absent. One Minor citation-range imprecision (pasture range starts 11 lines early in the equation's own comments) + one Informational (crop range loose) + missing epistemic badges/closing statement (0-weight). Score 9/10, no drift.
