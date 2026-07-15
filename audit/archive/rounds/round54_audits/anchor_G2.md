# Audit Report: G2 (vm_carbon_stock — M52 computation & M56 GHG-policy cost entry)

**Round**: 54 (calibration anchor, `scope: calibration_anchor`)
**Auditor**: Opus, code-verified against `/tmp/magpie_develop_ro` (MAgPIE develop)
**Answer method**: docs-only (answerer explicitly states no raw `.gms` read this session)

## Overall Verdict: ACCURATE
## Accuracy Score: 10/10
## drift_observed: FALSE

Every load-bearing claim, and every peripheral file:line I spot-checked, verified EXACTLY against code. The answer matches the G2 ground-truth summary on all points and correctly nails the two historical failure modes for this anchor (producer-vs-consumer; parallel-vs-serial readers, R51/MANDATE-21).

---

## Verified Claims (all confirmed against code)

| Claim in answer | Code evidence | Status |
|---|---|---|
| `vm_carbon_stock` DECLARED in M56, NOT M52 | `modules/56_ghg_policy/price_aug22/declarations.gms:34` (`vm_carbon_stock(j,land,c_pools,stockType)`); ABSENT from `modules/52_carbon/normal_dec17/declarations.gms` (only `q52_emis_co2_actual` at :30) | ✓ EXACT |
| M52 has ONE equation, only READS the interface | `modules/52_carbon/normal_dec17/equations.gms:16-19`, reads `pcm_carbon_stock(...,"actual") - vm_carbon_stock(...,"actual")`, writes `vm_emissions_reg(...,"co2_c")` | ✓ verbatim quote matches |
| Populators: M29 crop, M31 past, M32 forestry, M34 urban(=0), M35 prim/secd/other, M59 soilc; +M30 `vm_carbon_stock_croparea` folded into M29 | `29_cropland/{simple,detail}_apr24/equations.gms`, `31_past/endo_jun13`, `32_forestry/dynamic_may24` (q32_carbon), `35_natveg/pot_forest_may24`, `59_som/cellpool_jan23/equations.gms:61-64` (q59_carbon_soil), `30_croparea/*` (vm_carbon_stock_croparea) | ✓ |
| M34 urban fixed to 0 via `.fx` in presolve | `modules/34_urban/exo_nov21/presolve.gms:8` (`vm_carbon_stock.fx(j,"urban",ag_pools,stockType) = 0;`) — solution-level, would be invisible to a `vm_carbon_stock(` grep | ✓ EXACT |
| M58 peatland does NOT populate vm_carbon_stock; routes to `vm_emissions_reg` via q58_peatland_emis | `58_peatland/v2/equations.gms:91-92`; positive-control grep confirms M58 references vm_land but not vm_carbon_stock | ✓ |
| stockType members `actual`, `actualNoAcEst` | `modules/56_ghg_policy/price_aug22/sets.gms:212-213` | ✓ EXACT |
| M56 chain q56_emis_pricing_co2 → v56_emis_pricing → q56_emission_cost_oneoff → v56_emission_cost → q56_emission_costs → vm_emission_costs(i) | `price_aug22/equations.gms:19-22, 45-52, 56-58` | ✓ verbatim quotes match |
| q56_emis_pricing_co2 reads the configurable `%c56_carbon_stock_pricing%` slice (vs M52's hardcoded `"actual"`) | `equations.gms:22` | ✓ |
| `c56_carbon_stock_pricing` default = `actualNoAcEst` | `config/default.cfg:1835`; `price_aug22/input.gms:90` | ✓ EXACT |
| pcm carry-forward: M56 postsolve (ag pools), M59 postsolve (soilc) | `price_aug22/postsolve.gms:8`; `cellpool_jan23/postsolve.gms:13` (comment: "as done for the above-ground pools in 56_ghg_policy") | ✓ EXACT |
| soil carry-forward added in commit 931db85c4 (2026-06-25) | `git log`: "59_som: carry soil pcm_carbon_stock forward each timestep", 2026-06-25 13:48 | ✓ EXACT |
| Defaults: c56_emis_policy=reddnatveg_nosoil, s56_minimum_cprice=3.67, mute until y2030 | `config/default.cfg:1828, 1747, 1744` | ✓ EXACT |
| vm_emissions_reg declared in M56 (parenthetical) | `price_aug22/declarations.gms:40` | ✓ EXACT |
| Named default realizations: normal_dec17, price_aug22, cellpool_jan23, exo_nov21, endo_jun13, dynamic_may24, pot_forest_may24 | all match `config/default.cfg` | ✓ EXACT |
| M52 (reported CO2) and M56 (priced CO2) are PARALLEL readers, not a serial hand-off | q52_emis_co2_actual and q56_emis_pricing_co2 both read vm_carbon_stock/pcm_carbon_stock independently; M56 does not consume M52's output | ✓ correct (the R51/MANDATE-21 trap, handled correctly) |
| No confabulation of `vm_carbon_stocks` or related names | answer uses exact names throughout | ✓ |

## Bugs Found
**None** (0 Critical, 0 Major, 0 Minor).

## Informational observations (weight 0; do not affect score)
- **M4 (epistemic badges)**: no per-claim 🟢/🟡/🟠 emoji badges. The answer instead discloses source globally up front ("Answered from magpie-agent documentation only … not re-verified against source"). Rubric §1 classifies missing epistemic markers as Informational.
- **M6 (closing source block)**: source stated in a top "Method" note rather than the sanctioned closing format ("Verified against … / Based on module_XX.md documentation"). Informational.
- **q56_reward_cdr_aff line range**: cited `equations.gms:67-79`; the equation named `q56_reward_cdr_aff` is at 73-79, while 67-71 is the sibling `q56_reward_cdr_aff_reg`. Over-inclusive by ~6 lines, but the named equation and `vm_cdr_aff` (line 77) both sit within the cited range, and 67-72 is the regional aggregation of the same reward (adjacent, similar content). Peripheral "distinct mechanism" aside. Tie-breaker → Informational.
- M4/M6 are mechanical-check indicators, not bugs; here they did NOT correlate with any content error — the docs-only answer transcribed accurate docs faithfully (no latent `doc_error` to record; the G2 docs are in good shape).

## Value-add beyond the ground-truth summary (correct enrichment, not drift)
- Correctly folds in M30's `vm_carbon_stock_croparea` → M29 crop slice.
- Emphasizes the parallel-readers distinction and that M56's priced CO2 uses `actualNoAcEst` while M52's reported CO2 uses `actual` — so priced ≠ reported CO2 by construction in a default run.
- Flags a possible doc-internal inconsistency in `module_56_notes.md:49` (chain listed as `q56_emis_pricing_co2 → v56_emis_pricing → q56_emis_pricing → vm_emissions_reg`). The answer correctly reasons from the verified equations that q56_emis_pricing (emis_annual slice, reads vm_emissions_reg) and q56_emis_pricing_co2 (emis_oneoff/co2_c slice) write DIFFERENT slices of v56_emis_pricing independently — neither feeds the other. This reasoning is CORRECT per `equations.gms:15-22`. Maintainer note: worth reviewing whether module_56_notes.md:49 reads as a misleading serial pipeline (potential future-reader hazard), but it did not affect this answer (answerer flagged rather than relied).

## Summary
Exemplary anchor performance. All ground-truth points hit; all checked file:line citations exact; correct handling of the two known G2 traps (declares-vs-reads; parallel-vs-serial). The only deviations are zero-weight formatting/epistemic-badge omissions. Score 10/10, no drift. Anchor stable and healthy at R54 (prior history: regressed to 7 at R26 on the populator-set doc bug, recovered to 9 at R27; this round the answer is fully correct including the populator set).
