# Round 33 Doc Audit — module_70.md (Livestock)

**Auditor**: Opus 4.8 (1M), adversarial doc auditor
**Target**: `magpie-agent/modules/module_70.md`
**Ground truth**: `/tmp/magpie_develop_ro` (develop worktree) + `config/default.cfg`
**Date**: 2026-05-30

---

## Overall Verdict: MOSTLY ACCURATE
## Accuracy Score: 8/10 (1 Major path-directness bug, 1 Major scaling-value bug, 3 Minor)

This is a high-quality doc. The pre-run advisory's worry — that the default realization might be misstated as `fbask_jul23` (the R3 Critical confabulation) — is **REFUTED**: the doc correctly states `fbask_jan16` and `config/default.cfg:2146` confirms `cfg$gms$livestock <- "fbask_jan16"`. Both realization directories (`fbask_jan16`, `fbask_jan16_sticky`) exist and the default is correct. Feed-basket variable/equation names are all correct. The livestock→feed→cropland cascade consumer claims are mostly correct, with ONE direct-vs-transitive error (M31).

---

## Advisory verification (the pre-run flag)

| Advisory item | Verdict | Evidence |
|---|---|---|
| Default realization `fbask_jan16` (NOT `fbask_jul23`) | CONFIRMED CORRECT | `config/default.cfg:2146`: `cfg$gms$livestock <- "fbask_jan16"   # def = fbask_jan16`; `ls modules/70_livestock/` → only `fbask_jan16`, `fbask_jan16_sticky` |
| Feed-basket variable/equation names | CONFIRMED CORRECT | `im_feed_baskets`, `vm_feed_balanceflow`, `vm_dem_feed`, `vm_feed_intake`, `q70_feed`, `q70_feed_intake_pre`, `q70_feed_intake`, `q70_feed_balanceflow` all match declarations.gms + equations.gms |
| Livestock→feed→cropland cascade consumers | PARTIALLY WRONG (see BUG-2) | M16/M53/M55/M14/M11 consumer claims correct; M31 "direct consumer of vm_dem_feed" is wrong (transitive) |

---

## Verified Claims (correct)

