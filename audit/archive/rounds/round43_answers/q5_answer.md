# Q5: How is timber demand satisfied in MAgPIE?

**Round 43 — Docs-only answer (sources: module_73.md, module_52.md, module_32.md, module_35.md)**

---

## (a) Default realization of Module 73 and what drives timber demand

**Default realization**: `default` (the only realization; `modules/73_timber/default/`).

Confirmed in `config/default.cfg:2205`:
```
cfg$gms$timber <- "default"
```

**What drives timber demand** (all 🟡 from module_73.md):

Timber demand is calculated **exogenously** in the preloop — it is NOT endogenous to the optimization. The demand signal is `pm_demand_forestry(t_ext,i,kforestry)` (mio. tDM/yr), provided to Modules 32 and 62.

The demand equation (module_73.md, `preloop.gms:20-28`) follows Lauri et al. 2019:

```
Demand(t) = Demand(t-1) × [Pop(t)/Pop(t-1)] × [GDP_pc(t)/GDP_pc(t-1)]^elasticity
```

Key drivers:
- **Population** (`im_pop_iso(t,iso)`, from Module 09) — linear multiplicative effect
- **Income** (`im_gdp_pc_ppp_iso(t,iso)`, from Module 09) — exponential effect via income elasticity from Morland et al. 2018 (`f73_income_elasticity.csv`, `input.gms:39-44`)
- **Demand saturation**: Income elasticity set to **zero** once GDP/capita exceeds `s73_income_threshold = 10,000 USD17PPP/cap/yr` (`preloop.gms:15`)
- **Woodfuel exception**: Woodfuel elasticity is always active (negative — demand decreases with income) (`preloop.gms:16`)
- **Historical anchor**: Before ~2020, demand is set to FAO values (`preloop.gms:11-12`); future projections grow from this historical base
- **Optional construction wood demand** can add to industrial roundwood: Churkina et al. 2020 scenarios (`c73_build_demand` = BAU/10pc/50pc/90pc, `preloop.gms:66-69`) or a simple linear expansion ramp (`s73_expansion > 0`, `preloop.gms:71-74`)

Demand is aggregated ISO country → 12 MAgPIE regions (`preloop.gms:30-31`) and converted from mio. m³/yr to mio. tDM/yr using a regional basic wood density `im_vol_conv(i)` (tDM/m³) provided by Module 52 (`preloop.gms:49-51`).

Only two product categories exist in the optimization: **wood** (industrial roundwood) and **woodfuel** — all FAO sub-categories are mapped to these via `kforestry_to_woodprod` (`sets.gms:37-41`).

---

## (b) The production variable and how harvested timber draws on standing stock

**Production variable**: `vm_prod(j,kforestry)` — total timber production per cell, in mio. tDM/yr.

Module 73 aggregates this from two sources via two balance equations (module_73.md, `equations.gms:43-61`):

### For industrial roundwood (q73_prod_wood, `equations.gms:43-50`):

```gams
vm_prod(j2,"wood") =e=
  vm_prod_forestry(j2,"wood")
  + sum((land_natveg), vm_prod_natveg(j2,land_natveg,"wood"))
  + v73_prod_heaven_timber(j2,"wood");
```

### For woodfuel (q73_prod_woodfuel, `equations.gms:52-61`):

```gams
vm_prod(j2,"woodfuel") =e=
  vm_prod_forestry(j2,"woodfuel")
  + sum((land_natveg), vm_prod_natveg(j2,land_natveg,"woodfuel"))
  + v73_prod_residues(j2)
  + v73_prod_heaven_timber(j2,"woodfuel");
```

**How each source draws on standing stock** (🟡 from module_32.md, module_35.md):

**Plantations** (`vm_prod_forestry`, from Module 32):
- Timber plantations are harvested at the rotation age when area is reduced (`v32_land_reduction(j,"plant",ac_sub)`)
- Harvested area = plantation area reduction: `q32_hvarea_forestry: v32_hvarea_forestry(j,ac_sub) =e= v32_land_reduction(j,"plant",ac_sub)` (module_32.md, `equations.gms:237-240`)
- Production = harvested area × growing stock at that age class / timestep length:
  `q32_prod_forestry: sum(kforestry, vm_prod_forestry(j,kforestry)) =e= sum(ac_sub, v32_hvarea_forestry(j,ac_sub) * im_growing_stock(ct,j,ac_sub,"forestry")) / m_timestep_length_forestry` (module_32.md, `equations.gms:246-249`)
