I now have all the documentation needed for a complete, accurate answer. Let me synthesize across Modules 56, 32, and 52.

---

## Causal Chain: CO2 Price → Afforestation → Carbon Sequestration Accounting

**Realizations:** M56 `price_aug22` (only realization), M32 `dynamic_may24` (only realization), M52 `normal_dec17` (only realization). All defaults.

---

### Stage 0: CO2 Price Construction — Module 56 Preloop

Before any optimization, M56 preloop runs a multi-stage price configuration (module_56.md, `preloop.gms:35-123`).

**Step 1 — Load prices** (`preloop.gms:35-45`):  
`im_pollutant_prices(t_all,i,pollutants,emis_source)` is populated from the scenario selected by `c56_pollutant_prices` (default: `R34M410-SSP2-NPi2025`, a near-zero No-Policy scenario).

**Step 2 — Apply policy matrix** (`preloop.gms:84-91`):  
Each price is multiplied by the binary `f56_emis_policy` matrix (0/1) for the scenario selected by `c56_emis_policy` (default: `reddnatveg_nosoil`). This zeros out any gas/source combinations not covered by the policy. Under `reddnatveg_nosoil`, `f56_emis_policy(...,"co2_c","secdforest_vegc") = 1` — so the afforestation-relevant CO2 price entry is not zeroed out by the matrix.

**Step 3 — Mute historical and near-term prices** (`preloop.gms:69-74`):  
`im_pollutant_prices = 0` for years ≤ `sm_fix_SSP2` (≈ 2025) and until `c56_mute_ghgprices_until` (default 2030).

**Step 4 — Construct age-class-specific afforestation prices** (`preloop.gms:93-123`):

```gams
p56_c_price_aff(t_all,i,ac) = im_pollutant_prices(t_all,i,"co2_c","%c56_cprice_aff%");
p56_c_price_aff(t_all,i,ac)$(ord(t_all)+ac.off<card(t_all)) = p56_c_price_aff(t_all+ac.off,i,"ac0");
```

The source emission type is `c56_cprice_aff = "secdforest_vegc"` (default). The price for each age class `ac` in timestep `t` is the CO2 price expected when that age class matures: `t + ac.off × 5 years`. Foresight horizon is `s56_c_price_exp_aff = 50` years (`input.gms:70`). This is a critical design feature: trees planted now are rewarded at the **future prices expected when they sequester most carbon**, not at today's price.

🟡 Source: module_56.md §3.8, preloop.gms:93-123

---

### Stage 1: CDR Reward Calculation — Module 56 Equations

The expected annual CDR reward is computed simultaneously during optimization.

**`q56_reward_cdr_aff(j2)`** (`equations.gms:67-79`):

```gams
v56_reward_cdr_aff(j2) =e=
  sum(ct, p56_fader_cpriceaff(ct)) *
  sum(ac,
    (sum(aff_effect, (1 - s56_buffer_aff) * vm_cdr_aff(j2,ac,aff_effect))
     * sum((cell(i2,j2),ct), p56_c_price_aff(ct,i2,ac)))
    / ((1 + sum((cell(i2,j2),ct), pm_interest(ct,i2)))**(ac.off*5))
  ) * sum((cell(i2,j2),ct), pm_interest(ct,i2)/(1+pm_interest(ct,i2)));
```

Breaking this down:
- `vm_cdr_aff(j,ac,aff_effect)` — expected CDR from Module 32's `aff` establishment, by age class (bgc = biogeochemical carbon removal; bph = biophysical)
- `(1 - s56_buffer_aff)` — only 50% of CDR credited (default `s56_buffer_aff = 0.5`), as permanence reserve
- `p56_c_price_aff(ct,i,ac)` — age-class-specific future price
- `/ (1+r)^(ac.off×5)` — discounts CDR from age class `ac` to present value
- `× r/(1+r)` — converts the present value to an equivalent **annual** payment (annuity due, infinite horizon, using `pm_interest`)

**`q56_reward_cdr_aff_reg(i2)`** (`equations.gms:60-66`):  
Aggregates cell-level `v56_reward_cdr_aff(j)` to regional `vm_reward_cdr_aff(i)`.

