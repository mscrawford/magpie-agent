# Doc Audit — reference/GAMS_Fundamentals.md (Round 32)

**Auditor**: Opus adversarial doc auditor
**Date**: 2026-05-30
**Target**: `<magpie-agent>/reference/GAMS_Fundamentals.md`
**Ground truth**: official GAMS language docs (gams.com/latest) for GAMS-language claims; `/tmp/magpie_develop_ro` for MAgPIE-convention claims.
**Rubric**: `audit/flywheel_rubric.md` v1.2.

---

## Overall verdict: MOSTLY ACCURATE (lower band)

This is a GAMS *fundamentals* (Phase 1) teaching doc. The pure GAMS-language content is **strong** — every GAMS-semantics claim I checked against gams.com was correct (comments, modelstat/solvestat codes, objective-variable requirements, variable-type default bounds, integer/binary defaults). The MAgPIE Module-10 worked examples are **verbatim correct** against current `develop`.

The errors cluster almost entirely in **§5.10 "Common Equation Patterns in MAgPIE"** (lines 1216-1256), where three of the four module-attributed example equations (Module 16, 43, 15) use **invented equation names, invented variable names, and fabricated formulas**, presented in the same authoritative `*'`-roxygen, module-numbered format as the *correct* Module-10 example. Because the Module-10 example is exactly right, a reader is primed to trust the fabricated ones. One Minor wrong-default (`s70_scavenging_ratio`) and one Minor GAMS-semantics imprecision (declaration-order "enforced") round out the findings.

**The pre-run advisory's three R12 flags are RESOLVED / REFUTED** in the current doc (details in §"Advisory re-check" below): the inline/eol comment syntax is **correct** per gams.com; `power()` non-integer-exponent claim and reversed `.prior` priority are **not present** in the current doc text at all.

---

## Advisory re-check (R12 flags) — all three resolved or refuted

| R12 flag | Current-doc status | Evidence |
|---|---|---|
| "wrong inline-comment syntax" | **REFUTED — doc is correct** | Doc lines 126-127: `$onEolCom` enables `!!`; `$onInline` enables `/* */`. gams.com (UG_GAMSPrograms / UG_DollarControlOptions) confirms: default EOL marker is `!!` (set by `$eolCom`), default inline delimiters are `/*` `*/` (set by `$inlineCom`). Both correct. |
| "power() non-integer-exponent claim" | **NOT PRESENT** | Only mention of "power" is line 1376 prose ("Nonlinear growth functions (exponential, power)") — no exponent claim. `rg "power" GAMS_Fundamentals.md` → only line 1376. |
| "reversed .prior priority" | **NOT PRESENT** | `rg "\.prior\|priority" GAMS_Fundamentals.md` → no match. The doc contains no `.prior` discussion. |

Conclusion: whatever the R12 scoring saw, those areas have since been edited/removed or were mis-flagged. The current text is clean on all three.

---

## Verified-correct claims (high-value confirmations)

**GAMS-language semantics (vs gams.com):**
- Comment syntax (§1.6, lines 119-141): full-line `*` col-1, `$onEolCom`/`!!`, `$onInline`/`/* */`, `$ontext`/`$offtext` — all correct.
- Variable-type default bounds (§4.3): free (−∞,+∞), positive [0,+∞), negative (−∞,0], binary {0,1}, integer [0,+∞) default upper bound +inf — all correct per UG_Variables Table 1. The doc does NOT claim a finite integer upper bound (e.g. 100), so no bug.
- Objective-variable requirements (line 1358): "must be scalar, of type `free`, and appear in at least one equation" — verbatim-correct per UG_ModelSolve ("The objective variable must be scalar and of type free, and must appear in at least one of the equations").
- modelstat codes 1-5 (lines 1402-1408) and solvestat codes 1-4 (lines 1410-1415) — all correct per UG_GAMSOutput.
- Relational operators `=e=`/`=l=`/`=g=` (§5.4) — correct.

