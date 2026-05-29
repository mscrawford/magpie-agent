# Audit Report: G2 (vm_carbon_stock computation in M52 + entry into M56 GHG-policy cost)

**Round**: 30 | **Type**: calibration anchor (regression question) | **Rubric**: v1.2
**Auditor verification**: all claims cross-checked against `/tmp/magpie_develop_ro` THIS session.

## Overall Verdict: ACCURATE
## Accuracy Score: 10/10
## drift_observed: false

The answer matches the G2 expected-answer summary on every load-bearing point and exceeds
it in (correctly verified) depth. Zero bugs. No confabulation. The anchor is stable.

---

## Realization context (both match config defaults)

- M52 default `carbon <- "normal_dec17"` — `config/default.cfg:1556`. Answer covers normal_dec17. ✓
- M56 default `ghg_policy <- "price_aug22"` — `config/default.cfg:1613`. Answer covers price_aug22. ✓
- M34 default `urban <- "exo_nov21"` — `config/default.cfg` (relevant for the "urban fixed=0" populator claim). ✓

---

## Verified Claims (the spine — all correct)

1. **`vm_carbon_stock` DECLARED in M56, not M52.**
   - `modules/56_ghg_policy/price_aug22/declarations.gms:34` — exact line match:
     `vm_carbon_stock(j,land,c_pools,stockType)  Carbon stock in vegetation soil and litter ... (mio. tC)`
   - ABSENT from `modules/52_carbon/normal_dec17/declarations.gms` — **double-confirmed**
     (grep empty + rg empty), with **positive control** `q52_emis_co2_actual` present at
     declarations.gms:30 (proves the search worked in that dir). Negative claim is safe.

2. **M52 only READS it, via `q52_emis_co2_actual`.**
   - `modules/52_carbon/normal_dec17/equations.gms:16-19` — answer's GAMS snippet matches
     code verbatim (writes `vm_emissions_reg`, reads `pcm_carbon_stock - vm_carbon_stock`
     over "actual" / m_timestep_length). ✓

3. **Populator set 29, 31, 32, 34, 35, 59 (+30 folding into 29).** Each references
   `vm_carbon_stock` in its DEFAULT realization's equations.gms (verified by grep per module):
   - 29 detail_apr24/simple_apr24, 31 endo_jun13, 32 dynamic_may24, 35 pot_forest_may24,
     59 cellpool_jan23/static_jan19 — all hit. ✓
   - 34 urban: NOT in equations.gms (correctly) — fixed via presolve:
     `vm_carbon_stock.fx(j,"urban",ag_pools,stockType) = 0` at both `static/presolve.gms:10`
     and the DEFAULT `exo_nov21/presolve.gms:8`. Answer's "Urban (fixed = 0)" is correct;
     framing it as a populator is accurate. ✓
   - 30 croparea references vm_carbon_stock too; answer correctly describes M30 as folding
     `vm_carbon_stock_croparea` into M29's crop vegc/litc. ✓

4. **M56 pricing chain — every equation verified at the cited lines.**
   - `q56_emis_pricing` → `v56_emis_pricing` (annual): equations.gms:15-17 ✓
   - `q56_emis_pricing_co2` → `v56_emis_pricing` (one-off, reads vm_carbon_stock directly): 19-22 ✓
   - `q56_emission_cost_oneoff` → `v56_emission_cost` (annuity): 45-52 ✓
   - `q56_emission_costs` → `vm_emission_costs(i2)`: 56-58 ✓
   - Chain exactly matches expected: `q56_emis_pricing_co2 → v56_emis_pricing →
     q56_emission_cost_oneoff → v56_emission_cost → q56_emission_costs → vm_emission_costs(i)`. ✓

