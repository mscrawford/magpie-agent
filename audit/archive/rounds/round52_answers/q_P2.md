# P2 answer (default emission-policy scope) — captured by coordinator from the answerer's returned message (agent declined to self-write; verbatim)

## CO2 Emission Pricing Coverage Under MAgPIE's Default Configuration

### The Default c56_emis_policy Value

The default value is **`reddnatveg_nosoil`**, set in `config/default.cfg:1810`. The policy matrix itself is loaded and applied in `modules/56_ghg_policy/price_aug22/preloop.gms:84-91` via `f56_emis_policy("%c56_emis_policy%",pollutants,emis_source)`, which is a 0/1 multiplier over all pollutant-source combinations (`module_56.md:490-514`). The data file is `f56_emis_policy.csv` (44 policies × 16 pollutants × 31 emission sources).

There is also a historical override at the same location (`preloop.gms:84-91`): for years <= `sm_fix_SSP2` (default 2025), `reddnatveg_nosoil` is applied unconditionally regardless of whatever `c56_emis_policy` is configured to.

### What Is Priced Under reddnatveg_nosoil (Policy Scope)

CO2 from natural vegetation carbon stocks (one-off pathway): Module 56 prices these via `q56_emis_pricing_co2` (equations.gms:19-22), computing the CO2 signal directly from `pcm_carbon_stock - vm_carbon_stock`, bypassing `vm_emissions_reg`. Priced pools under `reddnatveg_nosoil`: `primforest_vegc`, `primforest_litc`, `secdforest_vegc`, `secdforest_litc`, `other_vegc`, `other_litc`. Cropland, pasture, and forestry plantation carbon stocks are excluded.

Peatland CO2, CH4, N2O (annual pathway): Module 58 (`v2`) computes peatland emissions via `q58_peatland_emis` and populates `vm_emissions_reg(i,"peatland",poll58)` where poll58 = {co2_c, ch4, n2o_n_direct}. Module 56 routes these through `q56_emis_pricing` (equations.gms:15-17), the annual pathway. reddnatveg_nosoil prices peatland co2_c. DOC maps to co2_c (module_58.md:241-247).

Agricultural CH4 and N2O: despite "nosoil", reddnatveg_nosoil also prices non-CO2 ag gases (CH4 from awms/resid_burn/rice/ent_ferm/peatland; N2O from inorg_fert/man_crop/awms/resid/resid_burn/man_past/som/rice + indirect). "nosoil" refers only to soil CO2 exclusion (module_56.md:499, module_56_notes.md:18-20).

### What Is Excluded

Soil carbon (soilc) — explicitly excluded: policy matrix entry is 0 for all *_soilc sources (cropland/pasture/forest/other soil). q56_emis_pricing_co2 sums over emis_land(emis_oneoff,land,c_pools); the soilc entries have 0 in f56_emis_policy("reddnatveg_nosoil","co2_c","*_soilc"). Module 59 (cellpool_jan23) populates vm_carbon_stock(j,land,"soilc",stockType) for all land types (module_59.md:160-165), but no price is applied. Soil/SOM carbon is NOT priced by default.

Cropland, pasture, plantation/forestry carbon (CO2): vegc/litc of crop, past, forestry not covered. Only primforest, secdforest, other have CO2 pricing under this default.

### Peatland (M58) vs Vegetation/Soil Carbon (M52)

Module 52 pathway: q52_emis_co2_actual (equations.gms:16-19) writes vm_emissions_reg(i,emis_oneoff,"co2_c"). But M56's q56_emis_pricing_co2 does NOT read vm_emissions_reg for one-off CO2; it reads vm_carbon_stock directly and computes (pcm_carbon_stock - vm_carbon_stock)/m_timestep_length (module_56.md:83-122). M52 and M56 independently compute the same stock-change signal — M52 for reporting, M56 for pricing.

Module 58 pathway: peatland does NOT populate vm_carbon_stock (module_52.md:424). M58 maintains v58_peatland(j,land58) and applies IPCC EFs via q58_peatland_emis_detail (equations.gms:84-87), aggregated via q58_peatland_emis into vm_emissions_reg(i,"peatland",poll58). M56 prices via the annual pathway q56_emis_pricing. Peatland CO2 is a recurring annual emission, not one-off LUC CO2.

### Caveat: Price Scope vs Price Magnitude

c56_emis_policy sets SCOPE; price LEVEL is set by c56_pollutant_prices (default R34M410-SSP2-NPi2025), zeroed for years <= sm_fix_SSP2 (2025) and muted until c56_mute_ghgprices_until (2030) via preloop.gms:69-74. Under the default near-zero price scenario, effective pricing is essentially zero in default reference runs (module_56.md:958-961).

### Source statement
Based on module_56.md, module_58.md, module_52.md, module_59.md (line 180 default confirmation), module_56_notes.md, module_58_notes.md.