**MAgPIE conventions / examples (vs /tmp/magpie_develop_ro):**
- `landmatrix_dec18` is the (only) Module-10 realization (lines 102/182/209). `ls modules/10_land/` → `input/`, `landmatrix_dec18/`. ✓
- `q10_land_area`, `q10_cost`, `q10_landdiff`, `q10_transition_to`, `q10_transition_from`, `q10_landexpansion`, `q10_landreduction` — all real, formulas match verbatim. `modules/10_land/landmatrix_dec18/equations.gms:13,30,42,50`. ✓ (Doc lines 214-217, 1021-1029, 1196-1199, 1270-1278.)
- `pm_land_start(j,land)`, `vm_landdiff`, `vm_land`, `vm_cost_land_transition(j)` — all declared in `modules/10_land/landmatrix_dec18/declarations.gms:9,15,...`. ✓
- Region sets `h` and `i` = 12 regions (CAZ…USA) — `core/sets.gms:17-21`. ✓ (Doc lines 376, 401-405.)
- `j` cells `CAZ_1*CAZ_5 … USA_183*USA_200` = 200 cells — `core/sets.gms:57-68`. ✓ (Doc lines 277-285, 385.)
- `m_weightedmean` macro `(sum(s,x*w)/sum(s,w))$(sum(s,w)>0) + 0$(sum(s,w)<=0)` — verbatim match `core/macros.gms:16`. ✓ (Doc line 664.)
- `m_linear_time_interpol` macro exists — `core/macros.gms`. ✓ (Doc line 633.)
- Module-70 parameter formulas: `p70_cattle_stock_proxy(t,i) = im_pop*pm_kcal_pc_initial(...,"livst_rum")/i70_livestock_productivity(...,"sys_beef")` matches `modules/70_livestock/fbask_jan16/presolve.gms:32-33`; `p70_cattle_feed_pc_proxy` matches presolve.gms:47. ✓ (Doc lines 550-552, 683-686.)
- `vm_feed_balanceflow.fx / .up / .lo` block — matches `modules/70_livestock/fbask_jan16/presolve.gms:9-11` verbatim. ✓ (Doc lines 853-857.)
- MAgPIE objective: `solve magpie USING nlp MINIMIZING vm_cost_glo;` — confirmed literal text `modules/80_optimization/nlp_apr17/solve.gms:34`. ✓ (Doc lines 1351/1374/1383/1441 etc.) [NOTE: earlier rg output appeared to show `ln`/`n` — that was an rg match-highlighting artifact; reading the file directly confirms `vm_cost_glo`. False-positive avoided.]
- MAgPIE uses `nlp` + `conopt4` — `config/default.cfg:2282` (`nlp_apr17`), `:2291` (`conopt4`); `solve.gms:14` `option nlp = conopt4`. ✓ (Doc lines 1374, 1497, 1513.)

---

## Bugs found

### BUG-1 (Major) — Invented variable names in §5.10 MAgPIE examples (bug class 2, hallucinated variable name)

**Doc lines 1233-1236, 1244-1245, 1254** present these as real MAgPIE interface variables/parameters:
`vm_trade_import`, `vm_trade_export`, `vm_seed_demand`, `vm_processing` (Module-16 example); `vm_water_withdrawal`, `pm_water_available` (Module-43 example); `pm_demand_min` (Module-15 example).

**Reality in code — none of these names exist:**
- `vm_water_withdrawal` → real var is `vm_watdem(wat_dem,j2)` (`modules/43_water_availability/total_water_aug13/equations.gms:11`).
- `pm_water_available` → real RHS is the internal variable `v43_watavail(wat_src,j2)` (same line) — a `v43_`, not a `pm_`.
- `vm_seed_demand` → real is `vm_dem_seed`; `vm_processing` → real is `vm_dem_processing` (`modules/16_demand/sector_may15/equations.gms:26,23`). The doc inverts the real `vm_dem_*` naming.
- `vm_trade_import`/`vm_trade_export` → not module-16 variables at all; module-16 supply has no trade terms (trade enters via `vm_prod_reg` from module 21). Module 21 declares only `vm_cost_trade_*`.
- `pm_demand_min` → not declared anywhere.

**File evidence**: `modules/43_water_availability/total_water_aug13/equations.gms:10-11`; `modules/16_demand/sector_may15/equations.gms:19-29`; `modules/15_food/anthro_iso_jun22/equations.gms:10-14`.