- **Default realization** `fbask_jan16`, alternative `fbask_jan16_sticky` (doc:4-13). config/default.cfg:2146 + `ls`. CORRECT.
- **7 equations (fbask_jan16) / 8 (sticky)** (doc:6, 28). declarations.gms:22-29 (7) and fbask_jan16_sticky/declarations.gms:22-31 (8). CORRECT.
- **All 7 equation formulas** (q70_feed eq.gms:17-20; q70_feed_balanceflow 25-29; q70_feed_intake_pre 35-37; q70_feed_intake 39-42; q70_cost_prod_liv_labor 59-62; q70_cost_prod_liv_capital 64-66; q70_cost_prod_fish 68-70). Verbatim match incl. constraint types (=g= for q70_feed, =e= elsewhere). CORRECT.
- **Sticky: replaces q70_cost_prod_liv_capital (investment-based) + adds q70_investment** (doc:208-274). fbask_jan16_sticky/equations.gms:72-74 (capital) + 79-82 (investment). Formulas match. CORRECT.
- **Sticky scalars**: s70_depreciation_rate=0.05 (input.gms:34), s70_multiplicator_capital_need=1 (input.gms:35). CORRECT.
- **p70_capital_need / p70_capital update** (doc:258-266). fbask_jan16_sticky/presolve.gms:78-93. CORRECT.
- **p70_initial_1995_prod from f70_hist_prod_livst("y1995",...)** (doc:270). sticky/preloop.gms:94. CORRECT.
- **Scalar defaults**: s70_pyld_intercept=0.24 (input.gms:25), s70_past_mngmnt_factor_fix=2005 (26), s70_scavenging_ratio=0.385 (27), s70_feed_intake_weight_balanceflow=1 (28), s70_subst_functional_form=1 (29), s70_feed_substitution_start=2025 (30), s70_feed_substitution_target=2050 (31), s70_cereal_scp_substitution=0 (32), s70_foddr_scp_substitution=0 (33). ALL CORRECT.
- **Switches**: c70_feed_scen=ssp2 (input.gms:8), c70_cereal_scp_scen=constant (18), c70_foddr_scp_scen=constant (19), c70_fac_req_regr=glo (21). ALL CORRECT.
- **5 livestock systems** sys_pig/sys_beef/sys_chicken/sys_hen/sys_dairy (sets.gms:20-21) + sys_to_kli mapping (sets.gms:30-36). CORRECT incl. the mapping sys_beef→livst_rum, sys_chicken→livst_chick, etc.
- **kcer70 = tece, maiz, trce, rice_pro** (sets.gms:38-39). CORRECT.
- **feed_scen70 = 10 scenarios** (ssp1-5, constant, SDP, SDP_EI, SDP_MC, SDP_RC) (sets.gms:16-18). Count 10. CORRECT.
- **fadeoutscen70 = 17 SCP scenarios** (sets.gms:41-45). Counted 17. CORRECT.
- **scen_countries70 = 249 countries** (doc:862, input.gms:87-112). Counted 249 unique ISO codes. CORRECT. (Doc correctly cites input.gms, not sets.gms.)
- **SCP substitution mechanism** (preloop.gms:54-78) — Nr-based cereal/fodder→SCP conversion, fadeout factors. doc:426-466 matches code (preloop.gms:63-78). CORRECT.
- **Factor-cost regression structure**: cost_regr_a/cost_regr_b, glo vs reg (preloop.gms:82-90). doc:506-532 matches incl. regional-intercept calibration formula. CORRECT.
- **Pasture management factor** full presolve chain (presolve.gms:32-68): p70_cattle_stock_proxy (32-33), p70_milk_cow_proxy (35-36), 20% lower bound (41-42), p70_cattle_feed_pc_proxy (47), p70_incr_cattle (52-58), fixed/dynamic pm_past_mngmnt_factor (63-68). doc:542-638 matches incl. the nested-exponent time scaling. CORRECT.
- **Min productivity 0.02** (preloop.gms:26), **pc70 init 0.001** (preloop.gms:10), **postsolve pc70 update** (postsolve.gms:9). CORRECT.
- **Interface OUTPUT consumers verified by grep across all modules**:
  - `vm_feed_intake` → M53 (53_methane/ipcc2006_aug22), M55 (55_awms/ipcc2006_aug16). doc:697-698 CORRECT.
  - `pm_past_mngmnt_factor` → M14 (14_yields/managementcalib_aug19, q14_yield_past eq.gms:38). doc:718 CORRECT (consumer set).
  - `vm_cost_prod_livst`, `vm_cost_prod_fish` → M11 (11_costs/default, q11_cost_reg eq.gms:18-19). doc:707-712 CORRECT incl. equation name `q11_cost_reg`.
  - `vm_costs_additional_mon(i)` → declared M71 foragebased_jul23/declarations.gms:11 (1D, "Punishment cost for additionally transported monogastric livst_egg"), independent of M70 cost path. doc:712 CORRECT, incl. M71 default realization.
  - `im_slaughter_feed_share` → M55 (only). doc:720-724 (vague "other modules") not wrong.
- **Input `vm_prod_reg` from M17** (declared 17_production/flexreg_apr16/declarations.gms). doc:728-732 CORRECT.
- **Realization.gms prose citations** (8-81, 9, 10, 20, 24-29, 42-45, 47-51, 53-62, 59-62, 64-70, 72-75, 77-80). All align with realization.gms content. CORRECT.
- **Input-data table line citations** (input.gms:36-39, 41-44, 46-49, 51-54, 57-62, 65-70, 72-76, 78-82). All match. CORRECT.

---

## Bugs Found

