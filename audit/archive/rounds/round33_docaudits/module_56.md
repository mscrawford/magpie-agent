# Round 33 Doc Audit — module_56.md (GHG Policy, price_aug22)

**Auditor**: Opus (adversarial doc auditor)
**Date**: 2026-05-30
**Target doc**: `magpie-agent/modules/module_56.md`
**Ground truth**: `/tmp/magpie_develop_ro` (develop worktree) + `config/default.cfg`
**Realization**: `price_aug22` (ONLY realization; confirmed default via `cfg$gms$ghg_policy <- "price_aug22"`, module.gms:27)

---

## Summary verdict

The doc body (Sections 1–8, 12.4) is **highly accurate**: all 7 equation citations, the carbon-stock populator set in §4.1, every scalar default, every setglobal, and the preloop stage citations check out against current develop. The errors cluster in the **auto-generated tail sections** (§ "Key Dependencies" summary line 1074, and the "Limitations" boilerplate at lines 1109/1113/1119), where a phantom realization, a wrong populator-set shorthand, and a bad arithmetic example appear. One body error: `vm_cdr_aff` is documented with the wrong unit (the checker lead — confirmed).

**Claims verified**: ~55 load-bearing claims (7 equations + citations, 13 scalar/setglobal defaults, populator set of 7 modules, consumer set, 3 scenario-set existence checks, ~12 preloop citations, units).

**Bugs**: 1 Major (body, the checker lead) + 3 Major (tail) + 3 Minor + 1 Informational.

---

## Verified-correct claims (high-value confirmations)

- **All 7 equation citations exact**: q56_emis_pricing (equations.gms:15-17), q56_emis_pricing_co2 (19-22), q56_emission_cost_annual (29-33), q56_emission_cost_oneoff (45-52), q56_emission_costs (56-58), q56_reward_cdr_aff_reg + q56_reward_cdr_aff (67-79). Equation code blocks in the doc match the source verbatim.
- **Equation count = 7** ✓ (`grep -c "^[ ]*q56_" declarations.gms` → 7).
- **vm_carbon_stock DECLARED in M56** at `price_aug22/declarations.gms:34` (positive-variables block) ✓ — matches G2 anchor (declaration is in M56, not M52).
- **Carbon-stock populator set (§4.1, line 583) is CORRECT**: M29 (crop pool, folds in vm_carbon_stock_croparea), M31 (past), M32 (forestry), M34 (urban, fixed to 0 via `.fx` in presolve), M35 (primforest/secdforest/other), M59 (soilc). M30 populates the separate `vm_carbon_stock_croparea`. M52 only READS it (q52_emis_co2_actual, normal_dec17/equations.gms:16-19) — NOT a populator. M58 does NOT touch vm_carbon_stock (verified, exit 1 + positive control on vm_emissions_reg). All confirmed against default realizations (cropland=detail_apr24, croparea=simple_apr24, past=endo_jun13, forestry=dynamic_may24, urban=exo_nov21, natveg=pot_forest_may24, som=cellpool_jan23).
- **All scalar defaults exact** (input.gms): s56_limit_ch4_n2o_price=4920 (:65), s56_cprice_red_factor=1 (:66), s56_minimum_cprice=3.67 (:67), s56_ghgprice_devstate_scaling=0 (:68), s56_c_price_induced_aff=1 (:69), s56_c_price_exp_aff=50 (:70), s56_buffer_aff=0.5 (:71), s56_ghgprice_fader=0 (:75). Cross-confirmed in default.cfg for the three exposed ones (s56_limit=4920 @1780, red_factor=1 @1620, exp_aff=50 @1760).
- **All setglobals exact** (input.gms:84-90): c56_pollutant_prices=R34M410-SSP2-NPi2025, c56_emis_policy=reddnatveg_nosoil, c56_cprice_aff=secdforest_vegc, c56_mute_ghgprices_until=y2030, c56_carbon_stock_pricing=actualNoAcEst.
- **GWP values correct** (R27 lead refuted): CH4 GWP 28, N2O GWP 265 (AR5) — matches preloop.gms:78 comment and the cap formulas at preloop.gms:80-81 (`*12/44*28`, `*12/44*265*44/28`). Doc lines 463-464 are right.
- **Carbon-price unit** USD17MER/Mg and USD17MER/tC — matches declarations.gms:9 ("USD17MER per Mg") and :11 ("USD17MER per tC"). R24 lead satisfied.
- **q56 pricing chain** (G2): q56_emis_pricing_co2 → v56_emis_pricing → q56_emission_cost_oneoff → v56_emission_cost → q56_emission_costs → vm_emission_costs(i) ✓.
- **vm_emission_costs** declared declarations.gms:39 ✓; **vm_reward_cdr_aff** declarations.gms:43 ✓; **im_pollutant_prices** declarations.gms:9 ✓; **p56_c_price_aff** declarations.gms:11 ✓.
- **Consumers of M56 outputs**: vm_emission_costs → M11 (costs/default/equations.gms) [+ M15 anthro_iso non-default]; vm_reward_cdr_aff → M11 only. Doc's "Enters Module 11" is right.
- **Scenario sets exist**: R34M410-SSP2-NPi2025 (sets.gms:73), -PkBudg1000 (:74), -PkBudg650 (:75); scen56 contains none/all/all_nosoil/reddnatveg_nosoil/redd+natveg_nosoil/sdp_all (sets.gms:119-164). Doc §5.1/§5.2 examples all real.
- **Preloop citations exact**: pcm init (10-11), region price share (18-23), devstate (51), fader (53-63), CO2 red factor (67), historic zeroing (70-74), CH4/N2O caps (80-82), emis-policy loop (85-91), age-class C price (114-123). Stage code blocks match.
- **sm_fix_SSP2 = 2025** (default.cfg:225) ✓.

