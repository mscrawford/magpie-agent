# Audit Report: water_scarcity_scenarios.md (Round 32 doc audit)

**Target**: `agent/helpers/water_scarcity_scenarios.md`
**Ground truth**: `/tmp/magpie_develop_ro` GAMS code + `config/default.cfg`
**Auditor**: Opus adversarial doc auditor
**Date**: 2026-05-30

## Overall Verdict: MOSTLY ACCURATE
## Accuracy Score: ~7/10 (2 Major + 1 Minor)

This is an unusually accurate, code-grounded helper. The core constraint equation, all interface variable/equation names, the irrigation-efficiency formula, every config default I checked, the EFP ramp logic, the groundwater-buffer logic, and both climate-scenario switch behaviors are all faithful to develop. The errors are concentrated in (a) one wrong mechanism description of the NON-default `agr_sector_aug13` realization, and (b) one internally-contradictory citation for the groundwater buffer.

---

## Pre-run advisory verdict

Advisory said: "Never validated. Verify module-42/43 switch names (e.g. s42_*, c42_*), realization names, and water-variable names (vm_watdem, v43_watavail) against develop module code + config/default.cfg."

**Verdict: REFUTED for the names themselves.** All switch names, realization names, and water-variable names are CORRECT against develop. Specifically verified-correct: `vm_watdem`, `v43_watavail`, `v42_irrig_eff`, `vm_water_cost`, `vm_AEI`, `vm_cost_AEI`, `q43_water`, `q42_water_demand`, `q42_water_cost`, `q41_area_irrig`, `q41_cost_AEI`, `oq43_water`, `ov43_watavail`; realizations `all_sectors_aug13` (default), `agr_sector_aug13`, `total_water_aug13` (default), `endo_apr13` (default); switches `c42_watdem_scenario`, `s42_watdem_nonagr_scenario`, `s42_irrig_eff_scenario`, `s42_irrigation_efficiency`, `s42_env_flow_scenario`, `s42_env_flow_fraction`, `s42_env_flow_base_fraction`, `c42_env_flow_policy`, `s42_efp_startyear`, `s42_efp_targetyear`, `s42_pumping`, `s42_reserved_fraction`, `s42_multiplier`, `s42_multiplier_startyear`, `c43_watavail_scenario`, `c41_initial_irrigation_area`, `s41_AEI_depreciation`. The defects that DO exist are semantic (mechanism + citation), not name fabrications.

---

## Verified Claims (correct)

