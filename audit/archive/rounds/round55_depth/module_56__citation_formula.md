# Round 55 depth audit — module_56.md — lens: citation_formula

**Target:** `modules/module_56.md` (Module 56 GHG Policy, realization `price_aug22`)
**Ground truth:** `/private/tmp/magpie_develop_ro` (develop worktree)
**Auditor lens:** citation_formula — entered from every `file:line` citation, mechanically checked file existence, line range, token presence, and equation-formula fidelity.

## Verdict

The doc is unusually clean. All 6 equation citations, all interface-variable attribution claims, all default-parameter values, all cross-module citations, and the set-membership counts verify exactly against develop. **One confirmed bug**: a worked annuity example whose stated numeric result is 10× its own inputs.

## Confirmed bug

### BUG-1 (Minor, formula) — annuity worked example off by 10×
- **doc_line:** module_56.md:203
- **claim:** "Annual cost = 10 Tg/yr × 10 yr × $100/tC × 0.05/1.05 ≈ $4,762/yr / This equals the annual payment on a $100,000 perpetuity at 5% interest"
- **reality:** The literal expression evaluates to **$476.19/yr**, not $4,762. `10*10*100*(0.05/1.05) = 476.19`. The stated result ($4,762) is the annuity-due payment on a **$100,000** present value, but the stated inputs (100 Tg total × $100/tC) hand-wave to only a **$10,000** PV → $476/yr. Internally inconsistent by exactly 10×.
- **verify_cmd:** `python3 -c "print(10*10*100*(0.05/1.05))"` → `476.19...`; and `100000*(0.05/1.05)` → `4761.9`.
- **note:** Explicitly labeled "Example:", so illustrative — the formula STRUCTURE, the annuity factor `r/(1+r)`, and `m_timestep_length` roles are all correct. Only the final number is wrong. Low severity.
- **proposed_fix:** Change "$4,762/yr" to "$476/yr" and "a $100,000 perpetuity" to "a $10,000 perpetuity"; OR raise the price to $1,000/tC to keep the $100,000/$4,762 pairing. Keep inputs and result mutually consistent.

## Verified-correct (high-value confirmations)

**Equation citations — all exact against `price_aug22/equations.gms` (79 lines):**
- q56_emis_pricing `15-17` ✓; q56_emis_pricing_co2 `19-22` ✓; q56_emission_cost_annual `29-33` ✓; q56_emission_cost_oneoff `45-52` ✓; q56_emission_costs `56-58` ✓; q56_reward_cdr_aff_reg & q56_reward_cdr_aff `67-79` ✓. All code blocks quoted in the doc match the source character-for-character.

**Declarations citations — all exact (`declarations.gms`, 64 lines):**
- `im_pollutant_prices`:9 ✓; `p56_c_price_aff`:11 ✓; `vm_carbon_stock`:34 ✓; `vm_emission_costs`:39 ✓; `vm_reward_cdr_aff`:43 ✓.

**Preloop stage citations (`preloop.gms`, 123 lines):** stages 1–8 (`35-45`, `50-51`, `53-63`, `65-67`, `69-74`, `76-82`, `84-91`, `93-123`) all land on the described operations; quoted snippets match. `preloop.gms:18-23` (region price share), `:70` (historic zeroing), `:74` (min cprice floor), `:87,89` (policy-matrix multiply), `:118` (age-class shift) all verified.

**Default parameters (`input.gms`) — all verified:**
- s56_limit_ch4_n2o_price `/4920/`:65 ✓; s56_cprice_red_factor `/1/`:66 ✓; s56_minimum_cprice `/3.67/`:67 ✓; s56_ghgprice_devstate_scaling `/0/`:68 ✓; s56_c_price_induced_aff `/1/`:69 ✓; s56_c_price_exp_aff `/50/`:70 ✓; s56_buffer_aff `/0.5/`:71 ✓; s56_ghgprice_fader `/0/`:75 ✓; fader start/end/target `2035/2050/1`:76-78 ✓.
- Config globals: c56_pollutant_prices=`R34M410-SSP2-NPi2025`:84 ✓; c56_emis_policy=`reddnatveg_nosoil`:86 ✓; c56_cprice_aff=`secdforest_vegc`:87 ✓; c56_mute_ghgprices_until=`y2030`:88 ✓; c56_carbon_stock_pricing=`actualNoAcEst`:90 ✓.
- `config/default.cfg` has NO c56 overrides → input.gms defaults are the active defaults. Doc correctly leads with `price_aug22` (the only realization).
- sm_fix_SSP2 default `2025` confirmed at `modules/09_drivers/aug17/input.gms:22`.

**Interface-variable attribution (checked vs `audit/integrated/depth_rolemap.json` + both-endpoints grep):**
- vm_carbon_stock populated_by {29,31,32,34,35,(56 init/postsolve),59}; peatland (58) correctly EXCLUDED. Doc's "M30 populates the separate vm_carbon_stock_croparea which M29 folds in" matches map (vm_carbon_stock_croparea populated_by 30, read_by 29,30). ✓
- vm_emissions_reg populated_by {51,52,53,58}, read_by {56,57}. Doc's "M57 only reads, does not populate" ✓.
- im_pollutant_prices populated_by {56}, read_by {56,57} ✓; vm_cdr_aff from 32 ✓; pm_interest from 12 ✓; pcm_carbon_stock populated_by {56,59} ✓.

**Cross-module citations (realizations confirmed default):**
- `modules/15_food/anthro_iso_jun22/intersolve.gms:23` → `vm_emission_costs.l(i)` for tax recycling ✓.
- `modules/59_som/cellpool_jan23/postsolve.gms:13` → `pcm_carbon_stock(j,land,"soilc",...) = vm_carbon_stock.l(...)` ✓ (som default = cellpool_jan23).
- `modules/57_maccs/on_aug22/preloop.gms:24-25` → reads `im_pollutant_prices` for MAC steps ✓.
- Commit `931db85c4` = "59_som: carry soil pcm_carbon_stock forward each timestep", 2026-06-25 ✓.

**Set counts:** scen56 = 44 policies (`sets.gms:119-163`) ✓; pollutants_all = 16 ✓; emis_source = 31 (`core/sets.gms:302-312`) ✓; ghgscen56 = 100+ (`sets.gms:15-117`) ✓. f56_emis_policy dims "44 × 16 × 31" ✓.

**Numeric checks:** CH4 cap `4920*12/44*28 = 37,571` ✓; N2O-N cap `4920*12/44*265*44/28 = 558,771` ✓; ac10 discount `1/1.05^10 = 0.614` ✓; min cprice `3.67*12/44 = $1/tCO2` ✓.

## Deferred (not verifiable this session — no bug asserted)

- **f56_emis_policy.csv row contents** (doc:499, 662-663, 666): the specific gas-source membership claims for `reddnatveg_nosoil` / `redd+natveg_nosoil` (which CH4/N2O sources priced, secdforest_vegc=1, etc.) CANNOT be verified — the CSV is absent from the worktree (`modules/56_ghg_policy/input/` holds only a `files` placeholder; it is a run-time input product). These claims are detailed and plausible but unchecked here.
- §5.1 price-magnitude table (doc:643-647): explicitly "Approximate values"; not code-derivable.
- §9.4 emission-cost sanity magnitudes: order-of-magnitude, not code claims.
- Centrality "Rank #3 / provides to 13 modules" (doc:1136-1150): cross-module graph metric not re-derived this session.
