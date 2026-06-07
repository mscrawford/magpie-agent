# Audit Report: Round 50 — m56-emis (vm_emissions_reg populators / readers in module 56)

**Question**: In module 56, which modules POPULATE vm_emissions_reg and for which emission-source subset (emis_oneoff vs emis_annual)? Does M52 populate it (which slice)? Does M57 populate or only read? Trace q56_emis_pricing's read of vm_emissions_reg and how q56_emis_pricing_co2 differs. Distinguish DECLARED/POPULATED/READ, cite file:line, be explicit about the default realization.

**Ground truth**: `/tmp/magpie_develop_ro` develop worktree.

## Overall Verdict: SIGNIFICANT ERRORS
## Accuracy Score: 5/10

The answer's mechanistic spine is correct and well-explained: q56_emis_pricing reads vm_emissions_reg over emis_annual; q56_emis_pricing_co2 BYPASSES vm_emissions_reg and reads carbon stocks directly; M52 populates the emis_oneoff×"co2_c" slice; M57 only READS vm_emissions_reg; and the subtle q52-vs-q56 stockType distinction ("actual"/"actual" vs "actual"/"%c56_carbon_stock_pricing%") is captured correctly. Default realizations are all correct. **However, the central ask — the POPULATOR set — is wrong on three modules**: it invents M50 and M55 as direct populators (phantom), and it both mischaracterizes and omits M58 (a real populator). This is the MANDATE-18 producer/consumer-confusion vein.

---

## Realizations / defaults verified (all CORRECT)