| Doc claim | Evidence |
|---|---|
| Default realizations: 42=`all_sectors_aug13`, 43=`total_water_aug13`, 41=`endo_apr13` | `config/default.cfg:1319,1406,1301` |
| Core constraint `q43_water(j2)`: `sum(wat_dem,vm_watdem(wat_dem,j2)) =l= sum(wat_src,v43_watavail(wat_src,j2))` at equations.gms:10-11 | `modules/43_water_availability/total_water_aug13/equations.gms:10-11` — exact match |
| `wat_dem` = agriculture, domestic, manufacturing, electricity, ecosystem (5 sectors) | `core/sets.gms:247` |
| `wat_src` = surface, ground, technical, ren_ground (only surface active; others 0) | `core/sets.gms:244`; `total_water_aug13/preloop.gms:8-12` |
| `q42_water_demand("agriculture",...)`: `vm_watdem*v42_irrig_eff = sum(kcr, vm_area*ic42_wat_req_k) + sum(kli, vm_prod*ic42_wat_req_k*v42_irrig_eff)` | `all_sectors_aug13/equations.gms:10-14` — matches the doc ASCII (lines 171-174) |
| `q41_area_irrig`: `sum(kcr,vm_area(j2,kcr,"irrigated")) =l= vm_AEI(j2)` | `endo_apr13/equations.gms:10-11` |
| `vm_water_cost` and `vm_cost_AEI` enter the objective (Module 11) | `modules/11_costs/default/equations.gms:29,46` |
| Irrigation-efficiency formula `1/(1+2.718282^((-22160-GDP_pc)/37767))` | `all_sectors_aug13/presolve.gms:13,18,20` — exact |
| Scenario 2 (default) uses 1995 GDP; scenario 3 uses current-year GDP | `presolve.gms:18` (im_gdp_pc_mer("y1995",i)) vs `:20` (im_gdp_pc_mer(t,i)) |
| `s42_irrig_eff_scenario` default 2; `s42_irrigation_efficiency` default 0.66 | `all_sectors_aug13/input.gms:14,19`; `config/default.cfg:1342,1346` |
| All Module 42 + 43 switch defaults in tables (cc, 2, 2, 0.66, 2, 0.2, 0.05, "off", 2025, 2040, 0, 0.5, cc) | `config/default.cfg:1325,1336,1342,1346,1380,1387,1391,1352,1358,1360,1394,1329,1412` |
| `c42_watdem_scenario` / `c43_watavail_scenario` options cc/nocc/nocc_hist; nocc→1995, nocc_hist→sm_fix_cc | `all_sectors_aug13/input.gms:44-47,84-85`; `total_water_aug13/input.gms:9-12,24-25` |
| `c41_initial_irrigation_area` options LUH3 / Mehta2024_Siebert2013 / Mehta2024_Meier2018, default LUH3 | `endo_apr13/sets.gms:13`; `config/default.cfg:1305-1307` |
| Env flows via Smakhtin (`i42_env_flows`) with base fraction (`i42_env_flows_base`), weighted by `ic42_env_flow_policy` | `all_sectors_aug13/presolve.gms:58-65,87-88`; `input.gms:31,111`; `realization.gms:47` |
| EFP ramps LINEARLY from start→target year | `all_sectors_aug13/preloop.gms:16` (`m_linear_time_interpol(p42_efp_fader, s42_efp_startyear, s42_efp_targetyear, 0, 1)`) |
| "mixed" policy weighted by population share `p42_EFP_region_shr` (HIC on / LIC,MIC off) | `presolve.gms:74,77-79`; `sets.gms` scen42_to_dev mapping |
| Groundwater buffer adds free groundwater when exogenous demand > supply, in Module 43 presolve | `total_water_aug13/presolve.gms:14-16` (keyed on `watdem_exo` vs `wat_src`) |
| `s42_pumping=1` activates `f42_pumping_cost`, with `s42_multiplier`/`s42_multiplier_startyear` (defaults 0/1995, OFF by default) | `all_sectors_aug13/presolve.gms:29-35`; `input.gms:40-41`; `config/default.cfg:1394,1397,1402` |
| `f43_wat_avail` = LPJmL surface water; ground/ren_ground/technical = 0 | `total_water_aug13/input.gms:16`; `preloop.gms:8-12` |
| Diagnostic output signatures `oq43_water(t,j,type)`, `ov43_watavail(t,wat_src,j,type)` | `total_water_aug13/declarations.gms:22-23` (type includes level/marginal) |

---

## Bugs Found

### WS-1 — `agr_sector_aug13` "excludes non-agricultural sectors" is the OPPOSITE of reality

