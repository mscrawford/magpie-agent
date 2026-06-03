# Q4: Are GHG Emissions Priced in MAgPIE's Default Configuration?

**Module 56 realization documented here**: `price_aug22` — this is the only realization of Module 56
and it IS the default realization. 🟡 Confirmed: `config/default.cfg:1613` reads
`cfg$gms$ghg_policy <- "price_aug22"  # def = price_aug22`

---

## (a) Default value of the GHG-price switch and its objective-function implications

**The key switch is `c56_pollutant_prices`.**

Default value (exact string from `config/default.cfg:1713`):
```
cfg$gms$c56_pollutant_prices <- "R34M410-SSP2-NPi2025"     # def = R34M410-SSP2-NPi2025
```

The `NPi2025` label stands for **"No Policy Improvement" (current policies)**. The module documentation
characterises this explicitly:

> "R34M410-SSP2-NPi2025: No additional policy (default) | 2050 CO2 Price: ~$0/tC | 2100 CO2 Price: ~$0/tC"
> (module_56.md §5.1)

In the preloop, the price-loading branch for a named scenario sets
`im_pollutant_prices(t_all,i,pollutants,emis_source)` from `f56_pollutant_prices(...)`, but the
historical-period zeroing (preloop Stage 5) then forces all prices to zero for years <= `sm_fix_SSP2`
(default 2025) and further mutes them until `c56_mute_ghgprices_until` (default `y2030`):
(module_56.md §3.5, `preloop.gms:69-74`).

The NPi2025 trajectory itself carries prices that are effectively ~$0 throughout the projection
horizon (module_56.md §5.1 table). The subsequent emission-policy matrix multiplication (Stage 7)
multiplies those already-zero prices by the `f56_emis_policy` matrix, leaving them at zero.

**Objective-function consequence:** `vm_emission_costs(i)` — which is the output of
`q56_emission_costs` (`equations.gms:54-58`) and which enters Module 11 (Costs) → the objective
function — evaluates to **zero** under the default configuration for all future periods. This means
GHG emission costs add nothing to the cost minimand. Land-use decisions are therefore made with
**no carbon price signal whatsoever** for positive emissions in the default run.

There is one narrow exception: a minimum C price floor of `s56_minimum_cprice = 3.67 USD17MER/tC`
is applied to CO2 after the muting step (`preloop.gms:74`, `config/default.cfg:1729`). This is a
technical floor "to avoid sudden jumps in carbon stock changes" — it is extremely small (~$13.4/tCO2
equivalent) and affects only the CO2 pricing path, not CH4 or N2O.

**Key companion switch — `c56_emis_policy`:**
Default value (`config/default.cfg:1810`):
```
cfg$gms$c56_emis_policy <- "reddnatveg_nosoil"     # def = reddnatveg_nosoil
```

This policy matrix defines WHICH gas-source combinations would be priced IF prices were non-zero.
Under `reddnatveg_nosoil`, the matrix has entries = 1 for CO2 from natural vegetation carbon stocks
(primforest vegc+litc, secdforest vegc+litc, other vegc+litc, peatland) but entries = 0 for CH4 and
N2O sources (module_56.md §3.7, §5.2). So even if `c56_pollutant_prices` were switched to a
mitigation scenario, CH4 and N2O would remain unpriced under the default emission policy.

---

## (b) Implications for Module 57 (MACC) abatement when pricing is OFF

Module 57's MACC calculations occur entirely in the **preloop** (module_57.md, "Execution Phases —
preloop `preloop.gms:8-110`"). The price-to-MACC-step mapping
(`preloop.gms:16-25`) reads `im_pollutant_prices` from Module 56 and converts them to MACC step
indices:

```
i57_mac_step_n2o = min(201, ceil(Price_N2O / 298 * 28/44 * 44/12 / Step_length) + 1)
i57_mac_step_ch4 = min(201, ceil(Price_CH4 / 25 * 44/12 / Step_length) + 1)
```

When `im_pollutant_prices = 0` for CH4 and N2O (which is the default, since `c56_emis_policy =
"reddnatveg_nosoil"` zeros those entries, and `c56_pollutant_prices = "R34M410-SSP2-NPi2025"` gives
~$0), the MACC step index evaluates to step 1. The zero-price exception explicitly traps this case
(`preloop.gms:42-44`, "Zero Price Exception"):

> "At step 1 (zero price): `im_maccs_mitigation` = 0 (no mitigation)"
> Condition `ord(maccs_steps) > 1` ensures this behavior. (module_57.md §Step 3)

**Therefore: with the default NPi2025 pricing, `im_maccs_mitigation` = 0 for all CH4 and N2O
sources, and MACC abatement does nothing.** No emission reductions are delivered by Module 57; no
MACC costs enter the objective. The module is architecturally active (realization `on_aug22` is
loaded) but produces zero mitigation because it receives zero prices from Module 56.

