# Audit Report: G2 (vm_carbon_stock propagation M52 -> M56)

**Round**: 38 (calibration anchor)
**Auditor**: Opus, verified against /tmp/magpie_develop_ro
**Date**: 2026-05-30

## Overall Verdict: ACCURATE
## Accuracy Score: 10/10
## drift_observed: false

---

## Verified Claims (all load-bearing claims confirmed against code)

| # | Claim | Evidence | Status |
|---|---|---|---|
| 1 | `vm_carbon_stock` DECLARED in M56, `declarations.gms:34` (positive variables) | `56_ghg_policy/price_aug22/declarations.gms:34` | ✓ exact |
| 2 | NOT computed in M52; M52 only READS it | `52_carbon/normal_dec17/equations.gms:16-19` | ✓ |
| 3 | Populators: 29, 31, 32, 34, 35, 59 | see below | ✓ all six |
| 4 | M52 single eq `q52_emis_co2_actual` at eq:16-19, `pcm_carbon_stock - vm_carbon_stock` ("actual") / m_timestep_length -> `vm_emissions_reg` | `52_carbon/normal_dec17/equations.gms:16-19` | ✓ exact |
| 5 | M52 has exactly ONE equation | only `q52_emis_co2_actual` in equations.gms + declarations.gms:30 | ✓ |
| 6 | M56 chain `q56_emis_pricing_co2`(19-22) -> `v56_emis_pricing` -> `q56_emission_cost_oneoff`(45-52) -> `v56_emission_cost` -> `q56_emission_costs`(56-58) -> `vm_emission_costs(i)` | `56_ghg_policy/price_aug22/equations.gms` | ✓ all exact |
| 7 | Annual pathway `q56_emis_pricing`(15-17) -> `q56_emission_cost_annual`(29-33), no m_timestep_length/annuity | equations.gms:15-17, 29-33 | ✓ exact |
| 8 | Default `c56_carbon_stock_pricing = actualNoAcEst` | `price_aug22/input.gms:90` | ✓ |
| 9 | M56 uses `%c56_carbon_stock_pricing%`; M52 hardcodes `"actual"` | equations.gms:22 vs 52_carbon eq:19 | ✓ |
| 10 | Default realizations: M56 `price_aug22`, M52 `normal_dec17` | `config/default.cfg:1611, 1554` | ✓ |
| 11 | Oneoff annuity factor `pm_interest/(1+pm_interest)` | equations.gms:50-52 | ✓ |
| 12 | Default policy `c56_emis_policy = reddnatveg_nosoil` | `price_aug22/input.gms:86` | ✓ |
| 13 | `f56_emis_policy` filter applied in preloop | `price_aug22/preloop.gms:85-91` (cited 84-91; 84 is comment header) | ✓ location correct |
| 14 | `emis_land` maps `emis_oneoff` -> (land, c_pools); `emis_oneoff`/`emis_annual` ⊂ `emis_source` | `core/sets.gms:314,320,332` | ✓ |

### Populator cross-check (the high-risk part)
- M29 cropland: `vm_carbon_stock(` in detail_apr24 + simple_apr24 equations.gms — ✓
- M31 pasture: `q...` eq LHS `vm_carbon_stock(j2,"past",...)` (endo_jun13 eq:23) AND `.fx` in static/presolve.gms:15 — ✓
- M32 forestry: `q32_carbon` LHS `vm_carbon_stock(j2,"forestry",...)` (dynamic_may24 eq:108) — ✓
- M34 urban: `vm_carbon_stock.fx(j,"urban",...) = 0` (exo_nov21 + static presolve.gms:8/10) — solution-level populator (invisible to `vm_carbon_stock(` grep; caught via `vm_carbon_stock.` grep per rubric SOLUTION-LEVEL rule) — ✓
- M35 natveg: LHS for primforest/secdforest/other (pot_forest_may24 eq:43,50,54) — ✓
- M59 som: `vm_carbon_stock(` in static_jan19 + cellpool_jan23 equations.gms; also preloop — ✓

The full populator set (29,31,32,34,35,59) is exactly right. M34 inclusion is correct and notable — it is a `.fx`=0 populator, the exact pattern the rubric warns can be missed.

---

## Bugs Found: NONE

No Critical, Major, Minor, or Informational content bugs on load-bearing claims. Every file:line citation verified exact against current develop. Variable-name fidelity perfect (`vm_carbon_stock`, not `vm_carbon_stocks`; `pcm_carbon_stock`, `v56_emis_pricing`, `v56_emission_cost`, `vm_emission_costs`, `im_pollutant_prices`, `pm_interest` all match declarations).

## Notes on peripheral / non-scored items

- **Priced-pool list under `reddnatveg_nosoil`** (primforest_vegc/litc, secdforest_vegc/litc, other_vegc/litc + peatland): this is a claim about the contents of the `f56_emis_policy` input data file, which is not readable from the GAMS source in this checkout. It is consistent with the policy name and standard MAgPIE behavior, and is peripheral to the G2 chain. NOT scored as a bug (cannot verify either way; plausible; non-load-bearing for the anchor). A future round could verify against the input `.cs3`/csv if desired.
- **Preloop policy framing**: the answer presents the `f56_emis_policy` multiplication as a single filter under `reddnatveg_nosoil`. The code (preloop.gms:85-91) branches: historic years always use `reddnatveg_nosoil`; future years use `%c56_emis_policy%`. Since the DEFAULT `c56_emis_policy` IS `reddnatveg_nosoil`, the effective filter is `reddnatveg_nosoil` throughout under default config — so the answer's framing is correct for the default. No bug.

## Value-add beyond expected summary

The answer correctly distinguishes the TWO pricing pathways (annual `vm_emissions_reg` pass-through via `q56_emis_pricing` vs one-off direct `vm_carbon_stock` recomputation via `q56_emis_pricing_co2`) and explains why one-off CO2 does NOT route through `vm_emissions_reg` in M56 — a real architectural insight beyond the linear chain in the expected summary. The annuity-factor rationale (`r/(1+r)` leveling one-off to perpetuity) is also correct and well-stated.

## Mechanical checks
- M1 file:line citations present: ✓ (many, all exact)
- M2 active realization stated: ✓ (names price_aug22 / normal_dec17 — matches default; expected summary itself names these)
- M3 variable prefixes valid: ✓
- M6 closing source statement: ✓ ("Sources: module_52.md, module_56.md")

## Summary

This anchor is rock-solid this round. The G2 chain — declaration in M56, populators 29/31/32/34/35/59, M52 as sole reader via `q52_emis_co2_actual`, and the full M56 cost chain to `vm_emission_costs` — matches code exactly, including the M34 `.fx` solution-level populator and the `actualNoAcEst` default. No drift from the expected ground-truth summary on any load-bearing point. The G2 anchor that regressed R22->R23->R26 (latent doc-bug in the populator list) is healthy: this answer re-enumerated populators correctly AND included M34. No `doc_error_answerer_beat_it` to record — the answer's populator set is correct, so no latent contradiction to chase. Score 10/10, drift_observed=false.
