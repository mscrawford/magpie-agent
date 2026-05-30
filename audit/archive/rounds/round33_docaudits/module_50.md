# Round 33 Doc Audit — module_50.md (Nitrogen Soil Budget)

**Target doc**: `magpie-agent/modules/module_50.md`
**Ground truth**: `/tmp/magpie_develop_ro` (develop worktree), `config/default.cfg`
**Auditor**: Opus 4.8 (1M), adversarial doc-vs-code
**Date**: 2026-05-30

## Overall verdict: ACCURATE (9.5/10)

This is one of the cleanest module docs audited. Every load-bearing claim — default
realization, equation names, equation formulas (quoted verbatim), interface-variable
declaration lines, upstream source-module attributions, downstream consumer set, the M51
emission-rescaling formula, the MACC-transformation formula, scalar defaults, config-switch
defaults, and the M51 citation line numbers — verifies against current develop code. Only one
concrete, reproducible discrepancy (a Minor off-by-one citation), plus a few informational
imprecisions that do not mislead.

The pre-run advisory is **REFUTED on all substantive points**:
- Default realization `macceff_aug22` — CONFIRMED (`config/default.cfg:1479`; only realization dir present).
- `q50_nr_bal_crp` and the cropland nitrogen-budget equation/variable names — CONFIRMED
  (`equations.gms:14-16`, declared `declarations.gms:25`; vars `vm_nr_eff`, `v50_nr_inputs`,
  `v50_nr_withdrawals` all in `declarations.gms`).
- `im_maccs_mitigation` reader claim — CONFIRMED (M50 reads it at `presolve.gms:56,58,61,63`;
  produced by M57 `on_aug22`). Only the cited line pair `56, 57` is off by one (see Bug 50-B1).
- Consumer sets — CONFIRMED exact (see below).

---

## Claims verified correct

### Realization / config
- Active/default realization `macceff_aug22`: `config/default.cfg:1479` `cfg$gms$nr_soil_budget <- "macceff_aug22"`. Only realization directory present (`ls modules/50_nr_soil_budget/` → `macceff_aug22`). ✓
- `s50_fertilizer_costs = 738` USD17MER/tN: `input.gms:29` `/ 738 /`. ✓ (Module scalar, correctly NOT in default.cfg.)
- `s50_maccs_global_ef = 1`: `input.gms:30` `/1/`. ✓
- `s50_maccs_implicit_nue_glo = 0.5`: `input.gms:31` `/0.5/`. ✓
- `c50_scen_neff` default `baseeff_add3_add5_add10_max65`: `input.gms:11`. ✓
- `c50_scen_neff_pasture` default `constant_min55_min60_min65`: `input.gms:21`. ✓
- `c50_dep_scen` default `history`: `input.gms:25`. ✓
- Config-switch block cited as `input.gms:11-26`: setglobals at 11,12,21,22,25 — within range. ✓

### Equations (names + formulas quoted verbatim, all line citations exact)
- `q50_nr_bal_crp` `equations.gms:14-16` ✓ (verbatim match)
- `q50_nr_bal_pasture` `equations.gms:55-59` ✓
- `q50_nr_inputs` `equations.gms:22-32` ✓ (full 9-term RHS quoted correctly)
- `q50_nr_inputs_pasture` `equations.gms:74-80` ✓
- `q50_nr_withdrawals` `equations.gms:36-43` ✓ ((1-NDFA)*(...) - seed structure correct)
- `q50_nr_withdrawals_pasture` `equations.gms:83-85` ✓
- `q50_nr_surplus` `equations.gms:46-49` ✓
- `q50_nr_surplus_pasture` `equations.gms:62-66` ✓
- `q50_nr_deposition` `equations.gms:88-90` ✓
- `q50_nr_cost_fert` `equations.gms:94-97` ✓
- All equation names confirmed in `declarations.gms:24-33`. ✓