**verify_cmd**:
```
grep -rl "vm_water_withdrawal" /tmp/magpie_develop_ro/modules /tmp/magpie_develop_ro/core   → (no files)
grep -rl "pm_water_available"  ...                                                          → (no files)
grep -rl "pm_demand_min"       ...                                                          → (no files)
grep -rhoE "vm_seed_demand\b|vm_processing\b" .../modules/*/*/declarations.gms              → (empty)
# positive control: grep -rl "vm_dem_food" .../15_food → module.gms, presolve.gms (tooling OK)
# positive control: grep -rhoE "vm_land\b" .../10_land/*/declarations.gms → vm_land (tooling OK)
```
confirmed = true. Class-2 (hallucinated variable name) is Critical-tendency; pulled to **Major** by tie-breaker because §5.10 is a syntax/pattern primer (not the authoritative module doc) — but the harm (a reader copies a non-existent name) is real. `tier_uncertainty` = true (Critical-leaning).

**proposed_fix**: rewrite the three §5.10 examples to use real names (see BUG-2/BUG-3 fix block, which replaces the whole examples).

---

### BUG-2 (Major) — Invented equation names attributed to real modules in §5.10 (bug class 9, wrong equation name)

**Doc line 1230**: `q16_food_supply(i,kall) ..` attributed "Food balance (Module 16)".
**Doc line 1243**: `q43_water_availability(i) ..` attributed "Water availability (Module 43)".

**Reality in code**:
- Module 16 has NO `q16_food_supply`. Actual supply equations are split by product group: `q16_supply_crops`, `q16_supply_livestock`, `q16_supply_secondary`, `q16_supply_residues`, `q16_supply_pasture`, `q16_supply_forestry` (+ `q16_seed_demand`, `q16_waste_demand`).
- Module 43 has NO `q43_water_availability`. Actual equation is `q43_water(j2)`.

**File evidence**: `modules/16_demand/sector_may15/equations.gms:19,31,40,...`; `modules/43_water_availability/total_water_aug13/equations.gms:10`.

**verify_cmd**:
```
grep -rhoE "q1[56]_[a-z_]+|q43_[a-z_]+" .../modules/16_demand/*/equations.gms .../15_food/*/equations.gms .../43_water_availability/*/equations.gms | sort -u
  → q15_food_demand, q16_supply_crops, q16_supply_livestock, ..., q43_water  (NO q16_food_supply, NO q43_water_availability)
```
confirmed = true. **Major** (per rubric §1 Major: misleads about behavior; "Invented equation name" is a Critical trigger but tie-breaker pulls to Major in pattern-primer context). `tier_uncertainty` = true.

**proposed_fix**: see combined fix block at BUG-3.

---

### BUG-3 (Major) — Fabricated formulas in §5.10 Module-16/43/15 examples (bug class 4, conceptual pseudo-code presented as real code)

The three example *bodies* do not match the real equations (independent of the name/var errors above):

- **Module 16** (doc 1230-1236): doc writes `vm_supply =e= vm_prod_reg + imports − exports − seed − processing`. Real `q16_supply_crops` (`equations.gms:19-29`) is `vm_supply(i2,kcr) =e= vm_dem_food + sum(kap4, vm_dem_feed) + vm_dem_processing + vm_dem_material + vm_dem_bioen + vm_dem_seed + v16_dem_waste + sum(ct, f16_domestic_balanceflow)` — a sum of *demand* components, with NO trade terms and a different structure.
- **Module 43** (doc 1242-1245): doc writes `sum(water_use, vm_water_withdrawal(i,water_use)) =l= pm_water_available(i)`. Real `q43_water(j2)` is `sum(wat_dem,vm_watdem(wat_dem,j2)) =l= sum(wat_src,v43_watavail(wat_src,j2))` — cell-indexed `j2` (not `i`), RHS is a *sum over sources*, sets are `wat_dem`/`wat_src` (not `water_use`).
- **Module 15** (doc 1251-1254): equation name `q15_food_demand` IS real, but doc writes `vm_supply(i,kall) =g= pm_demand_min(i,kall)`. Real `q15_food_demand(i2,kfo)` (`equations.gms:10-14`) is `(vm_dem_food(i2,kfo) + sum(ct,f15_household_balanceflow(...,"dm"))) * sum(ct,fm_nutrition_attributes(...,"kcal")*10**6) =g= sum(ct,im_pop(ct,i2)*p15_kcal_pc_calibrated(ct,i2,kfo)) * 365` — a kcal-conversion ≥ population×per-capita-calibrated×365. Entirely different; uses `vm_dem_food`/`kfo`, not `vm_supply`/`kall`/`pm_demand_min`.

