# Module 45 (Climate): Default Realization, Climate Data Provided, and Dynamic vs Static Impact

## Default Realization

The default (and only) realization is `static`. There are no alternative realizations. All MAgPIE runs use this realization unconditionally.

Source: `modules/module_45.md` (Status: "Realization: `static`"; "No alternative realizations exist")

---

## What Climate Data Module 45 Provides

Module 45 is a **pure data provider** with 0 equations, 0 variables, and 1 parameter. It loads Köppen-Geiger climate classification shares from a static input file and makes them available to downstream modules via a single parameter:

**`pm_climate_class(j, clcl)`**
- Dimensions: `j` (simulation cells, ~200 at cluster resolution) × `clcl` (31 Köppen-Geiger climate types)
- Unit: dimensionless share (0–1), summing to 1.0 within each cell
- Loaded once at model start from `modules/45_climate/static/input/koeppen_geiger.cs3` via a table statement in `input.gms:10-13`
- Data source: Rubel et al. (2010), 1976–2000 climatological average (25-year mean)

The 31 `clcl` types span the full Köppen-Geiger hierarchy: 4 tropical (A), 4 arid (B), 9 temperate (C), 12 continental (D), 2 polar (E) — set defined in `sets.gms:11-45`.

Module 45 does **not** provide quantitative climate variables (temperatures, precipitation, growing degree days). It provides classification labels and area shares only; quantitative climate-indexed parameters are held in module-specific input files (e.g., `f52_growth_par(clcl,...)` in Module 52).

---

## How Each Downstream Module Uses pm_climate_class

### Module 14 (Yields)

Location: `modules/14_yields/managementcalib_aug19/presolve.gms:27-62`

Used to compute a climate-weighted IPCC Biomass Expansion Factor (BEF):

```gams
sum(clcl, pm_climate_class(j,clcl) * fm_ipcc_bef(clcl))
```

This is 1-dimensional (uniform across `land_timber` types) as of a 2026-04-20 update (prior to that, `f14_ipcc_bce(clcl, forest_type)` was 2-D, distinguishing plantations from natural vegetation; changed in PR #869).

### Module 52 (Carbon)

Locations: `modules/52_carbon/normal_dec17/start.gms:17-35` and `preloop.gms:22-31`

Used for two purposes:

1. Climate-weighted growth parameters (k, m) in the Chapman-Richards equation — applied to plantation, secondary forest, and other natural land carbon stocks:
   ```gams
   sum(clcl, pm_climate_class(j,clcl) * f52_growth_par(clcl,"k",forest_type))
   sum(clcl, pm_climate_class(j,clcl) * f52_growth_par(clcl,"m",forest_type))
   ```

2. Climate-weighted volumetric wood density for growing-stock calibration:
   ```gams
   sum((cell(i,j), clcl), pm_climate_class(j,clcl) * f52_volumetric_conversion(clcl)) / sum(cell(i,j), 1)
   ```
   producing `im_vol_conv(i)`.

### Module 58 (Peatland)

Location: `modules/58_peatland/v2/preloop.gms:~50`

Maps the 31 Köppen-Geiger types to 6 aggregated peatland climate zones via a set-mapping aggregation:
```gams
p58_mapping_cell_climate(j,clcl58) = sum(clcl_mapping(clcl,clcl58), pm_climate_class(j,clcl))
```

### Module 59 (SOM — Soil Organic Matter)

Location: `modules/59_som/cellpool_jan23/preloop.gms:16-89`

Maps 31 types to 3 SOM climate categories, used for climate-weighted C:N ratios:
```gams
sum(clcl_climate59(clcl,climate59), pm_climate_class(j,clcl)) * f59_cratio_landuse(i,climate59,kcr)
```

### Module 35 (Natural Vegetation)

Module 45's documentation does not record a direct consumer relationship with Module 35 (natveg). Module 35's climate-sensitive behavior (e.g., natural disturbance rates) is parameterized from external input files, but Module 45's `pm_climate_class` is not listed among its consumers in `module_45.md`. This absence should be verified against raw code before asserting Module 35 is not a consumer; the docs record confirmed usages only.

---

## Is Climate Impact Dynamic or Static Under the Default Config?

**Fully static.** Under the `static` realization (the only realization):

- `pm_climate_class(j,clcl)` is loaded **once** at model initialization and **never updated** during the simulation.
- A cell classified as, say, `Dfb` (warm-summer humid continental) in the first timestep remains `Dfb` in 2100, regardless of any real-world climate trajectory.
- The data represent 1976–2000 historical conditions and predate the most recent ~0.5°C of warming (2000–2025).

The module's own realization description explicitly states: "Temporal variations in climate classification are not considered" (`static/realization.gms:12`).

**What this means downstream:** Modules 14, 52, 58, and 59 receive fixed climate zone shares for the entire simulation. If those downstream modules have *time-varying* climate-indexed parameters (e.g., `f52_growth_par` indexed by both `clcl` and `t`), those parameters can implicitly capture warming effects — but the zone-boundary weights `pm_climate_class(j,clcl)` themselves do not shift. There is no feedback from model land-use state or emissions trajectories back to climate classification.

---

## Summary Table

| Aspect | Value |
|---|---|
| Default realization | `static` (only realization) |
| Parameter provided | `pm_climate_class(j, clcl)` |
| Climate system | 31 Köppen-Geiger types |
| Data period | 1976–2000 (Rubel et al. 2010) |
| Equations | 0 |
| Variables | 0 |
| Climate dynamics | None — fully static |
| Consumers (confirmed) | M14 (yields/BEF), M52 (carbon growth + wood density), M58 (peatland zones), M59 (SOM C:N ratios) |
| M35 (natveg) consumer? | Not confirmed in docs — verify in code before asserting |

---

## Epistemic Status

- 🟡 **Documented**: All claims above are drawn from `modules/module_45.md`, read this session. No raw GAMS code was read per task constraint.
- The 2026-04-20 note on the BEF dimensionality change (PR #869) is recorded in the docs and flagged as post-dating the original verification date (2025-10-13); if the docs were not re-verified after that PR, the BEF usage detail should be confirmed against current code before citing it in high-stakes work.
- The M35 (natveg) claim is explicitly negative-evidence: absence from the consumer list in docs. This is not a verified absence from code.

Source cited: `<magpie-agent>/modules/module_45.md`
