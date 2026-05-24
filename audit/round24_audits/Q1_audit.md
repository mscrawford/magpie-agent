# Audit Report: Q1 (Module 53 CH4-rice → Module 56 GHG pricing chain)

## Overall Verdict: MOSTLY ACCURATE (lower band)
## Accuracy Score: 5/10

The Sonnet answer correctly identifies the core equations, variables, dimensions, and the chain `q53_emissionbal_ch4_rice → vm_emissions_reg → q56_emis_pricing → v56_emis_pricing → q56_emission_cost_annual → v56_emission_cost → q56_emission_costs → vm_emission_costs`. Equation text and cited line ranges are accurate (q53_emissionbal_ch4_rice at equations.gms:59-63; q56_emis_pricing at 15-17; q56_emission_cost_annual at 29-33; q56_emission_costs at 56-58). Realization (`ipcc2006_aug22`), input file (`f53_EFch4Rice.cs4` at input.gms:19), set membership (`rice` ∈ `emis_annual` in `core/sets.gms:320-322`), variable declarations (`vm_emissions_reg` in Module 56 at declarations.gms:40), and dimension orders for `im_pollutant_prices(t_all,i,pollutants,emis_source)` are all correct.

However, the answer has one Major default-state inversion (it hedges about whether rice CH4 is priced under default `reddnatveg_nosoil` when it IS priced); plus several Minor inaccuracies: units of `im_pollutant_prices` stated as "USD17MER per Tg" when the declaration says "USD17MER per Mg"; the file used to encode the on/off policy mask is misidentified as `f56_pollutant_prices.cs3` when it is `f56_emis_policy.csv`; specific MACC technologies ("alternate wetting and drying (AWD), mid-season drainage, and improved cultivars") are presented as model content but appear nowhere in the MAgPIE source tree. Informational: sloppy attribution of `vm_area` to "Module 30 or Module 17" (only Module 30 declares it), MACC framing as "adoption-rate driven" (price-step driven by default), and a stale verification-date footer.

---

## Verified Claims (correct)

- **Default realization is `ipcc2006_aug22`**: `config/default.cfg:1581` confirms `cfg$gms$methane <- "ipcc2006_aug22"`.
- **q53_emissionbal_ch4_rice exists and writes to vm_emissions_reg(i2,"rice","ch4")**: `modules/53_methane/ipcc2006_aug22/equations.gms:59-63`. Exact reproduction of the equation text is correct.
- **Equation structure**: outer sum over `(cell(i2,j2),w)` over `vm_area(j2,"rice_pro",w) * sum(ct, f53_ef_ch4_rice(ct,i2))` times `(1 - sum(ct, im_maccs_mitigation(ct,i2,"rice","ch4")))`. Matches equations.gms:59-63 verbatim.
- **f53_ef_ch4_rice(t_all,i) dimensions**: `modules/53_methane/ipcc2006_aug22/input.gms:16` declares `parameter f53_ef_ch4_rice(t_all,i) CH4 emission per ha rice (CH4 per ha)`. Matches.
- **Input file `f53_EFch4Rice.cs4` loaded at input.gms:19**: confirmed at `modules/53_methane/ipcc2006_aug22/input.gms:19` (`$include "./modules/53_methane/input/f53_EFch4Rice.cs4"`). File exists in `modules/53_methane/input/`.
- **Interface variable name is `vm_emissions_reg`** (not `vm_emissions`): `modules/56_ghg_policy/price_aug22/declarations.gms:40` confirms `vm_emissions_reg(i,emis_source,pollutants)`.
- **vm_emissions_reg declared in Module 56, not Module 53**: confirmed — declarations.gms:40 of `price_aug22` is the only declaration site.
- **q56_emis_pricing at equations.gms:15-17, exact text**: `q56_emis_pricing(i2,pollutants,emis_annual) .. v56_emis_pricing(i2,emis_annual,pollutants) =e= vm_emissions_reg(i2,emis_annual,pollutants);`. Matches.
- **q56_emission_cost_annual at equations.gms:29-33, exact text**: matches.
- **q56_emission_costs at equations.gms:56-58, exact text**: matches.
- **im_pollutant_prices dimension order `(t_all,i,pollutants,emis_source)`**: confirmed at `modules/56_ghg_policy/price_aug22/declarations.gms:9`. Sonnet's usage `im_pollutant_prices(ct,i2,"ch4","rice")` is in the correct dimension order.
- **`rice` is a member of `emis_annual`**: confirmed at `core/sets.gms:320-322` (`emis_annual` set contains `rice`). The routing of rice CH4 through the annual (not one-off) pricing path is correct.
- **`rice_pro` is a member of `kcr`**: confirmed at `core/sets.gms:230`.
- **vm_emission_costs flows into Module 11**: confirmed at `modules/11_costs/default/equations.gms:26` (`+ vm_emission_costs(i2)`).
- **One-off CO2 reserved for `q56_emis_pricing_co2`**: correct framing — equations.gms:19-22 handles `emis_oneoff` only.
- **MANDATE 10 framing about preserving `sum(w, ...)` rather than expanding**: correctly applied.
- **`c56_emis_policy` mask is the gating mechanism for which (gas, source) combos get a nonzero price**: confirmed at `modules/56_ghg_policy/price_aug22/preloop.gms:89` where `im_pollutant_prices ... = im_pollutant_prices ... * f56_emis_policy("%c56_emis_policy%",pollutants,emis_source);`. The conceptual claim is right, even though the filename is wrong.