---

## Bugs found

### 56-B1 (Major) — vm_cdr_aff documented with wrong unit  [CHECKER LEAD: CONFIRMED]
- **Doc lines**: 286 ("vm_cdr_aff(j,ac,aff_effect): Expected CDR from afforestation per age class **(tC/ha/yr)**"), 602 ("...per age class **(tC/ha/yr)**"). Also the §2.6 component gloss.
- **Reality**: `vm_cdr_aff(j,ac,aff_effect)` is declared in `modules/32_forestry/dynamic_may24/declarations.gms:83` with unit **`mio. tC`** and description "Expected bgc (CDR) and local bph effects of afforestation depending on planning horizon". It is an absolute stock-equivalent (mio. tC), not a per-hectare annual flux.
- **verify_cmd**: `rg -n 'vm_cdr_aff' /tmp/magpie_develop_ro/modules/32_forestry/dynamic_may24/declarations.gms` → `83: vm_cdr_aff(j,ac,aff_effect)  Expected bgc (CDR) and local bph effects of afforestation depending on planning horizon (mio. tC)`
- **Severity trigger**: Major — "right concept, wrong number/unit"; a unit error on a cross-module interface variable misleads about scale (per-ha flux vs absolute mio. tC). Class 3/12.
- **Fix**: replace both `(tC/ha/yr)` with `(mio. tC)` and align the description to "expected CDR (bgc) + local bph effects of afforestation, by age class".

### 56-B2 (Major) — phantom realization `price_jan20` in Limitation 3
- **Doc line**: 1113 — "The `price_aug22` realization uses total stock changes (`vm_carbon_stock`), while `price_jan20` uses separate annual emission terms. This means switching realizations can fundamentally change how forests and carbon sequestration are valued."
- **Reality**: `price_aug22` is the **only** realization of module 56. `price_jan20` does not exist anywhere in develop. There is no alternative realization to "switch" to.
- **verify_cmd**: `find /tmp/magpie_develop_ro/modules/56_ghg_policy/ -type d` → only `price_aug22` + `input`; `rg -rln 'price_jan20' /tmp/magpie_develop_ro/modules/` → exit 1 (no matches).
- **Severity trigger**: Major — invented/stale realization name presented as a live alternative (MANDATE 8). Not Critical because it is not a *default* claim. Class 8.
- **Fix**: delete the `price_jan20` clause. Replace Limitation 3 with: "Module 56 has a single realization (`price_aug22`). CO2 from LULUCF is priced via total carbon-stock changes (`vm_carbon_stock`), with the priced pools governed by `c56_carbon_stock_pricing` (default `actualNoAcEst`)." (Or drop the limitation, since 'varies by implementation' is false.)

