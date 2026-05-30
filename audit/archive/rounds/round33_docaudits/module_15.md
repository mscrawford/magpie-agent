# Round 33 doc audit — module_15.md (Food Demand & Anthropometric Estimation)

**Target doc**: `magpie-agent/modules/module_15.md`
**Ground truth**: `/tmp/magpie_develop_ro` (develop worktree), `config/default.cfg`
**Realization audited**: `anthro_iso_jun22` (default — confirmed `config/default.cfg:410` `cfg$gms$food <- "anthro_iso_jun22"`; only realization dir present)
**Date**: 2026-05-30
**Auditor model**: Opus 4.8 (1M)

---

## Overall verdict: MOSTLY ACCURATE

This is a high-quality, heavily-verified doc. The equation set (18 equations: 1 MAgPIE constraint + 17 standalone model), all equation formulas, all equation file:line citations, all 15 input-file citations, the primary interface variable (`vm_dem_food`) consumer set, all scalar/switch defaults, and the Module-09 dependency set are accurate. Three code-verifiable errors found: one Major count drift (×3 occurrences), one Major wrong-consumer-attribution, and one Minor fabricated number.

**Accuracy score: 7/10** (1 Major[×3 loc] count + 1 Major attribution + 1 Minor = 2·2 + 1 = 5 → 10−5 = 5; but the two Majors are a single count-drift root and a single attribution root, and the doc is otherwise exceptionally clean — scoring at the "3-5 bugs, some Major" lower band ≈ 7).

---

## Advisory checker resolution (pre-run flag)

The pre-run advisory asked to verify: *"Expected default realization anthro_iso_jun22. Confirm s15_exo_diet default = 0. Verify the diet→food-demand chain."*

- **Realization `anthro_iso_jun22` = default**: CONFIRMED. `config/default.cfg:410`.
- **`s15_exo_diet` default = 0**: CONFIRMED (doc is CORRECT). `input.gms:76` → `s15_exo_diet ... / 0 /`. Doc:484 states default 0. **No inverted-Boolean bug.** (This was the Critical-prone item; refuted.)
- **Diet→food-demand chain**: VERIFIED. `s15_exo_diet=1` triggers `exodietmacro.gms` (included at `presolve.gms:321`), which adjusts `p15_kcal_pc_iso` → `p15_kcal_pc` → `p15_kcal_pc_calibrated`, fed into the MAgPIE constraint `q15_food_demand` (`equations.gms:10-14`) on the RHS. Chain variable/equation names in the doc are correct.

---

## Verified-correct claims (high-value confirmations)

| Doc claim | Evidence |
|---|---|
| Realization `anthro_iso_jun22`, 249 ISO countries | `config/default.cfg:410`; `scen_countries15` list = 249 members (`input.gms:34-58`, counted) |
| 18 equations = 1 MAgPIE constraint + 17 standalone | 18 q15_ defined in `equations.gms`; model block `m15_food_demand` (`declarations.gms:207-230`) has 17 (all except q15_food_demand) |
| All 18 equation formulas + line cites (q15_food_demand 10-14, q15_aim 31-35, q15_budget 48-52, q15_regr_bmi_shr 71-76, 6 bmi_shr eqs 81-123, q15_bmi_shr_agg 129-134, q15_intake 141-151, q15_regr_kcal 160-163, q15_regr 169-173, 4 foodtree eqs 181-207) | All match `equations.gms` line-for-line |
| All 15 input-file citations (input.gms:117-125, 135-159, 168-173, 204-257) | Every cited line range matches `input.gms` (spot-checked all 15; ≤1-line drift on File 8 only, content correct) |
| `vm_dem_food(i,kall)` Positive, mio. tDM/yr; `.fx(i,knf)=0` | `declarations.gms:14`; `presolve.gms:217` |
| **Direct consumers of `vm_dem_food` = Modules 16, 20, 62** (doc:20, 768-781, 892) | M16 `sector_may15/equations.gms:21` (+33,42); M20 `substitution_may21/equations.gms:33`; M62 `exo_flexreg_apr16/presolve.gms:22` (+postsolve:15). Positive control confirms M17/M21 do NOT directly read it. Consumer set complete, no phantoms, citations exact. All 3 consumer realizations are defaults. |
| Module-09 dependency set: im_pop, im_pop_iso, im_gdp_pc_ppp_iso, im_gdp_pc_mer_iso, im_demography, im_physical_inactivity | All 6 referenced in module-15 .gms (rg count, all present) |
| All scalar/switch defaults: s15_elastic_demand 0, s15_calibrate 1, s15_exo_diet 0, s15_exo_waste 0, s15_maxiter 10, s15_convergence 0.005, s15_exo_* components 1, s15_*_substitution 0, food_substitution_start/target 2025/2050 | `input.gms:66-114` — every default matches |
| c15_calibscen constant, c15_EAT_scen FLX, c15_kcal_scen healthy_BMI | `input.gms:9-27` |
| 10 optimization variables in food demand model | `declarations.gms:42-56` (9 positive + v15_objective free) |
| `v15_income_pc_real_ppp_iso.lo = 10` | `presolve.gms:243,268` |
| NLP solver CONOPT4 with CONOPT3 fallback | `presolve.gms:26,251` |
| Schofield intake = (intercept + slope·weight)·PAL; PAL 1.53-1.76 | `presolve.gms:189-197` |
| Value-added margins, Chen et al. 2025 coeffs, postsolve.gms:16-31 | `postsolve.gms:13-14,17-30` |
| Body height recursive update postsolve.gms:34-109 | `postsolve.gms:34-109` |
| India milk→chicken/egg/fish substitution presolve.gms:97-109 | `presolve.gms:97-108` (1/3 each) |
| Realization header cites realization.gms:20-40, FAO break 48-66 | `realization.gms:20-40`, 48-65 |

