## Audit Report: G2 (vm_carbon_stock in M52 / GHG-policy cost in M56) — Round 33 calibration anchor

### Overall Verdict: ACCURATE
### Accuracy Score: 9/10

Audited against `/tmp/magpie_develop_ro` (M52 = single realization `normal_dec17`; M56 = single realization `price_aug22`).

---

### Verified Claims (all load-bearing claims confirmed in code)

| Claim in answer | Code evidence | Status |
|---|---|---|
| `vm_carbon_stock(j,land,c_pools,stockType)` DECLARED in M56 `declarations.gms:34` (mio. tC), NOT in M52 | `modules/56_ghg_policy/price_aug22/declarations.gms:34` exact match | ✓ — central anchor point CORRECT (no M52-attribution error) |
| Land modules 29/31/32/34/35 + M59 (soilc) POPULATE it | `rg vm_carbon_stock` hits in 29 (detail_apr24/simple_apr24 equations.gms), 31 (endo_jun13 eq, static presolve), 32 (dynamic_may24 eq), 34 (presolve), 35 (pot_forest_may24 eq), 59 (static_jan19 + cellpool_jan23) | ✓ |
| M34 urban writes 0 | `modules/34_urban/{static,exo_nov21}/presolve.gms`: `vm_carbon_stock.fx(j,"urban",ag_pools,stockType) = 0` | ✓ |
| M29 incorporates `vm_carbon_stock_croparea` (from M30) | `modules/29_cropland/detail_apr24/equations.gms:40` references `vm_carbon_stock_croparea(j2,ag_pools)`; M29 default = `detail_apr24` (default.cfg:795) | ✓ |
| M52 reads via `q52_emis_co2_actual`, `equations.gms:16-19` | exact: `vm_emissions_reg(i2,ln,"co2_c") =e= sum(...,(pcm_carbon_stock(...,"actual") - vm_carbon_stock(...,"actual"))/m_timestep_length)` (note: declared with set `ln`, used as alias `emis_oneoff`) | ✓ |
| `q52_emis_co2_actual` declared `declarations.gms:30` | confirmed | ✓ |
| M56 `q56_emis_pricing_co2` `equations.gms:19-22`, reads `vm_carbon_stock(...,"%c56_carbon_stock_pricing%")` | exact match, lines 19-22 | ✓ |
| `c56_carbon_stock_pricing` default `actualNoAcEst` | input.gms:90 `$setglobal ... actualNoAcEst`; default.cfg:1817 | ✓ |
| `q56_emission_cost_oneoff` `equations.gms:45-52`; annuity `pm_interest/(1+pm_interest)` | lines 45-52; line 52 `* pm_interest(ct,i2)/(1+pm_interest(ct,i2))`; `* m_timestep_length`; `* im_pollutant_prices` | ✓ |
| `q56_emission_costs` `equations.gms:56-58` → `vm_emission_costs(i2)` = sum(emis_source, v56_emission_cost) | exact match | ✓ |
| `vm_emission_costs(i)` declared `declarations.gms:39` | confirmed | ✓ |
| Chain spine `q56_emis_pricing_co2 -> v56_emis_pricing -> q56_emission_cost_oneoff -> v56_emission_cost -> q56_emission_costs -> vm_emission_costs(i)` | matches expected ground-truth summary exactly | ✓ |
| M52 density params: `fm_carbon_density` input.gms:16-20; `pm_carbon_density_secdforest_ac` start.gms:28,31 + recalibrated preloop.gms:71-73; plantation start.gms:17,20 + preloop.gms:114-116; other start.gms:48,51 (not calibrated) | all line numbers verified; calibration guarded by `if(s52_growingstock_calib=1...)` preloop.gms:23 | ✓ |
| `s52_growingstock_calib` default = 1 (ON) | input.gms:46 `/ 1 /` | ✓ |
| `c56_emis_policy` default `reddnatveg_nosoil` | default.cfg:1810 overrides input.gms:86 setglobal `ln` (config wins) | ✓ |

The answer correctly flags the key design subtlety: M56 re-reads `vm_carbon_stock` directly for CO2 pricing (`q56_emis_pricing_co2`) rather than routing through `vm_emissions_reg`, so `c56_carbon_stock_pricing` can exclude stock types independently of M52's reporting equation. This is verified by the two parallel equations (M52 uses `"actual"`; M56 uses `"%c56_carbon_stock_pricing%"`).