### BUG module_70-B1 — vm_dem_feed listed as DIRECT output to Module 31 (transitive, not direct)
- **Severity**: Major
- **Class**: 15 (latent doc error) / MANDATE 17 (direct vs transitive consumer)
- **Trigger** (§1 Major): "Wrong variable prefix / semantic scope wrong" adjacent — here a consumer-set directness error that misleads modification-safety reasoning. Resembles R24 Q4-B3 anchor (module_30.md:360, scored Major doc_error).
- **Claim in doc** (doc:690): "`vm_dem_feed(i,kap,kall)` ... **To Module 31 (Pasture)**: Pasture feed demand drives pasture area requirements (`module.gms:16-17`)". Also doc:1141 ("Module 31 (Pasture): Pasture feed demand drives pasture area requirements") and doc:1236.
- **Reality in code**: Module 31 does NOT reference `vm_dem_feed` (or any `vm_feed*`) in any of its files. M31 derives pasture production via `q31_prod`: `vm_prod(j2,"pasture") =l= vm_land(j2,"past") * vm_yld(j2,"pasture","rainfed")` (31_past/endo_jun13/equations.gms:16-18). The pasture-feed-demand signal reaches M31 transitively: `vm_dem_feed` → M16 (demand balance) → M21 (trade) → `vm_prod_reg`/`vm_prod`. The cited module.gms:16-19 itself says the flow is "organized via interfaces `vm_dem_feed`, `vm_supply` and `vm_prod_reg` **via modules [16_demand] and [21_trade]**" — i.e. explicitly indirect.
- **File evidence**: `modules/31_past/endo_jun13/equations.gms:16-18` (M31 reads vm_land+vm_yld, not vm_dem_feed); absence of vm_feed in `modules/31_past/` confirmed with positive control (vm_land found in 3 files, vm_feed in 0).
- **verify_cmd**: `rg -ln "vm_feed" /tmp/magpie_develop_ro/modules/31_past/` → (empty); positive control `rg -ln "vm_land" /tmp/magpie_develop_ro/modules/31_past/` → 3 files (endo_jun13/equations.gms, endo_jun13/presolve.gms, static/presolve.gms). `rg -ln "vm_dem_feed" .../modules/` → only 16_demand + 70_livestock.
- **confirmed**: true
- **Anchor reference**: R24 Q4-B3 (MANDATE 17) — module_30.md claimed direct M52/M56 consumption that was actually M30→M29→aggregate→M52/M56.
- **Proposed fix**: In doc:690 replace "**To Module 31 (Pasture)**: Pasture feed demand drives pasture area requirements (`module.gms:16-17`)" with "**To Module 31 (Pasture) — INDIRECT**: pasture feed demand reaches M31 transitively (`vm_dem_feed` → Module 16 demand balance → Module 21 trade → `vm_prod_reg`); M31 itself reads `vm_prod`/`vm_land`/`vm_yld`, NOT `vm_dem_feed` directly (`modules/31_past/endo_jun13/equations.gms:16-18`, q31_prod). The interface flow is organized via Modules 16 and 21 (`module.gms:18-19`)." Apply the same "indirect/via 16+21" qualifier to doc:1141 and doc:1236.

