# R24-Q2 Sonnet answer (Bioenergy default + switches)

## Bioenergy Demand Default Scenario — Module 60

### (a) Default Realization

The default realization of Module 60 is `1st2ndgen_priced_feb24`, confirmed in `config/default.cfg` via `cfg$gms$bioenergy <- "1st2ndgen_priced_feb24"`. The alternative realization `1stgen_priced_dec18` supports only first-generation bioenergy pricing and is not the default.

Source: `modules/module_60.md`, header and configuration sections.

---

### (b) Scenario Switches with Default Values

The following switches and scalar parameters appear in the module documentation as declared in `modules/60_bioenergy/1st2ndgen_priced_feb24/input.gms` (the authoritative location for defaults in the documentation). All paths are relative to the MAgPIE project root.

**Demand-level control:**

| Switch | Default | Effect |
|---|---|---|
| `c60_biodem_level` | `1` | 0 = global demand constraint active (`q60_bioenergy_glo`); 1 = regional constraint active (`q60_bioenergy_reg`) — default is regional |
| `c60_2ndgen_biodem` | `"R34M410-SSP2-NPi2025"` | Selects the 2nd-generation dedicated bioenergy demand scenario from 90+ options |
| `c60_2ndgen_biodem_noselect` | `"R34M410-SSP2-NPi2025"` | Scenario applied to non-selected countries (population-weighted blending) |
| `c60_res_2ndgenBE_dem` | `"ssp2"` | Selects residue demand scenario (ssp1–5, sdp, off) |
| `c60_1stgen_biodem` | `"const2020"` | 1st-generation demand trajectory (const2020, const2030, phaseout2020) |
| `c60_price_implementation` | `"lin"` | Price trajectory for subsidies: linear, exponential, or constant |

**Scalar floor and subsidy parameters** (declared in `input.gms`):

| Parameter | Default | Units | Purpose |
|---|---|---|---|
| `s60_2ndgen_bioenergy_dem_min` | `1` | mio. GJ per yr | Minimum 2nd-gen dedicated demand per region (numerical floor) |
| `s60_bioenergy_1st_subsidy` | `6.5` | USD17MER per GJ | Mass-based constant subsidy floor for 1st-generation bioenergy |
| `s60_bioenergy_1st_price` | `0` | USD17MER per GJ | Energy-based price target for 1st-gen subsidy in 2100 |
| `s60_bioenergy_2nd_price` | `0` | USD17MER per GJ | Energy-based price target for 2nd-gen subsidy in 2100 |

The parameter names `s60_biodem_level_min_em` and `s60_2ndgen_bioenergy_dem_min_post` do not appear anywhere in the module_60.md documentation. Per anti-confabulation MANDATE 7 (variable-name lookup) and MANDATE 3 (default-parameter verification), I cannot assert that these parameters exist in declarations.gms without having read that file in this session — and MANDATE 16 prohibits citing line numbers not read this session. These names may be from a different realization, a future code change, or may be non-existent. The only `s60_*` minimum-floor parameter documented is `s60_2ndgen_bioenergy_dem_min`.

**Minimum floor enforcement** (documented at `presolve.gms:56-57`):

```gams
i60_bioenergy_dem(t,i)$(i60_bioenergy_dem(t,i) < s60_2ndgen_bioenergy_dem_min)
    = s60_2ndgen_bioenergy_dem_min
```

This conditional assignment runs in presolve, before the optimization, enforcing that `i60_bioenergy_dem` (the regional 2nd-gen demand parameter fed into the constraints) is never below 1 mio. GJ per year per region. This is a pre-processing override, not an optimization constraint.

---

### (c) Equation Enforcing the 2nd-Generation Bioenergy Floor

The floor itself is not enforced by a single GAMS equation with an `=g=` constraint in the equation block — it is applied as a **parameter override in presolve**. The downstream equations that then enforce the minimum-floored value as an optimization constraint are:

**Regional mode (default, `c60_biodem_level = 1`):**

`q60_bioenergy_reg` (`modules/60_bioenergy/1st2ndgen_priced_feb24/equations.gms:46-47`):

```gams
sum(kbe60, v60_2ndgen_bioenergy_dem_dedicated(i2,kbe60)) =g=
    sum(ct, i60_bioenergy_dem(ct,i2)) * c60_biodem_level
```

With `c60_biodem_level = 1`, the right-hand side equals `i60_bioenergy_dem(ct,i2)` — the regional 2nd-gen demand target, which has already had the floor of `s60_2ndgen_bioenergy_dem_min = 1` applied. So `q60_bioenergy_reg` is the optimization-level equation that enforces the floored minimum, requiring each region's sum of dedicated 2nd-gen bioenergy crops (betr + begr) to meet or exceed the floored demand.

**Global mode (non-default, `c60_biodem_level = 0`):**

`q60_bioenergy_glo` (`equations.gms:43-44`):

```gams
sum((kbe60,i2), v60_2ndgen_bioenergy_dem_dedicated(i2,kbe60)) =g=
    sum((ct,i2), i60_bioenergy_dem(ct,i2)) * (1 - c60_biodem_level)
```

Under the default configuration this equation is inactive (right-hand side = 0 because `c60_biodem_level = 1`).

**The complete chain under default settings:**

1. Presolve applies `s60_2ndgen_bioenergy_dem_min = 1` floor to `i60_bioenergy_dem` for any region with sub-minimum demand (`presolve.gms:56-57`).
2. The optimization then enforces `q60_bioenergy_reg` (≥ inequality) to require each region's `v60_2ndgen_bioenergy_dem_dedicated` to meet the floored `i60_bioenergy_dem` value.
3. The overall bioenergy constraint `q60_bioenergy` (`equations.gms:16-21`) then links the mass-based `vm_dem_bioen(i,kall)` (converted to energy units via `fm_attributes("ge",kall)`) to the sum of 1st-gen, 2nd-gen dedicated, and 2nd-gen residue demands — ensuring all streams together are satisfied.

---

**Default scenario summary**: Under the default configuration, MAgPIE applies the `1st2ndgen_priced_feb24` realization with the `R34M410-SSP2-NPi2025` scenario for 2nd-generation dedicated bioenergy (regional enforcement via `q60_bioenergy_reg`), `ssp2` residues, `const2020` first-generation, a linear subsidy trajectory starting at zero, and a numerical floor of 1 mio. GJ per year per region enforced pre-optimization via `s60_2ndgen_bioenergy_dem_min`.

---

Source statement:
- 🟡 Based on `modules/module_60.md` documentation (last verified 2025-10-13 against `../modules/60_*/1st2ndgen_priced_feb24/*.gms`)
- Specific citations: `modules/60_bioenergy/1st2ndgen_priced_feb24/input.gms` (switch defaults), `modules/60_bioenergy/1st2ndgen_priced_feb24/equations.gms:16-21, 43-44, 46-47`, `modules/60_bioenergy/1st2ndgen_priced_feb24/presolve.gms:56-57`
- Parameters `s60_biodem_level_min_em` and `s60_2ndgen_bioenergy_dem_min_post` are not documented in module_60.md and were not verified in raw GAMS source per flywheel R24 rules. I cannot confirm their existence.
