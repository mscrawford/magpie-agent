# Q2 Answer: Feed Demand Cascade — Module 70 to Crop/Pasture Land

**Docs-only answer** (no raw .gms files read this session). All claims tagged 🟡 (documented) unless otherwise noted.

---

## (a) Default Feed-Basket Realization of Module 70 and Where It Is Set

**Default realization**: `fbask_jan16`

**Set in**: `config/default.cfg` line 2146:
```
cfg$gms$livestock <- "fbask_jan16"   # def = fbask_jan16
```
🟡 module_70.md:12-13 ("Default Realization: `fbask_jan16` … Confirmed in `config/default.cfg`: `cfg$gms$livestock <- 'fbask_jan16'`")

The alternative realization `fbask_jan16_sticky` adds a sticky capital-stock mechanism but does not change the feed-basket structure; it is not the default.

---

## (b) Parameter Holding the Feed Baskets and Variable Carrying Feed Demand into Crop Demand

### Feed basket parameter: `im_feed_baskets(ct,i,kap,kall)`

The raw scenario-specific input is read from file as:
```
f70_feed_baskets(t_all,i,kap,kall,feed_scen70)
```
🟡 module_70.md:333-349 (`input.gms:36-39`)

In preloop, the scenario slice is selected and SCP substitutions applied to produce the working parameter:
```
im_feed_baskets(t,i,kap,kall)
```
🟡 module_70.md:343-345 (`preloop.gms:13-23`)

**Dimensions**: time × region × livestock product (kap) × all feed items (kall) — units tDM feed per tDM product.

Historical period (≤ `sm_fix_SSP2`) always uses SSP2 baskets; the future trajectory is selected by `c70_feed_scen` (default `"ssp2"`) 🟡 module_70.md:343-345.

### Interface variable carrying feed demand: `vm_dem_feed(i,kap,kall)`

Defined by equation `q70_feed` (`equations.gms:17-20`):
```gams
vm_dem_feed(i2,kap,kall) =g=
    vm_prod_reg(i2,kap) * sum(ct, im_feed_baskets(ct,i2,kap,kall))
    + sum(ct, vm_feed_balanceflow(i2,kap,kall))
```
🟡 module_70.md:80-95

The inequality (≥) means feed demand must be at least production × feed basket plus balance flows (which can include negative scavenging adjustments for ruminant pasture).

`vm_dem_feed` is the variable that leaves Module 70 and enters Module 16 (Demand) 🟡 module_70.md:687-692 (`declarations.gms:11`; `module.gms:18`).

---

## (c) How Feed Demand Reaches Module 30 (Cropland/Croparea) and Module 31 (Pasture), and How Module 14 Yields Mediate Land

### The routing chain: M70 → M16 → M21 → M17 → M30/M31

Feed demand does **not** flow directly from Module 70 to Module 30 or Module 31. The route is transitive through three hubs:

**Step 1 — Module 16 aggregates into `vm_supply`.**

For crops, Module 16 (`sector_may15`, the only realization) sums `vm_dem_feed` across all livestock types into crop supply via `q16_supply_crops` (`equations.gms:19-29`):
```gams
vm_supply(i2,kcr) =e=
    vm_dem_food(i2,kcr)
    + sum(kap4, vm_dem_feed(i2,kap4,kcr))
    + vm_dem_processing(i2,kcr) + ...
```
🟡 module_16.md:66-97

For pasture, Module 16 has an even simpler equation `q16_supply_pasture` (`equations.gms:62-63`):
```gams
vm_supply(i2,"pasture") =e= sum(kap4, vm_dem_feed(i2,kap4,"pasture"))
```
🟡 module_16.md:190-200

Pasture supply is therefore the regional sum of pasture feed demand across all livestock types — with no food, seed, waste, or balanceflow terms.

**Step 2 — Module 21 (Trade) creates the global supply-demand balance.**

`vm_supply` enters Module 21 which calculates trade flows and creates `vm_prod_reg(i,kall)` — the regional production level required to meet net demand after trade. This is the variable Module 17 then enforces 🟡 module_70.md:1143-1151.

**Step 3 — Module 17 (Production) provides `vm_prod_reg` back to Module 70.**

`vm_prod_reg(i,kap)` (regional livestock production) is what drives the feed demand equation in Module 70 in the first place (`q70_feed`). This creates the circular dependency: M70 → M16 → M21 → M17 → M70. The solver finds the simultaneous equilibrium 🟡 module_70.md:1147-1151.

### How feed demand reaches Module 30 (Croparea)

For crop feed items (cereals, fodder, oilseeds, etc.), `vm_dem_feed` adds to crop supply requirements via `q16_supply_crops`. This flows through Module 21 into regional crop production requirements, which Module 30 (`simple_apr24`, `config/default.cfg` line 896) satisfies via:

```gams
q30_prod(j2,kcr) ..
  vm_prod(j2,kcr) =e= sum(w, vm_area(j2,kcr,w) * vm_yld(j2,kcr,w))
```
🟡 module_30.md:61-80 (`simple_apr24/equations.gms:14-15`)