### MACC transformation (Section 11)
- Comment formula `MACCs_T = MACCs_O * NUE_b / (1 + MACCs_O * (NUE_b - 1))` at `presolve.gms:40` — doc's displayed formula matches verbatim. ✓
- Approach 1 `E_1 = I_1 * EF * (1 - MACCs_O)` (`presolve.gms:16`) and Approach 2 `E_2 = I_2 * (1 - NUE_2)/(1 - NUE_ef) * EF` (`presolve.gms:18`) — doc matches. ✓
- `vm_nr_eff.fx(i) = 1 - (1-i50_nr_eff_bau(t,i)) * (1 - i50_maccs_mitigation_transf(t,i));` and pasture analogue at `presolve.gms:76-77` — quoted verbatim. ✓ Variables FIXED via `.fx`. ✓

### Interface variables — declarations (Section 7, declarations.gms:10-20)
All 11 variables map to the exact declared lines: `vm_nr_inorg_fert_reg`(10), `vm_nr_inorg_fert_costs`(11), `vm_nr_eff`(12), `vm_nr_eff_pasture`(13), `v50_nr_inputs`(14), `v50_nr_withdrawals`(15), `v50_nr_surplus_cropland`(16), `v50_nr_inputs_pasture`(17), `v50_nr_withdrawals_pasture`(18), `v50_nr_surplus_pasture`(19), `v50_nr_deposition`(20). ✓
- `i50_nr_eff_bau`(declarations.gms:43), `i50_nr_eff_pasture_bau`(44) — Section 8 citations correct. ✓

### Upstream source-module attributions (Section 6.1) — all confirmed by declaration-site grep
- `vm_dem_seed`→M16, `vm_prod_reg`→M17, `vm_res_recycling`→M18 (`18_residues/.../declarations.gms`), `vm_res_biomass_ag/bg`→M18, `vm_area`→M30 (`30_croparea`), `vm_fallow`→M29 (`29_cropland`), `vm_manure_recycling`+`vm_manure`→M55 (`55_awms`), `vm_nr_som_fertilizer`→M59 (`59_som`), `vm_land`→M10, `im_maccs_mitigation`→M57. ✓
- M50-side equation line citations for each (eqns 42, 39/85, 24, 40-41, 25, 26, 27, 28/77, 30, 79/90) all verified against `equations.gms`. ✓

### Downstream consumer set (Section 6.2) — EXACT, no phantoms, no omissions
Verified via `grep -rln` over `modules/` (cross-checked, with positive control `vm_land` in core/):
- `vm_nr_inorg_fert_costs`: consumed outside M50 only by **M11** (`11_costs/default/equations.gms:24`, cost aggregation). ✓
- `vm_nr_eff`: consumed outside M50 only by **M51** (`51_nitrogen/rescaled_jan21/equations.gms:26,34,46,59`). ✓ — doc's exact line list.
- `vm_nr_eff_pasture`: consumed outside M50 only by **M51** (`equations.gms:37,80`). ✓ — doc's exact line list.
- `vm_nr_inorg_fert_reg`: consumed outside M50 only by **M51** (`equations.gms:33,36`). ✓ — doc's exact line list.
- No consumers in `core/` (confirmed: `vm_nr_eff`, `vm_nr_inorg_fert*` absent; positive control `vm_land` present in `core/macros.gms`). ✓
- M51 rescaling formula `N_loss = N_inorganic_fert / (1 - SNUpE_base) × (1 - SNUpE)` matches `q51_emissions_inorg_fert` at `51_nitrogen/rescaled_jan21/equations.gms:33-34`. ✓

### Sets (Section 10)
- `scen_neff_cropland50` at `sets.gms:13-20` (doc cites 13-20) ✓; doc lists a representative subset, explicitly framed as "Available scenarios" (no count claimed → no truncation bug).
- `scen_neff_pasture50` at `sets.gms:22-23`: `{constant, constant_min55_min60_min65}` — doc lists both exactly. ✓
- `dep_scen50` = `{history}` (`sets.gms:25-26`) — consistent with doc's "currently only has history". ✓

### Data source / deposition
- `f50_atmospheric_deposition_rates` from `input/f50_AtmosphericDepositionRates.cs3`: `input.gms:140-142`. ✓
- Section 8 parameter declaration lines (89, 96, 104, 111, 126, 133, 140) all verified. ✓

### preloop (Section 10.1, 12 item 10)
- `preloop.gms:24-41` loop quoted (cropland branch) matches code verbatim; pasture branch elided but consistent. ✓
- Country-switch / region-share calc `preloop.gms:13-21` ✓.