- ghg_policy = `price_aug22` (default.cfg), single realization. ✓
- carbon = `normal_dec17`. ✓
- maccs = `on_aug22`. ✓
- nitrogen = `rescaled_jan21`. ✓
- methane = `ipcc2006_aug22`. ✓
- peatland = `v2`. ✓ (answer implicitly correct; M58 v2 is the populator)
- `c56_carbon_stock_pricing` default = `actualNoAcEst` — verified in `modules/56_ghg_policy/price_aug22/input.gms:90` AND `config/default.cfg:1817`. ✓
- `pollutants_maccs57` = { ch4, n2o_n_direct } — `modules/57_maccs/on_aug22/sets.gms:26`. ✓ (answer's claim exactly right)

## Verified Claims (correct)

- **vm_emissions_reg DECLARED in M56**: `modules/56_ghg_policy/price_aug22/declarations.gms:40` ("after technical mitigation N CH4 C (Tg per yr)"). ✓ (answer's table says "56 … DECLARED"; missing the :40 line number but correct module.)
- **M52 POPULATES emis_oneoff×"co2_c"** via q52_emis_co2_actual at `modules/52_carbon/normal_dec17/equations.gms:16-19`, stock-difference `(pcm_carbon_stock(...,"actual") - vm_carbon_stock(...,"actual"))/m_timestep_length`. ✓ Citation 16-19 exact.
- **M51 POPULATES emis_annual N slices** via 8 equations (verified count = 8): q51_emissions_man_crop (22), _inorg_fert (30), _resid (42), _resid_burn (49), _som (55), q51_emissionbal_awms (65), q51_emissionbal_man_past (74), q51_emissions_indirect_n2o (83) — `modules/51_nitrogen/rescaled_jan21/equations.gms`. ✓ "8 equations" correct; q51_emissions_man_crop snippet + 22-27 citation correct.
- **M53 POPULATES emis_annual×"ch4"** via 4 equations: q53_emissionbal_ch4_ent_ferm (22), _awms (49), _rice (60), q53_emissions_resid_burn (71) — `modules/53_methane/ipcc2006_aug22/equations.gms`. ✓ The "(1-im_maccs_mitigation)" factor on 3 of 4, with resid_burn the exception, verified at lines 29/52/63 (present) and 71-72 (absent). The answer's lines 29/52/63 are EXACT — strong.
- **M57 only READS vm_emissions_reg**: only refs are RHS in q57_labor_costs / q57_capital_costs at `modules/57_maccs/on_aug22/equations.gms:38,40,47,50`. ✓ Read-only conclusion correct. The reasoning that im_maccs_mitigation (computed by M57) feeds INTO M51/M53/M50's populating equations — an upstream influence, not M57 writing vm_emissions_reg — is a correct MANDATE-17 (direct-vs-transitive) application.
- **q56_emis_pricing reads emis_annual** (all pollutants): `modules/56_ghg_policy/price_aug22/equations.gms:15-17`. ✓ dimension order `(i2,pollutants,emis_annual)` correct.
- **q56_emis_pricing_co2 bypasses vm_emissions_reg**, reads `pcm_carbon_stock(...,"actual") - vm_carbon_stock(...,"%c56_carbon_stock_pricing%")`: `equations.gms:19-22`. ✓ Citation exact. The "actualNoAcEst excludes afforestation-establishment carbon to avoid double-counting with vm_reward_cdr_aff" framing is consistent with the code/design.
- **q56_emission_cost_oneoff** annuity treatment (`× m_timestep_length × price × r/(1+r)`): `equations.gms:45-52`. ✓ Citation exact.
- **M57 outputs vm_maccs_costs to M11 + M36**: vm_maccs_costs consumed in `modules/11_costs/default/equations.gms` and `modules/36_employment/exo_may22/equations.gms`. ✓
- **im_maccs_mitigation DECLARED in M57** (`modules/57_maccs/on_aug22/declarations.gms:13`), consumed by M50 (presolve), M51, M53. ✓
- **emis_oneoff / emis_annual set members**: `core/sets.gms:314-318` (oneoff = 21 land×pool CO2 sources) and `320-322` (annual = inorg_fert, man_crop, awms, resid, man_past, som, rice, ent_ferm, resid_burn, **peatland**). ✓ answer's emis_land enumeration + 314-318 citation correct.

---

## Bugs Found

### Bug m56-emis-B1 — Phantom populators: "Modules 50 (SOM) and 55 (AWMS) also write into the emis_annual slice"
- **Severity**: Major (tier_uncertainty: true — could be argued Minor since the som/awms slices DO get populated, just by M51, so the emission still exists; the error is purely which module)
- **Class**: 18-style producer mis-attribution (DECLARED-vs-POPULATED-vs-READ)
- **Trigger**: producer attribution wrong in a way that misleads about behavior (which module produces which slice)
- **Claim in answer**: §2 — "Modules 50 (SOM) and 55 (AWMS) also write into the emis_annual slice for their respective sources".
- **Reality in code**: M50 (`50_nr_soil_budget`) and M55 (`55_awms`) have **ZERO** references to vm_emissions_reg (grep count = 0 in each; positive control passed — M55 has 16 "awms" hits, M50 equations.gms has vm_area/vm_land/etc.). The "som" and "awms" emis_annual slices are populated by **M51**: `modules/51_nitrogen/rescaled_jan21/equations.gms:55-56` (som) and `:65-66` (awms). M50/M55 compute upstream quantities (NUE/soil-N budget, manure) that FEED M51's equations — transitive, not direct (MANDATE 17/18).
- **Root cause**: answerer_confabulation. Not doc-sourced — neither module_56.md nor module_52.md attributes vm_emissions_reg to M50/M55. Pattern-matched M50→"som", M55→"awms" without checking which module owns the equation.

### Bug m56-emis-B2 — M58 (peatland) mischaracterized ("uses its own emission path") and OMITTED from the populator summary table
- **Severity**: Major
- **Class**: 18 producer-set incompleteness (omitted real populator) + mischaracterization
- **Trigger**: producer set wrong/incomplete; a reader enumerating emission populators from the §6 table would miss peatland (R20 anchor: producer/consumer-set omission misleads refactors)
- **Claim in answer**: §2 — "Module 58 (peatland) uses its own emission path." And §6 summary table lists populators as {52, 51, 53} only — **M58 absent**.
- **Reality in code**: M58 (peatland, v2) DIRECTLY POPULATES vm_emissions_reg via **q58_peatland_emis** at `modules/58_peatland/v2/equations.gms:91-94` — LHS `vm_emissions_reg(i2,"peatland",poll58)`; the comment at line 89 reads "Aggregation of detailed peatland GHG emissions for interface `vm_emissions_reg`". "peatland" is an **emis_annual** source (`core/sets.gms:322`), so M58 populates the emis_annual slice — not a "separate path." Ironically module_56.md:66/:1024 lists 58 correctly as a provider; the answer dropped it.
- **Root cause**: answerer_confabulation (the answer overrode a correct doc list, asserting 58 is separate, and omitted it from the deliverable table).

### Bug m56-emis-B3 — M51 listed as populating "rice" N2O
- **Severity**: Minor
- **Class**: 18 producer/source over-listing
- **Trigger**: wrong detail; a careful reader checking M51's equations wouldn't find a rice equation
- **Claim in answer**: §2 — "Similar equations populate `"inorg_fert"`, `"resid"`, `"resid_burn"`, `"som"`, `"man_past"`, `"rice"` (N2O), and indirect N2O sources."
- **Reality in code**: M51 has NO `vm_emissions_reg(i2,"rice",...)` equation. Its direct populators are man_crop, inorg_fert, resid, resid_burn, som, awms, man_past; indirect uses `emis_source_n51` = {inorg_fert, man_crop, awms, resid, resid_burn, man_past, som} (`modules/51_nitrogen/rescaled_jan21/sets.gms:15-16`) — rice excluded. Rice CH4 is M53; rice N2O is not populated into vm_emissions_reg by any module. Likely pattern-matched from module_56.md:662's policy *source* list (which lists rice among priced N2O sources — but priced-source ≠ populated-slice).
- **Root cause**: answerer_confabulation.

### Bug m56-emis-B4 — q56_emis_pricing citation "equations.gms:12-17" over-extends into the comment block
- **Severity**: Informational
- **Class**: 10 (citation range, mild)
- **Claim in answer**: §4 cites q56_emis_pricing at "equations.gms:12-17".
- **Reality in code**: the equation is at lines 15-17; lines 12-14 are doc comments (`*'`). The equation IS within the range so a reader is not misdirected to wrong content (hence Informational, not Minor). Every other line citation in the answer is exact.
- **Root cause**: answerer_style_or_framing.

### Bug m56-emis-B5 — Summary-table equation wildcard "q53_emissionbal_* (4 eqns)"
- **Severity**: Informational
- **Class**: 9 (equation-name imprecision, minor)
- **Claim in answer**: §6 table — "q53_emissionbal_* (4 eqns)".
- **Reality in code**: only 3 of the 4 are `q53_emissionbal_*`; the residue-burning one is `q53_emissions_resid_burn` (`equations.gms:71`). The answer's §-Module-53 body text describes all 4 correctly and cites the right specific name for the example, so this is a table-shorthand nit only.
- **Root cause**: answerer_style_or_framing.

**Score**: max(0, 10 − 2·2 − 1·1 − 0·2) = 10 − 4 − 1 = **5/10**.

---

## Latent doc bugs (recorded regardless of answer score — §1.5 mandate)

### Latent Doc Bug m56-emis-LD1 — module_56.md lists "57 MACC-adjusted" as a PROVIDER of vm_emissions_reg
- **Severity**: Critical (by future-reader harm — wrong producer set, the G2/R20 anchor class)
- **Class**: 15 (latent doc error) / MANDATE 18 (DECLARED-vs-POPULATED-vs-READ)
- **Doc location**: `modules/module_56.md:66` ("Actual regional emissions from the emission modules (51 N2O, 52 LULUCF CO2, 53 CH4, **57 MACC-adjusted**, 58 peatland)") AND `modules/module_56.md:1024` (§12.2 "**Receives Emissions From** … 51 N2O, 52 LULUCF CO2, 53 CH4, **57 MACC-adjusted**, 58 peatland").
- **Code reality**: M57 only READS vm_emissions_reg (RHS in q57_labor_costs/q57_capital_costs, `modules/57_maccs/on_aug22/equations.gms:38,40,47,50`); it does NOT populate it. The §12.2 header "Receives Emissions From" makes the framing explicit — these are meant to be the modules M56 receives vm_emissions_reg values from, i.e. the populators. The correct set is **{51, 52, 53, 58}**. The "after technical mitigation" property of vm_emissions_reg (declarations.gms:40) is achieved by M51/M53/M50 multiplying by (1-im_maccs_mitigation) INSIDE their own equations; M57 supplies the *factor*, not the emission values. The doc conflates "factor source" with "emission source."
- **Why latent**: the answer QUOTED this list verbatim in §2 ("the set of providers"), so it propagated the wrong "57 as provider" into its prose — yet the answer's §3 and §6 table independently and correctly classify M57 as READ-only. The answer beat the doc in its final classification but did not flag the doc's error. A future answerer who trusts the doc list without re-deriving would state M57 populates vm_emissions_reg — the exact G2-class regression the rubric warns about (R22→R23→R26).
- **Root cause**: doc_error_answerer_beat_it.
- **Fix (Step 5, unconditional)**: in module_56.md:66 and :1024, change the provider/source list from "(51 N2O, 52 LULUCF CO2, 53 CH4, 57 MACC-adjusted, 58 peatland)" to "(51 N2O, 52 LULUCF CO2, 53 CH4, 58 peatland)" and add a clarifying clause: "values are post-MACC; the mitigation factor `im_maccs_mitigation` comes from M57, which READS vm_emissions_reg but does not populate it." (module_52.md is already correct: line 435-436 and 1113 attribute declaration to M56 and writing to M52.)

---

## Missing nuances (not scored)
- The answer could have stated the full ground-truth populator set up front: **{51 (emis_annual N), 52 (emis_oneoff×co2_c), 53 (emis_annual×ch4), 58 (emis_annual peatland)}**. Instead the populator set is scattered and wrong on 50/55/58.
- The §6 table's DECLARED line for M56 omits the line number (declarations.gms:40).

## Summary
Core mechanics, equations, default realizations, the carbon-stock-pricing distinction, and the M57 read-only/transitive-influence reasoning are all correct and precisely cited (line citations are unusually exact — 29/52/63 for the methane mitigation term is spot-on). The damage is concentrated in the producer-set enumeration, the literal center of the question: M50/M55 invented as direct populators (B1, Major), M58 mischaracterized and dropped from the deliverable table (B2, Major), and a spurious "rice" N2O attribution to M51 (B3, Minor). Net **5/10**. Separately, module_56.md:66/:1024 carry a Critical latent doc error (M57 listed as a vm_emissions_reg provider) that must be fixed regardless of this round's score — it is the precise DECLARED-vs-POPULATED-vs-READ trap that has regressed the G2 anchor before.