**File evidence**: `modules/16_demand/sector_may15/equations.gms:19-29`; `modules/43_water_availability/total_water_aug13/equations.gms:10-11`; `modules/15_food/anthro_iso_jun22/equations.gms:10-14`.

**verify_cmd**: `Read` of the three files (contents quoted above). confirmed = true. **Major** (MANDATE 1 — formula without faithful provenance presumed fabricated; rubric "Fabricated formula presented as the code's actual implementation" is Critical-trigger, pulled to Major by pattern-primer tie-breaker). `tier_uncertainty` = true.

**Combined proposed_fix for BUG-1/2/3** — replace §5.10 lines 1227-1256 with real code (keep Module-10 conservation example unchanged), e.g.:

```gams
#### Mass Balance (Equality)
*' Crop supply balance (Module 16, sector_may15):
q16_supply_crops(i2,kcr) ..
  vm_supply(i2,kcr) =e=
    vm_dem_food(i2,kcr)
    + sum(kap4, vm_dem_feed(i2,kap4,kcr))
    + vm_dem_processing(i2,kcr)
    + vm_dem_material(i2,kcr)
    + vm_dem_bioen(i2,kcr)
    + vm_dem_seed(i2,kcr)
    + v16_dem_waste(i2,kcr)
    + sum(ct, f16_domestic_balanceflow(ct,i2,kcr));
(modules/16_demand/sector_may15/equations.gms:19-29)

#### Resource Constraints (Inequality <=)
*' Water constraint (Module 43, total_water_aug13):
q43_water(j2) ..
  sum(wat_dem, vm_watdem(wat_dem,j2)) =l=
  sum(wat_src, v43_watavail(wat_src,j2));
(modules/43_water_availability/total_water_aug13/equations.gms:10-11)

#### Demand Satisfaction (Inequality >=)
*' Food demand (Module 15, anthro_iso_jun22):
q15_food_demand(i2,kfo) ..
  (vm_dem_food(i2,kfo) + sum(ct, f15_household_balanceflow(ct,i2,kfo,"dm")))
    * sum(ct, fm_nutrition_attributes(ct,kfo,"kcal") * 10**6) =g=
  sum(ct, im_pop(ct,i2) * p15_kcal_pc_calibrated(ct,i2,kfo)) * 365;
(modules/15_food/anthro_iso_jun22/equations.gms:10-14)
```
(If the author prefers to keep §5.10 abstract/illustrative rather than load-bearing, the alternative fix is to switch these three to generic `q_*` names with abstract variables — like §5.4 — and DROP the "(Module NN)" attributions. Either fix removes the false authoritative claims.)

---

### BUG-4 (Minor) — Wrong scalar default value for `s70_scavenging_ratio` (bug class 13, wrong parameter default)

**Doc line 500**: `Scalar s70_scavenging_ratio     Scavenging ratio / 0.15 /;` (under §3.3 Method-1 "MAgPIE example").

**Reality in code**: `s70_scavenging_ratio ... / 0.385 /` — `modules/70_livestock/fbask_jan16/input.gms:27` (description: "Ratio to adjust estimated pasture feed demand using scavenged feed sources (1)").

**verify_cmd**: `rg -n "s70_scavenging_ratio" /tmp/magpie_develop_ro/modules/70_livestock/fbask_jan16/*.gms` → `input.gms:27:  s70_scavenging_ratio ... / 0.385 /`. confirmed = true.

**Severity**: **Minor**. It is an illustrative List-format syntax example, not a behavior claim a user acts on; but the value is concretely wrong and `s70_scavenging_ratio` is a real scalar, so it should match. (Class-13 is Critical-tendency for *behavioral* default claims; this is a syntax illustration → Minor by tie-breaker.)