### Self-flagged source-code label issue (Section 7 note, lines 298-301)
- `declarations.gms:12-13` DO label `vm_nr_eff`/`vm_nr_eff_pasture` as "(Tg N per yr)" while they are dimensionless efficiency fractions (used as multipliers in `q50_nr_bal_crp`). The doc CORRECTLY identifies this as a source-code documentation error. This is accurate meta-commentary, not a doc bug. ✓

---

## Bugs found

### 50-B1 (Minor) — im_maccs_mitigation citation off by one (adjacent related content)
- **Class**: Stale/off-by-few file:line citation (Bug_Taxonomy 10; rubric §1 Minor "off-by-few line citation where adjacent lines say similar things").
- **doc_line**: module_50.md:249 (Section 6.1 dependency table row) — also echoed implicitly in Section 11.1 text.
- **Claim in doc**: `| 57_maccs | im_maccs_mitigation | MACC curves for N2O mitigation | presolve.gms:56, 57 |`
- **Reality in code**: `im_maccs_mitigation` is READ at `presolve.gms:56` (cropland transform RHS) and `presolve.gms:58` (pasture transform RHS). Line 57 is the LHS assignment `i50_maccs_mitigation_pasture_transf(t,i) =` and does NOT reference `im_maccs_mitigation`. The two actual read lines are 56 and 58 (also 61, 63 in the else-branch when `s50_maccs_global_ef=0`).
- **File evidence**: `modules/50_nr_soil_budget/macceff_aug22/presolve.gms:56` (read), `:57` (LHS `i50_maccs_mitigation_pasture_transf(t,i) =`), `:58` (read).
- **Severity rationale**: line 57 sits between the two reads and contains the closely-related pasture-transform parameter being defined; a careful reader is not misled into a wrong edit. Tie-breaker pulls to Minor (not Major) because the cited content is adjacent and topically identical (still MACC transform). Off-by-one only.
- **Proposed fix**: change `presolve.gms:56, 57` to `presolve.gms:56, 58` in the Section 6.1 table row.

---

## Deferred (not code-verifiable or too minor to edit; NOT bugs)

1. **Section 8 dimension labels use `t` where code uses `t_all`** (f50_snupe_base, f50_nue_base_pasture, f50_nr_fix_ndfa, f50_nitrogen_balanceflow, f50_nr_fixation_rates_pasture, f50_atmospheric_deposition_rates). Code: `input.gms:89,96,104,111,133,140` all use `t_all`. `t_all` is the superset of `t`; the simplification does not change parameter meaning for a reader. Informational; not editing.
2. **Section 11.1 implementation range `presolve.gms:54-65`**: the `if/else` block actually runs lines 54-64 (line 64 = `);`, line 65 blank). Overshoots by one blank line. Informational off-by-one; not editing.
3. **Bottom "Interface Variables" table (module_50.md:890-891) units "Tg N/yr" for vm_nr_eff/vm_nr_eff_pasture**: faithfully reproduces the (wrong) GAMS source label, and Section 7 already flags it as a source-code error and states they are fractions. Internally self-correcting; the doc is reporting code truth + the caveat. Not a doc bug.
4. **Scenario-name semantics** (e.g., "baseeff_add3_add5_add10_max65 = +3% by 2030, +5% by 2050, +10% by 2100, max 65%"): depends on input `.cs4` data values not readable here. Cannot confirm the exact percentage trajectory from code; doc's interpretation is plausible from the name. Deferred.
5. **Section 9 "binary" units label for s50_maccs_global_ef**: code comment says "(binary)" and value `/1/`. Consistent. (Listed for completeness; verified, not a bug.)

---

## Mechanical checks
- M1 (file:line citations present): PASS (dense, accurate).
- M2 (active realization stated): PASS (`macceff_aug22`, matches default).
- M3 (variable prefixes valid): PASS (all vm_/v50_/i50_/f50_/s50_/c50_ names verified against declarations).
- Variable-name fabrication: NONE found. Equation-name fabrication: NONE found.

## Bottom line
Doc quality is excellent. One Minor citation fix (50-B1). Advisory concerns refuted. No
Critical/Major issues: no wrong realization, no inverted defaults, no phantom or omitted
consumers, no fabricated formulas or variable/equation names.
