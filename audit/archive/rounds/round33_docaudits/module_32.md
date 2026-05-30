# Audit Report: module_32.md (Forestry) — Round 33 doc-centric audit

**Auditor**: Opus (highest capability), adversarial doc-vs-code audit
**Target doc**: `magpie-agent/modules/module_32.md`
**Ground truth**: `/tmp/magpie_develop_ro` (develop worktree) + `config/default.cfg`
**Date**: 2026-05-30
**Realization audited**: `dynamic_may24` (confirmed only realization; default per `config/default.cfg:976` `cfg$gms$forestry <- "dynamic_may24"`)

---

## Overall Verdict: MOSTLY ACCURATE (lower band)

### Accuracy Score: 6/10 (doc-quality; many citation drifts + a wrong-variable cluster + two wrong producer attributions; equation algebra and core mechanism descriptions are sound)

The doc's **equation formulas, mechanism descriptions, set definitions, scalar default VALUES, and early-file (lines ≤140) equation citations are accurate**. The errors cluster in three families:
1. **Citation drift** — every presolve.gms citation past line ~68 is off by +5/+6 lines (a block of disturbance/comment lines was inserted upstream); late-file equation citations (q32_cost_establishment onward) are off by +8/+9 lines. A handful land on *materially different* content (Major); most land on adjacent content (Minor).
2. **Wrong carbon-density variable names** — `aff` and `ndc` use the `_uncalib` carbon-density variants in code; the doc states the calibrated names in §4.5 / §9.4 / §10.2 (but correctly says `_uncalib` for ndc in §2.2 — internally inconsistent).
3. **Two wrong producer-module attributions** in the §8.2 "Receives From" table (`pm_max_forest_est` and `pm_land_conservation` both mis-listed under `10_land`).

---

## Mechanical checks
- M1 file:line citations present: PASS (abundant)
- M3 variable prefixes valid: PASS (no invented `vm_/pm_/s32_` names found; all names resolve in code)
- Realization default stated correctly: PASS (`dynamic_may24`, only realization)

---

## Verified Claims (correct) — sample