---

## Bugs found

### M15-B1 — "18 ages" / "18 age groups" (actual: 21) — Major, ×3 occurrences

- **Severity**: Major. **Trigger** (§1 Major): "Fabricated count for a set". **Class**: 6 (Hardcoded counts drift).
- **Doc lines**:
  - `module_15.md:572`: "**By**: Sex, age (18 age groups: 0-4, 5-9, ..., 100+)" (File 4, f15_bmi)
  - `module_15.md:813`: "BMI distribution by country, sex, age (6 BMI groups × 18 ages × 2 sexes)"
  - `module_15.md:1514`: "**6 BMI groups × 18 ages × 2 sexes**: Detailed demographic structure"
- **Reality in code**: The `age` set has **21** members: `0--4, 5--9, 10--14, 15--19, 20--24, 25--29, 30--34, 35--39, 40--44, 45--49, 50--54, 55--59, 60--64, 65--69, 70--74, 75--79, 80--84, 85--89, 90--94, 95--99, 100+`. `f15_bmi`, `p15_bodyweight`, `p15_intake` are all indexed by the full `age` set (21), not by `adult15` (which has 18). The doc's explicit enumeration starts at "0-4" (i.e. the full set), so "18" is the wrong count for the thing being described. (The `adult15` subset has 18 members — likely the source of the slip — but it is not what these three statements describe.)
- **File evidence**: `modules/09_drivers/aug17/sets.gms:13-19` (age set, 21 members). f15_bmi index: `modules/15_food/anthro_iso_jun22/input.gms:145`; p15_intake index: `declarations.gms:105`.
- **verify_cmd**: `sed -n '13,19p' modules/09_drivers/aug17/sets.gms` → 21 members enumerated (0--4 … 100+). Cross-check: `awk` count of comma-separated members = 21.
- **Confirmed**: true.
- **Proposed fix**: Replace "18 ages"/"18 age groups" with "21 ages"/"21 age groups" at all three locations:
  - 572: `**By**: Sex, age (21 age groups: 0-4, 5-9, ..., 100+)`
  - 813: `(6 BMI groups × 21 ages × 2 sexes)`
  - 1514: `**6 BMI groups × 21 ages × 2 sexes**: Detailed demographic structure`

### M15-B2 — `pm_kcal_pc_initial` (and `fm_nutrition_attributes`) attributed to Module 16; actual consumer is Module 70 — Major

- **Severity**: Major. **Trigger** (§1 Major): wrong consumer attribution that misleads about behavior (related to R20 anchor / MANDATE 13/17 family, but not the primary interface var so below the Critical bar). **Class**: 15 (latent doc error) / 13 (interface-consumer).
- **Doc line**: `module_15.md:766-771` — under "PROVIDES TO (3 modules) → 1. Module 16 (Demand)", the doc lists three variables provided to Module 16:
  > "`vm_dem_food(i,kfo)` ... ; `pm_kcal_pc_initial(t,i,kfo)`: Initial per capita demand (kcal/cap/day); `fm_nutrition_attributes(t,kfo,nutrition)`: Nutrition content"
