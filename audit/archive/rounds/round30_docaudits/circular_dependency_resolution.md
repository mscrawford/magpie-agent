# Doc Audit — cross_module/circular_dependency_resolution.md

**Round**: 30 (doc audits)
**Auditor model**: Opus (highest capability)
**Target**: `magpie-agent/cross_module/circular_dependency_resolution.md`
**Ground truth**: `/tmp/magpie_develop_ro` @ `ee98739fd` (Merge PR #887)
**Config**: `/tmp/magpie_develop_ro/config/default.cfg`
**Date**: 2026-05-29

---

## Scope note

This doc is overwhelmingly **conceptual / methodological** (how recursive-dynamic structure breaks circular dependencies). Much of it is non-code-checkable prose, illustrative pseudocode (clearly `* Example:`-labeled), R verification snippets, graph-theory references, and a self-labeled "Inferred / Suspected" cycle catalog (§8.2). Per the method, I enumerated and verified only the **load-bearing, code-checkable** claims: interface variable/parameter/equation names, file:line citations in Appendix A and the "Code Evidence" blocks, realization-default assumptions, scalar defaults, and the equation forms presented as actual code.

The doc's realization names are all correct (`landmatrix_dec18`, `price_aug22`, `select_apr20`, `endo_jan22`, `normal_dec17`, `endo_apr13`, `area_based_apr22`, `managementcalib_aug19`, `flexreg_apr16` — all verified against `config/default.cfg` and `ls`). The core equation forms it cites verbatim (`q10_land_area`) are exact. Most variable names are real and correctly attributed. The bugs concentrate in three places: the Type-1 carbon "Code Evidence" block (§2.1), the Type-2 trade example (§2.2), and one categorization row in Appendix A.

---

## Verified-correct claims (sample)

- **§1.2 / §3.2 `q10_land_area`** — doc shows `q10_land_area(j2) .. sum(land, vm_land(j2,land)) =e= sum(land, pcm_land(j2,land));`. Exact match to `modules/10_land/landmatrix_dec18/equations.gms:13-15`. Set-based sum preserved (MANDATE 10 respected). ✅
- **§1.2 / Appendix A `pcm_land`** — `pcm_land(j,land) = vm_land.l(j,land);` cited at `modules/10_land/landmatrix_dec18/postsolve.gms:9`. Exact match (line 9). ✅
- **Appendix A `pcm_carbon_stock(j,land,c_pools,stockType)` / Module 56 / postsolve.gms:8** — declaration `modules/56_ghg_policy/price_aug22/declarations.gms:19` uses `c_pools`; updated at `price_aug22/postsolve.gms:8`. Module + line + dims all correct. ✅ (Note: this is the CORRECT version; §2.1 contradicts it — see Bug 2.)
- **Appendix A `pcm_tau(j,tautype)` / Module 13 / postsolve.gms:16** — `pcm_tau(j, tautype) = vm_tau.l(j, tautype);` at `modules/13_tc/endo_jan22/postsolve.gms:16`. Exact. ✅
- **§3.3 Cycle 3 (irrigation)** — `pc41_AEI_start(j) = vm_AEI.l(j);` at `modules/41_area_equipped_for_irrigation/endo_apr13/postsolve.gms:8` ✅. `q41_area_irrig`: code is `sum(kcr, vm_area(j2,kcr,"irrigated")) =l= vm_AEI(j2)` (equations.gms:11); doc's `vm_AEI(j2) =g= sum(kcr, vm_area(...))` is the algebraically-equivalent rearrangement (acceptable). `vm_AEI`, `vm_area` real. Default realization `endo_apr13` correct.
- **§3.4 Cycle 4 variable names** — all real and correctly attributed: `vm_reward_cdr_aff(i)` (M56 decl:43), `vm_emissions_reg(i,emis_source,pollutants)` (M56 decl:40; doc's `(i,"co2_c")` drops a dim for illustration but `co2_c` is a valid pollutant, used at `price_aug22/equations.gms:20`), `vm_carbon_stock(j,land,c_pools,stockType)` (M56 decl:34 — consistent with G2 anchor: declared in 56 not 52), `vm_lu_transitions(j,land_from,land_to)` (M10 decl:23), `vm_cost_glo` (M11/default decl:9).
- **§3.4 scalar defaults** — `s56_c_price_induced_aff` default `/ 1 /` (on), `s56_buffer_aff` default `/ 0.5 /` (input.gms:69,71). Doc's "1/0" enable switch and "50% buffer" descriptions are correct.
- **§2.4 / §3.1 `vm_tech_cost(i)`** — M13 decl:10 ✅ (doc attributes to Module 13 ✅). `pm_yields_semi_calib(j,kve,w)` — M14 `managementcalib_aug19` decl:18, exact dims ✅. M14 `managementcalib_aug19/preloop.gms` exists (the §2.4 calibration citation has a valid file).
- **§2.2 note "vm_import/vm_export do NOT exist"** — CONFIRMED. `grep` + `rg` both return zero matches tree-wide. The doc is correct on this negative claim.
- **§2.2 `q21_trade_glo`** — real, in the DEFAULT realization (`modules/21_trade/selfsuff_reduced/declarations.gms:27`, equation at `equations.gms:12`). `q17_prod_reg` real (`modules/17_production/flexreg_apr16/equations.gms:10`). `vm_supply` real (M16). `vm_prod(j,k)`, `vm_prod_reg(i,kall)` real (M17 decl:9-10).

---

## Bugs found

### Bug 1 — §2.2 Trade example describes the NON-DEFAULT bilateral realization + fabricates `q21_trade_bilat`

- **Severity**: Major (tier_uncertainty: true — has a Critical trigger; tie-broken down)
- **Class**: 9 (Wrong equation name) + non-default-realization mechanism
- **Trigger**: "Invented equation name presented as authoritative" (Critical trigger) AND "Module described as if a non-default realization were active" (Critical trigger); tie-broken to Major because both appear inside one illustrative "Type 2" conceptual example with bracketed equation labels rather than a hard file:line code citation, and 2 of the 3 named equations are correct + in the default.
- **Doc lines**: circular_dependency_resolution.md:139-145
- **Claim in doc**:
  ```
  vm_prod_reg(i,kall) = sum(cell(i,j), vm_prod(j,kall))      [q17_prod_reg]
  sum(i, vm_prod_reg(i,k)) ≥ sum(i, vm_supply(i,k))          [q21_trade_glo]
  v21_trade(i_ex,i_im,k_trade) handles bilateral trade flows  [q21_trade_bilat]
  ...
  **Note**: vm_import/vm_export do NOT exist — trade uses bilateral flows via `v21_trade`
  ```
- **Reality in code**:
  - Default trade realization is **`selfsuff_reduced`** (`config/default.cfg:650`), which is NOT bilateral. It uses a self-sufficiency pool + comparative-advantage pool (`q21_trade_glo`, `q21_trade_reg`, `q21_trade_reg_up`, `q21_excess_dem`, `q21_excess_supply`). Internal trade vars are `v21_excess_prod`, `v21_excess_dem`, `v21_import_for_feasibility` — NOT `v21_trade`.
  - `v21_trade` exists ONLY in the non-default `selfsuff_reduced_bilateral22` realization.
  - `q21_trade_bilat` exists **nowhere** in the codebase (fabricated).
  - A user on a default run will not find `v21_trade` in their GDX and will never find `q21_trade_bilat`.
- **File evidence**:
  - `config/default.cfg:650` → `cfg$gms$trade <- "selfsuff_reduced"`
  - `modules/21_trade/selfsuff_reduced/equations.gms:12-14` (real default mechanism: `q21_trade_glo .. sum(i2,vm_prod_reg(i2,k_trade)) =g= sum(i2,vm_supply(i2,k_trade)) + balanceflow`)
  - `v21_trade` only in `modules/21_trade/selfsuff_reduced_bilateral22/{equations,declarations,postsolve}.gms`
- **verify_cmd**:
  - `grep -n 'cfg$gms$trade' config/default.cfg` → `cfg$gms$trade <- "selfsuff_reduced"`
  - `rg -l 'v21_trade' modules/21_trade/` → only `selfsuff_reduced_bilateral22/*` (3 files)
  - `rg -l 'q21_trade_bilat' modules/` → no match (exit 1); `grep -rln 'q21_trade_bilat' modules/` → no match (exit 1). Two methods agree: absent.
- **confirmed**: true
- **Proposed fix**: Rewrite the §2.2 example to reflect the default `selfsuff_reduced` mechanism. Replace lines 139-145 with:
  ```
   vm_prod_reg(i,kall) = sum(cell(i,j), vm_prod(j,kall))            [q17_prod_reg]
   sum(i2, vm_prod_reg(i2,k_trade)) ≥ sum(i2, vm_supply(i2,k_trade)) + balanceflow   [q21_trade_glo]
   * Default trade (selfsuff_reduced) splits demand into a self-sufficiency pool
   * (q21_trade_reg / q21_trade_reg_up) and a comparative-advantage pool (q21_trade_glo).
   ```
   Then change the Note to: "Note: `vm_import`/`vm_export` do NOT exist. The default `selfsuff_reduced` realization (config/default.cfg:650) is pool-based, not bilateral; bilateral flows via `v21_trade` exist only in the non-default `selfsuff_reduced_bilateral22` realization." Delete the fabricated `[q21_trade_bilat]` label entirely.

---

### Bug 2 — §2.1 "Code Evidence" attributes the `pcm_carbon_stock` update to Module 52 (it is Module 56) and uses wrong dimensions

- **Severity**: Major
- **Class**: 11 (Wrong GAMS filename / wrong-module attribution) + 3 (Suffix/dimension truncation)
- **Trigger**: "Citation points at content that's no longer at the cited [location], AND the actual cited content says something materially different" — here the assignment is in a different module's postsolve than claimed; presented under a "Code Evidence" header (authoritative framing). The G2 anchor specifically guards the 52-vs-56 carbon-stock distinction.
- **Doc lines**: circular_dependency_resolution.md:109-111
- **Claim in doc**:
  ```gams
  * Module 52, postsolve.gms:
  pcm_carbon_stock(j,land,c_pools) = vm_carbon_stock.l(j,land,c_pools);
  ```
- **Reality in code**:
  - This assignment lives in **Module 56's** postsolve, NOT Module 52's. Module 52's `normal_dec17/postsolve.gms` contains only `q52_emis_co2_actual` output definitions (8 lines, no `pcm_carbon_stock`).
  - The actual statement is 4-dimensional: `pcm_carbon_stock(j,land,ag_pools,stockType) = vm_carbon_stock.l(j,land,ag_pools,stockType);` (doc shows 3 dims `(j,land,c_pools)`).
  - The doc's OWN Appendix A row (line 968) correctly attributes `pcm_carbon_stock(j,land,c_pools,stockType)` to Module 56 @ `price_aug22/postsolve.gms:8` — so §2.1 is internally inconsistent with Appendix A.
- **File evidence**:
  - `modules/56_ghg_policy/price_aug22/postsolve.gms:8` → `pcm_carbon_stock(j,land,ag_pools,stockType) = vm_carbon_stock.l(j,land,ag_pools,stockType);`
  - `modules/52_carbon/normal_dec17/postsolve.gms:1-13` → only q52 output defs; no `pcm_carbon_stock` (grep exit 1).
- **verify_cmd**:
  - `grep -rn 'pcm_carbon_stock' modules/56_ghg_policy/price_aug22/postsolve.gms` → `8:pcm_carbon_stock(j,land,ag_pools,stockType) = vm_carbon_stock.l(j,land,ag_pools,stockType);`
  - `grep -rn 'pcm_carbon_stock' modules/52_carbon/normal_dec17/postsolve.gms` → no match (exit 1)
- **confirmed**: true
- **Proposed fix**: Change the comment from `* Module 52, postsolve.gms:` to `* Module 56, postsolve.gms:8:` and the statement to `pcm_carbon_stock(j,land,ag_pools,stockType) = vm_carbon_stock.l(j,land,ag_pools,stockType);`.

---

### Bug 3 — §2.1 uses non-existent variable `pcm_carbon_density` (actual is `pm_carbon_density`)

- **Severity**: Major (tier_uncertainty: true — "Invented variable name presented as authoritative" is a Critical trigger; tie-broken down because the name appears in a conceptual ASCII diagram + numbered resolution narrative, not in a backticked code/citation line)
- **Class**: 2 (Hallucinated variable name)
- **Trigger**: "Invented variable name presented as authoritative (no such `vm_*`/`pm_*`/`v{N}_*` exists)".
- **Doc lines**: circular_dependency_resolution.md:98, 104, 105
- **Claim in doc**:
  - line 98: `pcm_carbon_density ←──── vm_carbon_stock`
  - line 104: `**Postsolve t-1**: pcm_carbon_density(t-1) ← f(vm_carbon_stock(t-1))`
  - line 105: `**Timestep t**: Use pcm_carbon_density(t-1) as **fixed parameter** for land costs`
- **Reality in code**: `pcm_carbon_density` does **not exist** anywhere in the tree (0 matches). The real parameter is `pm_carbon_density` (positive control: present in M14, M29, M32, M35, M52). The doc's own line 114 correctly uses `pm_carbon_density` ("Uses pm_carbon_density from PREVIOUS timestep") — so §2.1 is internally inconsistent.
- **File evidence**:
  - `pm_carbon_density` (real): `modules/52_carbon/normal_dec17/declarations.gms`, `modules/29_cropland/detail_apr24/preloop.gms`, `modules/32_forestry/dynamic_may24/{preloop,presolve}.gms`, `modules/35_natveg/pot_forest_may24/presolve.gms`, `modules/14_yields/managementcalib_aug19/presolve.gms`.
- **verify_cmd**:
  - `rg -c 'pcm_carbon_density' /tmp/magpie_develop_ro/` → `0 matches for pcm_carbon_density in entire develop tree`
  - `grep -rln 'pcm_carbon_density' modules/ core/` → no match (exit 1)
  - Positive control: `grep -rln 'pm_carbon_density' modules/` → 9 files
- **confirmed**: true
- **Proposed fix**: Replace all three occurrences of `pcm_carbon_density` (lines 98, 104, 105) with `pm_carbon_density`. (Optional, more precise: note that `pm_carbon_density` is a calculated parameter, not a `pcm_`-prefixed lagged var; it is recomputed each timestep from inputs, with the previous-timestep land state effectively fixing the per-timestep density. But the minimal fix is the name correction.)

---

### Bug 4 — Appendix A lists `pm_interest` in a table titled "Complete List of pcm_* Variables (representing previous timestep state)"

- **Severity**: Minor
- **Class**: 1 (GAMS prefix confusion — `pm_` vs `pcm_`) / mis-categorization
- **Trigger**: "Wrong variable prefix (vm_ vs v{N}_, pm_ vs p{N}_) — semantic scope wrong" is a Major trigger, but here the variable NAME `pm_interest` is correct and correctly cited; only its placement in a `pcm_*`-titled table mis-categorizes it. A careful reader sees the `pm_` prefix and the `(t_all,i)` all-timestep indexing. Tie-broken to Minor (metadata table, name+citation correct).
- **Doc lines**: circular_dependency_resolution.md:961-969 (table header at 963; offending row at 969)
- **Claim in doc**: Table header "Complete List of pcm_* Variables (representing previous timestep state)" — row: `pm_interest(t_all,i) | 12_interest_rate | Interest rates | modules/12_interest_rate/select_apr20/preloop.gms:23`.
- **Reality in code**: `pm_interest(t_all,i)` is a calculated parameter indexed over **all** timesteps (`t_all`), declared `modules/12_interest_rate/select_apr20/declarations.gms:9`; it is NOT a `pcm_*` previous-timestep lagged variable. The citation (preloop.gms:23) is correct for the assignment under the default `gdp_dependent` branch (`config/default.cfg:249`). The mismatch is solely the categorization: a `pm_` parameter sits in a `pcm_*`/"previous timestep state" table.
- **File evidence**: `modules/12_interest_rate/select_apr20/declarations.gms:9` (`pm_interest(t_all,i)`), `preloop.gms:23` (assignment).
- **verify_cmd**:
  - `grep -rn 'pm_interest' modules/12_interest_rate/select_apr20/declarations.gms` → `9: pm_interest(t_all,i) ... (% per yr)`
  - `grep -rn 'pm_interest' .../preloop.gms` → `23: pm_interest(t_all,i) = ( ... )`
  - `grep -n 'c12_interest_rate' config/default.cfg` → `gdp_dependent` (confirms line 23 is the active branch)
- **confirmed**: true
- **Proposed fix**: Either (a) remove the `pm_interest` row from the Appendix A "pcm_* Variables" table (it is not a `pcm_*` lagged variable), or (b) re-title/split the table to "Lagged-state and persistent calculated parameters" and add a column noting `pm_interest` is `t_all`-indexed (persistent, not previous-timestep). Option (a) is cleaner given the table's stated purpose ("representing previous timestep state").

---

## Deferred (uncertain / not code-falsifiable — NOT edited)

- **Executive Summary "26 circular dependency cycles"** and §8.1 source citation "Module_Dependencies.md (lines 149-179)". The count of cycles is an analytical artifact (depends on cycle-enumeration method/granularity), not directly grep-falsifiable. §8.2 is self-labeled "Inferred / Suspected" (22 cycles, "...", with "Action Required: Full enumeration"). Not auditable against code; the doc already hedges it. The cited Module_Dependencies.md line range was not cross-checked (out of ground-truth scope — this is a magpie-agent internal doc, not develop code).
- **§3.2 Cycle 2 diagram tag "`pm_land_conservation` [22] → `vm_land.lo(j,land_natveg)` [10]"**. The parameter `pm_land_conservation(t,j,land,consv_type)` is correct (M22 decl:15) and the consv_type member `"protect"` is real. The bounds ARE set on Module-10's `vm_land.lo` — but the read+bound-setting happens in **Module 35's** `pot_forest_may24/presolve.gms:162,201,231` (and M29 for crop), not in Module 10 itself. Tagging the bounded variable "[10]" (its home module) is defensible doc shorthand; the variable/parameter names and the mechanism are correct. This is a MANDATE-17 borderline (direct vs transitive), but unlike the R24 anchor it does not mis-attribute a *consumer* in a way that would mislead modification-safety reasoning (the bounded variable genuinely belongs to M10). Left as a nuance, not flagged.
- **§6.1 "Modifying Module 10 (Land): EXTREME RISK (4+ cycles, 15 consumers)"** and "Module 54: 0 cycles, 1 connection". `vm_land` is consumed by 10+ modules (partial enumeration: 10,29,30,31,32,34,35,50,58,59 in equations+presolve alone), so "15 consumers" is order-of-magnitude plausible but "consumer" is undefined here (declared-read vs equation-read; which files counted). Not falsifiable to a precise integer without a fixed definition. Left as illustrative magnitude.
- **§7.3 parallelization claims** ("modules 37, 45, 54 independent"; "water system 41-42-43 isolatable"). Architectural/analytical assertions, not single-line code facts. Not audited.
- **§2.4 "Yields ↔ TC ↔ Livestock require multiple model runs to converge"**. The tau calibration is a documented multi-run MAgPIE procedure; the M14 `managementcalib_aug19/preloop.gms` cited exists. The high-level mechanism description is broadly consistent with MAgPIE's calibration design; not falsifiable at this granularity. Left as-is.
- **Illustrative `* Example:` blocks in §6.2, §7.2, §9** (e.g., `vm_cost_landcon(j,land) =g= pcm_carbon_stock(j,land) * conversion_cost`, damping-factor postsolve, tau adjustment). These are explicitly labeled hypothetical modification patterns (MANDATE 5 permits labeled conceptual code). `vm_cost_landcon` (M39) and `pm_water_avail`/`pm_water_available` are not verified for these blocks because they are pedagogical, not code-evidence claims.

---

## Summary

Verified ~30 load-bearing code-checkable claims. The doc's realizations, defaults, and the verbatim `q10_land_area` equation are all correct, and its Appendix A `pcm_*` citations (land, carbon_stock→M56, tau) are accurate. Four bugs: (1) Major — §2.2 trade example describes the non-default bilateral realization and fabricates equation `q21_trade_bilat` (default is `selfsuff_reduced`, pool-based; `v21_trade` is non-default-only); (2) Major — §2.1 "Code Evidence" attributes the `pcm_carbon_stock` update to Module 52 (actually Module 56) with wrong dims, contradicting the doc's own Appendix A; (3) Major — §2.1 uses non-existent `pcm_carbon_density` (actual `pm_carbon_density`), contradicting the doc's own line 114; (4) Minor — Appendix A files `pm_interest` (a `t_all`-indexed calculated parameter) under a "pcm_* / previous-timestep-state" table. Bugs 2 and 3 are internal inconsistencies (the doc states the correct fact elsewhere), making them low-risk fixes.