- `type32 / aff, ndc, plant /` at `sets.gms:16-17` — CONFIRMED.
- `shock_scen32 / none, 002lin2030, 004lin2030, 008lin2030, 016lin2030 /` at `sets.gms:44-46` — CONFIRMED.
- 31 equations (`rg -c "^\s*q32_" declarations.gms` = 31) — CONFIRMED.
- Scalar default VALUES all correct: `s32_est_cost_plant=2460`, `s32_est_cost_natveg=2460`, `s32_est_cost_plant_reest=1230`, `s32_recurring_cost=615`, `s32_harvesting_cost=1230`, `s32_planning_horizon=50`, `s32_rotation_extension=1`, `s32_free_land_cost=1e6`, `s32_max_aff_area=Inf`, `s32_aff_plantation=0`, `s32_max_aff_area_glo=1`, `s32_annual_aff_limit=0.03`, `s32_npi_ndc_reversal=Inf`, `s32_aff_bii_coeff=0`, `s32_hvarea=2` — all CONFIRMED against `input.gms` + `default.cfg`.
- All equation FORMULAS quoted match code verbatim (q32_cost_total, q32_cdr_aff, q32_bgp_aff, q32_aff_est, q32_land, q32_land_type32, q32_land_diff, q32_land_expansion, q32_land_reduction, q32_land_expansion_forestry, q32_land_reduction_forestry, q32_aff_pol, q32_ndc_aff_limit, q32_co2p_aff_limit, q32_max_aff, q32_max_aff_reg, q32_carbon, q32_bv_*, q32_cost_establishment [incl. new replanting-discount term], q32_cost_recur, q32_prod_forestry_future, q32_establishment_demand, q32_establishment_hvarea, q32_establishment_fixed, q32_forestry_est, q32_hvarea_forestry, q32_prod_forestry, q32_cost_hvarea, q32_land_replant) — CONFIRMED.
- Early-file equation citations (lines 21–141) all correct: q32_cost_total 21-27, q32_cdr_aff 36-39, q32_bgp_aff 41-43, q32_aff_est 46, q32_land 55-56, q32_land_type32 58-59, q32_land_*_forestry 61-65, q32_land_replant 67-70, q32_aff_pol 74-75, q32_ndc_aff_limit 79-80, q32_co2p_aff_limit 84-86, q32_max_aff(_reg) 94-100, q32_carbon 108-109, q32_land_diff 113-115, q32_land_expansion 117-119, q32_land_reduction 121-122, q32_bv_aff/ndc/plant 128-141 — CONFIRMED.
- `i32_growing_stock_at_harvest` rename (PR #869) — CONFIRMED present at `declarations.gms:24` (tDM/ha); `q32_prod_forestry` uses `im_growing_stock` at `equations.gms:249`; `i32_growing_stock_at_harvest` computed at `presolve.gms:181`. Rename narrative accurate.
- `s32_est_cost_plant_reest` replanting-discount term — CONFIRMED in `q32_cost_establishment` (`equations.gms:170`); default 1230 (`input.gms:25`); `im_timber_prod_cost` now region-dimensioned `(i2,kforestry)` (`equations.gms:172`, declared `73_timber/default/declarations.gms:17`) — CONFIRMED.
- `pm_land_plantation(j,ac)` declared `declarations.gms:59` (NEW) — CONFIRMED; consumer is Module 52 — CONFIRMED (but at wrong line, see B-09).
- `vm_cdr_aff` consumed by Module 56 (`price_aug22/equations.gms:77`) — CONFIRMED (M56 default realization is price_aug22).
- `vm_carbon_stock` correctly treated as POPULATED by M32 (forestry slice) via q32_carbon, NOT declared here (declared `56_ghg_policy/price_aug22/declarations.gms:34`, per G2 anchor) — CONFIRMED, no misattribution.
- `im_growing_stock` from Module 14 (`14_yields/managementcalib_aug19/declarations.gms:17`), `im_timber_prod_cost` + `pm_demand_forestry` from Module 73 — CONFIRMED.
- `c32_aff_mask=noboreal` (default ✓), `c32_shock_scenario=none` (default ✓), `c32_rot_calc_type=current_annual_increment` (default ✓) — CONFIRMED.

---

## Bugs Found

### B-01 (Major) — Citation drift to a DIFFERENT equation: vm_prod_forestry table cite
- **Class**: 10 (stale file:line citation) / 12 (content-level mismatch)
- **Doc line**: module_32.md:696 (§8.1 Provides-To table)
- **Claim**: `| 73_timber | vm_prod_forestry | ... | equations.gms:237-240 |`
- **Reality**: `equations.gms:237-240` is `q32_hvarea_forestry` (`v32_hvarea_forestry = v32_land_reduction(...,"plant",...)`), NOT the production equation. `vm_prod_forestry` is defined in `q32_prod_forestry` at `equations.gms:246-249` (the doc's own §4.4 cites 246-249 correctly).
- **Verify cmd**: `rg -n "q32_prod_forestry\b" .../equations.gms` → 246; `sed -n '237,240p'` shows q32_hvarea_forestry.
- **Fix**: change `equations.gms:237-240` → `equations.gms:246-249`.

### B-02 (Major) — Citation drift to a DIFFERENT equation: q32_cost_recur
- **Class**: 10/12
- **Doc line**: module_32.md:519 (§5.2)
- **Claim**: `**q32_cost_recur** (equations.gms:172-173)`
- **Reality**: `q32_cost_recur` is at `equations.gms:181-182`. Lines 172-173 are the TAIL of `q32_cost_establishment` (the discounting denominator). Citation lands on a different equation.
- **Verify cmd**: `rg -n "q32_cost_recur" .../equations.gms` → 181.
- **Fix**: `equations.gms:172-173` → `equations.gms:181-182`.

### B-03 (Major) — Citation drift to a DIFFERENT equation: q32_establishment_demand
- **Class**: 10/12
- **Doc line**: module_32.md:296 (§4.3)
- **Claim**: `**q32_establishment_demand** (equations.gms:196-200)`
- **Reality**: `q32_establishment_demand` is at `equations.gms:205-209`. Lines 196-200 are the comment block + the START of `q32_prod_forestry_future` (which the doc separately and correctly cites at 197-201). The 196-200 cite both drifts and overlaps a different equation.
- **Verify cmd**: `rg -n "q32_establishment_demand" .../equations.gms` → 205.
- **Fix**: `equations.gms:196-200` → `equations.gms:205-209`.

### B-04 (Major) — Wrong carbon-density variable for aff/ndc (calibrated vs `_uncalib`)
- **Class**: 2/7 (variable name — wrong variant selected)
- **Doc lines**: module_32.md:378 (§4.5), 853 + 857 (§9.4), 921-923 (§10.2)
- **Claim**: §4.5: "`ndc`: `pm_carbon_density_secdforest_ac`"; "`aff`: `pm_carbon_density_secdforest_ac` OR `pm_carbon_density_plantation_ac`". §9.4: "Carbon density follows `pm_carbon_density_secdforest_ac`" (s32_aff_plantation=0) / "`pm_carbon_density_plantation_ac`" (=1). §10.2: ndc → `pm_carbon_density_secdforest_ac`.
- **Reality** (`presolve.gms:58-68`): `aff` (switch=0) and `ndc` use `pm_carbon_density_secdforest_ac_uncalib`; `aff` (switch=1) uses `pm_carbon_density_plantation_ac_uncalib`. Only `plant` uses the calibrated `pm_carbon_density_plantation_ac` (`presolve.gms:65`). Both the calibrated and `_uncalib` variants are DISTINCT declared parameters in Module 52 (`normal_dec17/declarations.gms:9-13`; calibration applied in `preloop.gms`). The doc's §2.2 line 81 already states `_uncalib` for ndc correctly — so the doc is internally inconsistent.
- **Verify cmd**: `rg -n "p32_carbon_density_ac\(t,j,\"(aff|ndc|plant)\"" .../presolve.gms`; `rg -n "pm_carbon_density_secdforest_ac(_uncalib)?\b" .../52_carbon/normal_dec17/declarations.gms` (both exist).
- **Fix**: In §4.5, §9.4, §10.2 replace `pm_carbon_density_secdforest_ac` → `pm_carbon_density_secdforest_ac_uncalib` (for aff and ndc) and the s32_aff_plantation=1 / aff-switch=1 `pm_carbon_density_plantation_ac` → `pm_carbon_density_plantation_ac_uncalib`. Keep `plant` = calibrated `pm_carbon_density_plantation_ac`.

### B-05 (Major) — Wrong producer module: pm_max_forest_est attributed to 10_land
- **Class**: 6 (wrong attribution) / MANDATE 13
- **Doc line**: module_32.md:702 (§8.2 Receives-From table)
- **Claim**: `| 10_land | pm_max_forest_est | Forest establishment potential | presolve.gms:22-23, equations.gms:86 |`
- **Reality**: `pm_max_forest_est` is PRODUCED in Module 35 (`35_natveg/pot_forest_may24/preloop.gms:63`, `postsolve.gms:22`), declared in `35_natveg/pot_forest_may24/declarations.gms`. M32 only CONSUMES it (the cited `presolve.gms:22-23` is M32's read site — correct). The "From Module" cell should be 35_natveg, not 10_land. (Doc §8.3 line 720 and §8 "Depends On" line 755 correctly say Module 35 — internal inconsistency.)
- **Verify cmd**: `rg -n "pm_max_forest_est\s*\(.*\)\s*=" modules/*/*/*.gms` → only 35_natveg assigns it.
- **Fix**: change the row's "From Module" from `10_land` to `35_natveg`.

### B-06 (Major) — Wrong producer module: pm_land_conservation attributed to 10_land
- **Class**: 6 / MANDATE 13
- **Doc line**: module_32.md:703 (§8.2 Receives-From table)
- **Claim**: `| 10_land | pm_land_conservation | Avoid conflict with secdforest restoration | presolve.gms:208-210 |`
- **Reality**: `pm_land_conservation` is produced/declared in Module 22 (`22_land_conservation/area_based_apr22/declarations.gms:15`, assigned in `presolve_ini.gms`). The doc ALSO lists it correctly under `22_conservation` at line 705 — so the 10_land row is a duplicate with a wrong source. (Citation `presolve.gms:208-210` also drifted; see B-07.)
- **Verify cmd**: `rg -n "pm_land_conservation\s*\(.*\)\s*=" modules/*/*/*.gms` → only 22_land_conservation assigns it.
- **Fix**: delete the `10_land | pm_land_conservation` row (line 703) as redundant/incorrect; the `22_conservation` row (705) already covers it. Update its citation per B-07.

### B-07 (Minor) — presolve.gms citation-drift cluster (+5/+6 lines, mostly adjacent/similar content)
- **Class**: 10 (stale file:line)
- **Doc lines & corrections** (all in `presolve.gms`; develop is post-merge — verified line-by-line):
  - L80 ndc protection `:138` → `:144`
  - L91 reversal block `:143-147` → `:149-153`
  - L533 reversal recurring-cost `:146` → `:152`
  - L561 s32_shift `:77` → `:83`
  - L570 shifting logic `:83-85` → `:89-91`
  - L634 disturbance section header `:68-72` → `:74-78`
  - L647 disturbance calc `:69-70` → `:75-76`
  - L654 disturbance distribution `:70-72` → `:76,78`
  - L694 pcm_land_forestry `:96` → `:102`
  - L703/705 pm_land_conservation `:208-210` → `:214-216`
  - L710 carbon density (M52 input) `:53-62` → `:58-68`
  - L711 pm_demand_forestry `:193-199` → `:197-205`
  - L132 + L1033 carbon-density-≤20 restriction `:170` → `:176`
  - L109 aff-switch carbon density `:58-56` (also a typo) → `:58-62`
- **Reality**: a block of disturbance/comment lines (~presolve.gms:54-78) shifted all later references by +5/+6. Each lands on adjacent/similar content (Minor), except where it crosses into a different statement.
- **Verify cmd**: per-line `rg -n "<token>" .../presolve.gms` (run; results recorded above).
- **Fix**: apply the offset corrections listed.

### B-08 (Minor) — input.gms scalar citation drift (+1/+2 lines)
- **Class**: 10
- **Reality**: the scalars block starts at `input.gms:21`; the doc's input.gms citations from ~line 25 onward are off by +1 to +2 because `s32_hvarea` (line 22), `s32_est_cost_plant/natveg` (23-24) are correct but `s32_est_cost_plant_reest` is at 25 (doc says 23), shifting subsequent ones.
- **Doc lines & corrections**:
  - `s32_est_cost_plant_reest` L500 + L966 `input.gms:23` → `input.gms:25`
  - `s32_recurring_cost` L527 + L880 `input.gms:25` → `input.gms:26`
  - `s32_harvesting_cost` L547 + L885 `input.gms:26` → `input.gms:27`
  - `s32_planning_horizon` L107 + L861 `input.gms:27` → `input.gms:28`
  - `s32_rotation_extension` L185 + L1100ff `input.gms:28` → `input.gms:29`
  - `s32_free_land_cost` L219 `input.gms:32` → `input.gms:33`
  - `s32_max_aff_area` L398 `input.gms:33` → `input.gms:34`
  - `s32_aff_plantation` L847 + L1142 `input.gms:34` → `input.gms:35`
  - `s32_aff_bii_coeff` L470 `input.gms:38` → `input.gms:39`
  - `s32_max_aff_area_glo` L1163 `input.gms:39` → `input.gms:40`
  - `s32_npi_ndc_reversal` L1121 `input.gms:47` → `input.gms:48`
  - `s32_annual_aff_limit` L407 `input.gms:49` → `input.gms:50`
- **Verify cmd**: `rg -n "<scalar>" .../input.gms` (run; line numbers recorded). NOTE: `s32_est_cost_plant`/`s32_est_cost_natveg` at 23-24 and `s32_hvarea` at 22 are CORRECT — do not change those.
- **Fix**: apply the +1/+2 corrections listed.

### B-09 (Minor) — pm_land_plantation consumer citation drift
- **Class**: 10
- **Doc line**: module_32.md:962 (§10.4)
- **Claim**: "Consumer: Module 52 (`preloop.gms:83`)"
- **Reality**: M52 consumes `pm_land_plantation` at `52_carbon/normal_dec17/preloop.gms:88, 90, 94` (not 83). Consumer module is correct; only the line is wrong.
- **Verify cmd**: `rg -n "pm_land_plantation" .../52_carbon/normal_dec17/preloop.gms` → 88,90,94.
- **Fix**: `preloop.gms:83` → `preloop.gms:88` (or `:88,90,94`).

### B-10 (Minor) — Late-file equation citation drift (+8/+9 lines)
- **Class**: 10
- **Reality**: equations after the inserted replanting-discount commentary (~equations.gms:158-164) shifted down. Beyond B-01/02/03 (escalated to Major for landing on different equations), the remaining late-file cites drift onto adjacent/similar content:
  - q32_cost_establishment L484 `:157-172` → `:166-173`
  - q32_establishment_hvarea L321 `:204-208` → `:213-217`
  - q32_establishment_fixed L332 `:215-216` → `:224-225`
  - q32_forestry_est L588 `:222-223` → `:231-232`
  - q32_hvarea_forestry L353 `:228-231` → `:237-240`
  - q32_cost_hvarea L537 `:245-249` → `:254-258`
- **Verify cmd**: `rg -n "<eqname>" .../equations.gms` (run; recorded).
- **Fix**: apply the corrections listed.

### B-11 (Minor) — Missing default + missing option for c32_aff_policy
- **Class**: 4 (capability vs default) / 3 (suffix truncation of option list)
- **Doc lines**: module_32.md:825-832 (§9.2), 909
- **Claim**: "`c32_aff_policy` = none, npi, ndc"; lists only 3 options; does not state which is default.
- **Reality**: code option list is `none, npi, ndc, affexp` (`input.gms:10` comment; `sets.gms:20` `pol32 / none, npi, ndc, affexp /`). **Default is `npi`** (`config/default.cfg:1008`, `input.gms:9`). So NPI afforestation is ACTIVE in the default config — a load-bearing default the doc omits. The 4th option `affexp` is also omitted.
- **Verify cmd**: `rg -n "c32_aff_policy" config/default.cfg` → `<- "npi"`; `rg -n "pol32" .../sets.gms`.
- **Fix**: §9.2 — add `affexp` to the option list and state "Default: `npi` (NPI policy afforestation is on by default)".

### B-12 (Minor) — s32_aff_prot default not stated (default is 1 = forever)
- **Class**: 4 (capability vs default)
- **Doc line**: module_32.md:110 (§2.3)
- **Claim**: "Protection duration: Until end of planning horizon (`s32_aff_prot = 0`) OR forever (`s32_aff_prot = 1`)" — no default indicated.
- **Reality**: default is `s32_aff_prot = 1` (forever) (`input.gms:41`, `config/default.cfg:1026`, with a comment recommending 1). The doc's phrasing leads with the `=0` case, implying it is the base behavior.
- **Verify cmd**: `rg -n "s32_aff_prot" config/default.cfg` → `<- 1`.
- **Fix**: mark `s32_aff_prot = 1` (forever) as the default.

### B-13 (Informational) — Wrong file count / line count in header + summary
- **Class**: 6 (hardcoded counts drift)
- **Doc lines**: module_32.md:5 ("1,313 lines across 11 files"), 1347 ("1,313 lines of code across 11 files")
- **Reality**: `dynamic_may24/` has **9 `.gms` files** totalling **1,332 lines** (1,358 incl. parent `module.gms`). Neither "11 files" nor "1,313 lines" matches. (Low-stakes metadata.)
- **Verify cmd**: `ls -1 .../dynamic_may24/*.gms | wc -l` → 9; `wc -l .../dynamic_may24/*.gms` → 1332 total.
- **Fix**: update to "1,332 lines across 9 files" (or 10 incl. module.gms — pick a convention).

### B-14 (Minor) — realization.gms:34 cite for "does not optimize rotations"
- **Class**: 10
- **Doc lines**: module_32.md:142 (§3), 1042 (§12.1)
- **Claim**: "Rotation lengths calculated in preloop, fixed during optimization (`realization.gms:34`)" / "Does NOT optimize rotation lengths - `realization.gms:34`"
- **Reality**: the `@limitations Rotation lengths for timber plantations are not endogenous.` line is `realization.gms:36`. Line 34 is about replanted-plantation reduced cost. The CAI/preloop description is lines 23-28 (cited correctly elsewhere at L990).
- **Verify cmd**: `rg -n "@limitations" .../realization.gms` → 36.
- **Fix**: `realization.gms:34` → `realization.gms:36`.

---

## Advisory verification (pre-run checker)

The pre-run advisory asked to verify: default realization `dynamic_may24`, vm_carbon_stock POPULATOR claims (DECLARED-in-M56 vs POPULATED-here vs READ), age-class + carbon-density variable names.

- **Default realization dynamic_may24** — CONFIRMED (`config/default.cfg:976`; only dir present).
- **vm_carbon_stock populator** — CONFIRMED CORRECT in doc: M32 populates the `(j,"forestry",...)` slice via `q32_carbon` (`equations.gms:108-109`); does NOT claim to declare it; the aggregate is declared in M56 (`price_aug22/declarations.gms:34`) and READ by M52 (`q52_emis_co2_actual`) — consistent with the G2 anchor. No bug. (The doc rightly omits `vm_carbon_stock` from its "Provided to Other Modules" table.)
- **Age-class names** — doc references `ac`, `ac_est`, `ac_sub`, `acx` consistently with code; no truncated `ac0...acN` enumeration present, so MANDATE 11 not triggered. No bug.
- **Carbon-density variable names** — REFUTED for aff/ndc: see B-04 (calibrated vs `_uncalib`).

---

## Deferred (not code-verifiable / out of scope — NOT edited)

- "Centrality: Rank 4 of 46", "16 connections", "Hub Type: Central Hub" (§8.1 Dependency Chains) — sourced from a cross-module centrality analysis, not directly checkable against GAMS; not flagged.
- "5-module Forest-Carbon-Price cycle ... back to Module 32" / "Depends On: Module 56 (Carbon price)" — this is an OPTIMIZER/economic-coupling claim, not a direct interface read. M32 does NOT directly grep-read any M56 carbon-price variable (confirmed: no `carbon_price`/`cprice`/`p56` token in M32 `.gms`); the coupling is via the optimizer pricing `vm_cdr_aff`. Consistent with the doc's own "Type 1 temporal + economic optimization" framing, so not scored as a direct-consumer bug. Flag for a future deeper cross-module pass if desired.
- "Module 11 (Costs + CDR rewards)" (§8.1 Dependency Chains line 753) — CDR rewards are computed in M56 and flow to M11 via emission costs; "+ CDR rewards" is loose but not a falsifiable interface claim about M32. Not flagged.
- "$3,690/ha (3×) / $2,460/ha (2×)" Module 35 harvest-cost comparison (§9.6) — pertains to Module 35; out of scope for this doc audit (would need M35 input.gms verification).
- "Fixed in commit `9ccd6290d` (2025-11-28)" and rename "PR #869, commit `75d7ee167`" (§2.1 / §5.1) — historical commit references; not verifiable from the worktree snapshot without git archaeology; the CURRENT code state they describe (compound discounting; im_growing_stock) is confirmed, so the substantive claim is fine.

---

## Summary

module_32.md is substantively accurate on mechanism, equation algebra, set definitions, and scalar default VALUES (all 15 checked defaults correct). The defects are: (1) a systematic citation-drift cluster — presolve.gms +5/+6, late-equations +8/+9, input.gms +1/+2 — three of which land on a *different equation* (Major: B-01/02/03); (2) a wrong carbon-density variable cluster for aff/ndc (calibrated vs `_uncalib`, Major B-04, internally inconsistent with the doc's own §2.2); (3) two wrong producer-module attributions in the §8.2 table (`pm_max_forest_est`→ should be 35, `pm_land_conservation`→ should be 22; both Major B-05/06, each contradicted by correct prose elsewhere in the same doc); (4) two missing-default notes (c32_aff_policy default npi + missing affexp option; s32_aff_prot default 1). All 31 equation formulas and the rename narratives (i32_growing_stock_at_harvest, replanting discount, region-dimensioned im_timber_prod_cost) are correct.
