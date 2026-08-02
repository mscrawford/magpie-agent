# R60 depth audit — `cross_module/water_balance_conservation.md`

**Lens**: `declare_populate` (enter from the declaring/populating side; verify which module DECLARES vs POPULATES each interface var, and whether equation bodies match the doc's attributed formulas)
**Ground truth**: MAgPIE `develop` read-only worktree
**Auditor mode**: adversarial, depth-first
**Claims verified**: 53
**Bugs found**: 6 (4 Major, 2 Minor) — all confirmed with reproducible commands

---

## What checked out clean (the doc is largely accurate)

The declare/populate spine of this doc is correct, which is worth stating explicitly because
that is exactly what this lens attacks:

| Claim | Verdict |
|---|---|
| `q43_water(j2) .. sum(wat_dem,vm_watdem(...)) =l= sum(wat_src,v43_watavail(...))` at `modules/43_water_availability/total_water_aug13/equations.gms:10-11` | ✅ byte-exact |
| `vm_watdem` DECLARED in module 42 (`modules/42_water_demand/all_sectors_aug13/declarations.gms:29`) | ✅ |
| `vm_watdem` POPULATED **only** by module 42 (eq. LHS for `"agriculture"`, `.fx` for the rest); module 43 only READS it | ✅ whole-tree grep: module 43's two hits are `vm_watdem.lo(...)` on the **RHS** of `presolve.gms:15-16`. (The role map lists `populated_by: ["42","43"]` — that "43" is a heuristic false positive from the `.lo` read inside a `.fx` assignment. Code wins; the doc is right.) |
| `im_wat_avail` DECLARED + POPULATED in module 43 (`declarations.gms:9`, `preloop.gms:8-12`), READ by module 42 (`presolve.gms:58,64`) | ✅ direction confirmed at both endpoints |
| `v43_watavail`, `q43_water` declared in module 43 | ✅ |
| Buffer at `modules/43_water_availability/total_water_aug13/presolve.gms:14-16`, incl. the `vm_watdem.lo` / `watdem_exo` / `*1.01` details | ✅ byte-exact |
| `wat_dem` = 5 members, `wat_src` = 4 members, exact labels | ✅ `core/sets.gms:244,247` |
| `watdem_exo` = domestic, manufacturing, electricity, ecosystem | ✅ `modules/42_water_demand/all_sectors_aug13/sets.gms:9-10` |
| `q42_water_demand` body and `q42_water_cost` body as quoted | ✅ `equations.gms:10-14`, `16-17` |
| Ecosystem `.fx` formula at `presolve.gms:87-88` | ✅ byte-exact |
| `s42_irrig_eff_scenario` default 2; flat `0.66` only under scenario 1 | ✅ `input.gms:14,19` + `config/default.cfg:1363,1367` |
| `s42_env_flow_scenario` default 2, options 0/1/2 as described; `s42_env_flow_fraction = 0.2`; base 0.05 | ✅ `input.gms:22,37,38` + `default.cfg:1401` |
| EFP ramp 2025→2040 | ✅ `input.gms:35-36` + `default.cfg:1379,1381` |
| "default: all ISO countries — the full **249**-member `iso` set" | ✅ counted: `EFP_countries` = 249, core `iso` = 249, set difference empty **both ways** |
| `c43_watavail_scenario` default `cc`, options cc/nocc/nocc_hist | ✅ `input.gms:9-12` + `default.cfg:1433` |
| `s42_watdem_nonagr_scenario` default 2 = SSP2 | ✅ |
| "~200 MAgPIE cells" | ✅ `default.cfg:26` cellular input is `…_c200_…` |
| `vm_AEI(j)` exists in module 41 (both realizations); module 41 default `endo_apr13` | ✅ |
| Realization directory names `all_sectors_aug13`, `total_water_aug13` | ✅ `ls` of both module dirs |
| Land set = 7 pools | ✅ `core/sets.gms:250-251` |

---

## BUG-01 — `vm_prod(j,kli)` attributed to modules 17 and 70; module 70 never touches it and module 71 is the real determinant

**Severity**: Major · **Class**: `attribution_populate`
**Doc lines**: `water_balance_conservation.md:420` (§6.5 heading), `:430`, `:910` (§11.3 Module Roles table)

**Doc says**

> ### 6.5 Module 17 (Production) and Module 70 (Livestock)
> **Role**: Calculate production including livestock water demand
> …
> - `vm_prod(j,kli)`: Livestock production from Module 17 (Mt DM/yr)

and in the Module Roles table:

> | 17, 70 | Livestock production (contributes to agricultural demand) | vm_prod(j,kli) |

**Reality in code**

- `vm_prod(j,k)` is **DECLARED** in module 17 — `modules/17_production/flexreg_apr16/declarations.gms:9`
  (`Production in each cell (mio. tDM per yr)`).
- Module 17 does **not** determine the livestock slice. Its only equation is the cell→region
  aggregation `vm_prod_reg(i2,k) =e= sum(cell(i2,j2), vm_prod(j2,k))`
  (`modules/17_production/flexreg_apr16/equations.gms:11`), plus a starting-level assignment
  `vm_prod.l(j,kcr) = pm_prod_init(j,kcr)` restricted to **`kcr`** (`presolve.gms:15`).
- **Module 70 never references `vm_prod` at all.** It works exclusively on the regional
  aggregate `vm_prod_reg`. Grep for `vm_prod(` and `vm_prod.` across
  `modules/70_livestock/` returns nothing, with a positive control proving the search works
  in that directory (6 hits for `vm_prod_reg` in the same file).
- The module that actually pins the **cellular livestock** slice is **71 (`disagg_lvst`,
  default `foragebased_jul23`)**: `q71_prod_mon_liv` bounds `vm_prod(j2,kli_mon)`
  (`modules/71_disagg_lvst/foragebased_jul23/equations.gms:55-59`) and `q71_feed_forage` /
  `q71_feed_rum_liv` constrain `vm_prod(j2,kli_rum)` against cellular forage supply
  (`equations.gms:14-17,21-24`). The doc never mentions module 71.

**verify_cmd**

```
rg -n "vm_prod\(|vm_prod\." modules/70_livestock/
  -> (no matches)
rg -c "vm_prod_reg" modules/70_livestock/fbask_jan16/equations.gms
  -> 6                      # positive control: the grep does work in this dir
rg -n "vm_prod" modules/17_production/flexreg_apr16/{declarations,equations,presolve}.gms
  -> declarations.gms:9  vm_prod(j,k)  Production in each cell (mio. tDM per yr)
     equations.gms:11    vm_prod_reg(i2,k) =e= sum(cell(i2,j2), vm_prod(j2,k));
     presolve.gms:15     vm_prod.l(j,kcr) = pm_prod_init(j,kcr);
rg -n "vm_prod\(" modules/71_disagg_lvst/foragebased_jul23/equations.gms
  -> 15, 23, 37, 56
rg -n "cfg\$gms\$disagg_lvst" config/default.cfg
  -> 2221: cfg$gms$disagg_lvst <- "foragebased_jul23"   # def = foragebased_jul23
```

Role map agrees: `vm_prod → declared_in 17_production, populated_by [30,31,71,73]` — **17 and 70
are both absent from the populator list**.

**Proposed fix**

- §6.5 heading → `### 6.5 Modules 17 / 71 (Production and its cellular livestock disaggregation)`.
- Line 430 → ``- `vm_prod(j,kli)`: cellular livestock production (mio. tDM/yr). DECLARED in module 17 (`modules/17_production/flexreg_apr16/declarations.gms:9`); module 17 only aggregates it to `vm_prod_reg` (`equations.gms:11`). The cellular livestock slice is pinned by module 71 (`disagg_lvst`, default `foragebased_jul23`) — `q71_prod_mon_liv` for monogastrics (`equations.gms:55-59`) and the forage-balance equations for ruminants (`equations.gms:14-17,21-24`).``
- §11.3 table row → `| 17 (declares), 71 (disaggregates to cells) | Cellular livestock production feeding agricultural water demand | vm_prod(j,kli) |` and drop module 70 from that row (module 70 sets feed baskets on `vm_prod_reg`, not `vm_prod`).

---

## BUG-02 — `oq43_water.level` is not a thing, and the sign of the claimed "surplus" is inverted

**Severity**: Major · **Class**: `formula`
**Doc lines**: `water_balance_conservation.md:211-212` (and the same symbol in the R recipes at `:667`, `:860`)

**Doc says**

> **Implications of Inequality**:
> 1. **Surplus water allowed**: Not all renewable water must be used
> 2. **Surplus variable**: `oq43_water.level` = available - withdrawals (≥ 0)
> 3. **Shadow price only when binding**: `oq43_water.marginal` > 0 only if constraint tight

**Reality in code**

1. `oq43_water` is a **parameter with an explicit `type` dimension**, not a variable/equation with
   GAMS attributes: `oq43_water(t,j,type)` at
   `modules/43_water_availability/total_water_aug13/declarations.gms:23`. `oq43_water.level` /
   `oq43_water.marginal` are not valid access paths in GAMS or in the GDX. The correct forms are
   `oq43_water(t,j,"level")` and `oq43_water(t,j,"marginal")`
   (`postsolve.gms:11,13`). magpie4 does exactly this: `readGDX(gdx, "oq43_water", "oq_water",
   format = "first_found")[, , "marginal"]` (magpie4 `R/water_price.R:25`).
2. What is stored under `"level"` is the **equation row activity**, not a surplus:
   `oq43_water(t,j,"level") = q43_water.l(j)` (`postsolve.gms:13`). Because `q43_water` is written
   `sum(wat_dem,vm_watdem(...)) =l= sum(wat_src,v43_watavail(...))` (`equations.gms:10-11`), the
   row normalizes to `withdrawals − availability =l= 0`, so its level is
   **withdrawals − availability ≤ 0** — the *negative* of the doc's quantity. A reader following the
   doc would compute surplus with the wrong sign and classify water-abundant cells as violations.
3. There is no "surplus variable" in the model at all. The unused-water slack is only recoverable
   as `−oq43_water(t,j,"level")` (or via `q43_water.slackup` inside GAMS).

**verify_cmd**

```
rg -n "oq43_water" modules/43_water_availability/
  -> total_water_aug13/declarations.gms:23:  oq43_water(t,j,type)  Local seasonal water constraints (mio. m^3 per yr)
     total_water_aug13/postsolve.gms:11:     oq43_water(t,j,"marginal") = q43_water.m(j);
     total_water_aug13/postsolve.gms:13:     oq43_water(t,j,"level")    = q43_water.l(j);
     total_water_aug13/postsolve.gms:15/17:  "upper"/"lower" = q43_water.up/.lo(j);
rg -n "oq43_water" <magpie4 clone>/R/
  -> R/water_price.R:25: readGDX(gdx,"oq43_water","oq_water",format="first_found")[, , "marginal"]
```

The object-type error is directly evidenced above; the sign follows from the `=l=` orientation in
`equations.gms:11` under GAMS row-activity semantics (variable terms moved left, constants right).

**Proposed fix**

Replace items 2-3 with:

> 2. **Unused water is a row slack, not a variable**: `oq43_water(t,j,"level")` stores the equation's
>    row activity `q43_water.l` = *withdrawals − availability* (≤ 0 by construction,
>    `modules/43_water_availability/total_water_aug13/postsolve.gms:13`). Unused water is therefore
>    `−oq43_water(t,j,"level")`; there is no dedicated surplus variable.
> 3. **Shadow price only when binding**: `oq43_water(t,j,"marginal")` ≠ 0 only if the constraint is tight
>    (`postsolve.gms:11`).

In the R recipes at `:667` and `:860`, drop the bogus `field="level"` argument (`field` applies to
variables/equations, not to this parameter) and use the magpie4-canonical read:
`shadow_price <- readGDX(gdx, "oq43_water", "oq_water", format = "first_found")[, , "marginal"]`.

---

## BUG-03 — the Environmental-Flow-Protection ramp is described without its default, which is OFF

**Severity**: Major · **Class**: `default_value`
**Doc lines**: `water_balance_conservation.md:101-105` (§2.3), `:531-545` (§7.4 mechanism + timeline), `:552-555` (§7.4 policy modes)

**Doc says**

> **Environmental Flow Protection (EFP) Policy** (Module 42, `…/input.gms:35-36`):
> - Linear ramp-up from 2025 (0%) to 2040 (100%)
> …
> **Mechanism**: 1. EFP policy ramps up 2025-2040 (linear increase from 0% to 100%) 2. Ecosystem water
> demand increases over time 3. Less water available for human use
> …
> **Policy Modes** (Module 42, `…/input.gms:122`):
> - `off`: No EFP (base protection only, 5%)
> - `on`: Full EFP (all countries)
> - `mixed`: Development-state dependent (high-income countries only)

**Reality in code**

`c42_env_flow_policy` **defaults to `off`**:
- `$setglobal c42_env_flow_policy  off` — `modules/42_water_demand/all_sectors_aug13/input.gms:122`
- `cfg$gms$c42_env_flow_policy <- "off"   # def = "off"` — `config/default.cfg:1373`

and under `off` the fader is identically zero: `p42_efp(t_all,"off") = 0`
(`modules/42_water_demand/all_sectors_aug13/preloop.gms:15`). Following the chain,
`i42_env_flow_policy(t,i) = p42_efp(t,"off")·shr + p42_efp(t,"off")·(1−shr) = 0`
(`presolve.gms:81-82`), hence
`vm_watdem.fx("ecosystem",j) = i42_env_flows_base(t,j)` = `s42_env_flow_base_fraction (0.05) ×
sum(wat_src, im_wat_avail)` (`presolve.gms:58,87-88`).

**In a default run the 2025→2040 ramp never engages and ecosystem demand is pinned at the flat 5%
base fraction for all years.** The doc marks defaults explicitly for the three neighbouring switches
(`SSP2 … - DEFAULT` at `:78`, `Scenario 2 … - DEFAULT` at `:99`, `cc … - DEFAULT` at `:139`) but not
for this one — the conspicuous omission invites the reader to assume the ramp is live.

Secondary, same lines: `mixed` is **not** "high-income countries only" — it scales EFP by the
continuous development-state index, `i42_env_flow_policy(t,i) = im_development_state(t,i) ·
p42_efp(t,"on") · p42_EFP_region_shr(t,i) + …` (`presolve.gms:78-79`).

**verify_cmd**

```
rg -n "c42_env_flow_policy" modules/42_water_demand/all_sectors_aug13/input.gms config/default.cfg
  -> input.gms:122:  $setglobal c42_env_flow_policy  off
     default.cfg:1373: cfg$gms$c42_env_flow_policy <- "off"   # def = "off"
rg -n "p42_efp" modules/42_water_demand/all_sectors_aug13/preloop.gms
  -> 15: p42_efp(t_all,"off") = 0;
     16: m_linear_time_interpol(p42_efp_fader, s42_efp_startyear, s42_efp_targetyear, 0, 1);
     17: p42_efp(t_all, "on") = p42_efp_fader(t_all);
```

**Proposed fix**

- §2.3, before the ramp bullets, insert: `**Default: OFF.** `c42_env_flow_policy` defaults to `off`
  (`modules/42_water_demand/all_sectors_aug13/input.gms:122`; `config/default.cfg:1373`), and
  `p42_efp(t,"off") = 0` (`preloop.gms:15`), so in a default run `vm_watdem.fx("ecosystem",j)` stays at
  the flat 5 % base fraction `s42_env_flow_base_fraction` and the ramp below never engages. The
  ramp applies only when the switch is set to `on` or `mixed`.`
- §7.4 opening line: `**Applies only when `c42_env_flow_policy` is set to `on` or `mixed` (default: `off`).**`
- §7.4 policy-mode list: mark `off` as `- DEFAULT`, and reword `mixed` to
  `` `mixed`: EFP weighted by the continuous development-state index `im_development_state` (presolve.gms:78-79) — not a binary HIC-only switch ``.

---

## BUG-04 — "No feedback from Module 43 water constraint to Module 41 investment" is false under the simultaneous solve

**Severity**: Major · **Class**: `mechanism`
**Doc lines**: `water_balance_conservation.md:411-416` (§6.4 Known Limitation)

**Doc says**

> **Known Limitation** (Module 41):
> - AEI expansion decisions do not account for future water scarcity
> - May over-invest in irrigation infrastructure that cannot be fully utilized
> - No feedback from Module 43 water constraint to Module 41 investment

**Reality in code**

MAgPIE solves **one simultaneous model per time step** containing all module equations:
`model magpie / all - m15_food_demand /;` (`main.gms:279`). Within that model, `vm_AEI` is coupled to
the water constraint by a two-hop equation chain, all in the same solve:

1. `q41_area_irrig(j2) .. sum(kcr, vm_area(j2,kcr,"irrigated")) =l= vm_AEI(j2);`
   — `modules/41_area_equipped_for_irrigation/endo_apr13/equations.gms:10-11`
2. `q42_water_demand("agriculture",j2) .. vm_watdem("agriculture",j2)*v42_irrig_eff(j2) =e= sum(kcr, vm_area(j2,kcr,"irrigated")*ic42_wat_req_k(j2,kcr)) + …`
   — `modules/42_water_demand/all_sectors_aug13/equations.gms:10-14`
3. `q43_water(j2) .. sum(wat_dem,vm_watdem(...)) =l= sum(wat_src,v43_watavail(...));`
   — `modules/43_water_availability/total_water_aug13/equations.gms:10-11`

and `vm_AEI` carries a cost into the objective through
`q41_cost_AEI(i2) .. vm_cost_AEI(i2) =e= sum(cell(i2,j2),(vm_AEI(j2)-pc41_AEI_start(j2))) * …`
(`endo_apr13/equations.gms:19-23`). So when `q43_water` binds, `q41_area_irrig` goes slack and
expanding `vm_AEI` buys nothing while still costing money — the water constraint **does** feed back
into AEI investment, through exactly the shadow-price channel the doc itself credits for module 30
two sections earlier (`:390-392`: "Module 30 responds indirectly via shadow prices in objective
function"). The doc is internally inconsistent.

What *is* genuinely absent: (a) any explicit water term inside module 41's own equations, and
(b) intertemporal foresight — MAgPIE is recursive-dynamic, and with the default
`s41_AEI_depreciation = 0` (`endo_apr13/input.gms:11`; `config/default.cfg:1332`) the presolve bound
`vm_AEI.lo(j) = pc41_AEI_start(j) / ((1 - s41_AEI_depreciation)**(m_timestep_length))`
(`endo_apr13/presolve.gms:11`) ratchets AEI so it can never shrink. *That* is the real stranded-asset
mechanism, and it is a cross-period effect, not a missing within-period link.

**verify_cmd**

```
rg -n "^model|solve " main.gms
  -> 279: model magpie / all - m15_food_demand /;
cat -n modules/41_area_equipped_for_irrigation/endo_apr13/equations.gms
  -> 10-11: q41_area_irrig(j2) .. sum(kcr, vm_area(j2,kcr,"irrigated")) =l= vm_AEI(j2);
     19-23: q41_cost_AEI(i2) .. vm_cost_AEI(i2) =e= sum(cell(i2,j2),(vm_AEI(j2)-pc41_AEI_start(j2))) * …
cat -n modules/41_area_equipped_for_irrigation/endo_apr13/presolve.gms
  -> 11: vm_AEI.lo(j) = pc41_AEI_start(j) / ((1 - s41_AEI_depreciation)**(m_timestep_length));
rg -n "s41_AEI_depreciation" modules/41_.../endo_apr13/input.gms config/default.cfg
  -> input.gms:11: … / 0 /     default.cfg:1332: cfg$gms$s41_AEI_depreciation <- 0   # def = 0
```

**Proposed fix**

Replace the three bullets with:

> **Known Limitation** (Module 41):
> - Module 41's own equations contain no water term — `q41_area_irrig` and `q41_cost_AEI`
>   (`modules/41_area_equipped_for_irrigation/endo_apr13/equations.gms:10-11,19-23`) reference only
>   land and cost.
> - Within a time step there *is* feedback: `vm_AEI → vm_area → vm_watdem → q43_water` are all in the
>   same simultaneous solve (`main.gms:279`), so a binding water constraint suppresses AEI expansion
>   through the same shadow-price channel described for Module 30 in §6.3.
> - What is missing is **intertemporal** foresight: AEI built while water was plentiful cannot be
>   released later, because `vm_AEI.lo(j) = pc41_AEI_start(j)/((1-s41_AEI_depreciation)**m_timestep_length)`
>   (`presolve.gms:11`) with `s41_AEI_depreciation = 0` by default (`config/default.cfg:1332`) ratchets
>   the stock. This — not a missing within-period link — is what produces stranded AEI under
>   declining runoff.

---

## BUG-05 — `water_demand()` is not a magpie4 function

**Severity**: Major · **Class**: `other`
**Doc lines**: `water_balance_conservation.md:607`, `:842`

**Doc says**

```r
watdem <- water_demand(gdx, level="cell", water_source=FALSE)
```

used both in §8.1 (constraint-satisfaction check) and in §10.3 Step 2 (post-modification testing
protocol).

**Reality in code**

The renv-pinned magpie4 clone exports no `water_demand`. Water-related exports are:
`waterEFR, waterEFVarea, waterEFViolation, waterEFVratio, waterStress, waterStressRatio,
waterStressedPopulation, water_AAI, water_AEI, water_avail, water_efficiency, water_price,
water_usage` (NAMESPACE:297-309). The intended reader is **`water_usage()`**, whose signature is
`water_usage(gdx, file = NULL, level = "reg", users = NULL, sum = FALSE, seasonality = "total",
abstractiontype = "withdrawal", digits = 4)` (`R/water_usage.R:30-32`). There is no `water_source`
argument anywhere; sector-wise output is selected with `users = "sectors"`, and the doc's
growing-period framing (§8.4) requires `seasonality = "grper"`.

**verify_cmd**

```
rg -n "water" <magpie4 clone>/NAMESPACE
  -> export(waterEFR) … export(water_avail) … export(water_usage)      # no export(water_demand)
ls <magpie4 clone>/R/ | rg -i water
  -> … water_avail.R  water_efficiency.R  water_price.R  water_usage.R  # no water_demand.R
sed -n '30,32p' <magpie4 clone>/R/water_usage.R
  -> water_usage <- function(gdx, file = NULL, level = "reg", users = NULL,
                             sum = FALSE, seasonality = "total", abstractiontype = "withdrawal",
                             digits = 4)
```

**Proposed fix**

In both places replace with

```r
watdem <- magpie4::water_usage(gdx, level = "cell", users = "sectors",
                               seasonality = "grper", abstractiontype = "withdrawal", sum = FALSE)
```

and update the §8.1 prose that names the function.

---

## BUG-06 — the magpie4 water recipes assume the wrong return shape and the wrong unit

**Severity**: Minor · **Class**: `other`
**Doc lines**: `water_balance_conservation.md:611-612`, `:618`, `:622`, `:650`, `:654`, `:774`, `:847`

**Doc says**

```r
watavail <- water_avail(gdx, level="cell")
total_avail <- dimSums(watavail, dim=3.1)   # Sum over sources
…
print(paste("Maximum constraint violation:", max_violation, "mio. m³"))
stopifnot(max_violation < 0.01)
…
abundant_cells <- which(surplus > 100)   # > 100 mio. m³ surplus
…
surface_avail <- watavail[,,"surface",]
```

**Reality in code**

- `water_avail()` defaults to `sum = TRUE` (`R/water_avail.R:21-22`), and with `sum = TRUE` it collapses
  the source dimension (`x <- dimSums(x, dim = 3.1)`, `R/water_avail.R:36-38`). So the doc's later
  `dimSums(watavail, dim=3.1)` is applied to an already-collapsed object, and
  `watavail[,,"surface",]` at `:774` cannot resolve — the `wat_src` dimension no longer exists.
- Units: GAMS carries `mio. m^3 per yr` (`modules/43_water_availability/total_water_aug13/declarations.gms:9,13`;
  `modules/42_water_demand/all_sectors_aug13/declarations.gms:29`), but magpie4 converts on the way out —
  `# from mio m^3 to km^3 ; x <- x / 1000` (`R/water_avail.R:46-47`), and likewise
  `# convert from mio m^3 to km^3 ; outout <- outout / 1000` (`R/water_usage.R:245-246`). Every
  threshold and label in §8.1/§8.2/§10.3 is therefore off by 1000× against what these functions return.

**verify_cmd**

```
sed -n '21,22p;36,38p;46,47p' <magpie4 clone>/R/water_avail.R
  -> water_avail <- function(gdx, file = NULL, level = "reg", sources = NULL, sum = TRUE, digits = 4)
     if (sum) { x <- dimSums(x, dim = 3.1) }
     # from mio m^3 to km^3
     x <- x / 1000
rg -n "1000|km\^3" <magpie4 clone>/R/water_avail.R <magpie4 clone>/R/water_usage.R
  -> water_avail.R:14 (km^3), :46-47 (/1000); water_usage.R:22 (km^3/yr), :245-246 (/1000)
```

**Proposed fix**

- `watavail <- magpie4::water_avail(gdx, level = "cell", sum = FALSE)` everywhere (§8.1 `:611`,
  §9.2 Check 3 `:774`, §10.3 Step 2 `:847`), keeping the explicit `dimSums(..., dim = 3.1)`.
- Relabel every printed unit and threshold in §8.1, §8.2 and §10.3 to **km³** (magpie4's output unit),
  and add one line under §8.1: `Note: GAMS carries mio. m³ (declarations.gms:9,13,29); magpie4's
  water_avail()/water_usage() divide by 1000 and return km³ (R/water_avail.R:46-47,
  R/water_usage.R:245-246).` Adjust the tolerances accordingly (`0.01 mio. m³` → `1e-5 km³`).

---

## Deferred (not flagged — could not be settled, or judgment-level)

1. §6.1 `:344-347` describes default irrigation efficiency as a "GDP-based sigmoidal function" but
   omits that under the default `s42_irrig_eff_scenario = 2` the sigmoid is evaluated at
   `im_gdp_pc_mer("y1995",i)` (`presolve.gms:18`), i.e. frozen at 1995 GDP with no improvement over
   time (only scenario 3 uses `im_gdp_pc_mer(t,i)`). Nothing stated is false, so recorded as an
   enhancement rather than a bug.
2. §2.2 `:69-72` renders the SSP fixation with a placeholder `ssp_scenario` inside a ```gams fence;
   the code has three literal branches (`"ssp1"/"ssp2"/"ssp3"`, `presolve.gms:41,45,48,51`) and forces
   `"ssp2"` for `m_year(t) <= sm_fix_SSP2` regardless of the switch. Pseudocode-labeling nit, not
   flagged as a content error.
3. §11.4 `:921` "7 land types (all endogenous except urban)" — the 7-member `land` set is confirmed
   (`core/sets.gms:250-251`), but I did not audit module 34's realization to confirm the
   endogenous/exogenous split; out of scope for a water doc.
4. §4.3 `:229-232` "Does not model river basin agreements / inter-basin transfers / water markets" —
   a negative claim I confirmed only to the extent that no inter-cell water term appears in
   `q43_water`; I did not exhaustively grep for a transfer mechanism elsewhere.
5. Whether `readGDX(..., field = "level")` (doc `:667`, `:860`) errors or is silently ignored for a
   GDX **parameter** — I did not read the `gdx` package source. The corrected read is given in BUG-02
   regardless.

---

*Auditor note on method*: every absence claim in this report was cross-checked with a second method
plus a positive control (see BUG-01's `vm_prod_reg` control). Each grep probe was run as its own
standalone command to avoid the `find -exec ... +` / errexit truncation trap. `rg -n` was used
throughout (never `rg -r`, which is `--replace`).
