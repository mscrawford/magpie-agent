# Round 35 Doc Audit — module_31.md (31_past, endo_jun13)

**Target doc**: `magpie-agent/modules/module_31.md`
**Ground truth**: `/tmp/magpie_develop_ro` (develop worktree) + `config/default.cfg`
**Date**: 2026-05-30
**Auditor**: adversarial doc auditor (Opus, R35)

---

## Overall Verdict: MOSTLY ACCURATE (lower band)

The equation core is excellent — all 5 equation formulas, dimensions, constraint types, and the q31_* line citations match develop exactly. The high-risk content (realization status, dependency direction, set-member labels, carbon-stock declaration site) carries the bugs. Score ≈ 7/10 (one Major-cluster of dependency/realization errors + minor set-label/attribution issues).

The doc's self-assessment "Zero errors found" / "100% verified, zero errors" (lines 699, 715) is itself falsified by the findings below.

---

## Verified Claims (correct)

- **Default realization** `endo_jun13`: CONFIRMED. `config/default.cfg:969` `cfg$gms$past <- "endo_jun13"`. Doc line 22-23 correct.
- **`s31_fac_req_past` default = 1**: CONFIRMED. `input.gms:10` `/ 1 /` and `config/default.cfg:972` `cfg$gms$s31_fac_req_past <- 1`. Doc line 372, 376-377 correct.
- **Zeroing in postsolve**: CONFIRMED. `endo_jun13/postsolve.gms:10` `s31_fac_req_past = 0;`. Doc line 376 correctly states the actual zeroing happens in postsolve.gms:10 (not equations.gms). Good precision.
- **q31_prod** (`equations.gms:16-18`): formula `vm_prod(j2,"pasture") =l= vm_land(j2,"past") * vm_yld(j2,"pasture","rainfed")` matches exactly. Inequality `=l=` correct. Doc lines 85-111 correct.
- **q31_carbon** (`equations.gms:22-24`): formula `vm_carbon_stock(j2,"past",ag_pools,stockType) =e= m_carbon_stock(vm_land,fm_carbon_density,"past")` matches. Doc lines 115-145 correct.
- **q31_cost_prod_past** (`equations.gms:31-32`): formula `vm_cost_prod_past(i2) =e= sum(cell(i2,j2), vm_prod(j2,"pasture")) * s31_fac_req_past` matches. Doc lines 149-179 correct.
- **q31_bv_manpast** (`equations.gms:38-40`) and **q31_bv_rangeland** (`equations.gms:42-44`): both formulas match exactly. Doc lines 183-246 correct.
- **m_carbon_stock macro** (`core/macros.gms:99-101`): multiplies land × carbon_density summed over ag_pools, gated on stockType — matches doc line 143.
- **ag_pools = {vegc, litc}**: CONFIRMED. `56_ghg_policy/price_aug22/sets.gms:209-210` `ag_pools(c_pools) ... / vegc, litc /`. Doc lines 137-138 correct. q31_carbon is above-ground only (dims `ag_pools`) — "above ground only" claims (lines 145, 604, 69) correct.
- **Declaration sites**: `vm_cost_prod_past` in `endo_jun13/declarations.gms:18` (doc 255 ✓); `vm_prod` in `17_production/flexreg_apr16/declarations.gms:9` (doc 299 ✓); `vm_yld` in `14_yields/managementcalib_aug19/declarations.gms:26` (doc 288 ✓); `vm_land` in `10_land/landmatrix_dec18/declarations.gms:19` (doc 275 ✓); `vm_bv` in `44_biodiversity/.../declarations.gms` (doc 319 ✓ — M44 is the declarer).
- **5 equations declared** in `declarations.gms:10-15` (doc 685 ✓). Equation domains in declarations use `(j)`/`(i)`; equation defs use `(j2)`/`(i2)` — doc cites `(j2)`/`(i2)` from equations.gms, consistent.
- **vm_cost_prod_past → Module 11**: CONFIRMED. `11_costs/default/equations.gms:17` `+ vm_cost_prod_past(i2)`. Doc 177, 264, 495 correct.
- **preloop.gms init**: lines 9-10 (manpast), 12-13 (rangeland), using `pcm_land(j,"past")`. Doc 215, 244, 325 cite preloop.gms:8-10 / 12-13 — within range (comment at 8, code 9-10). Correct. `pcm_land` name correct.
- **presolve.gms:9**: `vm_land.lo(j,"past") = sum(consv_type, pm_land_conservation(t,j,"past",consv_type));` matches doc 281, 471 exactly.
- **vm_carbon_stock READ by M52**: CONFIRMED. `52_carbon/normal_dec17/equations.gms:16-19` (`q52_emis_co2_actual`). Doc 145 cross-ref correct.
- **vm_carbon_stock populators include M31**: CONFIRMED. M31 populates the "past" slice via q31_carbon. Full populator set from code: M29, M31, M32, M34 (presolve fx), M35, M52, M56, M59. (G2 anchor populator-set check passes for M31.)