- **Reality in code**: Only `vm_dem_food` is consumed by Module 16. `pm_kcal_pc_initial` is consumed by **Module 70 (livestock)** — NOT Module 16 — at `modules/70_livestock/fbask_jan16/presolve.gms:32,35,47` (cattle/milk/feed proxies). It is not referenced anywhere in `modules/16_demand/`. `fm_nutrition_attributes` is a global `fm_` parameter loaded in module 15's input.gms and consumed broadly (e.g. M70), but is also not referenced in `modules/16_demand/`. Module 70 is not listed anywhere in the doc's "PROVIDES TO" section, so a reader tracing module-15 outputs would both (a) wrongly expect M16 to read `pm_kcal_pc_initial`, and (b) miss M70 entirely.
- **File evidence**: `modules/70_livestock/fbask_jan16/presolve.gms:32,35,47` (consumer). Declaration: `modules/15_food/anthro_iso_jun22/declarations.gms:135` (`pm_kcal_pc_initial(t,i,kall)`).
- **verify_cmd**: `rg -ln "pm_kcal_pc_initial" modules/ --glob "*.gms"` → only module_15 (decl/presolve) + module_70 (fbask_jan16, fbask_jan16_sticky); `rg -ln "pm_kcal_pc_initial" modules/16_demand/` → exit 1 (no match); positive control `rg -cn "vm_dem_food" modules/16_demand/sector_may15/equations.gms` → 3 (grep works in that dir).
- **Confirmed**: true.
- **Proposed fix**: Remove `pm_kcal_pc_initial` and `fm_nutrition_attributes` from the Module-16 "Variable provided" sub-list (Module 16 receives only `vm_dem_food`). Add Module 70 (livestock) as a consumer of `pm_kcal_pc_initial`: e.g. add to "PROVIDES TO" — "**Module 70 (Livestock)**: `pm_kcal_pc_initial(t,i,kall)` — initial per capita demand used for cattle-stock / milk / feed proxies (`modules/70_livestock/fbask_jan16/presolve.gms:32,35,47`)." Note `pm_kcal_pc_initial` is declared `(t,i,kall)`, not `(t,i,kfo)` (declarations.gms:135).

### M15-B3 — "newborns × 760 kcal" pregnancy energy (actual: weighted 845 & 675 ≈ 778) — Minor

- **Severity**: Minor (tie_uncertainty: could be Major as a fabricated number, but ~2% off, descriptive in a "what it DOES" bullet, and the correct coefficients appear elsewhere in the same doc → tie-break down). **Trigger** (§1 Minor): wrong detail a careful reader wouldn't act on. **Class**: 6 / fabricated number.
- **Doc line**: `module_15.md:817` — "Extra energy for pregnancy/lactation: newborns × 760 kcal".
- **Reality in code**: `i15_kcal_pregnancy(t,iso) = sum(sex, im_demography(t,iso,sex,"0--4")/5) * ((40/66)*845 + (26/66)*675)`. The per-newborn coefficient is the weighted sum `(40/66)·845 + (26/66)·675 = 778.03` kcal — not 760. The figure "760" appears nowhere in the code. (Internally inconsistent: `module_15.md:451` correctly cites "Newborns × 845/675 kcal".)
- **File evidence**: `modules/15_food/anthro_iso_jun22/presolve.gms:203`.
- **verify_cmd**: `sed -n '203p' presolve.gms` → formula as above; `python3 -c "print((40/66)*845+(26/66)*675)"` → 778.03.
- **Confirmed**: true.
- **Proposed fix**: Change "newborns × 760 kcal" to "newborns × (weighted 845 and 675 kcal, ≈778 kcal/newborn)" at line 817, to match both the code and the doc's own line 451. (Or simply "newborns × 845/675 kcal" to mirror line 451.)

---

## Deferred (not code-verifiable / not edited)

- Doc's pedagogical "hierarchical tree" ASCII diagrams (doc:131-139, 319-330) — conceptual illustrations, not 1:1 code structures; not flagged.
- "PRIMARY DRIVER of agricultural production", "up to 8 GtCO2eq/yr mitigation" (doc:773, 1569) — qualitative/literature claims, not code-checkable here.
- Data-source provenance attributions (FAO FB2010/SUA2010, NCD-RisC, Global Burden of Disease, Willett 2019) — upstream-data claims; realization.gms confirms the FAO methodological-break narrative but the source datasets are preprocessing-side (route to PREPROC_AGENT for definitive provenance).
- Section 9 R/`readGDX` validation snippets — illustrative test code; object names (`ov_dem_food`, `p15_kcal_pc_calibrated`, `ov15_kcal_regr`) exist in `declarations.gms` R-section, but the snippets are pedagogical and not asserted as runnable against a specific GDX.
- Waste-ratio illustrative ranges (doc:1027-1031, "1.3-1.5 high-income" etc.) — labeled as illustrative; `s15_waste_scen` default 1.2 is confirmed, the ranges are not code values.

---

## Notes for the flywheel

- The `vm_dem_food` primary-interface consumer set (M16/M20/M62) is CORRECT and citation-exact — this is the high-stakes R20-anchor surface and it passed. The attribution error (B2) is on a secondary parameter (`pm_kcal_pc_initial`) whose real consumer (M70) was omitted; this is the same MANDATE-13/17 class but one tier down in stakes.
- The "18 vs 21 age" slip (B1) is a classic subset-vs-superset count drift (`adult15`=18 vs `age`=21) — analogous to the R16 ac140/ac300 anchor but far smaller in magnitude (1.17× vs 35×), hence Major not Critical.
- Equation count (18 total / 17 standalone) is correct — the R6 "22 equations" Major bug has stayed fixed.