Note the one override path: the `s57_maxmac_*` scalars can force specific MACC steps independent of
price. But all five are defaulted to -1 (inactive) (`config/default.cfg` implicitly; module_57.md
§"Override Scalars `input.gms:14-18`"`), so this override is also dormant by default.

---

## (c) Which emission types would be priced once GHG pricing is enabled?

This depends on the combination of `c56_pollutant_prices` (the price level) AND `c56_emis_policy`
(the policy matrix that gates which gas-source combinations receive non-zero prices).

The relevant switch names are `c56_pollutant_prices` and `c56_emis_policy` — both `c56_*`
(character string switches, not scalar `s56_*`). There is no single binary ON/OFF scalar; enabling
pricing requires choosing both a price scenario (e.g., `"R34M410-SSP2-PkBudg650"`) and an emission
policy (e.g., `"all_nosoil"`).

### Under the DEFAULT emission policy (`c56_emis_policy = "reddnatveg_nosoil"`) with a
non-zero price scenario:

| Gas | Sources priced | Sources NOT priced |
|-----|---------------|--------------------|
| **CO2** | primforest vegc+litc, secdforest vegc+litc, other vegc+litc, peatland | soilc (all land types), cropland carbon, pasture carbon, plantation carbon |
| **CH4** | None | All (enteric fermentation, AWMS, rice) |
| **N2O** | None | All (fertilizer, AWMS, residues, etc.) |

Source: module_56.md §3.7 (policy matrix description) and §5.2 (policy table).

### Under a comprehensive emission policy (`c56_emis_policy = "all_nosoil"`):

- **CO2 (Module 52):** CO2 from land-use change across all land types (except soil carbon) would be
  priced via `q56_emis_pricing_co2`, which reads carbon stock changes directly from `vm_carbon_stock`
  (bypassing `vm_emissions_reg`). The pricing uses the `c56_carbon_stock_pricing` switch (default
  `"actualNoAcEst"`) to select which carbon pools count. (module_56.md §2.2, `equations.gms:19-22`)

- **CH4 (Module 53):** CH4 from enteric fermentation, rice paddy, and AWMS would be priced via
  `q56_emission_cost_annual`, which reads `vm_emissions_reg` from Module 53. These are annual
  (recurring) emission sources. (module_56.md §2.1, §2.3; module_57.md upstream dependencies table)

- **N2O (Module 51):** N2O (specifically `n2o_n_direct` and `n2o_n_indirect`) from inorganic
  fertilizer application, manure, residues, AWMS, and other soil sources would be priced via the same
  `q56_emission_cost_annual` pathway reading `vm_emissions_reg` from Module 51. (module_56.md §2.1,
  §2.3; module_51.md purpose statement)

### Equation file citations for the pricing calculation:

- Annual emissions pricing equation: `equations.gms:12-17` (`q56_emis_pricing`) — routes CH4 and N2O
  through `vm_emissions_reg`
- One-off CO2 pricing equation: `equations.gms:12-22` (`q56_emis_pricing_co2`) — reads carbon stocks
  directly
- Cost calculation for annual sources: `equations.gms:26-33` (`q56_emission_cost_annual`)
- Cost calculation for one-off sources: `equations.gms:35-52` (`q56_emission_cost_oneoff`)
- Total cost aggregation: `equations.gms:54-58` (`q56_emission_costs`) — output is `vm_emission_costs`

(All equation file citations are from module_56.md documentation, line numbers represent the doc's
last-verified state. Verify against current source if lines may have shifted.)

---

## Summary

**Default configuration: GHG emissions are NOT priced** (except for the technical $3.67/tC CO2 floor).
The switch `c56_pollutant_prices = "R34M410-SSP2-NPi2025"` delivers ~$0 GHG prices throughout the
projection, and `c56_mute_ghgprices_until = "y2030"` additionally suppresses any residual price until
2030. Consequently, `vm_emission_costs` = 0 in the objective function, Module 57 MACC abatement
delivers zero mitigation (all `im_maccs_mitigation = 0`), and land-use optimization proceeds with no
carbon cost incentive.

To enable pricing: set `c56_pollutant_prices` to a mitigation scenario (e.g.,
`"R34M410-SSP2-PkBudg650"`) and, to include CH4/N2O, also change `c56_emis_policy` from
`"reddnatveg_nosoil"` to a broader policy such as `"all_nosoil"`.

---

## Source Statement

- 🟡 **Module documentation**: `/magpie-agent/modules/module_56.md` (verified 2025-10-12,
  fully cross-referenced with source)
- 🟡 **Module documentation**: `/magpie-agent/modules/module_57.md` (verified 2025-10-12)
- 🟡 **Module documentation**: `/magpie-agent/modules/module_51.md` (verified 2025-10-12)
- 🟡 **Module documentation**: `/magpie-agent/modules/module_53.md` (verified 2025-10-12)
- 🟡 **Config file (authoritative)**: `/magpie/config/default.cfg`, lines 1613, 1713-1714, 1726,
  1729, 1741, 1754, 1767, 1780, 1810, 1817 (read this session)

No raw `.gms` files were read. All code-level claims derive from the verified AI documentation above.