- `im_growing_stock(t,j,ac,"forestry")` is the stem biomass (tDM/ha) at age class `ac`, computed by Module 14 from `pm_carbon_density_plantation_ac` (FRA-calibrated when `s52_growingstock_calib = 1`)
- Harvested plantations are replanted to the youngest age class; replanting is not counted as net land expansion (`q32_land_expansion_forestry`, `equations.gms:61-62`)

**Natural vegetation** (`vm_prod_natveg`, from Module 35) — three forest types:
- **Secondary forest** (q35_prod_secdforest, module_35.md `equations.gms:144-147`):
  `sum(kforestry, vm_prod_natveg(j,"secdforest",kforestry)) =e= sum(ac_sub, v35_hvarea_secdforest(j,ac_sub) * im_growing_stock(ct,j,ac_sub,"secdforest")) / m_timestep_length_forestry`
  Harvest area ≤ area reduction (`q35_hvarea_secdforest`, `equations.gms:176-179`)
- **Primary forest** (q35_prod_primforest, `equations.gms:153-156`):
  Uses `im_growing_stock(t,j,"acx","primforest")` — always the mature "acx" value since primforest has no age-class structure
- **Other land** (q35_prod_other, `equations.gms:162-168`):
  `othernat` uses "other" growing stock; `youngsecdf` uses "secdforest" growing stock

**Harvest control for natural vegetation** (module_35.md): The fraction of natural vegetation available for harvest is bounded by `s35_natveg_harvest_shr` (scalar, `input.gms`). The default for `s35_hvarea` is 2 (endogenous harvest), but this is only activated when `s73_timber_demand_switch = 1`. Natural-origin secondary forest area (`pc35_secdforest_natural`) is **protected from harvest** by a lower bound on `v35_secdforest` (`presolve.gms:177-180`).

**Residues** (`v73_prod_residues`) contribute to woodfuel only:
- Upper bound: `v73_prod_residues(j) ≤ (Σ vm_prod_forestry(j,kforestry) + Σ vm_prod_natveg(j,land_natveg,kforestry)) × 0.15` (`q73_prod_residues`, `equations.gms:75-81`)
- Source: 27% of stem harvest is residues × 52% technical recovery ≈ 15% (`s73_residue_ratio = 0.15`, `input.gms:20`)

**Emergency slack** (`v73_prod_heaven_timber`): Activated only when real forest supply cannot meet demand. Cost = 1,000,000 USD17MER/tDM (`s73_free_prod_cost`, `input.gms:17`) — prohibitively expensive, signals supply shortage.

---

## (c) How harvesting interacts with Module 52 carbon stock (does harvest release carbon?)

**Yes, harvest releases carbon — via the stock-difference method in Module 52.** The mechanism operates as follows (🟡 from module_52.md, module_32.md, module_35.md):

### Step 1: Carbon stocks are computed by land modules

Module 32 computes `vm_carbon_stock(j,"forestry",ag_pools,stockType)` as area × age-class-specific carbon density (`q32_carbon`, module_32.md `equations.gms:108-109`):
```gams
vm_carbon_stock(j2,"forestry",ag_pools,stockType) =e=
  m_carbon_stock_ac(v32_land, p32_carbon_density_ac, "type32,ac","type32,ac_sub");
```
When a plantation is harvested, `v32_land(j,"plant",ac_sub)` drops to zero for the harvested age class — the standing carbon disappears from the current-timestep carbon stock.

Module 35 computes `vm_carbon_stock(j,"secdforest",...)` and `vm_carbon_stock(j,"primforest",...)` similarly. When secondary or primary forest is harvested, those areas shrink, reducing the carbon stock.

### Step 2: Module 52 computes emissions from the stock change

Module 52's single equation `q52_emis_co2_actual` (`equations.gms:16-19`) is:

```gams
vm_emissions_reg(i2,emis_oneoff,"co2_c") =e=
  sum((cell(i2,j2), emis_land(emis_oneoff,land,c_pools)),
    (pcm_carbon_stock(j2,land,c_pools,"actual")
     - vm_carbon_stock(j2,land,c_pools,"actual"))
    / m_timestep_length);
```