## Bugs Found

### Bug Q1-B1: Default-state hedge inverts whether rice CH4 is priced under default policy

- **Severity**: Major
- **Class**: 13 (Wrong parameter default value) + 4 (Conceptual pseudo-code)
- **Trigger matched**: §1 Major — "Missing default-state caveat (mechanism described as if always active when it's OFF by default)". Here the inverse applies: mechanism described as MAYBE OFF when it is unconditionally ON. The anchor "Active mechanism claimed when actually OFF by default" reads in reverse — same kind of default-state inversion.
- **Claim in answer**: "Under the default policy `reddnatveg_nosoil`, soil-based CH4 sources may or may not be included; this is determined by the policy configuration table in `f56_pollutant_prices.cs3`."
- **Reality in code**: Under `reddnatveg_nosoil` in `modules/56_ghg_policy/input/f56_emis_policy.csv`, the row `reddnatveg_nosoil,ch4,0,0,1,0,1,0,0,1,1,0,...` has rice = 1 (rice column is position 9 in the data, after `inorg_fert,man_crop,awms,resid,resid_burn,man_past,som`). Rice CH4 IS unconditionally priced when the default scenario is active. The `all_nosoil` scenario also has rice = 1 in the CH4 row. Rice is not a "soil-based CH4 source" in the model's classification — it has its own `emis_source` element.
- **File evidence**: `modules/56_ghg_policy/input/f56_emis_policy.csv` rows for `(reddnatveg_nosoil, ch4)` and `(all_nosoil, ch4)`; both have value 1 at the rice column.
- **Anchor reference**: §1 Major anchor — "Active mechanism claimed when actually OFF by default (e.g., `s42_pumping = 1` claimed when default is 0)" — same shape, opposite direction.
- **Tier uncertainty**: false (clean Major).

### Bug Q1-B2: Wrong file for the emission-policy on/off mask