The optimization allocates `vm_area(j,kcr,w)` (crop area) until the production constraint can be met. Higher feed demand → higher required production → potentially more cropland, depending on yields.

### How feed demand reaches Module 31 (Pasture)

For the "pasture" feed item, the routing is analogous but simpler because `q16_supply_pasture` has only the feed term. The resulting production requirement is enforced by Module 31 (`endo_jun13`, `config/default.cfg` line 969) via an inequality:

```gams
q31_prod(j2) ..
  vm_prod(j2,"pasture") =l= vm_land(j2,"past") * vm_yld(j2,"pasture","rainfed")
```
🟡 module_31.md:85-111 (`equations.gms:16-18`)

The optimizer expands `vm_land(j,"past")` (pasture area, a decision variable from Module 10) until this inequality is satisfied at minimum cost. Higher pasture feed demand → higher required pasture production → more pasture land needed (all else equal).

### How Module 14 Yields Mediate Land Required

**For crops** (`managementcalib_aug19`, `config/default.cfg` line 354), `vm_yld(j,kcr,w)` is set by:
```gams
q14_yield_crop(j2,kcr,w) ..
  vm_yld(j2,kcr,w) =e=
    sum(ct, i14_yields_calib(ct,j2,kcr,w))
    * vm_tau(j2,"crop") / sum((cell(i2,j2), supreg(h2,i2)), fm_tau1995(h2))
```
🟡 module_14.md:41-79 (`equations.gms:14-16`)

`i14_yields_calib` is a preloop-computed parameter (LPJmL biophysical baseline calibrated to FAO regional statistics); `vm_tau` is the Module 13 technological change factor. For a given production target, a higher yield means less land needed (area = production / yield).

**For pasture**, `vm_yld(j,"pasture","rainfed")` is set by:
```gams
q14_yield_past(j2,w) ..
  vm_yld(j2,"pasture",w) =e=
    sum(ct, i14_yields_calib(ct,j2,"pasture",w)
    * sum(cell(i2,j2), pm_past_mngmnt_factor(ct,i2)))
    * (1 + s14_yld_past_switch * (sum(..., pcm_tau(j2,"crop") / fm_tau1995(h2)) - 1))
```
🟡 module_14.md:83-121 (`equations.gms:35-39`)

Three components drive pasture yield:
1. **Calibrated LPJmL baseline** `i14_yields_calib` (pasture-management-corrected)
2. **`pm_past_mngmnt_factor(ct,i)`** — an exogenous intensification factor calculated in Module 70's presolve from cattle stock change proxies (`presolve.gms:23-70`), then consumed by Module 14 🟡 module_70.md:538-542; module_14.md:109-111
3. **Spillover from crop intensification** controlled by `s14_yld_past_switch` (default 0.25 = 25% of crop τ improvement benefits pasture) 🟡 module_14.md:110-113; `input.gms:20`

This means Module 70 provides `pm_past_mngmnt_factor` to Module 14, which in turn scales pasture yields that Module 31 uses to determine how much land is needed. It is the one direct M70→M14 interface 🟡 module_14.md:740-742 (`equations.gms:38`).

### Summary cascade (default configuration)

```
M70 fbask_jan16: vm_prod_reg × im_feed_baskets → vm_dem_feed(i,kap,kall)  [q70_feed]
                                                           |
                        M16 sector_may15: q16_supply_crops / q16_supply_pasture
                              → vm_supply(i,kcr) and vm_supply(i,"pasture")
                                                           |
                                          M21 Trade: → vm_prod_reg(i,kall)
                                                           |
             For crops:                                         For pasture:
             M30 simple_apr24: q30_prod                         M31 endo_jun13: q31_prod
             vm_prod(j,kcr) = vm_area × vm_yld                vm_prod(j,"pasture") ≤ vm_land × vm_yld
                    ^                                                    ^
                    |__________ M14 managementcalib_aug19 ______________|
                                    q14_yield_crop                  q14_yield_past
                                    (LPJmL × τ)              (LPJmL × pm_past_mngmnt_factor × τ-spillover)
                                                                           ^
                                                M70 presolve: pm_past_mngmnt_factor
                                                (cattle-stock proxy → pasture intensification)
```

---

## Closing Source Statement

Claims sourced from:

- `<magpie-agent>/modules/module_70.md` (🟡 documented; last verified 2026-03-06)
- `<magpie-agent>/modules/module_16.md` (🟡 documented)
- `<magpie-agent>/modules/module_30.md` (🟡 documented; status 100% verified)
- `<magpie-agent>/modules/module_31.md` (🟡 documented; last verified 2025-10-13)
- `<magpie-agent>/modules/module_14.md` (🟡 documented; status fully verified 2025-10-12)
- `<magpie-root>/config/default.cfg` (default realization confirmations — lines 354, 896, 969, 2146)

No raw GAMS `.gms` files were read this session. Line-number citations within module docs were verified at each module's "Last Verified" date and may have shifted since then. For critical work, verify against current code.
