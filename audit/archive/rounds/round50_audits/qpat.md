# Audit Report: Round 50 — Query_Patterns_Reference.md worked-example accuracy (qpat)

**Question (anchored on `core_docs/Query_Patterns_Reference.md`)**: Pick two worked query patterns that trace a concrete variable/mechanism through the model. Verify every identifier, equation, realization, and file:line against current GAMS code. Are the examples still code-accurate, or has any drifted?

**Answer audited**: chose (1) Pattern 2's tree-cover -> SOM -> CO2 three-step chain, (2) Pattern 4 Example 3 (Module 52 Chapman-Richards, MECHANISTIC).

**Ground truth**: `/tmp/magpie_develop_ro` develop worktree + `config/default.cfg`.

---

## Overall Verdict: ACCURATE
## Accuracy Score: 10/10

The answer is code-accurate on every load-bearing claim. Notably it independently surfaced a real documentation-completeness drift (the FRA 2025 growing-stock bisection calibration, default ON, that now dominates the "calibrated growth curve parameters" wording in Pattern 4 Example 3) — and that finding checks out fully against code. No Critical/Major/Minor content errors. One Informational over-hedge (see below). This is a high-quality, mechanically-grounded audit-of-an-audit; the answer's own verdicts match code.

---

## Verified Claims (correct)

### Realizations / defaults (MANDATE 8, 3)
- `cfg$gms$cropland <- "detail_apr24"`, `cfg$gms$carbon <- "normal_dec17"`, `cfg$gms$som <- "cellpool_jan23"` — all three are defaults (`/tmp/magpie_develop_ro/config/default.cfg`). Directory listing confirms each realization dir exists (`ls modules/29_cropland/`, `52_carbon/`, `59_som/`). Answer's "all confirmed as defaults" is correct.

### Pattern 2 — tree cover -> SOM -> CO2
- **Step 1**: `q29_treecover(j2) .. vm_treecover(j2) =e= sum(ac, v29_treecover(j2,ac));` at `modules/29_cropland/detail_apr24/equations.gms:83-84` — EXACT. Line 83 = equation name, line 84 = body. The doc's citation (`Query_Patterns_Reference.md:113`) is code-correct. `v29_treecover(j,ac)` and `vm_treecover(j)` both real (declared `modules/29_cropland/detail_apr24/declarations.gms`).
- **vm_treecover consumer set**: ripgrep sweep -> referenced by M29 (own), M59 (`cellpool_jan23` + `static_jan19` equations.gms), and M22 (`area_based_apr22/presolve_ini.gms:87,98,109` via `vm_treecover.l`, solution-level — MANDATE 20 case). M52 does NOT reference `vm_treecover` directly (consistent with the chain: 52 reads `vm_carbon_stock`). Doc's "used by Modules 22 and 59" is correct.
- **Step 2**: SOM target `q59_som_target_cropland` at `modules/59_som/cellpool_jan23/equations.gms:20-27`; treecover term `+ vm_treecover(j2) * i59_cratio_treecover` on line 26; whole bracket multiplied by `sum(ct,f59_topsoilc_density(ct,j2))` on line 27. `i59_cratio_treecover = 1;` at `modules/59_som/cellpool_jan23/preloop.gms:82` — EXACT (code `= 1`, doc `1.0`; identical value). Answer's structural critique is CORRECT: `f59_topsoilc_density` is a *shared* factor over (crop + SCM + fallow + treecover) terms, not a treecover-only multiplier. Answer rightly labeled the doc formula "notational compression," not a factual error.
- **Step 3**: `q59_carbon_soil(j2,land,stockType) ..` at `modules/59_som/cellpool_jan23/equations.gms:61-64`; writes `vm_carbon_stock(j2,land,"soilc",stockType)` on line 62 (doc cites `:62`). EXACT. `q52_emis_co2_actual(i2,emis_oneoff) ..` at `modules/52_carbon/normal_dec17/equations.gms:16-19`; reads `vm_carbon_stock` on RHS line 19 as a stock difference `(pcm_carbon_stock - vm_carbon_stock)/m_timestep_length`. EXACT. Answer's "52 reads, does not re-aggregate" — verified (the only equation in that file). `vm_carbon_stock` DECLARED in M56 (`price_aug22/declarations.gms:34`); the M30 hit is the look-alike `vm_carbon_stock_croparea` (`30_croparea/detail_apr24/declarations.gms:23`), NOT the same variable — answer correctly avoided any false M30/M52 declaration claim.

