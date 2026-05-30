# Module 71 — Livestock Disaggregation: Mechanism, Linkage to Module 70, and Key Variables

## Default Realization

**`foragebased_jul23`** (confirmed: `config/default.cfg`: `cfg$gms$disagg_lvst <- "foragebased_jul23"`).

Alternatives: `foragebased_aug18` (legacy, no LP/NLP switching support), `off` (no disaggregation).

Source: `modules/module_71.md`

---

## Core Purpose

Module 71 takes regional livestock production totals — optimized at region level by Module 70 — and distributes them onto simulation cells (0.5 grid cells). Without Module 71, cellular livestock distribution would be determined solely by transport costs (Module 40) and water availability (Module 42), producing unrealistic spatial concentration.

The module implements two mechanistically distinct distribution logics:

1. **Ruminants** (beef, dairy — set `kli_rum`): constrained by local forage feed availability (pasture + fodder). Forage is treated as non-transportable.
2. **Monogastrics** (pigs, chickens, eggs — set `kli_mon`): distributed according to urban area share as a population proxy, with a 10% flexibility scalar.

---

## The vm_prod / vm_dem_feed Linkage (Module 70 → 71)

The bridge between the two modules runs through two interface variables provided by Module 70:

| Variable | Direction | Content |
|---|---|---|
| `im_feed_baskets(t,i,kli,kall)` | M70 → M71 | Regional feed composition: tDM feed per tDM livestock product; covers all feed items including pasture and fodder |
| `vm_feed_balanceflow(i,kli_rum,kforage)` | M70 → M71 | Regional balance flow correcting for FAO feed-use inconsistencies (can be positive or negative) |
| `vm_prod_reg(i,kli)` | Shared/optimized | Regional livestock production totals (mio. tDM/yr) that Module 71 disaggregates to cells |

**On the Module 70 side**: equation `q70_feed` (`equations.gms:17-20`) calculates `vm_dem_feed(i,kap,kall)` — regional feed demand — as:

```
vm_dem_feed(i,kap,kall) >= vm_prod_reg(i,kap) * im_feed_baskets(t,i,kap,kall)
                            + vm_feed_balanceflow(i,kap,kall)
```

This `vm_dem_feed` flows downstream to Module 16 (Demand), which aggregates all commodity demands for Module 21 (Trade). It is NOT directly consumed by Module 71.

**On the Module 71 side**: Module 71 does not receive `vm_dem_feed` directly. Instead it uses `im_feed_baskets` and `vm_feed_balanceflow` to enforce that the spatial distribution of `vm_prod(j,kli_rum)` is consistent with local forage availability. The link is therefore:

```
Module 70 computes  vm_prod_reg(i,kli)        [regional total]
                    im_feed_baskets(...)       [feed composition]
                    vm_feed_balanceflow(...)   [balance correction]
                                  |
                                  v
Module 71 constrains vm_prod(j,kli_rum)        [cellular allocation]
          using forage availability at cell j
```

`vm_prod(j,kli)` is the shared cellular production variable that both modules touch — Module 70 sets it at regional level via `vm_prod_reg`, and Module 71 constrains its spatial allocation via forage constraints.

---

## Key Equations (foragebased_jul23, 6 total)

### q71_feed_rum_liv — Ruminant Forage Production Constraint

Ensures local forage production in each cell meets ruminant requirements:

```
vm_prod(j,kforage) >= v71_feed_forage(j,kforage) + v71_feed_balanceflow(j,kforage)
```

Inequality: cells can produce excess forage. Separate constraints for pasture and foddr.
Source: `module_71.md`, `equations.gms:14-17`

### q71_feed_forage — Forage Feed Requirements

Calculates how much forage each cell needs, using regional feed baskets:

```
sum(kforage) v71_feed_forage(j,kforage) =
    sum(kli_rum,kforage) [ vm_prod(j,kli_rum) * im_feed_baskets(t,i,kli_rum,kforage) ]
```

Feed baskets are regional parameters from Module 70 — there are no cell-specific feed baskets.
Source: `module_71.md`, `equations.gms:21-24`

### q71_feed_balanceflow_nlp — Balance Flow Distribution (NLP, default)

Active when `s71_lp_fix = 0` (default). Distributes the regional balance flow from Module 70 to cells in proportion to each cell's share of regional ruminant production:

```
sum(kforage) v71_feed_balanceflow(j,kforage) =
    sum(ct,cell(i,j),kli_rum,kforage) [
        vm_feed_balanceflow(i,kli_rum,kforage)
        * (vm_prod(j,kli_rum) / vm_prod_reg(i,kli_rum))
    ]
```

The division makes this nonlinear — CONOPT required. Division-by-zero is prevented by `vm_prod_reg.lo(i,kli_rum) = 1e-6` (preloop.gms:17).
Source: `module_71.md`, `equations.gms:34-37`