- **Severity**: Major
- **Trigger**: "The claim is wrong in a way that misleads about behavior" (§1 Major) — wrong-mechanism description of an alternative realization the user is told to switch to.
- **Class**: 4 (conceptual pseudo-code / wrong mechanism) — latent doc error (class 15 flavor).
- **Doc line**: water_scarcity_scenarios.md:239
- **Claim in doc**: "To fully remove water constraints, you must switch to the `agr_sector_aug13` realization, which excludes non-agricultural sectors — but this still enforces agricultural water limits."
- **Reality in code**: `agr_sector_aug13` does NOT exclude non-agricultural sectors. Its `watdem_exo` set still contains `manufacturing, electricity, domestic, ecosystem`, and presolve.gms RESERVES water for non-ag use: `vm_watdem.fx("manufacturing",j) = sum(wat_src, im_wat_avail(t,wat_src,j)) * s42_reserved_fraction` (default 0.5 → 50% of available water reserved). `electricity` and `domestic` are set to 0, and `ecosystem` is set to env flows exactly as in the default realization. The realization's own docstring states: "Water demand from all other sectors is treated exogenously. The scalar `s42_reserved_fraction` determines how much water is reserved for non agricultural purposes. Technically, it is assigned to industrial use ... The default value is 0.5." So switching to this realization RESERVES MORE water away from agriculture (a coarse 50% block), not "removes water constraints" or "excludes non-ag sectors".
- **File evidence**: `modules/42_water_demand/agr_sector_aug13/presolve.gms:38-40`; `modules/42_water_demand/agr_sector_aug13/sets.gms` (watdem_exo); `modules/42_water_demand/agr_sector_aug13/realization.gms:44-50`
- **verify_cmd / result**:
  `rg -n "wat_dem|watdem_exo|watdem_ineldo|vm_watdem" .../agr_sector_aug13/presolve.gms` →
  `38: vm_watdem.fx("manufacturing",j) = sum(wat_src, im_wat_avail(t,wat_src,j)) * s42_reserved_fraction;`
  `39: vm_watdem.fx("electricity",j) = 0;  40: vm_watdem.fx("domestic",j) = 0;  76: vm_watdem.fx("ecosystem",j) = ...env flows...`
  and `agr_sector_aug13/realization.gms:44-50` (docstring quoted above).
- **confirmed**: true
- **Proposed fix**: Replace the sentence with: "To change how water constraints are applied, you can switch to the `agr_sector_aug13` realization. It does NOT remove water constraints: it still enforces `q43_water` and agricultural water limits, but instead of modeling domestic/manufacturing/electricity demand explicitly it RESERVES a fixed fraction of available water for non-agricultural use (`s42_reserved_fraction`, default 0.5, assigned to manufacturing; electricity and domestic set to 0). This generally makes LESS water available to agriculture, not more."

### WS-2 — Groundwater-buffer citation is internally contradictory and drifts to wrong content

- **Severity**: Major
- **Trigger**: "File:line citation drift to adjacent but different content (would mislead a careful reader)" + "Citation points at content materially different from the claim" (§1 Major).
- **Class**: 12 (content-level citation mismatch) / 10 (stale file:line).
- **Doc line**: water_scarcity_scenarios.md:157
- **Claim in doc**: "The groundwater infeasibility buffer in Module 43 (`modules/42_water_demand/all_sectors_aug13/presolve.gms:14-16`) adds free groundwater when exogenous demands exceed supply..."
- **Reality in code**: The cited file/line (`modules/42_water_demand/all_sectors_aug13/presolve.gms:14-16`) contains the IRRIGATION-EFFICIENCY sigmoidal block (`v42_irrig_eff.fx(j) = 1/(1+2.718282**(...))`), not a groundwater buffer. The groundwater infeasibility buffer is in MODULE 43: `modules/43_water_availability/total_water_aug13/presolve.gms:14-16` (`v43_watavail.fx("ground",j) = v43_watavail.up("ground",j) + ((sum(watdem_exo, vm_watdem.lo(...))-sum(wat_src,v43_watavail.up(...)))*1.01)$(...>0)`). The prose text "in Module 43" is correct but contradicts the Module-42 path it cites. (Note: the SAME buffer is cited CORRECTLY at doc line 243 as `modules/43_water_availability/total_water_aug13/presolve.gms:14-16`.)
- **File evidence**: buffer at `modules/43_water_availability/total_water_aug13/presolve.gms:13-16`; the Module-42 path the doc points at is irrigation efficiency at `modules/42_water_demand/all_sectors_aug13/presolve.gms:11-22`.
- **verify_cmd / result**:
  `Read modules/43_water_availability/total_water_aug13/presolve.gms` → lines 13-16 = the groundwater buffer.
  `Read modules/42_water_demand/all_sectors_aug13/presolve.gms` → lines 11-22 = irrigation efficiency, NOT a buffer.
- **confirmed**: true
- **Proposed fix**: On line 157, change the parenthetical citation from `modules/42_water_demand/all_sectors_aug13/presolve.gms:14-16` to `modules/43_water_availability/total_water_aug13/presolve.gms:14-16` (matching the correct citation already used at line 243).

### WS-3 — `s42_reserved_fraction` listed in the default-realization switch table without its realization caveat (and imprecise description)