### BUG module_70-B2 — Variable scaling values wrong (both lines + 10^6 claim)
- **Severity**: Major
- **Class**: 13 (wrong parameter/value) / 12 (content-level citation mismatch)
- **Trigger** (§1 Major): "Right concept, wrong number". Both numeric values at the cited lines are wrong, and they are not equal as the doc implies.
- **Claim in doc** (doc:1062-1063, 1066): "`vm_cost_prod_livst.scale(i,factors) = 10e5` / `vm_cost_prod_fish.scale(i) = 10e5`" and "Scale factor of 10^6 (million USD)...".
- **Reality in code**: `vm_cost_prod_livst.scale(i,factors) = 1e4;` and `vm_cost_prod_fish.scale(i) = 1e5;` — the two are DIFFERENT (1e4 vs 1e5), neither equals 10e5 (=1e6). (Identical in both realizations' scaling.gms.)
- **File evidence**: `modules/70_livestock/fbask_jan16/scaling.gms:9-10` (and `fbask_jan16_sticky/scaling.gms:9-10`).
- **verify_cmd**: `sed -n '9,11p' /tmp/magpie_develop_ro/modules/70_livestock/fbask_jan16/scaling.gms` → `vm_cost_prod_livst.scale(i,factors) = 1e4;` / `vm_cost_prod_fish.scale(i) = 1e5;` / `*q70_feed.scale(i,kap,kall) = 1e-2;`
- **confirmed**: true
- **Proposed fix**: Replace the doc code block with:
  ```
  vm_cost_prod_livst.scale(i,factors) = 1e4
  vm_cost_prod_fish.scale(i) = 1e5
  ```
  and replace the following sentence with: "Scale factors (10,000 for livestock factor costs, 100,000 for fish) improve solver numerics for the cost equations. (Identical in `fbask_jan16` and `fbask_jan16_sticky`.)"

### BUG module_70-B3 — vm_yld pasture: wrong set-member label "past" + malformed index order
- **Severity**: Minor
- **Class**: MANDATE 12 (exact set-member labels) / 3 (suffix/index)
- **Trigger** (§1 Minor): "Wrong detail, careful reader not misled into action" — but the label "past" is a real, distinct set member, so it is a genuine confusion.
- **Claim in doc** (doc:540, doc:1224, doc:1237): "`vm_yld(j,"past",kve)`" (Module 14 scales pasture yields).
- **Reality in code**: `vm_yld(j,kve,w)` declared in 14_yields/managementcalib_aug19/declarations.gms:26; pasture yield is `vm_yld(j2,"pasture",w)` (q14_yield_past, equations.gms:36) and `vm_yld(j2,"pasture","rainfed")` (q31_prod, 31_past/endo_jun13/equations.gms:18). The crop-set member is **"pasture"**, NOT "past" (which is the `vm_land` land-type member). Also the doc's index order puts `kve` in the 3rd slot, but the 3rd index is `w` (water/irrigation); the crop member belongs in the 2nd (kve) slot.
- **File evidence**: `modules/14_yields/managementcalib_aug19/declarations.gms:26` + `.../equations.gms:36`.
- **verify_cmd**: `rg -n "vm_yld" /tmp/magpie_develop_ro/modules/14_yields/managementcalib_aug19/declarations.gms` → `vm_yld(j,kve,w)`; `rg -n '"pasture"' .../equations.gms` → `vm_yld(j2,"pasture",w)`
- **confirmed**: true
- **Proposed fix**: In doc:540, 1224, 1237 replace `vm_yld(j,"past",kve)` with `vm_yld(j,"pasture",w)` (member is "pasture", water dim is `w`).

### BUG module_70-B4 — module.gms:16 citation for the Module-14 yields link points at Module-31 content
- **Severity**: Minor
- **Class**: 12 (content-level citation mismatch)
- **Trigger** (§1 Minor): "Off-by citation where adjacent content says something different; careful reader would notice". The underlying claim (M14 consumes the factor) is TRUE and correctly cited elsewhere (doc:538 → presolve.gms:23-70), so this is a localized citation slip.
- **Claim in doc** (doc:718): "**To Module 14 (Yields)**: Scales pasture yields to account for exogenous intensification (`module.gms:16`)".
- **Reality in code**: `module.gms` contains NO reference to Module 14, "yields", or `pm_past_mngmnt_factor` (module.gms:16-17 is about Module 31 / pasture feed demand). The pm_past_mngmnt_factor→M14 relationship is defined in presolve.gms:24-26 ("used to scale biophysical pasture yields in the module [14_yields]") and consumed in 14_yields/.../equations.gms:38.
- **File evidence**: `modules/70_livestock/module.gms` (no M14 mention); `modules/70_livestock/fbask_jan16/presolve.gms:24-26`.
- **verify_cmd**: `rg -n "14_yields|yields|pm_past_mngmnt" /tmp/magpie_develop_ro/modules/70_livestock/module.gms` → EXIT 1 (no match). Positive control: vm_dem_feed grep does hit module.gms, so the file IS searched.
- **confirmed**: true
- **Proposed fix**: In doc:718 change the citation from `(module.gms:16)` to `(presolve.gms:23-26; consumed in modules/14_yields/managementcalib_aug19/equations.gms:38)`.

### BUG module_70-B5 — Factor-requirement formula uses bare `livestock_productivity` and drops the sys_to_kli sum
- **Severity**: Minor
- **Class**: 2 (hallucinated variable name) / MANDATE 10 (set-sum non-expansion)
- **Trigger** (§1 Minor, tie-breaker pulls down): the bare name is a recognizable shorthand and the doc uses the correct name `i70_livestock_productivity` elsewhere (doc:552, 1078), so a careful reader is not misled into editing a non-existent variable; but it is presented with a code citation (`preloop.gms:88`) and the `sys` index is left dangling.
- **Claim in doc** (doc:156-157 and doc:478-480): "`i70_fac_req_livst(t,i,kli) = i70_cost_regr(i,kli,"cost_regr_b") * livestock_productivity(t,i,sys) + i70_cost_regr(i,kli,"cost_regr_a")`".
- **Reality in code** (preloop.gms:88): `i70_fac_req_livst(t_all,i,kli) = i70_cost_regr(i,kli,"cost_regr_b") * sum(sys_to_kli(sys,kli), i70_livestock_productivity(t_all,i,sys)) + i70_cost_regr(i,kli,"cost_regr_a");` — variable is `i70_livestock_productivity` (not bare `livestock_productivity`), and it is wrapped in `sum(sys_to_kli(sys,kli), ...)` to map the system to the product `kli` (the doc's bare `(t,i,sys)` leaves `sys` unbound).
- **File evidence**: `modules/70_livestock/fbask_jan16/preloop.gms:88` (identical in sticky/preloop.gms:88).
- **verify_cmd**: `sed -n '88p' /tmp/magpie_develop_ro/modules/70_livestock/fbask_jan16/preloop.gms` (read in session) → confirms `sum(sys_to_kli(sys,kli), i70_livestock_productivity(t_all,i,sys))`.
- **confirmed**: true
- **Proposed fix**: In doc:156-157 and doc:478-480 replace `livestock_productivity(t,i,sys)` with `sum(sys_to_kli(sys,kli), i70_livestock_productivity(t,i,sys))` to match the code (correct variable name + mapping sum).

---

## Deferred (not flagged — uncertain or not code-actionable)

- **Module 36 reads `vm_cost_prod_livst(i2,"labor")`** (36_employment/exo_may22/equations.gms:24) but the doc's OUTPUT section (doc:707-712) lists only Module 11 as a consumer. Per MANDATE 13 this is an incomplete consumer set, but the doc DOES document the M70↔M36 relationship in the other direction (M70 reads wage params from M36, doc:740-746), and M36's read is for employment accounting, not cost aggregation. Borderline Informational; defer rather than risk over-flagging. Candidate addition: note M36 also reads `vm_cost_prod_livst("labor")` for labor-demand reporting.
- **"~450 lines of code"** (doc:7, 1256, 1294). Actual fbask_jan16 total is 625 lines (incl. license headers + R-output sections); ~534 excluding R-output blocks. The "~" qualifier and LoC being non-load-bearing metadata make this Informational at most; not something a user acts on. Defer.
- **doc:95 "alongside food, material, seed, and bioenergy demands (`module.gms:18-19`)"** — module.gms:18-19 names the interface variables but does not enumerate food/material/seed/bioenergy (that is Module 16 domain). The enumeration is correct as M16 behavior; the citation is to the interface declaration. Not a clear bug; defer.
- **doc:720-724 `im_slaughter_feed_share` "To Other Modules ... for mass balance"** — vague; sole direct consumer is M55 (awms). Doc is imprecise but not wrong. Defer (could be sharpened to name M55).
- **`vm_supply` interface** mentioned in module.gms:18 is not discussed in the doc; not an error of commission. Defer.

---

## Summary

Strong doc. Default realization correct (`fbask_jan16` — the R3 `fbask_jul23` confabulation is NOT present). All 7+8 equations, all scalar/switch defaults, all set definitions/counts (5 systems, 10 feed scen, 17 SCP scen, 249 countries, kcer70), the SCP and pasture-management mechanisms, and the input-data citations are verbatim-correct. Two Major bugs: (B1) `vm_dem_feed` is listed as a direct output to Module 31 but M31 reads it only transitively via Modules 16+21 (MANDATE 17 / R24 anchor); (B2) both `scaling.gms` values are wrong (`1e4`/`1e5`, not `10e5`/`10e5`). Three Minor: (B3) `vm_yld(j,"past",kve)` wrong member+index, (B4) module.gms:16 citation for the M14 link points at M31 content, (B5) factor-req formula uses bare `livestock_productivity` and drops the `sum(sys_to_kli...)`.
