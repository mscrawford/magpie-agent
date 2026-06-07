# Audit Report: carbon_balance_conservation.md

**Doc**: `cross_module/carbon_balance_conservation.md`
**Ground truth**: `/tmp/magpie_develop_ro` (develop worktree)
**Date**: 2026-06-06
**Auditor**: adversarial doc auditor (round49)

## Overall Verdict: ACCURATE (one Minor citation-imprecision bug, repeated)

This is a high-quality cross-module doc. The single highest-risk content — the `vm_carbon_stock`
populator/reader SETS (the G2 / R20 Critical-prone anchor area) — is **complete and correct**,
verified mechanically including solution-level `.fx`/`.l` reads (MANDATE 20). All realization
defaults, equation names, equation citations, scalar defaults, and set counts check out.

Score: 9/10 (one Minor bug).

---

## Verified claims (correct)

### Realizations / defaults (MANDATE 8, 3)
- 52_carbon default `normal_dec17` — `config/default.cfg` (`cfg$gms$carbon <- "normal_dec17"`). ✓
- 59_som default `cellpool_jan23` — `cfg$gms$som <- "cellpool_jan23"`. ✓ (also `static_jan19` exists)
- 53_methane default `ipcc2006_aug22`, 57_maccs default `on_aug22`. ✓ (doc doesn't misname these)
- Land-module realizations cited all match defaults: cropland `detail_apr24`, past `endo_jun13`,
  forestry `dynamic_may24`, urban `exo_nov21`, natveg `pot_forest_may24`. ✓
  (Note: default croparea is `simple_apr24`, not detail — but doc cites M29 detail_apr24 for the
  crop-slice equation, which is correct; `vm_carbon_stock_croparea` exists in BOTH croparea
  realizations, simple_apr24/equations.gms:50 and detail_apr24/equations.gms:88.)

### vm_carbon_stock DECLARED / POPULATED / READ (G2 anchor, MANDATE 18) — the load-bearing core
- DECLARED in M56 `price_aug22/declarations.gms:34` (4D `(j,land,c_pools,stockType)`). ✓ (doc line 101)
  Only declaration site in the tree. `pcm_carbon_stock` also declared in M56 (declarations.gms:19). ✓
- POPULATED by:
  - M29 crop slice — `q29_carbon`, detail_apr24/equations.gms:39 (reads vm_carbon_stock_croparea). ✓ (doc 593)
  - M31 past — endo_jun13/equations.gms:23. ✓
  - M32 forestry — `q32_carbon`, dynamic_may24/equations.gms:108. ✓
  - M35 primforest/secdforest/other — pot_forest_may24/equations.gms:43,50,54. ✓
  - M34 urban (`.fx`=0) — exo_nov21/presolve.gms:8 (`vm_carbon_stock.fx(j,"urban",ag_pools,stockType)=0`). ✓ (doc 605, exact match)
  - M59 soilc slice (all land) — `q59_carbon_soil`, cellpool_jan23/equations.gms:61-64. ✓
- READ by:
  - M52 `q52_emis_co2_actual`, normal_dec17/equations.gms:16-19. ✓
  - M56 `q56...`, price_aug22/equations.gms:22. ✓
- MANDATE 17 (direct vs transitive): M30 populates `vm_carbon_stock_croparea` (NOT vm_carbon_stock
  directly); doc §7.5 line 594 correctly states "M30 computes vm_carbon_stock_croparea; M29 is the
  direct populator of the crop slice." ✓
- MANDATE 20 solution-level sweep (`vm_carbon_stock.` in presolve/postsolve/preloop): hits M34, M56,
  M59 (+ M31 static, non-default) — all already in the doc's populator/reader set. **No undocumented
  consumer; no phantom.** ✓

### Equations & citations (MANDATE 16)
- q52_emis_co2_actual quote (doc 267-275) matches normal_dec17/equations.gms:16-19 verbatim. ✓
- q59_som_target_cropland — cellpool_jan23/equations.gms:20-27 (doc 124); 4-term structure (base +
  SCM uplift + fallow + treecover) × topsoilc_density matches doc 126-131. ✓
- q59_som_pool — equations.gms:46-52 (doc 358): lossrate·target + (1-lossrate)·legacy. ✓
- q59_carbon_soil — equations.gms:61-64 (doc 542): topsoil pool + subsoil density. ✓
- Chapman-Richards macro `m_growth_vegc(S,A,k,m,ac) = S + (A-S)*(1-exp(-k*(ac*5)))**m` —
  core/macros.gms:18 (doc 435). ✓ exact.
- Litter linear-20yr macro `m_growth_litc_soilc` — macros.gms:20 (doc 73,166,208 narrative). ✓
- start.gms:19-20,30-31 litter "20-year IPCC" comments (doc 77). ✓
- f52_growth_par.csv parameter+include — input.gms:37-43 (doc 451). ✓ filename exact.

### Sets (MANDATE 11, 12)
- c_pools `/vegc,litc,soilc/` — core/sets.gms:324-325 (doc 34). ✓
- emis_oneoff 21 members = 7 land × 3 pools — core/sets.gms:314-318 (doc 310-312). ✓ (counted: 21)
- emis_land mapping — core/sets.gms:332-354 (doc 325); `crop_vegc . (crop) . (vegc)` matches doc 327. ✓
- Land-type list crop/past/forestry/primforest/secdforest/urban/other (doc 314). ✓

### Scalars / switches (MANDATE 3)
- s59_cost_scm_recur default 65 USD17MER/ha — cellpool_jan23/input.gms:15 (doc 709). ✓
- i59_lossrate = 1-0.85^m_yeardiff (15%/yr) — preloop.gms:45 (doc 380). ✓
- i59_subsoilc_density derived from fm_carbon_density(other,soilc) − topsoil — preloop.gms:12 (doc 94). ✓
- c52_carbon_scenario default `cc` — input.gms:8. ✓ (cc/nocc/nocc_hist all real options)
- c59_irrigation_scenario name correct, default `on` — input.gms:61 (doc 140,420). ✓
- s59_scm_target=0.5 (doc 708) is presented as an illustrative INTERVENTION value, not a default;
  actual default is 0 (input.gms:11). Doc does NOT misstate the default. ✓
- pasture "natural carbon density / no degradation" — realization.gms:21-24 @limitations (doc 152). ✓

### Cross-module interface variables (MANDATE 7, 18)
- pm_climate_class(j,clcl) provided by M45 climate (45_climate/static/input.gms); read by M52 start.gms,
  M59 preloop.gms (doc 464). ✓
- M53 four CH4 sources ent_ferm/awms/rice/resid_burn — ipcc2006_aug22/equations.gms:22,49,60,71 (doc 551-555). ✓
- M53 reads vm_feed_intake (eq:23), vm_area rice_pro (eq:61), im_maccs_mitigation (eq:29);
  writes vm_emissions_reg(*,"ch4"). ✓ (doc 558-563)
- M57 declares im_maccs_mitigation(t,i,emis_source,pollutants) (decl:13) and vm_maccs_costs(i,factors)
  (decl:25). ✓ (doc 577-578)  [doc writes "pollutant" singular vs set "pollutants" — dimension-label
  nitpick, variable name correct; not flagged]
- vm_nr_som consumed by M51 (doc 525 "to Module 51"). ✓
- vm_cost_scm consumed by M11 (doc 526 "to Module 11"). ✓
- M59 "Receives" attributions all correct by DECLARED site: vm_area←M30, vm_fallow←M29,
  vm_treecover←M29, vm_land←M10, vm_lu_transitions←M10. ✓ (doc 529-533)
- M52 "Provides" pm_carbon_density_{plantation,secdforest,other}_ac — start.gms:17,28,48. ✓

### Units
- 44/12 = 3.67 (doc 346-348). ✓  1 mio. tC = 1 Tg C (doc 342). ✓

---

## Bugs found

### BUG cbc-soil-B1 — c52_carbon_scenario citation points only at the application lines, missing the switch definition + cc default
- **Severity**: Minor
- **Trigger** (§1 Minor): "Off-by-few line citation where adjacent lines say similar things."
- **Class**: 10 (stale/imprecise file:line citation)
- **doc_line**: carbon_balance_conservation.md:512 (repeated at :697)
- **Claim in doc**: "**Climate Scenarios** (Module 52, `modules/52_carbon/normal_dec17/input.gms:22-23`): - `cc`: ... - `nocc`: ... - `nocc_hist`: ..." (and line 697: "**Configuration** (Module 52, `modules/52_carbon/normal_dec17/input.gms:22-23`): - `c52_carbon_scenario = "cc"`: ...")
- **Reality in code**: The switch is DEFINED at `input.gms:8` (`$setglobal c52_carbon_scenario cc`), with the three options listed as comments at lines 9-11. Lines 22-23 only contain the `$if` APPLICATION logic for `nocc` (line 22) and `nocc_hist` (line 23); the default `cc` is the no-`$if` fallthrough and does NOT appear at 22-23. So a reader checking 22-23 finds nocc/nocc_hist but not where `cc` (the default) or the switch itself live.
- **file_evidence**: `/tmp/magpie_develop_ro/modules/52_carbon/normal_dec17/input.gms:8` (`$setglobal c52_carbon_scenario  cc`), options at :9-11, application at :22-23.
- **verify_cmd**: `grep -n "c52_carbon_scenario" .../normal_dec17/input.gms` →
  `8:$setglobal c52_carbon_scenario  cc` / `9-11:` option comments / `22:$if ..."nocc"...` / `23:$if ..."nocc_hist"...`
- **confirmed**: true
- **proposed_fix**: Change both citations from `modules/52_carbon/normal_dec17/input.gms:22-23` to `modules/52_carbon/normal_dec17/input.gms:8-23` (covers the `$setglobal ... cc` switch definition + option comments at 8-11 and the nocc/nocc_hist application at 22-23).

---

## Deferred (not bugs; uncertain or non-code-contradicting nuance — DO NOT edit)

1. **start.gms:17 / start.gms:28 cited for the inline Chapman-Richards formula** (doc 169, 211, 458):
   those lines are the macro INVOCATIONS (`pm_carbon_density_plantation_ac(...) = m_growth_vegc(...)`
   / `..._secdforest_ac(...) = m_growth_vegc(...)`), and the displayed formula is the macro BODY at
   core/macros.gms:18 (which the doc separately and correctly cites at line 435). Showing the expanded
   macro body next to its invocation line is defensible pedagogy — the cited line DOES compute vegc via
   that macro. Not a code-contradiction; left as-is.

2. **Growing-stock calibration omitted**: `s52_growingstock_calib` defaults to 1 (on)
   (normal_dec17/input.gms:46), so by default the secdforest/plantation `k` is calibrated against FRA
   growing stock (i52_k_calib_* adjustments) on top of the climate-weighted `f52_growth_par` k. The doc
   (§3.3/§3.5/§6, esp. lines 177, 459-460) presents the climate-weighted k as the effective k without
   mentioning the default-on calibration layer. This is an OMISSION of a default-on step, not a false
   statement — the functional form (Chapman-Richards) is correct and the calibration operates within it.
   Nothing the doc asserts contradicts code. Recorded as a nuance, not edited.

3. **c52_carbon_scenario "22-23" content**: borderline Minor vs Informational (lines 22-23 DO mention
   the scenarios, just not the default). Scored Minor per tie-breaker leaning on "would mislead a reader
   trying to find/set the default." If the reviewer prefers Informational, that is acceptable; the
   proposed fix is harmless either way.

4. **Code-comment inconsistency (not a doc bug, FYI)**: realization.gms:42 / preloop.gms:42 code comment
   says lossrate "44% in 5 years"; the formula gives 1-0.85^5 = 0.556 ≈ 56%. The DOC (lines 388, 399)
   correctly says 56% converged / 44% legacy for 5 years. The doc is RIGHT; the code comment has the
   internal typo. No doc action.

5. **im_maccs_mitigation dimension label** "pollutant" (doc 577) vs set name "pollutants" (decl:13):
   variable name correct; singular/plural of a dimension label is below the bug threshold.

---

## Summary

Doc is accurate. The G2/R20 high-risk populator/reader sets for `vm_carbon_stock` are complete and
correct (verified incl. `.fx`/`.l` solution-level reads). All defaults, realization names, equation
names, equation citations, scalar defaults, and set counts verified against develop. One Minor bug: the
`c52_carbon_scenario` citation (input.gms:22-23, twice) points only at the nocc/nocc_hist application
lines and misses the switch definition + `cc` default at input.gms:8 — widen to input.gms:8-23.
