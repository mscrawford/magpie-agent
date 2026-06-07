# Audit Report: NFB (Module 50 soil nitrogen budget trace)

## Overall Verdict: ACCURATE
## Accuracy Score: 9/10

Question (anchored on `cross_module/nitrogen_food_balance.md`): trace the M50 soil-N budget — the balance equation, input/withdrawal/loss terms, and the interface variables carrying N from M50 → M51 and M55 → M50/M51, with DECLARED-vs-POPULATED attribution and file:line.

Ground truth: develop worktree `/tmp/magpie_develop_ro`. Defaults from `config/default.cfg`.

---

## Realizations / defaults (all correct)

`config/default.cfg`:
- `cfg$gms$nr_soil_budget <- "macceff_aug22"` ✓ (M50 has only this realization + `input/`)
- `cfg$gms$nitrogen <- "rescaled_jan21"` ✓ (M51: `off`, `rescaled_jan21`)
- `cfg$gms$awms <- "ipcc2006_aug16"` ✓ (M55: `off`, `ipcc2006_aug16`)

The answer named all three correct defaults up front (M2 pass).

---

## Verified Claims (correct)

### Balance equations
- TWO balance equations (crop + pasture), correctly distinguished:
  - `q50_nr_bal_crp(i2)` at `modules/50_nr_soil_budget/macceff_aug22/equations.gms:14-16`; form `vm_nr_eff(i2) * v50_nr_inputs(i2) =g= sum(kcr, v50_nr_withdrawals(i2,kcr));` — verified verbatim, including the `=g=` inequality. ✓
  - `q50_nr_bal_pasture(i2)` at `equations.gms:55-59` with `vm_nr_eff_pasture` — verified. ✓

### Cropland input terms (`q50_nr_inputs`, equations.gms:22-32) — all 9 correct
Verified line-by-line: `vm_res_recycling`(24), BNF legume `vm_area*f50_nr_fix_area`(25), BNF fallow `vm_fallow*f50_nr_fix_area("tece")`(26), `vm_manure_recycling`(27), `vm_manure(...,"stubble_grazing",...)`(28), `vm_nr_inorg_fert_reg(...,"crop")`(29), `vm_nr_som_fertilizer`(30), `f50_nitrogen_balanceflow`(31), `v50_nr_deposition(...,"crop")`(32). Every per-row citation correct. `f50_nr_fix_area` (input.gms:126), `f50_nitrogen_balanceflow` (input.gms:111) confirmed as parameters → answer's parameterization-not-mechanistic framing for BNF/deposition is correct.

### Pasture input terms (`q50_nr_inputs_pasture`, equations.gms:74-80) — 4 terms, correct
grazing manure(77), `vm_nr_inorg_fert_reg(...,"past")`(78), `vm_land(j2,"past")*f50_nr_fixation_rates_pasture`(79), `v50_nr_deposition(...,"past")`(80). ✓ (count "four" correct.)

### Withdrawals
- `q50_nr_withdrawals` (eq:36-43): `(1 - f50_nr_fix_ndfa)*(vm_prod_reg*fm_attributes + vm_res_biomass_ag + vm_res_biomass_bg) - vm_dem_seed*fm_attributes`. Answer's NDFA description and the seed-subtraction sign are correct. ✓
- `q50_nr_withdrawals_pasture` (eq:83-85): `vm_prod_reg(i2,"pasture")*fm_attributes("nr","pasture")`. ✓
- Surplus residual `q50_nr_surplus`(46-49) + `q50_nr_surplus_pasture`(62-66) = inputs − withdrawals. ✓

### Withdrawal/input var DECLARED-by attribution (all correct, whole-tree greps)
`vm_prod_reg`→M17 (`17_production/flexreg_apr16/declarations.gms:10`); `vm_res_biomass_ag/bg`, `vm_res_recycling`→M18; `vm_dem_seed`→M16 (`16_demand/sector_may15/declarations.gms:13`); `vm_nr_som_fertilizer`→M59; `vm_fallow`→M29; `vm_area`→M30; `vm_land`→M10. ✓