### 56-B3 (Major) — wrong carbon-stock populator set in Key Dependencies summary
- **Doc line**: 1074 — "**Upstream:** Emission modules (51-55), Forestry CDR (32), Carbon stocks **(30,31,32,35,58)**, Discount rates (12)".
- **Reality**: vm_carbon_stock is populated by **29, 31, 32, 34, 35, 59** (+ M30 via the separate `vm_carbon_stock_croparea`). Line 1074 **omits 29, 34, 59** and **wrongly lists 58** (peatland does not touch vm_carbon_stock; it routes through vm_emissions_reg). This contradicts the doc's own correct §4.1 (line 583) and §12.4.
- **verify_cmd**: `rg -l 'vm_carbon_stock' /tmp/magpie_develop_ro/modules/*/*/equations.gms` → 29,30,31,32,35,52,56,59 (52 is reader); M34 via `.fx` in presolve; `rg -rn 'vm_carbon_stock' .../58_peatland/ -g '*.gms'` → exit 1 (positive control vm_emissions_reg hits).
- **Severity trigger**: R20-anchor class (wrong populator set). Tie-breaker pulls to **Major** (not Critical) because the authoritative §4.1 nearby is correct and this is a parenthetical summary; `tier_uncertainty: true`. Class 15 (latent doc error in a summary that could be trusted in isolation).
- **Fix**: change `(30,31,32,35,58)` → `(29,31,32,34,35,59; M30 via vm_carbon_stock_croparea)`.