**proposed_fix**: change `/ 0.15 /` to `/ 0.385 /` and align the description, OR use a clearly-generic scalar name to avoid implying it states the real default. Recommended: `Scalar s70_scavenging_ratio     Scavenging ratio (1) / 0.385 /;`.

---

### BUG-5 (Minor) — "This order ... is enforced by GAMS" overstates the rule (GAMS-semantics imprecision)

**Doc line 51**: "This order is not just convention—it's enforced by GAMS. You **must** declare entities before using them." — where "This order" refers to the 7-step block sequence SETS → DATA → VARIABLES → EQUATIONS → MODEL → SOLVE (lines 42-49).

**Reality (gams.com, UG_ModelSolve)**: GAMS enforces **declaration-before-use only**, NOT the fixed block ordering. A variable may be declared before a set; data assignments may interleave with declarations; the SETS-then-DATA-then-VARIABLES-then-EQUATIONS sequence is convention, not a compiler rule. The doc's second sentence states the true rule correctly, but the first sentence ("This order ... is enforced") is wrong.

**verify_cmd**: WebFetch gams.com UG_ModelSolve → "GAMS enforces that each identifier be declared before it is referenced, but does not mandate a rigid block structure for SETS, DATA, VARIABLES, and EQUATIONS." confirmed = true.

**Severity**: **Minor** — the adjacent correct sentence softens it, and it's conceptual prose; but it could mislead a reader into thinking the block order is mandatory.

**proposed_fix**: replace line 51 with: "GAMS does not enforce this *block ordering* — it is convention. What GAMS **does** enforce is **declaration-before-use**: every identifier must be declared before it is referenced (a variable may be declared before a set, etc.)."

---

## Deferred (not code-verifiable as bugs / explicitly mitigated — do NOT edit)

- `f10_land_initial(j,land)` + `./input/f10_land_initial.csv` (doc lines 525-529): the real Module-10 input is `f10_land(t_ini10,j,land)` from `avl_land_t.cs3` (`modules/10_land/landmatrix_dec18/input.gms:8-12`). NOT flagged as a bug because `f10_land_initial` is explicitly allowlisted in the doc header (line 3: `<!-- check-gams-vars: allow f10_land_initial,... -->`) — the author deliberately uses it as an illustrative placeholder, and the *syntax* shown (`$ondelim`/`$include`/`$offdelim` Table load) is correct. Noting only; the allowlist signals intent. (If the author wants realism, `f10_land` + `avl_land_t.cs3` is the real pair.)
- `s_interest_rate / 0.05 /` (line 472) and `s_start_year / 1995 /` (line 473): allowlisted (`s_interest_rate`) / generic scalar-syntax illustration. Not verified as real defaults; presented as syntax examples, not behavior claims. Deferred.
- `vm_x1`, `v70_feed` (allowlisted, line 3) used as deliberate "bad-name" / generic placeholders — not bugs.
- Module-15/16 default-realization names: `grep cfg$gms$food` / `cfg$gms$demand` in default.cfg returned no match under those exact keys; I did not need the default for the §5.10 findings (the equation NAMES are wrong regardless of realization, and I read the real equations directly). The exact cfg key for these modules is left unverified → deferred (not a bug).
- "Other IAMs" / general optimization prose — not MAgPIE-code-checkable.

---

## Summary

Pure GAMS-language content and the Module-10 worked examples are accurate (and the three R12-flagged areas are resolved/refuted). All 5 bugs are confirmed against current `develop` + gams.com. Four of five concentrate in §5.10's Module-16/43/15 "pattern" examples, which fabricate equation names (`q16_food_supply`, `q43_water_availability`), variable names (`vm_water_withdrawal`, `pm_water_available`, `vm_trade_import/export`, `vm_seed_demand`, `vm_processing`, `pm_demand_min`), and formulas, in authoritative module-attributed form alongside a verbatim-correct Module-10 example. Recommended fix: replace the three bad §5.10 examples with the real equations (provided), or de-attribute them to generic `q_*` illustrations. Plus one Minor wrong scalar default (`s70_scavenging_ratio` 0.15 → 0.385) and one Minor GAMS-semantics imprecision (declaration block-order "enforced").