### Pattern 4 Example 3 — Chapman-Richards (MECHANISTIC)
- **Macro**: `$macro m_growth_vegc(S,A,k,m,ac) S + (A-S)*(1-exp(-k*(ac*5)))**m;` at `core/macros.gms:18` — EXACT, quoted verbatim by the answer.
- **S=0 special case**: `pc52_carbon_density_start(t_all,j,"vegc") = 0;` at `modules/52_carbon/normal_dec17/start.gms:9`. So the curve reduces to `A*(1-exp(-k*ac*5))^m`, matching the doc's `A*(1-exp(-k*age))^m`. Answer's "simplified form correct for S=0" — verified (holds for plantation, secdforest, and also `other` land).
- **Used in start.gms, not the optimization equation**: macro invoked at `start.gms:17,28,48`; module 52's `equations.gms` has exactly ONE equation (`q52_emis_co2_actual`, file is 20 lines). Answer's architectural nuance — verified.
- **FRA 2025 bisection calibration (answer's substantive addition) — FULLY VERIFIED**:
  - `s52_growingstock_calib` default ON: `input.gms:46  ... (1) / 1 /` — EXACT.
  - Bisection block `if(s52_growingstock_calib = 1, ...)` at `preloop.gms:23-118`; secdforest k bisection (loop `iter52`, lines 49-68) overwrites `pm_carbon_density_secdforest_ac` with calibrated `i52_k_calib_secdf` at lines 71-73; plantation bisection (84-103) recomputes `pm_carbon_density_plantation_ac` with `i52_k_calib_plant` at 114-116; matches FRA targets `f52_fra_nrf_gs`/`f52_fra_pla_gs`; log "Growing stock calibration to FRA 2025 (m3/ha)" at line 106. (Answer cited `preloop.gms:1-118`; the active block is 23-118, lines 1-22 are header/`im_vol_conv` setup — file is 118 lines, so the range is loose but not wrong.)
  - Uncalibrated copies preserved: `pm_carbon_density_secdforest_ac_uncalib` / `..._plantation_ac_uncalib` declared (`declarations.gms:10,13`), copied from pre-calibration values at `start.gms:43-44` ("Save uncalibrated growth curves before calibration overwrites pm_ params"). Consumed by M29 (`detail_apr24/preloop.gms`, tree cover on cropland), M32 (`dynamic_may24/presolve.gms`, afforestation/NDC), M35 (`pot_forest_may24/presolve.gms`, secondary-forest establishment) — matches answer's "afforestation, NDC, tree cover on cropland" list. Calibrated k stays inside M52 (no use of `i52_k_calib_*` outside module 52).
- **Feedback: Yes** — age classes advance, carbon accumulates — consistent with the per-ac growth-curve design. Correct.

---

## Bugs Found

### qpat-B1
- **Severity**: Informational
- **Class**: §1 Informational trigger "Conservative tag (issued when a stronger verification was available)"
- **Trigger**: over-hedged caveat — the answer labeled a code-correct, in-doc citation as "NOT confirmed by AI docs / latent drift risk."
- **Claim in answer**: "Line `equations.gms:83-84` — NOT confirmed by AI docs. module_29.md Section 10 cites the source as equations.gms without a line number ... Line drift is possible and the doc does not confirm it."
- **Reality**: (a) the citation IS present in the doc under audit — `core_docs/Query_Patterns_Reference.md:113` reads ``Location: `modules/29_cropland/detail_apr24/equations.gms:83-84` ``; (b) it is code-correct (q29_treecover occupies lines 83-84 in current develop). The answer cross-referenced a different doc (module_29.md Section 10) and reported "unconfirmed," missing that the audited doc itself carries the (correct) line number. Because the answer self-disclosed "No raw GAMS source was read," it could not promote this to verified — but the caveat overstates risk on a line that is in fact accurate.
- **File evidence**: `modules/29_cropland/detail_apr24/equations.gms:83-84` (q29_treecover); doc citation at `core_docs/Query_Patterns_Reference.md:113`.
- **Impact on score**: none (Informational, weight 0). Does not change the answer's P2 verdict ("all accurate"), which is correct.
- **Root cause**: answerer_style_or_framing.

---

## Latent doc bugs (recorded independent of answer score)

**None at the rubric §1.5 bar.** No load-bearing doc claim (interface var / equation / populator-consumer set / realization / default) in either worked example is WRONG vs code. Every identifier, equation name, realization, default, and file:line in Pattern 2 and Pattern 4 Example 3 resolves correctly against develop.

**Doc-drift note (sub-§1.5, informational — for the maintainer, not a required fix):** Pattern 4 Example 3 says "Parameters: Calibrated growth curve parameters (biological)." This is still *literally true* and not a §1.5 latent bug (it names no wrong identifier/equation/realization/default). But as the answer correctly observed, it is now *under-specified*: since PR-added FRA 2025 bisection calibration (`preloop.gms:23-118`, `s52_growingstock_calib` default ON), "calibrated" in a default run means FRA growing-stock-matched k (per-region bisection), with the Humpenoder-style literature k surviving only in the `_uncalib` copies used for new establishment. A one-line addition to Example 3 pointing at `preloop.gms` + the uncalib copies would make the example reflect the dominant default-run behavior. Optional enhancement; the existing text is not erroneous.

(Also confirmed NOT a bug: the doc Pattern 2 formula `vm_treecover x i59_cratio_treecover x f59_topsoilc_density` compresses a shared-factor structure but presents it as the treecover *contribution*, which is a correct subset of `q59_som_target_cropland`. The answer flagged this as compression, not error — agreed.)

---

## Missing Nuances (answer)
- Minor: the answer's "overwrites the k in `pm_carbon_density_secdforest_ac`" is shorthand — the calibration computes a calibrated k (`i52_k_calib_secdf`) and *recomputes the whole density parameter* with it inline (`preloop.gms:71-73`); the parameter does not store k. Substantively correct (effective k changes); framing only.
- The `s52_k_high_secdf = 0.1` / `s52_k_high_plant = 0.15` bisection upper bounds (`input.gms:47-48`) are the calibration's tuning knobs; not needed for the answer's point but worth knowing for "what k does the model use."
- Provenance details the answer relayed from docs (PR #869, date 2026-04-20) are not verifiable from the code tree alone (no git-history read); not load-bearing to the code-accuracy question, so not scored.

---

## Summary
Both worked examples in `Query_Patterns_Reference.md` are code-accurate in current develop: Pattern 2's tree-cover -> SOM -> CO2 chain (all identifiers, the q29_treecover :83-84 citation, i59_cratio_treecover=1 @ preloop.gms:82, the q59_carbon_soil :62 write, and the q52_emis_co2_actual :16-19 read) and Pattern 4 Example 3's Chapman-Richards macro (`core/macros.gms:18`, S=0 special case @ start.gms:9, used in start.gms not equations.gms). The answer verified all of these correctly and additionally surfaced a genuine, code-confirmed documentation-completeness drift (FRA 2025 bisection calibration, default ON). The single defect is an over-hedged caveat on the one citation (qpat-B1, Informational) that is in fact present in the audited doc and correct. Score 10/10.

**Mechanical checks**: M1 file:line citations present (yes, many) PASS; M2 active realization stated (detail_apr24/normal_dec17/cellpool_jan23, all flagged as default) PASS; M3 variable prefixes valid PASS; M4 epistemic badges present (closing 🟡 block) PASS; M5 confidence-tier vs depth — answer is honestly 🟡 (docs-only, self-disclosed) PASS; M6 closing source statement PASS.
