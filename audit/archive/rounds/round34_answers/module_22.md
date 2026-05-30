# Module 22 (Land Conservation): Protected-Area Constraints

## Default Realization

The default and only realization is `area_based_apr22` (April 2022 version), located at `modules/22_land_conservation/area_based_apr22/`.

---

## Architecture: No Equations, Parameter Calculation Only

Module 22 is a **data provider module with no GAMS equations**. All work happens in `preloop` and `presolve_ini` phases before the optimization solve. It computes `pm_land_conservation` from exogenous WDPA + China protected-area data plus optional priority-area scenarios, and passes those values to land allocation modules as binding lower bounds.

---

## Key Variable

**`pm_land_conservation(t,j,land,consv_type)`** — the single critical output.

- Dimensions: time step, cluster, land type (`primforest`, `secdforest`, `other`, `past`), conservation type (`protect` or `restore`)
- Units: mio. ha
- Declared in `declarations.gms:12-24`
- This is a **parameter**, not an optimization variable. It imposes lower bounds on `vm_land` in the consuming modules.

Note: there is no variable named `vm_land_conservation` in this realization. The module-22 output is the parameter `pm_land_conservation`. Do not confuse with `vm_land` (Module 10's optimization variable for land area).

---

## Conservation Type Dimension

`consv_type` has two elements:

| Value | Meaning |
|-------|---------|
| `protect` | Minimum land that must be retained; prevents conversion of existing natural land |
| `restore` | Land that must be actively restored (when target exceeds current area) |

---

## Baseline Data: WDPA + China (`presolve_ini.gms:20-26`)

For 1995-2020 (`m_year(t) <= sm_fix_SSP2`):

```gams
p22_conservation_area(t,j,land) = sum(cell(i,j),
  p22_wdpa_baseline(t,j,"%c22_base_protect%",land) * p22_country_weight(i)
  + p22_wdpa_baseline(t,j,"%c22_base_protect_noselect%",land) * (1-p22_country_weight(i))
);
```

- Historical protected-area time series from WDPA (IUCN categories Ia, Ib, III, IV, V, VI + legally designated areas) plus China PAs (@wang_over_2024)
- Coverage: 954.9 Mha in 1995 → 1855.7 Mha in 2020 (14.3% of land)
- Post-2020 values are held constant at 2020 levels (via `m_fillmissingyears` in `input.gms:57`)
- Default switch: `c22_base_protect = WDPA`

---

## Additional Conservation Priority Areas (`presolve_ini.gms:28-44`)

For post-2020 timesteps, additive priority areas are stacked on the WDPA baseline:

```gams
p22_conservation_area(t,j,land_consv) =
  <wdpa_baseline_terms>
  + sum(cell(i,j),
      p22_add_consv(t,j,"%c22_protect_scenario%",land_consv) * p22_country_weight(i)
      + p22_add_consv(t,j,"%c22_protect_scenario_noselect%",land_consv) * (1-p22_country_weight(i))
    );
```

- Default scenario: `c22_protect_scenario = none` (no additional areas)
- Available options (set `consv_prio22` in `sets.gms:21-24`): BH, IFL, BH_IFL, KBA, 30by30, GSN_DSA, GSN_RarePhen, GSN_AreaIntct, GSN_ClimTier1/2, GSN_HalfEarth, IrrC_50/75/95/99/100pc, CCA, PBL_HalfEarth
- Phase-in governed by sigmoid fader `p22_conservation_fader(t)` over 2025-2050 (default)
- Note: additional conservation applies only to the `land_consv` set = {`primforest`, `secdforest`, `other`}; **`past` is not in `land_consv`** for future scenarios (only receives historical WDPA protection)

Special case for IFL and BH_IFL scenarios (`presolve_ini.gms:16-17`): all remaining primary forest is automatically included in the protection target regardless of IFL map coverage.

---

## Protection Calculation (`presolve_ini.gms:47-55`)

```gams
pm_land_conservation(t,j,land,"protect") = p22_conservation_area(t,j,land);
pm_land_conservation(t,j,land,"protect")$(
  pm_land_conservation(t,j,land,"protect") > pcm_land(j,land)) = pcm_land(j,land);
```

Protection is capped at the current land area of that type (`pcm_land`), because you cannot protect more land than currently exists. The gap between the target and the current area becomes the restoration requirement.

---

## Restoration Calculation (`presolve_ini.gms:58-118`)

Active only when `s22_restore_land = 1` (default) or during historical period.

**Grassland restoration** (`presolve_ini.gms:64-67`):
```gams
pm_land_conservation(t,j,"past","restore")$(p22_conservation_area(t,j,"past") > pcm_land(j,"past")) =
  p22_conservation_area(t,j,"past") - pcm_land(j,"past");
```

**Forest restoration** (`presolve_ini.gms:68-74`):
```gams
pm_land_conservation(t,j,"secdforest","restore") =
  (p22_conservation_area(t,j,"primforest") + p22_conservation_area(t,j,"secdforest"))
  - (pcm_land(j,"primforest") + pcm_land(j,"secdforest"));
```
All forest restoration (both primforest and secdforest deficits combined) is attributed to `secdforest` because primary forest cannot be actively created. Very small values (<1e-6) are zeroed out.

**Other land restoration** (`presolve_ini.gms:75-77`): same pattern — deficit between target and current `other` land.

**Restoration potential limits** (`presolve_ini.gms:82-111`): restoration is capped by available land computed as:

```
Restoration potential = Total land
                        - Urban
                        - Timber plantations
                        - Protected pasture
                        - vm_land.lo(j,"crop")  [minimum cropland]
                        - vm_treecover.l(j)     [from Module 32]
```

Priority order for allocation: secondary forest first, then pasture, then other land.

**No-restoration mode** (`presolve_ini.gms:113-118`): if `s22_restore_land = 0` and post-historical, all restore values are set to zero.

---

## Key Switches and Scalars

| Switch | Default | Effect |
|--------|---------|--------|
| `c22_base_protect` | `WDPA` | WDPA category set for baseline |
| `c22_protect_scenario` | `none` | Additional priority area scenario |
| `s22_restore_land` | `1` | Enable (1) or disable (0) restoration |
| `s22_conservation_start` | `2025` | Start year of phase-in sigmoid |
| `s22_conservation_target` | `2050` | Target year for full implementation |
| `s22_base_protect_reversal` | `Inf` | Year protection is lifted (default: never) |

---

## Equations

**Module 22 has no GAMS equations (`=e=`, `=l=`, `=g=`).** All conservation logic is expressed as parameter assignments in `presolve_ini.gms`. The conservation constraints that actually appear as equations are written in the consuming modules (Modules 10, 35, 31) in the form:

```
vm_land(j,land) >= pm_land_conservation(t,j,land,"protect")
                  + pm_land_conservation(t,j,land,"restore")
```

Module 22 itself only produces the right-hand-side parameter.

---

## Modules That Consume `pm_land_conservation`

| Module | Land types consumed | Role |
|--------|---------------------|------|
| **Module 10 (Land)** | All (`primforest`, `secdforest`, `other`, `past`) | PRIMARY — imposes land conservation constraints in the land allocation optimization |
| **Module 35 (NatVeg)** | `primforest`, `secdforest`, `other` | Natural vegetation protection/restoration targets |
| **Module 31 (Pasture)** | `past` | Grassland protection and restoration targets |

Module 32 (Forestry) also interacts via `vm_treecover.l(j)` flowing INTO Module 22's restoration potential calculation, but Module 32 does not directly read `pm_land_conservation`.

---

## What Module 22 Does NOT Do

- No optimization of where to protect (scenarios are fully exogenous)
- No conservation costs calculated (opportunity costs handled by Module 39)
- No restoration dynamics or timescales (restoration is instantaneous)
- No effectiveness variation by governance quality (100% enforcement assumed)
- No marine protected areas (terrestrial only)
- No climate-driven range shifts of protected area boundaries
- No partial protection levels (binary: protected or not)

---

## Epistemic Status

All claims above are sourced from `modules/module_22.md` (documentation verified against `modules/22_land_conservation/area_based_apr22/*.gms` as of 2026-03-06, with WDPA numbers updated for PR #857 / China PA data inclusion). No raw GAMS source was read this session; citations to `presolve_ini.gms` line numbers are from the doc's last-verified state and may have drifted if code changed after 2026-03-06.

**Epistemic tier**: 🟡 Documented — read from official module_22.md documentation this session (cited above); not independently re-verified against current GAMS source.