5. **Pathway A vs B architectural point (the key insight).** Directly confirmed by the two
   equations: `q56_emis_pricing(i2,pollutants,emis_annual)` routes CH4/N2O/recurring-CO2 via
   `vm_emissions_reg` (annual sources only); `q56_emis_pricing_co2(i2,emis_oneoff)` reads
   `vm_carbon_stock` directly, bypassing `vm_emissions_reg`. The difference vs M52's equation —
   one-off pricing uses `%c56_carbon_stock_pricing%` on the current-stock dimension rather than
   "actual" — is verbatim correct (equations.gms:22). ✓

6. **No confabulated `vm_carbon_stocks` (plural)** anywhere in the answer. ✓ (a G2 calibration target)

---

## Verified Extra Depth (beyond the expected summary — all correct, not confabulated)

- `c56_carbon_stock_pricing` default = `actualNoAcEst` — `price_aug22/input.gms:90` +
  `default.cfg:1817`. ✓ (answer's rationale "excludes afforestation establishment area to
  avoid double-counting with CDR reward" is consistent with the actualNoAcEst semantics.)
- `c56_emis_policy` default = `reddnatveg_nosoil` — `price_aug22/input.gms:86` + `default.cfg:1810`. ✓
- `s52_growingstock_calib` default = 1 — `normal_dec17/input.gms:46`. ✓
- M52 carbon-density citations — ALL exact line matches:
  - plantation vegc start.gms:17, litc :20; secdforest vegc :28, litc :31; other vegc :48, litc :51 ✓
  - `fm_carbon_density` table input.gms:16, `$include lpj_carbon_stocks.cs3` :18 (block 16-20) ✓
  - preloop calibration overwrites: plantation vegc :114 (cited 114-116), secdforest vegc :71
    (cited 71-73); both inside `if(s52_growingstock_calib = 1, ...)` opening at preloop.gms:23 ✓
- `im_pollutant_prices` policy-matrix multiply — cited preloop:84-91; actual multiply at
  preloop.gms:87 (coupling branch, hardcoded "reddnatveg_nosoil") and :89 (`%c56_emis_policy%`),
  both inside the cited span. Within range, not drift. ✓

---

## Bugs Found

None.

---

## Missing Nuances / non-load-bearing observations (NOT bugs)

- **reddnatveg_nosoil pool coverage** ("prices primforest/secdforest/other vegc+litc + peatland;
  not soilc/cropland/pasture"): this list lives in `f56_emis_policy.csv`
  (`price_aug22/input.gms:113-115`, a GENERATED input not present in the read-only modules tree),
  so it could not be line-verified here. It is consistent with the realization-name semantics
  (redd = deforestation, natveg = natural vegetation, nosoil = excl. soil) and with the config
  comment at `default.cfg:1753`. Not part of the G2 spine; treated as accurate-but-unverified
  metadata, not a scored claim.
- The `emis_annual` / `emis_oneoff` set membership is core-level; the Pathway A/B distinction is
  fully established by the two equation bodies read this session, so set-membership lookup was not
  load-bearing.

---

## Mechanical checks
- M1 file:line citations present: PASS (dozens, all verified)
- M2 active realization stated: PASS (M56 price_aug22, M52 normal_dec17 both named)
- M3 variable prefixes valid: PASS (vm_/pm_/v56_/c56_/s52_/fm_ all correct)
- M4/M5/M6 epistemic badges / closing source: the answer body is the technical content; closing
  source statement and per-claim badges are handled at the harness layer for anchor answers — not
  scored as content bugs.

## Summary

G2 is fully stable at round 30. The declaration site (M56:34), the producer/consumer split
(populators 29/31/32/34/35/59 + 30-folds-into-29 write; M52 reads), the M52 reader equation, and
the complete M56 pricing-to-cost chain are all verified correct at exact line numbers. The
two-pathway architecture (one-off CO2 bypasses vm_emissions_reg via q56_emis_pricing_co2 reading
vm_carbon_stock directly) is the load-bearing insight and is confirmed verbatim. No confabulated
variable names, no wrong attributions, no citation drift beyond cited ranges. Score 10/10,
no drift. This is a healthy anchor and a good signal that nothing near it broke this round.