- **Severity**: Minor
- **Trigger**: "Missing default-state caveat" / "Wrong detail, but a careful reader wouldn't be misled into action" (§1 Minor). Tie-broken DOWN from Major because the doc does describe the default realization elsewhere and the switch is real with a correct default value.
- **Class**: 13-adjacent (parameter default context) — but the value 0.5 IS correct; the defect is the missing "only under `agr_sector_aug13`" scope plus the "(not withdrawn)" wording.
- **Doc line**: water_scarcity_scenarios.md:63
- **Claim in doc**: "`s42_reserved_fraction` | `0.5` | 0–1 | Fraction of available water reserved (not withdrawn)" — placed in the Module 42 switch table of a doc whose Quick Reference states the default realization is `all_sectors_aug13`.
- **Reality in code**: `s42_reserved_fraction` is declared and used ONLY in the non-default `agr_sector_aug13` realization (`input.gms:9`, `presolve.gms:38,44`). It is NOT declared in the default `all_sectors_aug13` realization (only a passing comment in realization.gms:45) and has NO effect under the default. Also "reserved (not withdrawn)" is imprecise: the reserved water is assigned to manufacturing WITHDRAWAL (`vm_watdem.fx("manufacturing",j) = ... * s42_reserved_fraction`), i.e. it is counted as a withdrawal, just non-agricultural.
- **File evidence**: `modules/42_water_demand/agr_sector_aug13/input.gms:9`; `.../agr_sector_aug13/presolve.gms:38,44`; absent from `modules/42_water_demand/all_sectors_aug13/input.gms` (grep exit 1, positive control `vm_watdem` = 5 hits in the same dir confirms search works).
- **verify_cmd / result**:
  `rg -n "s42_reserved_fraction" modules/42_water_demand/` → only `agr_sector_aug13/{input.gms:9,presolve.gms:38,44,realization.gms:47,60}` + a comment in `all_sectors_aug13/realization.gms:45`.
  `rg -n "s42_reserved_fraction" .../all_sectors_aug13/input.gms` → exit 1 (absent); positive control `rg -c vm_watdem .../all_sectors_aug13/presolve.gms` → 5.
- **confirmed**: true
- **Proposed fix**: Append a note to the `s42_reserved_fraction` row, e.g. change Description to "Fraction of available water reserved for non-agricultural use — **only active in the `agr_sector_aug13` realization** (no effect under the default `all_sectors_aug13`); assigned to manufacturing withdrawal." Alternatively move the row into a clearly-labeled "agr_sector_aug13-only switches" sub-table.

---

## Deferred (not code-verifiable or code self-inconsistent — NOT edited)

- **`vm_water_cost` units**: Doc (line 34) gives "mio. USD17MER/yr" with description "Pumping cost (if enabled)". The code DECLARATION says `vm_water_cost(i) Cost of irrigation water (USD17MER per m^3)` (`all_sectors_aug13/declarations.gms:31`), but the EQUATION `q42_water_cost` (`equations.gms:16-17`: `vm_water_cost = sum(cell, vm_watdem("agriculture",j)) * ic42_pumping_cost`) is dimensionally mio-m3/yr × USD/m3 = mio USD/yr, and it is summed directly into the Module-11 objective (mio USD/yr). The doc's unit matches the EQUATION dimension; the code's own declaration label is the internally-inconsistent artifact. Not a clear doc bug — flag the code, not the doc. (Also: the variable is the per-region pumping-cost cost variable, so "Pumping cost (if enabled)" is fair.)
- **"Pumping costs parameterized primarily for India"** (doc lines 157, 247): `f42_pumping_cost` is real (`input.gms:126`, loaded from `f42_pumping_cost.cs4`), but whether the data values are India-centric is a data-file (.cs4) claim I cannot parse from GAMS source. Plausible and consistent with the module's history, but not code-verifiable here.
- **`f43_wat_avail(t,j)` vs `f43_wat_avail(t_all,j)`** (doc ASCII line 187): the declared index is `t_all`, the doc writes `t`. Cosmetic index imprecision in an ASCII diagram, not load-bearing; not flagged.