- `pcm_carbon_stock` = **previous** timestep's carbon stock (mio. tC)
- `vm_carbon_stock` = **current** timestep's carbon stock (optimized, mio. tC)
- When harvest reduces `vm_carbon_stock` below `pcm_carbon_stock`, the difference / timestep length = **positive CO2-C emissions** (Tg C/yr)

This is the **stock-difference method**: MAgPIE does not track emission processes; it simply measures the net change in land carbon. Every tonne of carbon removed from a standing forest through harvest appears as an emission in the accounting.

### Important caveat: No wood product carbon pools

Module 52's documentation explicitly flags this (module_52.md, Limitations §3, "No wood product pools"):
> "Harvested wood products (HWP) not tracked. Carbon in timber immediately emitted upon harvest. Ignores long-term carbon storage in buildings, furniture (decades to centuries)."

This means MAgPIE **does not apply a wood products delay** — all harvested carbon is counted as immediately emitted in the timestep of harvest. There is no HWP pool that sequesters carbon for decades before eventual decay.

### How carbon pricing interacts with harvest decisions

`vm_emissions_reg` flows to Module 56 (GHG Policy), which applies a carbon price. Higher carbon prices therefore:
1. Increase the cost of harvesting forests (because harvest causes emissions)
2. Can incentivize carbon-price-driven afforestation via Module 32's `aff` type
3. Create a trade-off that the optimizer resolves: plantation timber revenue vs. carbon cost of the harvest

### Harvest followed by replanting (plantations)

For plantation `plant` type in Module 32: harvested area is replanted to the youngest age class. In the next timestep, `v32_land(j,"plant",ac0)` begins growing again, so the carbon stock starts recovering. The emission is thus temporary — a carbon debt that is repaid as the replanted stand grows back. However, within MAgPIE's 5-year timestep resolution, the initial harvest emission appears in full at harvest time, with sequestration credit accumulating over subsequent timesteps.

---

## Summary

| Aspect | Key mechanism | Source |
|--------|--------------|--------|
| Demand driver | Exogenous GDP/population projections via Lauri 2019 + Morland 2018 elasticities | module_73.md `preloop.gms:14-31` |
| Demand saturation | Elasticity = 0 above 10,000 USD17PPP/cap | module_73.md `preloop.gms:15` |
| Production variable | `vm_prod(j,kforestry)` aggregated by q73_prod_wood/woodfuel | module_73.md `equations.gms:43-61` |
| Plantation production | `harvested area × im_growing_stock / timestep` (q32_prod_forestry) | module_32.md `equations.gms:246-249` |
| Natveg production | Same formula applied to secdforest/primforest/other (q35_prod_*) | module_35.md `equations.gms:144-168` |
| Carbon emission mechanism | Stock-difference: `(pcm_carbon_stock - vm_carbon_stock) / timestep` | module_52.md `equations.gms:16-19` |
| No HWP delay | Harvested carbon emitted immediately — no wood product pools | module_52.md Limitations §3 |
| Carbon pricing feedback | Emissions flow to M56 → carbon price → harvest cost signal | module_52.md §3; module_32.md |

---

## Sources

🟡 module_73.md (docs verified against `modules/73_timber/default/*.gms`)
🟡 module_52.md (docs verified against `modules/52_carbon/normal_dec17/*.gms`)
🟡 module_32.md (docs verified against `modules/32_forestry/dynamic_may24/*.gms`)
🟡 module_35.md (docs verified against `modules/35_natveg/pot_forest_may24/*.gms`)
🟡 `config/default.cfg:2205` — realization confirmation

All claims are 🟡 (read from AI documentation this session, not independently re-verified against raw GAMS code). No `.gms` files were opened.

**Doc wished existed**: A dedicated cross-module document tracing the full timber-carbon feedback loop: `vm_prod_forestry` → area reduction in M32 → `vm_carbon_stock` drop in M32/M35 → M52 emission calculation → M56 carbon price signal → M32 establishment decision. The carbon-balance cross-module doc (`cross_module/carbon_balance_conservation.md`) covers the accounting side but not this end-to-end harvest-to-emission pathway. A "timber production and carbon interaction" entry in `cross_module/` covering the HWP omission and replanting dynamics would also clarify the immediate-emission assumption for users modeling carbon policy.