---

## Bugs Found

### Bug R35-31-1 — static realization mislabeled as "deprecated"
- **Severity**: Major
- **Class**: 12 (content-level mismatch) / borderline 8 (realization status)
- **Trigger** (§1 Major): "claim is wrong in a way that misleads about behavior" — would steer a user away from a valid, functional realization for sensitivity analysis.
- **Claim in doc** (module_31.md:578): "**Status**: Appears to be deprecated (`modules/31_past/static/not_used.txt` file present)." (also line 696 footer: "static deprecated")
- **Reality in code**: `not_used.txt` is a STANDARD MAgPIE convention file present in **26 realizations**, including *default/active* ones (`38_factor_costs/sticky_labor/not_used.txt`, `59_som/cellpool_jan23/not_used.txt`, `29_cropland/simple_apr24/not_used.txt`). Its content is a CSV (`name,type,reason`) listing interface inputs the realization does NOT consume (here: `vm_prod, vm_yld, pm_land_conservation`). It is NOT a deprecation marker. The `static` realization is a fully functional alternative: `static/realization.gms` has a normal `@description`/`@limitations` block; `static/presolve.gms` fixes `vm_land.fx(j,"past")=pcm_land`, `vm_carbon_stock.fx`, `vm_bv.fx`, `vm_cost_prod_past.fx(i)=0`. Nothing indicates deprecation.
- **File evidence**: `/tmp/magpie_develop_ro/modules/31_past/static/not_used.txt` (CSV header `name,type,reason`); `static/realization.gms` (full description); `static/presolve.gms:1-30` (functional fixings); `find ... -name not_used.txt | wc -l` = 26.
- **verify_cmd / result**: `cat /tmp/magpie_develop_ro/modules/31_past/static/not_used.txt` → `name,type,reason / vm_prod, input, not needed / vm_yld, input, not needed / pm_land_conservation,input,questionnaire`. `find /tmp/magpie_develop_ro/modules -name not_used.txt | wc -l` → `26`.
- **Proposed fix**: Replace doc lines 576-582 with: "**Description**: Fixed (exogenous) pasture area. `presolve.gms` fixes `vm_land.fx(j,\"past\") = pcm_land(j,\"past\")` and correspondingly fixes `vm_carbon_stock`, `vm_bv`, and `vm_cost_prod_past` to zero. **Status**: Functional alternative realization (NOT deprecated — the `not_used.txt` file is a standard MAgPIE convention listing interface inputs the realization does not consume; it is present in 26 realizations including default ones, and does not signify deprecation). **When Used**: Sensitivity analysis where pasture area is held at initial spatially explicit patterns from Module 10. **Files**: `realization.gms`, `presolve.gms` (plus the conventional `not_used.txt`)." Also remove "static deprecated" from the line-696 metric.