### M50 interface vars: DECLARED vs POPULATED (correct, the MANDATE-18 spine)
- `vm_nr_inorg_fert_reg` DECLARED `50_.../declarations.gms:10` (positive var, solver-optimized) ✓
- `vm_nr_eff` DECLARED `declarations.gms:12`, POPULATED `presolve.gms:76` via `.fx` ✓
- `vm_nr_eff_pasture` DECLARED `declarations.gms:13`, POPULATED `presolve.gms:77` via `.fx` ✓
- "FIXED not optimized" claim verified: `vm_nr_eff.fx(i) = 1 - (1-i50_nr_eff_bau)*(1-i50_maccs_mitigation_transf)` at presolve:76-77. ✓

### M50 → M51 consumption (paren AND attribute greps run; only M50+M51 consume)
- `vm_nr_eff` consumed M51 `rescaled_jan21/equations.gms:26,34,46,59` ✓
- `vm_nr_eff_pasture` consumed M51 `equations.gms:37,80` ✓
- `vm_nr_inorg_fert_reg` consumed M51 `equations.gms:33,36` ✓ (whole-tree: only M50 and M51 consume it — no missed consumer)

### M55 declarations / populators (correct)
- `vm_manure` DECLARED `55_awms/ipcc2006_aug16/declarations.gms:19`, `vm_manure_recycling` :21, `vm_manure_confinement` :22 ✓
- POPULATED: `vm_manure_recycling` by `q55_manure_recycling` (LHS line 84) ✓; `vm_manure` by `q55_bal_manure` (eq 68-71, LHS 69) ✓; `vm_manure_confinement` by `q55_manure_confinement` (LHS 76) ✓

### M55 → M50 and M55 → M51 (correct, including the exact lines the doc gets wrong — see latent bug)
- M55→M50: `vm_manure_recycling` at M50 eq:27; `vm_manure(...,"stubble_grazing",...)` at M50 eq:28; `vm_manure(...,"grazing",...)` at M50 eq:77. ✓
- M55→M51: `vm_manure_confinement` at M51 eq:69 (`q51_emissionbal_awms`) ✓; `vm_manure(...,awms_prp,...)` at M51 eq:**78** (`q51_emissionbal_man_past`) ✓; `vm_manure_recycling` at M51 eq:25 (`q51_emissions_man_crop`) ✓
- `awms_prp = {grazing, stubble_grazing}` verified at `55_awms/ipcc2006_aug16/sets.gms:13-14`. ✓
- "`vm_manure_recycling` consumed by BOTH M50 and M51" verified. ✓

### Defaults / scalars
- `s51_snupe_base = 0.5` — VERIFIED (literal `grep -F`): `51_nitrogen/rescaled_jan21/input.gms:8` `Scalar s51_snupe_base ... / 0.5 /;`; used in eq at 26,34,46,59. `s51_nue_pasture_base = 0.5` at input.gms:9; used at 37,80. (Note: an `rg` display artifact initially rendered these as a scalar `n`/`(1-n)`; literal `-F` grep + Read + `sed` all confirm the real names are `s51_snupe_base`/`s51_nue_pasture_base`. Positive control passed.)

### Architecture claims (correct)
- "M51 does not read the surplus variable directly" — VERIFIED: `v50_nr_surplus_cropland`/`v50_nr_surplus_pasture` consumed only inside M50 (declarations/equations/postsolve); not in M51. ✓
- "M50 does not calculate emissions; passes efficiency to M51 which reconstructs losses" — consistent with M51 NUE-rescaling form. ✓
- Illustrative NUE formula `Emissions = N_source/(1-s51_snupe_base)*(1-vm_nr_eff)*EF` matches q51 structure (eq 25-27) and is labeled illustrative. ✓

---

## Bugs Found

