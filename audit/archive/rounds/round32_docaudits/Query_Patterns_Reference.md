# Round 32 Doc Audit — core_docs/Query_Patterns_Reference.md

**Auditor**: Opus 4.8 (1M), adversarial doc auditor
**Date**: 2026-05-30
**Target**: `<magpie-agent>/core_docs/Query_Patterns_Reference.md`
**Ground truth**: `/tmp/magpie_develop_ro` @ HEAD `ee98739fd` (Merge PR #887)
**Rubric**: `audit/flywheel_rubric.md` v1.2

---

## Scope note

This doc is mostly **methodology/prose** (how to recognize and answer query types). It is NOT a module reference. But it embeds concrete code-checkable claims inside its worked-example response patterns: file:line citations, equation/variable/parameter names, parameter defaults, set members, equation formulas, and one cross-module producer/consumer chain. Those are the auditable surface. Pure advice text (e.g., "always trace the FULL chain", "systematic verification beats intuition", the decision-tree shape) is non-code-checkable and deferred.

**Pre-run advisory** ("verify the GAMS examples and the parameterization-vs-mechanistic appendix claims; defer non-code-checkable methodology prose"): **largely REFUTED.** Every appendix classification example and every Pattern-1 SOM workflow citation verified accurate against develop. One real citation-path defect (Pattern 2) and two lower-severity item(s) found. See below.

---

## Claims verified ACCURATE (with code evidence)

### Pattern 1 (Parameterized-vs-implemented, SOM tillage)
- `i59_tillage_share(i,tillage59)=0;` and `i59_tillage_share(i,"full_tillage")=1;` hardcoded — **CONFIRMED** at `modules/59_som/cellpool_jan23/preloop.gms:52-53`. Doc cites `cellpool_jan23/preloop.gms:52-53` (line 46) — **exact match**.
- Sets `tillage59`, `inputs59` exist — **CONFIRMED** `cellpool_jan23/sets.gms:13,16`.
- `f59_cratio_tillage` loaded as a table in input.gms — **CONFIRMED** `cellpool_jan23/input.gms:49` (doc step 2 greps it in input.gms; resolves).
- `i59_cratio` used in preloop — **CONFIRMED** `cellpool_jan23/preloop.gms:60` (doc step 3 greps it in preloop.gms; resolves).
- RED FLAG #4 example `s29_treecover_target = 0  ! Disabled by default` — **CONFIRMED**: `config/default.cfg:849` (`<- 0   # def = 0`) and `modules/29_cropland/detail_apr24/input.gms:24` (`/ 0 /`). Default verified per MANDATE 3.
- Default realization of M59 is `cellpool_jan23` — **CONFIRMED** `config/default.cfg:1916`.

### Pattern 2 (cross-module mechanism trace) — variable/equation names
- `v29_treecover(j,ac)`, `q29_treecover`, `vm_treecover(j)` all exist — **CONFIRMED** `modules/29_cropland/detail_apr24/declarations.gms:39,40,58` and `equations.gms:83-84`.
- Aggregation `q29_treecover(j2) .. vm_treecover(j2) =e= sum(ac, v29_treecover(j2,ac))` — **CONFIRMED** verbatim at `detail_apr24/equations.gms:83-84`.
- `i59_cratio_treecover` = 1 — **CONFIRMED** `cellpool_jan23/preloop.gms:82` (`i59_cratio_treecover = 1;`); doc says `1.0`, same value.
- `vm_carbon_stock` is the interface variable for carbon (declared M56) — **CONFIRMED** `modules/56_ghg_policy/price_aug22/declarations.gms:34` `vm_carbon_stock(j,land,c_pools,stockType)` (matches G2 anchor).

### Pattern 3 (temporal) — names/formulas
- `q59_som_target_cropland`, `q59_som_target_noncropland` — **CONFIRMED** `cellpool_jan23/equations.gms:20,31`; declarations.gms:28,29.
- `i59_lossrate(t) = 1 - 0.85^timestep_length` — code: `i59_lossrate(t)=1-0.85**m_yeardiff(t);` (`cellpool_jan23/preloop.gms:45`). `m_yeardiff(t)` = `m_year(t)-m_year(t-1)` (`core/macros.gms:41`) = timestep length in years. Doc's prose form is **conceptually faithful** (not flagged).
- `vm_lu_transitions` is real with index order `(j,land_from,land_to)` — **CONFIRMED** `modules/10_land/.../declarations.gms:23`. (Set-member label `"forest"` issue: see Bug QPR-B3.)

### Pattern 4 APPENDIX (parameterization-vs-mechanistic classification examples) — ALL ACCURATE
- **Ex.1 Module 51 PARAMETERIZED**: `q51_emissions_*` apply emission factors (`f51_ef_resid_burn`, `f51_ef3_confinement`) — **CONFIRMED** `modules/51_nitrogen/rescaled_jan21/equations.gms:22-83`. Default realization `rescaled_jan21` (`config:1550`). Classification correct.
- **Ex.2 Module 35 disturbance PARAMETERIZED**: `wildfire` is a set member (`pot_forest_may24/sets.gms:12,15`); `f35_forest_disturbance_share` loaded from `f35_forest_disturbance_share.cs4` (`input.gms:50,53`); disturbance loss = `pc35_secdforest × share × timestep` (`presolve.gms:14-15`). "Applies historical rates labeled 'wildfire', not fire simulation" — **CONFIRMED**. Default `pot_forest_may24` (`config:1135`).
- **Ex.3 Module 52 Chapman-Richards MECHANISTIC**: `realization.gms:12,16` "Chapman-Richards growth model"; `f52_growth_par(clcl,chap_par,forest_type)` "chapman-richards equation" (`input.gms:37`); calibrated k via bisection (`preloop.gms:9`); macro `m_growth_vegc(S,A,k,m,ac) = S + (A-S)*(1-exp(-k*(ac*5)))**m` (`core/macros.gms:18`). Doc's generic form `C(age)=A×(1-exp(-k×age))^m` (line 328) matches Chapman-Richards. **CONFIRMED.** Default `normal_dec17` (`config:1556`).
- **Ex.4 Module 42 water demand HYBRID**: `q42_water_demand` computes `vm_watdem × irrig_eff =e= sum(kcr, vm_prod × wat_req) + sum(kli, ...)` (`all_sectors_aug13/equations.gms:10-14`). "Fixed water requirements × dynamic crop areas" — **CONFIRMED.** Default `all_sectors_aug13` (`config:1319`).
- The mechanistic-illustration `vm_carbon(j,ac) =e= f_chapman_richards(A,k,m,ac)` (line 242) is explicitly pseudocode (`f_chapman_richards` is not a real function) used to illustrate equation *structure* — correctly framed; not flagged (MANDATE 5 satisfied by context).

### Pattern 5 (debugging tree)
- `vm_cost_glo` — **CONFIRMED** `modules/11_costs/default/declarations.gms:9`; `q11_cost_glo .. vm_cost_glo =e= sum(i2, v11_cost_reg(i2))` (`equations.gms:10`). "Check: vm_cost_glo has all components" is accurate.
- modelstat codes (4 infeasible, 3 unbounded, 13 error, 1-2 optimal) are standard GAMS solver conventions, not MAgPIE-code claims — correct GAMS general knowledge; not a doc-vs-code matter (deferred as non-MAgPIE-specific).

---

## Bugs Found

### Bug QPR-B1 — Pattern 2 citation points at wrong module file (treecover aggregation)
- **Severity**: Major
- **Trigger** (§1 Major): "Citation points at content ... AND the actual cited content says something materially different (citation drift to wrong content)."
- **Class**: 11 (Wrong GAMS filename / path) + 10 (stale file:line citation)
- **Doc line**: Query_Patterns_Reference.md:113
- **Claim**: Under "**1. Module 29 (Cropland)** - Tree cover optimization", lists `q29_treecover aggregates to vm_treecover(j)` with `Location: modules/59_som/cellpool_jan23/equations.gms:83-84`.
- **Reality**: `q29_treecover`/`vm_treecover` live in `modules/29_cropland/detail_apr24/equations.gms:83-84`. The cited `modules/59_som/cellpool_jan23/equations.gms:83-84` is a DIFFERENT equation — `q59_nr_som_fertilizer` (nitrogen made available from SOM loss). The line numbers (83-84) coincide; the module path is wrong.
- **File evidence**: correct → `modules/29_cropland/detail_apr24/equations.gms:83` (`q29_treecover(j2) ..`), `:84` (`vm_treecover(j2) =e= sum(ac, v29_treecover(j2,ac));`). Wrong-target content → `modules/59_som/cellpool_jan23/equations.gms:81-90` is `q59_nr_som_fertilizer`/`q59_nr_som_fertilizer2`.
- **verify_cmd**: `sed -n '83,84p' /tmp/magpie_develop_ro/modules/29_cropland/detail_apr24/equations.gms` → prints `q29_treecover(j2) .. / vm_treecover(j2) =e= sum(ac, v29_treecover(j2,ac));`; and `sed -n '78,92p' .../59_som/cellpool_jan23/equations.gms` → prints `q59_nr_som_fertilizer(j2) ..` etc. (materially different).
- **confirmed**: true
- **Proposed fix**: replace `> - Location: \`modules/59_som/cellpool_jan23/equations.gms:83-84\`` with `> - Location: \`modules/29_cropland/detail_apr24/equations.gms:83-84\``

### Bug QPR-B2 — Pattern 2 attributes soil-carbon-stock production to Module 52 (producer/consumer inversion)
- **Severity**: Major (held at moderate confidence; illustrative prose; tie-breaker keeps it below Critical)
- **Trigger** (§1 Major): producer/consumer mischaracterization for a load-bearing interface variable (R20/G2 anchor concern: user tracing the chain looks in the wrong module). Not Critical because it sits in an explicitly illustrative response-pattern block and the variable name itself is correct.
- **Class**: 15 (latent doc error — wrong populator/consumer attribution, prose)
- **Doc line**: Query_Patterns_Reference.md:120-122
- **Claim**: "**3. Module 52 (Carbon)** - Stock aggregation: Aggregates SOM into total soil carbon. Reports: `vm_carbon_stock(j,"crop","soilc")`."
- **Reality**: Module 59 (SOM) POPULATES the soilc pool of `vm_carbon_stock` (`vm_carbon_stock(j2,land,"soilc",stockType)`). Module 52 only READS `vm_carbon_stock` to compute CO2 emissions (`q52_emis_co2_actual`), it does NOT aggregate SOM into the soil-carbon stock. Per G2 anchor: `vm_carbon_stock` is declared in M56, populated by land modules + M59, and M52 is a consumer. (Secondary: the signature is `(j,land,c_pools,stockType)` — 4 indices; doc's `(j,"crop","soilc")` drops `stockType`. Minor abbreviation, folded into this bug.)
- **File evidence**: populator → `modules/59_som/cellpool_jan23/equations.gms:62` (`vm_carbon_stock(j2, land,"soilc",stockType)`); reader → `modules/52_carbon/normal_dec17/equations.gms:19` (`(pcm_carbon_stock(...) - vm_carbon_stock(j2,land,c_pools,"actual"))`); realization.gms:14 calls it "the interface `vm_carbon_stock`"; declaration → `modules/56_ghg_policy/price_aug22/declarations.gms:34`.
- **verify_cmd**: `rg -n 'vm_carbon_stock\(.*"soilc"' .../59_som/cellpool_jan23/*.gms` → `equations.gms:62`; `rg -n "vm_carbon_stock" .../52_carbon/normal_dec17/equations.gms` → `:14` (comment "in the interface vm_carbon_stock"), `:19` (read). No write of soilc in M52.
- **confirmed**: true (the code facts); the *severity/framing* carries moderate confidence because the text is an illustrative template, not a reference claim.
- **Proposed fix**: reword to reflect populate-vs-read. Replace lines 120-122 with:
  `> **3. Module 59 (SOM) populates → Module 52 (Carbon) reads** - Stock accounting:`
  `> - Module 59 writes the soil-carbon pool of the interface variable: \`vm_carbon_stock(j,land,"soilc",stockType)\` (modules/59_som/cellpool_jan23/equations.gms:62)`
  `> - Module 52 READS \`vm_carbon_stock\` to compute CO2 emissions in \`q52_emis_co2_actual\` (modules/52_carbon/normal_dec17/equations.gms:16-19); it does not aggregate SOM into the stock`
  (Note for fixer: `vm_carbon_stock` is declared in Module 56, not 52 — see G2 anchor; avoid re-introducing "Module 52 declares/owns vm_carbon_stock".)

### Bug QPR-B3 — Pattern 3 uses non-existent land-set member `"forest"`
- **Severity**: Minor
- **Trigger** (§1 Minor): wrong detail in an illustrative template; variable name + index order correct; tie-breaker pulls down. MANDATE 12 (exact set-member labels).
- **Class**: 12 (content-level mismatch / set-member label)
- **Doc line**: Query_Patterns_Reference.md:146
- **Claim**: "Tracked by: `vm_lu_transitions(j,"forest","crop")`" (and the prose "Forest → cropland via land-use transition matrix").
- **Reality**: The `land` set is `/ crop, past, forestry, primforest, secdforest, urban, other /` (`core/sets.gms:251`). There is no member `"forest"`. `vm_lu_transitions(j,land_from,land_to)` with `land_from`/`land_to` aliased to `land` (`modules/10_land/.../sets.gms:19-20`). A real forest→crop transition would use `"primforest"`/`"secdforest"`/`"forestry"`.
- **File evidence**: `core/sets.gms:251` land members; `modules/10_land/dynamic_apr24/declarations.gms:23` `vm_lu_transitions(j,land_from,land_to)`; `modules/10_land/.../sets.gms:19-20` `alias(land,land_from); alias(land,land_to);`.
- **verify_cmd**: `sed -n '248,262p' /tmp/magpie_develop_ro/core/sets.gms` → land members list (no "forest"); `rg -n 'vm_land\(.*"forest"' .../modules/` → no hits (confirming "forest" is not used as a land label anywhere).
- **confirmed**: true
- **Proposed fix**: replace both occurrences in the Pattern 3 block: `vm_lu_transitions(j,"forest","crop")` → `vm_lu_transitions(j,"secdforest","crop")`, and "Forest → cropland" → "Secondary forest → cropland". (Any of forestry/primforest/secdforest is valid; secdforest is the most representative of natural-forest loss.)

---

## Deferred (not code-verifiable or out of scope — NOT edited)

- All Pattern advice prose (e.g., "Always trace the FULL chain", "Systematic verification beats intuition", the "80% of complex queries" claim, response-structure recommendations). Methodology, not a code claim.
- modelstat numeric codes in Pattern 5 (4/3/13/1-2): standard GAMS solver conventions, correct, but not a MAgPIE-source claim — nothing to verify against the develop tree.
- The "60-80% of natural level" / "10-22% SOM increase from no-tillage" figures (lines 51, 124, 165): these are interpretive/IPCC-literature magnitudes used illustratively, not pinned to a single code parameter; not adversarially checkable against a `.gms` line without the input `.cs3`/`.cs4` data (which is unreadable here). No bug asserted.
- Pattern 3 convergence percentages ("5y: 44%, 10y: 80%, 20y: 96%"): arithmetic consequences of `1-0.85^n` framing; internally consistent illustration, not a code claim. Not flagged.

---

## Summary

8 distinct code-checkable claim families verified; the parameterization-vs-mechanistic appendix (the advisory's specific concern) is fully accurate. 3 bugs: **2 Major** (QPR-B1 wrong module path in a treecover citation — clean reproducible defect; QPR-B2 producer/consumer inversion attributing soil-C stock production to M52 in an illustrative chain), **1 Minor** (QPR-B3 non-existent `"forest"` land-set label). No Critical. All Pattern-1 SOM citations, the four Pattern-4 classification examples, `i59_lossrate`, `i59_cratio_treecover`, `s29_treecover_target=0`, `vm_cost_glo`, and the Chapman-Richards macro form are correct.