- **Severity**: Minor
- **Class**: 11 (Wrong GAMS filename)
- **Trigger matched**: §1 Minor — "Wrong detail, but a careful reader wouldn't be misled into action or misunderstanding." The conceptual claim that a policy table determines pricing is correct; the filename is wrong but findable by `ls`-ing `modules/56_ghg_policy/input/`. The reader is recoverable. Tie-breaker (§1) pulls Major-vs-Minor to Minor since the surrounding logic is right.
- **Claim in answer**: "this is determined by the policy configuration table in `f56_pollutant_prices.cs3`."
- **Reality in code**: The policy on/off mask is `f56_emis_policy.csv` (declared in `input.gms:111-117` as `table f56_emis_policy(scen56,pollutants_all,emis_source)`). `f56_pollutant_prices.cs3` is a different table — the actual price values, not the policy mask.
- **File evidence**: `modules/56_ghg_policy/price_aug22/input.gms:113-117` (declares `f56_emis_policy` from `f56_emis_policy.csv`); `modules/56_ghg_policy/price_aug22/preloop.gms:89` (applies the mask to `im_pollutant_prices`).
- **Anchor reference**: none specifically.
- **Tier uncertainty**: true — defensible as Major (a reader would open the wrong file). Pulled down per §1 tie-breaker.

### Bug Q1-B3: Wrong units on `im_pollutant_prices`

- **Severity**: Minor
- **Class**: 6 (Hardcoded counts drift — adapted: hardcoded unit suffix wrong)
- **Trigger matched**: §1 Minor — "Wrong detail" not load-bearing; the cost product (Tg × $/Mg = $million/yr) works out correctly with the right units, but the answer never relies on this conversion.
- **Claim in answer**: "`im_pollutant_prices(ct,i,pollutants,emis_source)` is the GHG price (USD17MER per Tg) ..."
- **Reality in code**: `modules/56_ghg_policy/price_aug22/declarations.gms:9` says `Certificate prices for N2O-N CH4 CO2-C used in the model (USD17MER per Mg)`. Units are per Mg (tonne), not per Tg.
- **File evidence**: `modules/56_ghg_policy/price_aug22/declarations.gms:9`.
- **Anchor reference**: none.
- **Tier uncertainty**: false.

### Bug Q1-B4: Fabricated MACC technology names presented as model content