### NFB-B1 — "eight terms" miscount for cropland inputs
- **Severity**: Minor
- **Class**: 6 (Hardcoded counts drift)
- **Trigger**: §1 Minor ("Wrong detail, but a careful reader wouldn't be misled into action").
- **Claim in answer**: "Cropland (`q50_nr_inputs`, `equations.gms:22-32`) — **eight terms**:" — followed by a table with **9 rows**.
- **Reality in code**: `q50_nr_inputs` has **9** RHS terms (lines 24-32). The answer's own table enumerates all 9 correctly with correct per-row citations; only the prose header undercounts.
- **File evidence**: `modules/50_nr_soil_budget/macceff_aug22/equations.gms:22-32` (9 summed terms).
- **Root cause**: answerer_confabulation (the docs state no term count; this is the answerer's own miscount). Self-contradicting with its own correct table → not misleading to a careful reader.
- **Anchor reference**: weaker analogue of R6 "22 vs 17 equations" (that was Major because the wrong count WAS the claim; here the enumeration is correct and complete, so Minor).

### NFB-B2 — garbled citation for s51_snupe_base
- **Severity**: Informational
- **Class**: 10/16-style (citation format), but content correct
- **Trigger**: §1 Informational (style/format; tie-breaker down from Minor).
- **Claim in answer**: "`s51_snupe_base = 0.5` (`module_51.md input.gms:8`)" — conflates the markdown doc name with the code file, omits the realization path.
- **Reality in code**: correct location is `modules/51_nitrogen/rescaled_jan21/input.gms:8`. Value 0.5, scalar name, and line 8 are all correct; only the path is malformed (and trivially resolvable — M51's only active realization is `rescaled_jan21`).
- **Root cause**: answerer_style_or_framing.

No Critical or Major bugs.

**Score**: max(0, 10 − 4·0 − 2·0 − 1·1) = **9**. (Informational contributes 0.)

---

## Latent doc bugs (recorded independent of answer score — §1.5)

### NFB-L1 — module_55.md:265 cites wrong line for `vm_manure(...,awms_prp,...)`
- **Doc claim**: `modules/.../magpie-agent/modules/module_55.md:265`: "`vm_manure(i,kli,awms_prp,npk)`: Manure from pasture/range/paddock systems (Mt N) (`equations.gms:69`)" — in the M51-consumers subsection.
- **Code reality**: M51 `rescaled_jan21/equations.gms:69` is `vm_manure_confinement(i2,kli,awms_conf,"nr")` (a DIFFERENT variable, `awms_conf` not `awms_prp`). The `vm_manure(...,awms_prp,...)` read is at `equations.gms:78` (inside `q51_emissionbal_man_past`). The only paren `vm_manure(` occurrence in M51 equations is line 78.
- **Why latent**: the ANSWER got this right (cited M51 eq:78 and named `q51_emissionbal_man_past`), beating the doc. A future answerer trusting module_55.md:265 would mis-cite line 69 and risk conflating `vm_manure`/`vm_manure_confinement`.
- **Severity (future-reader harm)**: Minor (tie-breaker down from Major; `tier_uncertainty: true`). Same file, adjacent equation block; the q51 equation name is correct elsewhere in the doc, so a careful reader self-corrects. The conflation of the two manure variables is the residual risk.
- **Root cause**: doc_error_answerer_beat_it.
- **Fix**: change module_55.md:265 `equations.gms:69` → `equations.gms:78`.

Note: module_55.md:264 (`vm_manure_confinement ... equations.gms:76`) refers to the M55 POPULATION site (q55_manure_confinement LHS at 76) and is correct; module_51.md:238 (`vm_manure_confinement ... equations.gms:69`) refers to the M51 CONSUMPTION site and is also correct. Only :265 swapped the line.

---

## Missing Nuances (not bugs)
- The answer (correctly, given the question's M50→51 / →55 scope) does not mention M53 reads `vm_manure(...,"confinement",...)` for CH4. Whole-tree grep confirms M53 is a real `vm_manure` consumer (`53_methane/ipcc2006_aug22/equations.gms`), but it is out of scope here. Not a bug.
- NDFA range "0.5-0.8 for legumes" is a 🔵 domain claim about `f50_nr_fix_ndfa` data values (a .cs4 input not read here); hedged ("can be"), so acceptable. The (1-NDFA) factor and its placement are code-verified.

## Summary
Near-flawless cross-module trace. Realizations, both balance equations, all 9 cropland + 4 pasture input terms, withdrawal terms, the DECLARED/POPULATED/READ distinctions for `vm_nr_eff`/`vm_nr_eff_pasture`/`vm_nr_inorg_fert_reg` and the M55 manure variables, the M50→M51 and M55→M50/M51 interface wiring, `awms_prp` membership, and `s51_snupe_base = 0.5` are all verified correct against current develop, with accurate file:line citations. Two trivial answer blemishes (a self-contradicting "eight"-vs-9 term miscount → Minor; one garbled citation path → Informational) give a score of 9. One latent doc citation error (module_55.md:265 line 69→78) was beaten by the answerer and is fixed regardless.