**Entry into the objective via Module 11:**  
`vm_reward_cdr_aff(i)` enters Module 11 (Costs) with a **negative sign** — it reduces total costs, creating a financial subsidy for afforestation. When expected CDR revenue (discounted, buffered) exceeds establishment + maintenance costs, the optimizer expands `v32_land(j,"aff",...)`.

🟡 Source: module_56.md §2.6, equations.gms:60-79; module_56.md §4.1 (sign convention)

---

### Stage 2: Module 32 Responds — Afforestation Area and CDR Provision

**The `aff` afforestation type** (`v32_land(j,"aff",ac)`) is the endogenous optimization variable that responds to the CDR reward signal. It is constrained by:
- Spatial mask (default: `noboreal` — no afforestation in boreal zones) (`input.gms:7-8`)
- Minimum carbon density threshold: `fm_carbon_density(t,j,"forestry","vegc") > 20 tC/ha` (`presolve.gms:176`)
- Annual afforestation rate limit: 3% of forest establishment potential per year via `q32_co2p_aff_limit` (`equations.gms:84-86`, `s32_annual_aff_limit = 0.03`)
- Optional global/regional area cap via `q32_max_aff` / `q32_max_aff_reg` (`equations.gms:94-100`, default: `s32_max_aff_area = Inf`)

**Module 32 provides the CDR signal back to Module 56.**

**`q32_cdr_aff(j2,ac)`** (`equations.gms:36-39`):

```gams
vm_cdr_aff(j2,ac,"bgc") =e=
  sum(ac_est, v32_land(j2,"aff",ac_est)) * sum(ct, p32_cdr_ac(ct,j2,ac));
```

- `v32_land(j,"aff",ac_est)` — land newly established in the current timestep (`ac_est` = youngest age classes)
- `p32_cdr_ac(t,j,ac)` — per-hectare CDR at age class `ac`, computed in presolve as the incremental carbon density gain between adjacent age classes (`presolve.gms:71-72`):

```gams
p32_cdr_ac(t,j,ac)$(ord(ac) > 1 AND (ord(ac)-1) <= s32_planning_horizon/5) =
  p32_carbon_density_ac(t,j,"aff",ac,"vegc") - p32_carbon_density_ac(t,j,"aff",ac-1,"vegc");
```

Only age classes within the 50-year planning horizon (`s32_planning_horizon = 50`) are credited.

**`q32_bgp_aff(j2,ac)`** (`equations.gms:41-43`):

```gams
vm_cdr_aff(j2,ac,"bph") =e=
  sum(ac_est, v32_land(j2,"aff",ac_est)) * p32_aff_bgp(j2,ac);
```

Captures biophysical effects (albedo, evapotranspiration) in addition to biogeochemical CDR.

**Carbon density source for `aff`** — critical detail:  
Module 32 uses **uncalibrated** carbon density from Module 52 for the `aff` type (`presolve.gms:59,61`, module_52.md:278):
- Default (`s32_aff_plantation = 0`): `pm_carbon_density_secdforest_ac_uncalib` (natural regrowth curve, uncalibrated)
- Alternative (`s32_aff_plantation = 1`): `pm_carbon_density_plantation_ac_uncalib`

The uncalibrated versions are used because they represent the Chapman-Richards potential growth trajectory from bare land — appropriate for **new establishment**, distinct from the calibrated versions (tuned to FAO FRA 2025 observed growing stock of existing managed forests).

🟡 Source: module_32.md §2.3, §4.2 (q32_cdr_aff), module_52.md §2.C (uncalibrated rationale)

---

### Stage 3: Module 32 Carbon Stock → Module 52/56 LULUCF Accounting

**`q32_carbon(j2,ag_pools,stockType)`** (`equations.gms:108-109`):

```gams
vm_carbon_stock(j2,"forestry",ag_pools,stockType) =e=
  m_carbon_stock_ac(v32_land, p32_carbon_density_ac, "type32,ac", "type32,ac_sub");
```

Macro expansion: `vm_carbon_stock(j,"forestry",...)` = Σ over `(type32, ac)` of `v32_land(j,type32,ac) × p32_carbon_density_ac(t,j,type32,ac,ag_pools)`.