- **Severity**: Minor
- **Class**: 4 (Conceptual pseudo-code)
- **Trigger matched**: §1 Minor — "Wrong detail" / flavor narrative not load-bearing. The named technologies (AWD, mid-season drainage, improved cultivars) are plausible domain knowledge from the rice-CH4 literature, but they are not named in the model source. A careful reader would treat them as illustrative. Tie-breaker (§1) pulls Major-vs-Minor to Minor since they don't drive a code action.
- **Claim in answer**: "Technologies include alternate wetting and drying (AWD), mid-season drainage, and improved cultivars."
- **Reality in code**: Neither "AWD", "alternate wetting", "mid-season drainage", nor "cultivar" appear anywhere in `modules/53_methane/` or `modules/57_maccs/` (verified by grep across both module trees). Module 57 (`on_aug22`) sources `im_maccs_mitigation` from PBL_2022 MACC data via the `c57_macc_version` switch; the underlying PBL methodology may reference these technologies, but the MAgPIE source does not name them.
- **File evidence**: `grep -ri "AWD\|alternate wetting\|mid-season drainage\|cultivar" modules/57_maccs/ modules/53_methane/` returns no matches.
- **Anchor reference**: none directly; pattern resembles "Conceptual pseudo-code" — descriptive flavor presented as model content.
- **Tier uncertainty**: true — defensible as Major (fabricated specifics presented as the model's content). Pulled down per §1 tie-breaker.

### Bug Q1-B5: Sloppy "Module 30 or Module 17" attribution for vm_area

- **Severity**: Informational
- **Class**: 12 (Content-level citation mismatch)
- **Trigger matched**: §1 Informational — minor sloppiness in module attribution that does not change meaning. The correct module (30) is stated first.
- **Claim in answer**: "`vm_area(j2,"rice_pro",w)` is the harvested area of rice (in ha) at cell level, provided by Module 30 (Croparea) or Module 17 (Production)."
- **Reality in code**: `vm_area(j,kcr,w)` is declared in Module 30 (`modules/30_croparea/simple_apr24/declarations.gms:18` and `modules/30_croparea/detail_apr24/declarations.gms:21`). Module 17 does not declare `vm_area`; it operates on `vm_prod` (production quantity).
- **File evidence**: `modules/30_croparea/simple_apr24/declarations.gms:18`; `modules/17_production/*/declarations.gms` (no `vm_area`).
- **Anchor reference**: none.
- **Tier uncertainty**: true — defensible as Minor.

### Bug Q1-B6: "Adoption-rate driven" framing of MACC mitigation

- **Severity**: Informational
- **Class**: 4 (Conceptual pseudo-code — minor characterization issue)
- **Trigger matched**: §1 Informational — the next sentence immediately corrects the framing ("If no carbon price is active ... Module 57 will provide zero mitigation"), so the reader gets the right picture. Style nitpick.
- **Claim in answer**: "MACC mitigation for rice is present in the code but is adoption-rate driven."
- **Reality in code**: In default config, `s57_maxmac_ch4_rice = -1` (price-driven). `im_maccs_mitigation` is set in `modules/57_maccs/on_aug22/preloop.gms` based on the price-step index `i57_mac_step_ch4`, which is derived from the GHG price.
- **File evidence**: `modules/57_maccs/on_aug22/input.gms:16` (default `-1`); `modules/57_maccs/on_aug22/preloop.gms:34, 56`.
- **Anchor reference**: none.
- **Tier uncertainty**: true — defensible as Minor.

### Bug Q1-B7: Stale verification date in footer

- **Severity**: Informational
- **Class**: 8 (Stale realization name in footer — extended for stale verification date)
- **Trigger matched**: §1 Informational — metadata staleness; reader does not act on the footer date.
- **Claim in answer**: "Based on `modules/module_53.md` (fully verified against `modules/53_methane/ipcc2006_aug22/*.gms`, last verified 2026-03-06) and `modules/module_56.md` (fully verified against `modules/56_ghg_policy/price_aug22/*.gms`, status verified 2025-10-12)."
- **Reality in code**: Today is 2026-05-24. The Module 56 verification date "2025-10-12" is ~7 months stale. The cited content is correct, but the metadata claim "fully verified" should bump on each re-verification.
- **File evidence**: metadata in answer.
- **Anchor reference**: none.
- **Tier uncertainty**: false.

## Missing Nuances

- The answer notes the regional emission factor is not distinguished by water management `w`, but does not flag that the `f53_ef_ch4_rice(t_all,i)` time dimension is used via `sum(ct,...)` — the standard MAgPIE idiom for "value at current time".
- The answer does not mention that `q56_emis_pricing` is defined over `(i2, pollutants, emis_annual)` — meaning it routes ALL pollutants for annual sources, not just CH4. For rice, this includes any future pollutant (in practice only CH4 is non-zero for rice). This is consistent with the equation as-is.
- The cost product Tg × $/Mg = mio USD/yr is not explained, which would have caught the units bug.
- `c56_emis_policy` default flip: in `input.gms:86` the GAMS-side `$setglobal` is `all_nosoil`, but `config/default.cfg:1808` overrides to `reddnatveg_nosoil`. The answer (correctly) uses `reddnatveg_nosoil` as the operative default — this is one of the few places where the answer is sensitive to the config override.

## Summary

- **Severity counts**: 0 Critical, 1 Major, 3 Minor, 3 Informational.
- **Score calculation** (§4): raw = 4·0 + 2·1 + 1·3 + 0·3 = 5. score = max(0, 10 − 5) = **5**.
- **Verdict** (§7): score 5 maps to "Significant Errors / Mostly Accurate (lower band)". The lower-band fit is more accurate given the answer's correct chain and equation reproductions — the bugs are peripheral default-state inversion, wrong filename, and minor descriptive inaccuracies.

The main lesson: the answer would have scored substantially higher if (a) the rice column of `f56_emis_policy.csv` had been checked to confirm rice CH4 IS priced under default `reddnatveg_nosoil`, and (b) the file containing the policy mask had been correctly named as `f56_emis_policy.csv` rather than confused with the prices file `f56_pollutant_prices.cs3`.

---

SCORE: 5/10 | BUGS: critical=0, major=1, minor=3, info=3