---

### Bugs Found

- **Bug ID**: G2-B1
- **Severity**: Minor (tie-breaker pull-down from possible Informational)
- **Class**: 4 (conceptual pseudo-code / over-attributed verification depth) — closest fit; not a clean taxonomy match
- **Trigger**: §1 Minor "wrong detail, but a careful reader wouldn't be misled into action"
- **Claim in answer**: §5 — "Under the default policy `reddnatveg_nosoil`, the CO2 entries set to 1 are: `primforest_vegc`, `primforest_litc`, `secdforest_vegc`, `secdforest_litc`, `other_vegc`, `other_litc`, and peatland."
- **Reality in code**: This per-pool 0/1 matrix lives in `f56_emis_policy.csv` (declared at input.gms:113-115, `$include ./modules/56_ghg_policy/input/f56_emis_policy.csv`). That CSV is a PREPROCESSING ARTIFACT and is ABSENT from the read-only clone — confirmed twice (`ls` -> No such file; `find /tmp/magpie_develop_ro -name f56_emis_policy.csv` -> empty) with positive control (M52's sibling `input/` dir likewise contains only a `files` manifest, no `.cs3`; the `files` manifest at `56_ghg_policy/input/files` lists `f56_emis_policy.csv` as expected-but-not-present). The enumeration is consistent with `reddnatveg_nosoil` semantics (REDD on natural-vegetation pools: primforest/secdforest/other; "nosoil" excludes soilc; cropland/pasture/plantation unpriced) and is very likely correct, but it is stated with source-specific precision the answerer could not have read from this clone, with no caveat that it rests on an input data file.
- **File evidence**: `modules/56_ghg_policy/price_aug22/input.gms:113-115` (table decl + include); `modules/56_ghg_policy/input/files:3` (manifest lists the absent CSV); preloop.gms:87 applies `f56_emis_policy("reddnatveg_nosoil",...)`.
- **Anchor reference**: none. Distinct from the R20/§1.5 populator-set anchor (that was a doc error; this is an answerer over-confidence on a data-file claim, substance likely correct).

---

### Missing Nuances (not bugs)

- **M2 (active realization)**: The answer never explicitly states that M52/`normal_dec17` and M56/`price_aug22` are each the sole (hence default) realization. Both modules have exactly one realization dir, so citations are unambiguous and no reader would be misled — not scored, but a one-line "both modules have a single realization" would have been cleaner.
- **`emis_oneoff` is an alias** for `ln(emis_source)` ("oneoff emission sources", `core/sets.gms`). Declarations use `ln`; equations use `emis_oneoff`. The answer uses `emis_oneoff` throughout (matching equations.gms) — correct, no confabulation, but the alias relationship is unstated.
- **M4 / M6 (style)**: No 🟢/🟡 epistemic badges and no closing "Verified against ..." source line. Informational per rubric §1 (style), not scored into severity.

---

### Drift assessment

**drift_observed = false.** Every load-bearing element of the expected ground-truth summary is present and correct: declaration site (M56 declarations.gms:34, NOT M52), M52-reads-only via q52_emis_co2_actual (normal_dec17/equations.gms:16-19), the full M56 pricing chain through vm_emission_costs(i), the `actualNoAcEst` default, and the 29/31/32/34/35/59 populator set. The answer goes BEYOND the expected summary (adds the M52 density-parameter supply chain and the calibration overwrites — all verified correct) without introducing errors in the spine. The G2 anchor is stable; nothing near it has broken. The single Minor is an answerer over-reach on a non-repo data file, not a regression in the documented chain.

### Summary

Score 10 − 1(Minor) = **9/10**. The answer is an accurate, well-cited walkthrough that correctly nails the historically error-prone point (declaration in M56, not M52 — the exact trap that regressed this anchor R22->R23->R26 per the §1.5 immutable anchor). It correctly distinguishes producer/consumer roles, gets the full cost chain and all line citations right, and uses MANDATE-16-compliant full relative paths. The only deduction is §5's specific 0/1 policy-matrix enumeration, which is stated with unverifiable precision (the source CSV is a preprocessing artifact absent from the clone) and lacks an "input data" caveat — substance very likely correct, harm negligible.