### Bug R35-31-2 — "Provides To: Module 22" is a reversed dependency (phantom direction)
- **Severity**: Major
- **Class**: 15 (latent doc error — wrong dependency set) / R20 consumer-set anchor class
- **Trigger** (§1 Major): wrong dependency direction in a load-bearing set; per the R20 anchor a wrong producer/consumer set is treated as high-harm (a user reasoning about modification blast-radius would be misled).
- **Claim in doc** (module_31.md:527, "Dependency Chains → Provides To"): "**Provides To**: Module 10 (Land), Module 11 (Costs), Module 17 (Production), Module 52 (Carbon), Module 70 (Livestock feed), **Module 22 (Conservation)**".
- **Reality in code**: M31 provides NOTHING to M22. The relationship is one-directional M22→M31: M22 supplies `pm_land_conservation` which M31 reads in `presolve.gms:9`. M31's outputs (`vm_cost_prod_past`, `vm_bv`, `vm_carbon_stock("past")`, the `vm_prod`/`vm_land` constraints) are not read anywhere in `22_*/`. The doc itself correctly lists M22 under "Receives Input From" (line 488), so listing it ALSO under "Provides To" is internally contradictory and wrong in the provides direction.
- **File evidence**: `rg -ln "vm_cost_prod_past" /tmp/magpie_develop_ro/modules/22_*/` → no output (NONE); `rg -ln "vm_bv" /tmp/magpie_develop_ro/modules/22_*/` → no output (NONE). Positive control: `vm_cost_prod_past` IS found in `11_costs/default/equations.gms` and `vm_bv` IS found across 44_biodiversity (so the search works).
- **verify_cmd / result**: `rg -ln "vm_cost_prod_past" /tmp/magpie_develop_ro/modules/22_*/` → (empty); `rg -ln "vm_bv" /tmp/magpie_develop_ro/modules/22_*/` → (empty); control `rg -ln "vm_bv" /tmp/magpie_develop_ro/modules/44_biodiversity/` → 7 files. Confirmed twice + positive control.
- **Proposed fix**: In doc line 527, remove "Module 22 (Conservation)" from the "Provides To" list. (M22 stays under "Receives Input From" / "Depends On" only.) The "Provides Output To" list at lines 493-498 already correctly omits M22 — make line 527 consistent with it: "**Provides To**: Module 10 (Land), Module 11 (Costs), Module 52 (Carbon), Module 70 (Livestock feed)". (Consider also dropping Module 17 — see Deferred — but M22 is the confirmed error.)

### Bug R35-31-3 — stockType members mislabeled ("reference stocks")
- **Severity**: Minor
- **Class**: 12 (exact set-member labels, MANDATE 12) — generalized label not traceable to code and factually wrong.
- **Trigger** (§1 Minor): wrong detail; a careful reader checking the set would notice. Not action-causing.
- **Claim in doc** (module_31.md:140-141): "**Stock Types** (`stockType`): Actual stocks vs. reference stocks (for carbon accounting)".
- **Reality in code**: `stockType` members are `actual` and `actualNoAcEst` (`56_ghg_policy/price_aug22/sets.gms:212-213` `/ actual, actualNoAcEst /`). There is no "reference" member. `actualNoAcEst` = actual stock excluding age-class establishment, not a "reference" stock. The m_carbon_stock macro gates on `sameas(stockType,"actual")` and `sameas(stockType,"actualNoAcEst")` (`core/macros.gms:100-101`).
- **File evidence**: `/tmp/magpie_develop_ro/modules/56_ghg_policy/price_aug22/sets.gms:212-213`; `/tmp/magpie_develop_ro/core/macros.gms:100-101`.
- **verify_cmd / result**: `sed -n '212,213p' .../56_ghg_policy/price_aug22/sets.gms` → `stockType Carbon stock types / actual, actualNoAcEst /`.
- **Proposed fix**: Replace doc lines 140-141 with: "**Stock Types** (`stockType`): `actual` (actual carbon stock) and `actualNoAcEst` (actual stock excluding age-class establishment) — see `modules/56_ghg_policy/price_aug22/sets.gms:212-213`."

### Bug R35-31-4 — vm_carbon_stock "Source: Module 52" misattributes the declaration site (G2)
- **Severity**: Minor (tier_uncertainty: true — between Minor and Major; pulled down per §1 tie-breaker because the doc explicitly adds "but calculated here" and uses "Source" loosely elsewhere)
- **Class**: 15 (latent doc error) / G2 declaration-site distinction
- **Trigger**: G2 anchor logic — `vm_carbon_stock` is DECLARED in Module 56, not Module 52; the doc attributes "Source: Module 52 (Carbon)". A reader equating "Source" with declaration site would look in the wrong module.
- **Claim in doc** (module_31.md:309-310): "`vm_carbon_stock(j,\"past\",ag_pools,stockType)` ... **Source**: Module 52 (Carbon) - but calculated here". Also lines 332-334 attribute `fm_carbon_density` Source: Module 52 (that parameter IS in M52 `normal_dec17/input.gms`, so that one is fine).
- **Reality in code**: `vm_carbon_stock(j,land,c_pools,stockType)` is DECLARED in `56_ghg_policy/price_aug22/declarations.gms:34`. Module 52 only READS it (`q52_emis_co2_actual`, equations.gms:16-19). The land modules incl. M31 POPULATE it. This is the exact DECLARED-in-M56 / POPULATED-by-land-modules / READ-by-M52 distinction the G2 regression guards.
- **File evidence**: `/tmp/magpie_develop_ro/modules/56_ghg_policy/price_aug22/declarations.gms:34`; not present in any `52_carbon/*/declarations.gms` (grep returned only M30 `vm_carbon_stock_croparea` and M56 for `vm_carbon_stock(`).
- **verify_cmd / result**: `rg -n "vm_carbon_stock" /tmp/magpie_develop_ro/modules/*/*/declarations.gms` → only `30_croparea/.../vm_carbon_stock_croparea` and `56_ghg_policy/price_aug22/declarations.gms:34: vm_carbon_stock(...)`. No M52 declaration.
- **Proposed fix**: In doc lines 309-310 and 497, change the parenthetical so it does not imply M52 declares the variable. Suggested line 309-310: "**Declared in**: Module 56 (GHG policy, `price_aug22/declarations.gms:34`). **Populated here** (q31_carbon, for the \"past\" slice). **Read by**: Module 52 (`q52_emis_co2_actual`) and Module 56." Keep `fm_carbon_density` Source: Module 52 as-is (correct).