### q71_feed_balanceflow_lp — Balance Flow Distribution (LP warmstart)

Active when `s71_lp_fix = 1` (set by Module 80 during LP phase). Drops the division and allows balance flow to distribute freely among cells:

```
sum(cell(i,j),kforage) v71_feed_balanceflow(j,kforage) =
    sum(ct,kli_rum,kforage) vm_feed_balanceflow(i,kli_rum,kforage)
```

Mutually exclusive with `q71_feed_balanceflow_nlp`.
Source: `module_71.md`, `equations.gms:44-46`

### q71_prod_mon_liv — Monogastric Distribution

Upper-bounds monogastric production in each cell by urban area share (plus slack):

```
vm_prod(j,kli_mon) <= i71_urban_area_share(j) * s71_scale_mon * vm_prod_reg(i,kli_mon)
                      + v71_additional_mon(j,kli_mon)
```

`s71_scale_mon = 1.10` (default) allows 10% overcapacity.
Source: `module_71.md`, `equations.gms:55-59`

### q71_punishment_mon — Monogastric Penalty Cost

Penalizes overcapacity production at 15,000 USD17MER per tDM:

```
vm_costs_additional_mon(i) = sum(cell(i,j),kli_mon) v71_additional_mon(j,kli_mon)
                              * s71_punish_additional_mon
```

Passed to Module 11 (Costs).
Source: `module_71.md`, `equations.gms:66-69`

---

## Key Variables Summary

| Variable | Type | Dimensions | Units | Role |
|---|---|---|---|---|
| `vm_prod(j,kli)` | Optimized interface | cell x livestock | mio. tDM/yr | Cellular livestock production — constrained by M71, aggregated to regional `vm_prod_reg` |
| `vm_prod_reg(i,kli)` | Optimized interface | region x livestock | mio. tDM/yr | Regional total; denominator in NLP balance flow equation |
| `im_feed_baskets(t,i,kli,kall)` | Parameter from M70 | time x region x livestock x feed | tDM feed / tDM product | Converts production to forage requirement |
| `vm_feed_balanceflow(i,kli_rum,kforage)` | Interface from M70 | region x ruminant x forage | mio. tDM/yr | Regional correction term; distributed to cells in M71 |
| `vm_dem_feed(i,kap,kall)` | Interface from M70 | region x livestock x feed | mio. tDM/yr | Regional feed demand computed by M70; NOT consumed by M71 — passes to M16 |
| `v71_feed_forage(j,kforage)` | Endogenous | cell x forage | mio. tDM/yr | Cell-level forage requirement for ruminants |
| `v71_feed_balanceflow(j,kforage)` | Endogenous | cell x forage | mio. tDM/yr | Cellular balance flow allocation |
| `v71_additional_mon(j,kli_mon)` | Slack | cell x monogastric | mio. tDM/yr | Excess monogastric production beyond urban constraint |
| `vm_costs_additional_mon(i)` | Interface to M11 | region | mio. USD17MER/yr | Penalty cost for monogastric overcapacity |
| `i71_urban_area_share(j)` | Parameter | cell | fraction | Cell's share of regional urban area; static (uses `pm_land_start`) |

---

## Configuration Scalars

| Scalar | Default | Effect |
|---|---|---|
| `s71_lp_fix` | 0 | 0 = NLP mode (`q71_feed_balanceflow_nlp`); 1 = LP mode (`q71_feed_balanceflow_lp`). Toggled by Module 80. |
| `s71_scale_mon` | 1.10 | Monogastric flexibility; 1.10 allows 10% overcapacity relative to urban area share |
| `s71_punish_additional_mon` | 15,000 | USD17MER/tDM penalty for excess monogastric production |

---

## Key Limitations

- Monogastrics are not constrained by feed availability — only by urban area. Concentrate feeds are assumed fully tradeable.
- Crop residues are excluded from ruminant forage constraints.
- Urban area shares are static (use `pm_land_start`, not dynamic Module 34 urbanization).
- Regional feed baskets from Module 70 are applied uniformly across all cells within a region — no cell-level heterogeneity in feed conversion.
- Forage is treated as strictly non-transportable between cells (no local hay/silage trade).

---

## Source

All claims based on:
- 🟡 `magpie-agent/modules/module_71.md` (verified 2025-10-13 against MAgPIE develop commit 96d1a59a8)
- 🟡 `magpie-agent/modules/module_70.md`

Epistemic status: 🟡 **Documented** — read from official AI documentation this session. Not re-verified against raw GAMS source code this session (would be 🟢 Verified). For high-stakes code modification, verify equation formulas directly in `../modules/71_disagg_lvst/foragebased_jul23/equations.gms` and `../modules/70_livestock/fbask_jan16/equations.gms`.