This populates `vm_carbon_stock` for all three M32 plantation types (`plant`, `ndc`, `aff`). M56 declared this variable (`modules/56_ghg_policy/price_aug22/declarations.gms:34`).

**Module 52 uses the updated `vm_carbon_stock` in `q52_emis_co2_actual`** (`equations.gms:16-19`):

```gams
vm_emissions_reg(i2,emis_oneoff,"co2_c") =e=
  sum((cell(i2,j2), emis_land(emis_oneoff,land,c_pools)),
    (pcm_carbon_stock(j2,land,c_pools,"actual") - vm_carbon_stock(j2,land,c_pools,"actual"))
    / m_timestep_length);
```

For afforestation:
- `vm_carbon_stock(j,"forestry","vegc","actual")` grows as `aff` area matures
- `pcm_carbon_stock - vm_carbon_stock < 0` → **negative CO2 emission** (net sequestration)
- Shows up as `vm_emissions_reg(i,"forestry_vegc","co2_c") < 0` and `vm_emissions_reg(i,"forestry_litc","co2_c") < 0`

🟡 Source: module_52.md §3, module_32.md §4.5, carbon_balance_conservation.md §8.2

---

### Stage 4: LULUCF Pricing Back in Module 56 — Double-Counting Avoidance

**`q56_emis_pricing_co2(i2,emis_oneoff)`** (`equations.gms:19-22`):

```gams
v56_emis_pricing(i2,emis_oneoff,"co2_c") =e=
  sum((cell(i2,j2), emis_land(emis_oneoff,land,c_pools)),
    (pcm_carbon_stock(j2,land,c_pools,"actual")
     - vm_carbon_stock(j2,land,c_pools,"%c56_carbon_stock_pricing%"))
    / m_timestep_length);
```

**Key: `c56_carbon_stock_pricing = "actualNoAcEst"` (default)**. This excludes the afforestation establishment age classes (`ac_est`) from the LULUCF pricing stock type — `"actualNoAcEst"` is a special stock type in which `ac_est` area is zeroed. This deliberately avoids pricing newly-established afforestation carbon twice (once via LULUCF stock-change, once via CDR reward). The module_56.md §1.3 documents this explicitly.

Afforestation carbon in **older age classes** (past establishment) does appear in the `"actual"` carry-forward (`pcm_carbon_stock`), contributing to a negative emission signal through `q56_emis_pricing_co2` (forest carbon increasing → negative LULUCF price signal). But the primary afforestation incentive mechanism is the CDR reward, not this LULUCF pathway.

**Cost flows to objective:**  
`q56_emission_cost_oneoff` (`equations.gms:45-52`) prices one-off emission sources (including `forestry_vegc`) using the annuity factor. For growing `aff` forests (negative `v56_emis_pricing`), this produces a negative cost contribution — a secondary revenue stream that adds to the CDR reward.  
`q56_emission_costs` (`equations.gms:56-58`) aggregates to `vm_emission_costs(i)` → Module 11.

🟡 Source: module_56.md §2.2, §5.2 (note on actualNoAcEst)

---

### Complete Variable/Equation Chain Summary