---

## Deferred (not edited — uncertain or not code-verifiable)

- **"Provides To: Module 17" (line 527)**: M31 does not declare/provide a distinct variable to M17 — `vm_prod` is M17-declared and M31 only adds a constraint `q31_prod` on it. Calling that "provides to M17" is loose/backwards, but the constraint genuinely shapes the optimization. Borderline; recommend dropping in the fix for R35-31-2 but flagging as lower-confidence (the "constrains vm_prod" framing under "Receives Input From" line 487 already covers it). Not independently confirmed as a hard phantom.
- **"Provides To: Module 70" / "Pasture production capacity feeds back to livestock feed availability" (lines 498, 527, 500)**: M70 does NOT directly read any M31-specific token (`rg -ln "vm_cost_prod_past|q31_|vm_bv" modules/70_*/` → empty). The feedback is indirect via shared `vm_prod`/`vm_dem_feed` through M16 supply balance (`16_demand/sector_may15/equations.gms` q16_supply_pasture). The economic linkage is real but transitive (MANDATE 17). Doc qualifies it ("feeds back") so not flagged hard.
- **Centrality "~20 of 46 modules, 6 connections" / "Provides To 5-7, depends on 3" (line 524)**: soft heuristic metric, not strictly code-derivable. Not verified.
- **"Pasture carbon stocks assumed at natural vegetation level" (line 510)**: a claim about input-data (`fm_carbon_density`) semantics, decided in the R preprocessing pipeline (LPJmL), not in GAMS. Not GAMS-code-verifiable; route to preproc-agent if challenged.
- **Circular dependency "Type 1 - Temporal Feedback" + centrality "Processing Hub" (lines 526, 537-541)**: cross_module-derived characterizations, not single-file verifiable. Not checked.
- **q16_supply / M16 / M21 chain detail (lines 390-393)**: M16 `q16_supply_pasture` and `vm_dem_feed(kap4)` exist; pasture is in the `kap` set (core/sets.gms:231). The chain claim is defensible; not flagged.

---

## Citation spot-check summary (all PASS)

| Doc citation | Verified content | Verdict |
|---|---|---|
| equations.gms:16-18 (q31_prod) | matches | PASS |
| equations.gms:22-24 (q31_carbon) | matches | PASS |
| equations.gms:31-32 (q31_cost_prod_past) | matches | PASS |
| equations.gms:38-40 / 42-44 (bv) | matches | PASS |
| equations.gms:26-29, 34-35 (comment blocks) | comment text present at those lines | PASS |
| input.gms:10 (scalar /1/) | matches | PASS |
| preloop.gms:8-10, 12-13 (vm_bv.l init) | matches (comment@8, code 9-10/12-13) | PASS |
| presolve.gms:8-9 / :9 (vm_land.lo) | matches | PASS |
| postsolve.gms:10 (=0) | matches | PASS |
| declarations.gms:18 (vm_cost_prod_past) | matches | PASS |
| declarations.gms:10-15 (5 equations) | matches | PASS |
| 56_ghg_policy/price_aug22/declarations.gms:34 (implied by G2) | vm_carbon_stock declared here | PASS (and is the basis for Bug-4) |

No file:line citation drift found — the equation/citation core is solid. All bugs are in dependency-direction, realization-status, and set-member-label prose.