### 56-B4 (Major) — wrong arithmetic + non-default value in Limitation 1
- **Doc line**: 1109 — "With `s56_limit_ch4_n2o_price = 1000`, methane and nitrous oxide prices are capped at **~33 USD17MER/tCO2eq** (converted from **1000 USD/tN2O**), limiting policy ambition."
- **Reality**: (a) default `s56_limit_ch4_n2o_price = 4920` USD/**tC**, not 1000 (input.gms:65; default.cfg:1780). (b) The scalar is in USD/tC, not USD/tN2O. (c) The cap converts tC→tCO2 by ×12/44, so 1000 USD/tC = **272.7** USD/tCO2eq (and the default 4920 → 1341.8 USD/tCO2eq). No reading yields "~33".
- **verify_cmd**: `python3 -c "print(1000*12/44, 4920*12/44)"` → `272.7 1341.8`; `grep s56_limit_ch4_n2o_price /tmp/magpie_develop_ro/config/default.cfg` → `<- 4920 # def = 4000 * 1.23`.
- **Severity trigger**: Major — "right concept, wrong number" (8× error) plus undeclared non-default value and unit confusion. `tier_uncertainty: true` (hedged as a conditional in boilerplate could read as Minor). Class 13-adjacent.
- **Fix**: "The default cap `s56_limit_ch4_n2o_price = 4920` USD17MER/tC bounds CH4 and N2O prices (CH4 cap ≈ 4920·12/44·28 ≈ 37,571 USD/tCH4; N2O-N cap ≈ 558,771 USD/tN), preventing numerical instability from very high non-CO2 prices."

### 56-B5 (Minor) — s56_cprice_red_factor conflated with price foresight
- **Doc line**: 1119 — "The CO2 price reduction factor `s56_cprice_red_factor` (default = 1, full price applied) scales the carbon price incentive — **setting it to 0 eliminates price foresight entirely**."
- **Reality**: `s56_cprice_red_factor` multiplies the CO2 *price level* (preloop.gms:67). Setting it to 0 zeros the CO2 price (no incentive at all); it does NOT "eliminate price foresight". Foresight is governed by `s56_c_price_exp_aff` (the 50-year horizon) and the age-class shift in preloop.gms:114-121.
- **verify_cmd**: `sed -n '67p' .../preloop.gms` → `im_pollutant_prices(...,"co2_c",...) = im_pollutant_prices(...,"co2_c",...)*s56_cprice_red_factor;`
- **Severity trigger**: Minor — conceptual mislabel in boilerplate; the §6.2 parameter table (line 704) correctly describes red_factor as a price multiplier, so a careful reader is not misled into action. Class 4.
- **Fix**: "...scales the CO2 price level — setting it to 0 removes the CO2-emission/afforestation price incentive entirely (it does not affect the foresight horizon, which is `s56_c_price_exp_aff`)."

### 56-B6 (Minor) — imprecise "emission modules 51-55 / 51-57" range
- **Doc lines**: 66 ("Module 51-57"), 590 ("From Module 51-55 (Emission Modules)"), 714/1024/1066 ("Modules 51-55").
- **Reality**: vm_emissions_reg is populated by **51, 52, 53, 57, 58**. "51-55" wrongly includes 54 (phosphorus) and 55 (awms) — neither populates vm_emissions_reg — and omits 57 (maccs) and 58 (peatland), which do. The peatland omission is notable given the doc repeatedly cites "peatland CO2" as a source.
- **verify_cmd**: per-module `rg -ln 'vm_emissions_reg' .../<m>_*/.../equations.gms` for m∈{50,51,52,53,54,55,57,58} → hits only for 51,52,53,57,58.
- **Severity trigger**: Minor — prose range shorthand for "emission modules"; imprecise in both directions but not a specific fabricated variable/equation claim. Class 6-adjacent.
- **Fix**: standardize to "Emission modules 51 (N2O), 52 (LULUCF CO2), 53 (CH4), 57 (MACC-adjusted), 58 (peatland)" or "the emission modules (51, 52, 53, 57, 58)".

### 56-B7 (Informational) — LOC and preloop range-end off-by-one
- **Doc line 4**: "Total Lines of Code: 708" — actual sum of price_aug22/*.gms = **709**.
- **Doc lines 322, 1060**: "preloop.gms:35–124" — preloop.gms is **123** lines (range end past EOF).
- **verify_cmd**: `wc -l .../price_aug22/*.gms` → 709 total; preloop.gms = 123.
- **Severity**: Informational — metadata/range-end; no reader acts on it. (MANDATE 16 documents range-end as an unchecked coverage gap.) Class 10.
- **Fix**: "708" → "709"; "preloop.gms:35–124" → "preloop.gms:35–123" (both occurrences).

---

## Deferred (not code-verifiable in this worktree; no edit proposed)

- **§3.7 / §5.2 / lines 499, 661, 967 — detailed f56_emis_policy.csv pool entries** (which exact pools = 1 for `reddnatveg_nosoil`: primforest_vegc, primforest_litc, secdforest_vegc/litc, other_vegc/litc, peatland). The CSV (`f56_emis_policy.csv`) is NOT present in the worktree (only an `input/files` manifest). The set `scen56` confirms the policy *names* exist, but the per-cell 0/1 values cannot be checked here. The claim is plausible and internally consistent; left unverified rather than flagged. To verify: read `modules/56_ghg_policy/input/f56_emis_policy.csv` in a populated input tree.
- **§5.1 illustrative 2050/2100 CO2 prices** (~$300/tC etc.) — explicitly labeled "Approximate values"; depend on f56_pollutant_prices.cs3 (not in worktree). Not a code-checkable claim.
- **§9.4 / §10 magnitude ranges** ($10-1000 M/region/yr; relative shares 40-60%) — labeled order-of-magnitude sanity checks, not code values.
- **§12.2 "Depends on 52 (carbon stocks)"** framing — M56 reads vm_emissions_reg (populated by M52 for co2_c) AND vm_carbon_stock (NOT populated by M52). The CO2-oneoff path bypasses vm_emissions_reg (per §2.2, which is correct), so M56's CO2 pricing does not actually depend on M52's emission output; but the annual path does read vm_emissions_reg which M52 helps populate. Borderline framing, not a clean code error — deferred rather than flagged.

---

## Notes for the flywheel

- The doc **body** (the human-verified core, "Status: Fully Verified 2025-10-12") is in excellent shape — G2 anchor content (§4.1 populator set, declaration site, pricing chain) is fully correct and matches the rubric's expected answer. The G2 regression is SAFE from this doc's body.
- All confirmed errors live in (a) one body unit (vm_cdr_aff, an out-of-module variable that the M56 author would not own) and (b) the auto-generated "Key Dependencies" summary + "Limitations" tail, which appear machine-templated and were not part of the 2025-10 manual verification. Recommend the maintainer treat the tail sections as a separate verification surface.
- Strongest fixes: 56-B2 (phantom price_jan20), 56-B3 (wrong populator summary contradicting own body), 56-B1 (checker-lead unit).