| Step | Equation | Variable(s) | Module:File:Line |
|------|----------|-------------|-----------------|
| Price load | — (preloop) | `im_pollutant_prices` ← `f56_pollutant_prices` | M56: preloop.gms:35-45 |
| Aff price | — (preloop) | `p56_c_price_aff(t,i,ac)` with 50-yr foresight | M56: preloop.gms:93-123 |
| CDR reward (cell) | `q56_reward_cdr_aff` | `v56_reward_cdr_aff(j)` ← `vm_cdr_aff × p56_c_price_aff` | M56: equations.gms:67-79 |
| CDR reward (region) | `q56_reward_cdr_aff_reg` | `vm_reward_cdr_aff(i)` → M11 (negative cost) | M56: equations.gms:60-66 |
| Aff CDR provision | `q32_cdr_aff` | `vm_cdr_aff(j,ac,"bgc")` ← `v32_land × p32_cdr_ac` | M32: equations.gms:36-39 |
| Biophys CDR | `q32_bgp_aff` | `vm_cdr_aff(j,ac,"bph")` ← `v32_land × p32_aff_bgp` | M32: equations.gms:41-43 |
| Aff carbon stock | `q32_carbon` | `vm_carbon_stock(j,"forestry",ag_pools,stockType)` | M32: equations.gms:108-109 |
| CO2 sequestration | `q52_emis_co2_actual` | `vm_emissions_reg(i,"forestry_*","co2_c") < 0` | M52: equations.gms:16-19 |
| LULUCF pricing | `q56_emis_pricing_co2` | `v56_emis_pricing` (excludes ac_est via actualNoAcEst) | M56: equations.gms:19-22 |
| Emission cost | `q56_emission_cost_oneoff` | `v56_emission_cost(i,forestry_*)` annuity factor | M56: equations.gms:45-52 |
| Total cost | `q56_emission_costs` | `vm_emission_costs(i)` → M11 | M56: equations.gms:56-58 |

---

### Is Afforestation C-Price Driven Under the Default Emission Policy?

**No, C-price-driven `aff` afforestation is effectively inactive under default settings.**

The logic:

1. **The switch is ON:** `s56_c_price_induced_aff = 1` (module_56.md `input.gms:69`). The policy matrix under `reddnatveg_nosoil` does not zero out `secdforest_vegc` — the CDR reward mechanism is not disabled.

2. **But prices are near-zero:** The default price scenario `c56_pollutant_prices = "R34M410-SSP2-NPi2025"` (No Policy Improvement) carries near-zero CO2 prices. Combined with `c56_mute_ghgprices_until = 2030` (`preloop.gms:70-72`), `im_pollutant_prices ≈ 0` for all near-term timesteps. Therefore `p56_c_price_aff(t,i,ac) ≈ 0` → `v56_reward_cdr_aff ≈ 0` → the CDR subsidy that would drive `v32_land(j,"aff",...)` upward is absent.

3. **Afforestation that occurs under defaults is NPI-policy-driven, not C-price-driven:** `c32_aff_policy = "npi"` (default, `input.gms:9-10`) activates the `ndc` afforestation type, not the `aff` type. This is governed by `q32_aff_pol(j2)` (`equations.gms:74-75`): `sum(ac_est, v32_land(j,"ndc",ac_est)) =e= p32_aff_pol_timestep(ct,j)`. Country NPI targets are enforced as a constraint — the model must meet them regardless of carbon price.

4. **C-price-driven `aff` afforestation requires a mitigation scenario.** Examples: `c56_pollutant_prices = "R34M410-SSP2-PkBudg650"` (1.5°C, CO2 reaching ~$300/tC by 2050) or `"R34M410-SSP2-PkBudg1000"` (2°C, ~$150/tC). At those price levels, the discounted CDR revenue (with 50% buffer, 50-year foresight) can exceed the establishment cost of $2,460/ha (`s32_est_cost_natveg`, `input.gms:24`) plus recurring maintenance of $615/ha/yr (`s32_recurring_cost`, `input.gms:26`).

🟡 Source: module_56.md §11.1, §5.1, module_32.md §9.2, module_56.md preloop.gms:69-74

---

## Closing Source Statement

🟡 **Based on module_32.md** (dynamic_may24 realization), **module_56.md** (price_aug22 realization), **module_52.md** (normal_dec17 realization), and **cross_module/carbon_balance_conservation.md**. No raw GAMS code was read this session (per task instructions). Line number citations are from the AI documentation, verified against MAgPIE develop as of the documentation's last sync (check `project/sync_log.json` for current staleness badge). No module notes file exists for M32; module_56_notes.md was consulted.

**Key provenance caveat:** The claim that `c56_carbon_stock_pricing = "actualNoAcEst"` applies specifically to establishment age classes is from module_56.md §1.3 and §5.2 — this is a design-level claim from the docs, not re-derived from GAMS code this session. For high-stakes implementation work, verify against `modules/56_ghg_policy/price_aug22/declarations.gms` and `postsolve.gms` directly.
