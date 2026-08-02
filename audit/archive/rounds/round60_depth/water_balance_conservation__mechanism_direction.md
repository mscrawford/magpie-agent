# Depth audit — `cross_module/water_balance_conservation.md`

**Lens**: `mechanism_direction` (equation bodies, cross-module data flow, causal direction,
serial-vs-parallel hand-offs, capability-vs-default, set membership/counts)
**Round**: R60 depth
**Ground truth**: MAgPIE `develop` read-only worktree (referred to below as `$DEV`) +
the renv-pinned magpie4 clone at `.cache/sources/magpie4/`
**Claims verified**: 47
**Bugs found**: 10 (0 Critical / 7 Major / 3 Minor)

All code paths below are repo-relative. `$DEV` = the read-only `develop` worktree root.

---

## Summary

The doc's **GAMS-side spine is in good shape**: `q43_water`, the `wat_dem` (5) / `wat_src` (4)
set counts, the four `im_wat_avail` assignments, the groundwater-buffer expression, every
`file.gms:LINE` citation I checked, the `s42_irrig_eff_scenario = 2` default, the
`s42_env_flow_scenario = 2` default, the 249-member `iso` set and the `~200` cluster count all
verify clean. The `im_wat_avail` 43→42 hand-off is a **genuine serial** hand-off (43 populates in
`preloop`, 42 reads in `presolve`) — not a false serial claim.

The defects cluster in three places the lens is built to find:

1. **Solver-output semantics are sign-inverted** (BUG-01, BUG-02). The doc asserts
   `oq43_water.marginal > 0` when the constraint binds and `oq43_water.level = available −
   withdrawals ≥ 0`. MAgPIE **minimizes** and `q43_water` is `=l=`, so both are the wrong sign.
   magpie4's own `water_price()` calls `abs()` on that marginal — decisive corroboration. The
   doc's own diagnostic `which(shadow_price > 0.01)` therefore returns **zero cells, always**.
2. **Two capability-vs-default omissions** (BUG-04 EFP, BUG-10 pumping costs). Under
   `config/default.cfg` the ecosystem water demand is the flat 5 % base fraction, *not* the
   cell-specific Smakhtin EFR the doc labels "DEFAULT"; and `vm_water_cost` is identically 0.
3. **One inverted mechanism claim** (BUG-03): "No feedback from Module 43 water constraint to
   Module 41 investment" is false *within* a time step — MAgPIE is one simultaneous NLP and the
   constraint chain `q43_water → q42_water_demand → q41_area_irrig → q41_cost_AEI → q11_cost_reg`
   is closed. The defensible version of the claim is inter-temporal myopia, which the doc's
   preceding bullet already states correctly.

Plus one attribution error (BUG-05: `vm_prod(j,kli)` given to modules 17 and 70; 17 declares and
reads, **71** determines the cell slice, 70 never references `vm_prod`), one fabricated magpie4
function (BUG-06: `water_demand()` does not exist), and a 1000× unit error in the verification
protocol (BUG-07: magpie4 returns km³, the doc labels and thresholds it as mio. m³).

---

## BUG-01 — `oq43_water.marginal` sign is inverted (Major, `mechanism`)

**Doc** `water_balance_conservation:213` (also `:675`, `:686`, `:860`):
> 3. **Shadow price only when binding**: `oq43_water.marginal` > 0 only if constraint tight

and `:675`
> `high_value_water <- which(shadow_price > 0.01)  # >$0.01/m³`

**Reality.** MAgPIE solves `MINIMIZING vm_cost_glo`
(`modules/80_optimization/nlp_apr17/solve.gms:34`) and `q43_water` is a `=l=` constraint
(`modules/43_water_availability/total_water_aug13/equations.gms:10-11`). Under the GAMS sign
convention, `=l=` equation marginals in a minimization are **non-positive**: relaxing the upper
bound lowers the objective. `postsolve.gms:11` stores the marginal verbatim with no sign flip
(`oq43_water(t,j,"marginal") = q43_water.m(j);`), so the GDX carries the negative value.

Decisive corroboration from the reporting layer: magpie4's `water_price()` reads exactly this
parameter and immediately takes the absolute value —

```r
p_water_cell <- readGDX(gdx, "oq43_water", "oq_water", format = "first_found")[, , "marginal"]
...
p_water_cell <- abs(p_water_cell)     # .cache/sources/magpie4/R/water_price.R:31
```

The `abs()` exists precisely because the raw marginal is negative where water is scarce.

**Consequence.** The doc's Section 8.3 diagnostic (`which(shadow_price > 0.01)`) and the
"Typical Values" table (`:682-686`, all positive $/m³) invert the sign. A user running the
Section 8.3 / Section 10.3 Step 4 protocol gets `Cells with scarce water: 0` in every run,
including runs where water is severely binding — a silent false negative in a verification
section.

**Evidence**
- `modules/80_optimization/nlp_apr17/solve.gms:34`
- `modules/43_water_availability/total_water_aug13/equations.gms:10-11`
- `modules/43_water_availability/total_water_aug13/postsolve.gms:11`
- `.cache/sources/magpie4/R/water_price.R:25,31`

**Fix.** Replace `:213` with: "`oq43_water.marginal` is **non-positive** (GAMS convention for a
`=l=` constraint in a minimization); it is `< 0` only where the constraint binds, and `0`
otherwise. Report the scarcity value as `abs(oq43_water.marginal)` — this is what
`magpie4::water_price()` does (`R/water_price.R:31`)." Change the Section 8.3 R code to
`shadow_price <- abs(...)` before the `> 0.01` filter (or use `water_price(gdx, level = "cell")`
directly), and mirror the change at `:860`.

---

## BUG-02 — `oq43_water.level` is described as a variable and with the wrong sign (Major, `formula`)

**Doc** `water_balance_conservation:211`:
> 2. **Surplus variable**: `oq43_water.level` = available - withdrawals (≥ 0)

**Reality.** `oq43_water` is an *equation* output parameter, not a variable:
`oq43_water(t,j,type)` is declared under "Local seasonal water constraints"
(`declarations.gms:23`) and its `"level"` slice stores the equation row activity
`q43_water.l(j)` (`postsolve.gms:13`). GAMS normalizes `f(x) =l= g(x)` by moving all variable
terms left, so the row activity of

```gams
q43_water(j2) .. sum(wat_dem,vm_watdem(wat_dem,j2)) =l= sum(wat_src,v43_watavail(wat_src,j2));
```

is `Σ vm_watdem − Σ v43_watavail`, i.e. **withdrawals − availability, bounded above by 0** — the
negative of what the doc states. `v43_watavail` is `.fx`-fixed in presolve
(`presolve.gms:8-11,14-16`), so there is no "surplus variable" anywhere in module 43; the surplus
only exists as the (non-positive) equation level or as the R-side difference the doc itself
computes correctly in Section 8.2 (`total_avail - total_demand`).

Note the two independent errors: "variable" (code-verified false — it is an equation level) and
the sign (follows from the equation orientation plus the GAMS row-activity convention).

**Evidence**
- `modules/43_water_availability/total_water_aug13/declarations.gms:16-18,23`
- `modules/43_water_availability/total_water_aug13/equations.gms:10-11`
- `modules/43_water_availability/total_water_aug13/postsolve.gms:13`
- `modules/43_water_availability/total_water_aug13/presolve.gms:8-11`

**Fix.** Replace `:211` with: "**Equation level** (not a variable): `oq43_water(t,j,'level')`
stores `q43_water.l`, the GAMS row activity `Σ vm_watdem − Σ v43_watavail` ≤ 0. The unused-water
surplus is therefore `-oq43_water(t,j,'level')`, or equivalently
`water_avail(gdx) - water_usage(gdx)` on the R side."

---

## BUG-03 — "No feedback from Module 43 water constraint to Module 41 investment" is false within a time step (Major, `mechanism`)

**Doc** `water_balance_conservation:414` (in "**Known Limitation** (Module 41)"):
> - No feedback from Module 43 water constraint to Module 41 investment

**Reality.** MAgPIE solves **all modules simultaneously** in one NLP per time step
(`modules/80_optimization/nlp_apr17/solve.gms:34`), and the constraint chain from the water
balance to AEI investment is closed inside that single solve:

| step | equation | file:line |
|---|---|---|
| water balance bounds total withdrawals | `q43_water(j2)` | `modules/43_water_availability/total_water_aug13/equations.gms:10-11` |
| agricultural withdrawal is tied to irrigated area | `q42_water_demand("agriculture",j2)` | `modules/42_water_demand/all_sectors_aug13/equations.gms:10-14` |
| irrigated area is bounded by AEI | `q41_area_irrig(j2)` | `modules/41_area_equipped_for_irrigation/endo_apr13/equations.gms:10-11` |
| AEI expansion is costed | `q41_cost_AEI(i2)` | `modules/41_area_equipped_for_irrigation/endo_apr13/equations.gms:19-23` |
| that cost enters the minimized objective | `q11_cost_reg` → `q11_cost_glo` | `modules/11_costs/default/equations.gms:29`, `:15`, `:10` |

`vm_AEI(j)` is a free positive decision variable (`endo_apr13/declarations.gms:19`) whose only
lower bound is last step's stock (`endo_apr13/presolve.gms:11`). So in a water-scarce cell the
optimizer has a direct, priced disincentive to expand AEI it cannot use — that *is* feedback from
the water constraint to AEI investment.

What is genuinely true, and is already the doc's preceding bullet (`:412`), is **inter-temporal
myopia**: the recursive-dynamic solve gives period *t* no information about period *t+1* water
availability. Combined with `cfg$gms$s41_AEI_depreciation <- 0` (`config/default.cfg`, and
`s41_AEI_depreciation` only enters `vm_AEI.lo` at `endo_apr13/presolve.gms:11`), AEI never
shrinks — which is the real stranding mechanism and is *why* stranding happens across time steps,
not within one.

**Consequence.** A developer reading `:414` would conclude module 41 needs a new coupling to
module 43 and could add a redundant (and potentially degenerate) constraint. The actual gap is
foresight, not coupling.

**Fix.** Replace `:411-416` with: "**Known Limitation** (Module 41): AEI expansion is decided
inside the same simultaneous solve as the water constraint, so a *currently* binding `q43_water`
does suppress AEI expansion (chain `q43_water → q42_water_demand → q41_area_irrig →
q41_cost_AEI → q11_cost_reg`). What is missing is **foresight**: MAgPIE is recursive-dynamic, so
period *t* investment cannot anticipate declining water availability in later periods, and with
the default `s41_AEI_depreciation = 0` (`config/default.cfg`) AEI never depreciates away. Result:
AEI built under favourable conditions can strand as later-period water availability falls."

---

## BUG-04 — EFP is `off` by default; default ecosystem demand is the 5 % base fraction, not Smakhtin EFR (Major, `default_value`)

**Doc** `water_balance_conservation:99` (and `:96-105`, `:534`, `:552-556`):
> - **Scenario 2**: LPJmL Smakhtin algorithm (cell-specific) - DEFAULT

and `:552-556`
> **Policy Modes** (Module 42, `.../input.gms:122`): `off` / `on` / `mixed`   ← no default marked

**Reality.** Two switches govern ecosystem demand, and the doc marks the default on only one of
them. `s42_env_flow_scenario = 2` is indeed the default (`input.gms:22`,
`config/default.cfg:1400`), **but** `c42_env_flow_policy` defaults to `off`
(`all_sectors_aug13/input.gms:122`, `config/default.cfg` `cfg$gms$c42_env_flow_policy <- "off"
# def = "off"`), and the policy weight is what selects between the two flow series:

```gams
p42_efp(t_all,"off") = 0;                                                 preloop.gms:15
i42_env_flow_policy(t,i) = p42_efp(t,"off")*shr + p42_efp(t,"off")*(1-shr);   presolve.gms:81-82  → 0
vm_watdem.fx("ecosystem",j) = sum(cell(i,j), i42_env_flows_base(t,j)*(1-0)
                                           + i42_env_flows(t,j)*0);          presolve.gms:87-88
```

So in a default run the Smakhtin series `i42_env_flows` (= `f42_env_flows`, `preloop.gms:9`) is
**multiplied by zero** and ecosystem demand collapses to
`i42_env_flows_base = s42_env_flow_base_fraction * sum(wat_src, im_wat_avail)` = **5 % of
available water, flat** (`presolve.gms:58`; `s42_env_flow_base_fraction = 0.05`, `input.gms:37`).
The 2025→2040 ramp (`:102`, `:534`) likewise never fires by default: `p42_efp_fader` only enters
via `p42_efp(t,"on")` (`preloop.gms:16-17`).

Everything else in this block verifies: `s42_efp_startyear/targetyear` = 2025/2040
(`input.gms:35-36`), and `EFP_countries` really is the full 249-member `iso` set (counted 249 in
`input.gms:52-76`; `core/sets.gms` `iso` = 249) — so `:104` is **correct**.

**Fix.** At `:99` add: "`s42_env_flow_scenario = 2` is the default, **but** it only takes effect
when an EFP policy is switched on." At `:96` insert a line: "**Default ecosystem demand**: with
`c42_env_flow_policy = off` (the default, `input.gms:122` / `config/default.cfg`),
`ic42_env_flow_policy(i) = 0`, so `vm_watdem.fx('ecosystem',j) = i42_env_flows_base(t,j)` = 5 % of
`sum(wat_src, im_wat_avail)` (`presolve.gms:58,87-88`). The Smakhtin values are computed but
weighted zero." At `:553` mark `off` as `- DEFAULT`, and open Section 7.4 with "This section
describes the **non-default** `c42_env_flow_policy = on|mixed` configuration."

---

## BUG-05 — `vm_prod(j,kli)` attributed to modules 17 and 70 (Major, `attribution_populate`)

**Doc** `water_balance_conservation:430` (heading `:420`, summary table `:910`):
> - `vm_prod(j,kli)`: Livestock production from Module 17 (Mt DM/yr)

> | 17, 70 | Livestock production (contributes to agricultural demand) | vm_prod(j,kli) |

**Reality (three roles, three different modules).**
- **DECLARED** in `17_production`: `vm_prod(j,k)  Production in each cell (mio. tDM per yr)`
  (`modules/17_production/flexreg_apr16/declarations.gms:9`).
- **READ** by module 17: `q17_prod` puts `vm_prod` on the RHS —
  `vm_prod_reg(i2,k) =e= sum(cell(i2,j2), vm_prod(j2,k));`
  (`flexreg_apr16/equations.gms:11`). Module 17 populates `vm_prod_reg`, not `vm_prod`.
- **POPULATED / cell-slice determined** for `kli` by `71_disagg_lvst` (default
  `foragebased_jul23`, `config/default.cfg:2221`): `q71_prod_mon_liv(j2,kli_mon) ..
  vm_prod(j2,kli_mon) =l= ...` (`foragebased_jul23/equations.gms:55-58`), with the ruminant slice
  pinned through `q71_feed_forage` / `q71_feed_balanceflow_nlp` (`:21-24`, `:34-37`).
- **Module 70_livestock never references `vm_prod` at all** — every `vm_prod*` occurrence in
  `modules/70_livestock/` is `vm_prod_reg` (regional), across both realizations.

The role map agrees: `vm_prod` → `declared_in: 17_production`, `populated_by: [30, 31, 71, 73]`,
`read_by: [17, 18, 31, 38, 40, 42, 71, 73]` — 17 is a **reader**, 70 appears in neither list.

**Consequence.** A reader tracing where cell-level livestock water demand comes from is sent to
modules 17 and 70; the module that actually determines `vm_prod(j,kli)` (71) is not mentioned
anywhere in the doc.

**Fix.** `:430` → "`vm_prod(j,kli)`: cell-level livestock production, **declared** in
`17_production` (`flexreg_apr16/declarations.gms:9`) and **read** there by `q17_prod`
(`equations.gms:11`); the cell-level `kli` slice is determined by `71_disagg_lvst`
(default `foragebased_jul23`, `equations.gms:21-24,34-37,55-58`). Regional livestock production
`vm_prod_reg` is where module 70 acts — module 70 never touches `vm_prod`."
`:420` heading → "Modules 17 (Production) and 71 (Livestock disaggregation)".
`:910` table row → `| 17 (declares), 71 (determines cell slice) | Cell-level livestock production |
vm_prod(j,kli) |`.

---

## BUG-06 — `water_demand()` is not a magpie4 function (Major, `citation`)

**Doc** `water_balance_conservation:607` (and `:842`):
> `watdem <- water_demand(gdx, level="cell", water_source=FALSE)`

**Reality.** No `water_demand` exists anywhere in the renv-pinned magpie4 clone — not in `R/`,
not in `NAMESPACE`, not in `man/`. The real accessor is `water_usage()`
(`.cache/sources/magpie4/NAMESPACE:309`, `R/water_usage.R`); `water_avail()` is at
`NAMESPACE:306`. `water_usage()` takes `users` (`NULL` / `"sectors"` / `"kcr"` / `"kli"`) and
`sum`, not a `water_source` argument.

**Second-order trap in the same call.** `water_usage()` defaults to `seasonality = "total"`, which
reports non-agricultural demand for the **entire year** from `i42_watdem_total`, while
`water_avail()` is growing-period only. Comparing the two at defaults does not reproduce
`q43_water` and would show spurious violations — the exact failure the doc's own Section 8.4
"Growing Period Caveat" warns about. The Section 8.1 check must pass `seasonality = "grper"`.

**Evidence**
- `.cache/sources/magpie4/NAMESPACE:306,309` (`export(water_avail)`, `export(water_usage)`)
- `.cache/sources/magpie4/R/water_usage.R:11-18,29-31` (arg list, `seasonality` default)
- whole-clone grep for `water_demand` returns nothing (positive control on the same path returns
  the two exports above)

**Fix.** Replace both occurrences with
`watdem <- water_usage(gdx, level = "cell", users = "sectors", sum = FALSE, seasonality = "grper")`
and add one line: "`water_usage()` defaults to `seasonality = 'total'` (full-year
non-agricultural demand); the water balance is a growing-period constraint, so `'grper'` is
required for this check."

---

## BUG-07 — magpie4 returns km³, the verification code labels and thresholds it as mio. m³ (Major, `other`)

**Doc** `water_balance_conservation:618`, `:621-622` (and `:650`, `:654`, `:847`):
> `print(paste("Maximum constraint violation:", max_violation, "mio. m³"))`
> `# Small positive values (< 0.01 mio. m³) = numerical tolerance`
> `stopifnot(max_violation < 0.01)`

**Reality.** The GAMS variables are in mio. m³ per yr
(`modules/43_water_availability/total_water_aug13/declarations.gms:9,13`;
`modules/42_water_demand/all_sectors_aug13/declarations.gms:29`), but both magpie4 accessors
convert **out** of that unit before returning:

```r
# from mio m^3 to km^3
x <- x / 1000            # .cache/sources/magpie4/R/water_avail.R:47-48
outout <- outout / 1000  # .cache/sources/magpie4/R/water_usage.R:245-246
```

Both roxygen blocks declare the return unit as km³ (`water_avail.R:14`, `water_usage.R:22`). So
every quantity in Sections 8.1, 8.2 and 10.3 Step 2 is in km³ while labelled "mio. m³" — a
**1000×** mismatch. Concretely: `stopifnot(max_violation < 0.01)` is a 10 mio. m³ tolerance, not
0.01; `scarce_cells <- which(surplus < 1)` (`:650`) is a 1000 mio. m³ threshold; and
`abundant_cells <- which(surplus > 100)` (`:654`) is 100 km³, which almost no MAgPIE cluster
reaches. Note Section 9.2 Check 2 (`:764-766`) reads `ov43_watavail` straight from the GDX and is
therefore correctly in mio. m³ — the two conventions sit three pages apart with no flag.

**Fix.** Label the Section 8.1 / 8.2 / 10.3 quantities `km³` (or multiply by 1000 immediately
after the magpie4 calls and keep mio. m³ throughout), rescale the thresholds accordingly
(`< 1e-5` km³ for the tolerance if 0.01 mio. m³ was intended), and add a one-line note:
"`magpie4::water_avail()` / `water_usage()` return **km³**; GDX-level `ov43_watavail` /
`ov_watdem` are in **mio. m³** (÷1000 at `water_avail.R:47`, `water_usage.R:245`)."

---

## BUG-08 — Shadow prices presented as an inter-module data hand-off and an objective term (Minor, `data_flow_direction`)

**Doc** `water_balance_conservation:341-342` (also `:362-363`, `:390-392`):
> **Receives from Module 43**:
> - Shadow prices from q43_water constraint → feed back to irrigation decisions

> - Module 30 responds indirectly via shadow prices in objective function

**Reality.** Module 42 contains **zero** references to `q43_water` — a whole-directory grep of
`modules/42_water_demand/` for `q43_water` returns only prose cross-references to the *module*
`[43_water_availability]` in `realization.gms` / `module.gms` (positive control on the same path:
`im_wat_avail` matches twice in `all_sectors_aug13/presolve.gms`). Nothing in MAgPIE reads
`q43_water.m` at all; it is written once to `oq43_water` in postsolve (`postsolve.gms:11`) for
reporting only.

The real coupling is **simultaneity, not a hand-off**: `q43_water`, `q42_water_demand` and
`q41_area_irrig` are all rows of one NLP solved together, sharing `vm_watdem`, `vm_area` and
`vm_AEI`. No water shadow price appears in any objective term — the only water-related term in
`q11_cost_reg` is `vm_water_cost(i2)` (`modules/11_costs/default/equations.gms:46`), and that is
identically zero by default (see BUG-10).

Contrast with the doc's *correct* serial claim at `:362`: `im_wat_avail` genuinely is a 43→42
hand-off (declared + populated in 43's `preloop.gms:8-12`, read in 42's `presolve.gms:58,64`),
and the role map confirms `im_wat_avail` → `declared_in: 43`, `populated_by: [43]`,
`read_by: [42, 43]`.

**Fix.** Reword `:341-342` to "**Coupled to Module 43 through shared variables (same solve)**:
`vm_watdem` appears in both `q42_water_demand` and `q43_water`; there is no code in module 42
that reads anything from module 43 except the parameter `im_wat_avail`. The scarcity value shows
up *after* the solve as `oq43_water(t,j,'marginal')` (reporting only)." Same for `:363` and
`:392` — replace "via shadow prices in objective function" with "because `q42_water_demand` ties
`vm_watdem('agriculture',j2)` directly to `vm_area(j2,kcr,'irrigated')` in the same solve".

---

## BUG-09 — The module-42 and module-41 equations are quoted but never named (Minor, `citation`)

**Doc** `water_balance_conservation:45-50` (repeated verbatim at `:326-331`, paraphrased at
`:891-894`, and `:406-408`).

The doc quotes the agricultural-water equation inside a ```gams fence three times but drops the
equation header, so the name **`q42_water_demand`** appears nowhere in the document (verified by
grep of the doc). The same applies to `q41_area_irrig`, which `:407` describes in prose
("actual irrigated area (Module 30) cannot exceed AEI") without naming it — and which lives in
module **41**, not 30. The doc names `q43_water` consistently, so the asymmetry reads as if
module 42's demand calculation had no named equation. Indices are also silently renamed
`j2 → j`, `i2 → i` inside a fence presented as code.

**Evidence**: `modules/42_water_demand/all_sectors_aug13/equations.gms:10` (`q42_water_demand("agriculture",j2) ..`),
`:16` (`q42_water_cost(i2) ..`), `modules/41_area_equipped_for_irrigation/endo_apr13/equations.gms:10-11`
(`q41_area_irrig(j2) .. sum(kcr, vm_area(j2,kcr,"irrigated")) =l= vm_AEI(j2);`).

**Fix.** Restore the equation headers verbatim in all three fences
(`q42_water_demand("agriculture",j2) ..` / `q42_water_cost(i2) ..`), keep the `j2`/`i2` indices,
and at `:407` cite `q41_area_irrig`
(`modules/41_area_equipped_for_irrigation/endo_apr13/equations.gms:10-11`) by name.

---

## BUG-10 — Pumping costs presented without the `s42_pumping = 0` default (Major, `default_value`)

**Doc** `water_balance_conservation:333-336` ("**Pumping Costs**", listed under Module 42's
"Key Equations") and `:829-832`:
> **✓ SAFE: Pumping costs** — Module 42, `s42_pumping` and `s42_multiplier`
> - Affects agricultural production costs, not water balance

**Reality.** `s42_pumping` defaults to **0** (`all_sectors_aug13/input.gms:39`;
`config/default.cfg:1415` `cfg$gms$s42_pumping <- 0  # def = 0`), and presolve unconditionally
zeroes the cost coefficient first:

```gams
ic42_pumping_cost(i) = 0;                       presolve.gms:26
if ((s42_pumping = 1),  ic42_pumping_cost(i) = f42_pumping_cost(t,i);  ... );   presolve.gms:29-35
```

So in a default run `q42_water_cost` yields `vm_water_cost(i) = 0` for every region and the term
`+ vm_water_cost(i2)` in `q11_cost_reg` (`modules/11_costs/default/equations.gms:46`) contributes
nothing. `s42_multiplier` also defaults to 0 (`input.gms:41`, `config/default.cfg`), so even
setting `s42_pumping = 1` leaves pumping costs at zero after `s42_multiplier_startyear` (1995)
unless the multiplier is also raised — an additional trap the doc's "SAFE" bullet does not
mention. The feature is documented upstream as India-only
(`config/default.cfg`: "only available for India currently").

This matches the rubric's Major trigger verbatim ("Missing default-state caveat — mechanism
described as if always active when it's OFF by default — `s42_pumping`").

**Fix.** At `:333` prepend: "**Pumping Costs** (inactive by default: `s42_pumping = 0`,
`input.gms:39` / `config/default.cfg`; `ic42_pumping_cost(i) = 0` at `presolve.gms:26`, so
`vm_water_cost = 0` in a default run)". At `:829-832` add: "Requires `s42_pumping = 1`
**and** `s42_multiplier > 0` (default 0) to have any effect after
`s42_multiplier_startyear = 1995`; upstream documents the cost data as India-only."

---

## Verified-clean (no bug) — checked under this lens

| Claim | Doc line | Verdict |
|---|---|---|
| `q43_water` body, `=l=`, cell index `j2` | 24-27, 171-174 | ✅ `43_water_availability/total_water_aug13/equations.gms:10-11` |
| 5 `wat_dem` members (agriculture, domestic, manufacturing, electricity, ecosystem) | 33, 183-184 | ✅ `core/sets.gms:247` |
| 4 `wat_src` members (surface, ground, technical, ren_ground) | 110, 186-187 | ✅ `core/sets.gms:244` |
| `watdem_exo` = manufacturing/electricity/domestic/ecosystem | 284 | ✅ `42_water_demand/all_sectors_aug13/sets.gms:9-10` |
| `im_wat_avail` surface assignment + 3 zeroed sources | 122-124, 153-158 | ✅ `total_water_aug13/preloop.gms:8-12` |
| Buffer expression, `× 1.01`, `watdem_exo`-only trigger | 258-266, 283-285 | ✅ `total_water_aug13/presolve.gms:14-16` |
| **43→42 `im_wat_avail` hand-off is genuinely serial** | 362 | ✅ 43 `preloop.gms:8-12` populates; 42 `presolve.gms:58,64` reads; role map `populated_by:[43] / read_by:[42,43]` |
| `v43_watavail` fixed yet kept a variable to expose marginals | 368-377 | ✅ `presolve.gms:8-11`; `postsolve.gms:10` |
| Irrigation efficiency default = GDP sigmoid via `s42_irrig_eff_scenario = 2`; flat 0.66 only under scenario 1 | 55, 344-347 | ✅ `input.gms:14-20`, `presolve.gms:12-22`, `config/default.cfg` (`def = 2`, `0.66`) |
| SSP2 default for non-agricultural demand | 78 | ✅ `input.gms:9` (`/ 2 /`), `config/default.cfg` |
| `c43_watavail_scenario` default `cc`; nocc / nocc_hist semantics | 138-141 | ✅ `43.../input.gms:9-12,24-26` |
| EFP country set = the full 249-member `iso` set | 104 | ✅ counted 249 in `42.../input.gms:52-76`; `core/sets.gms` `iso` = 249 |
| EFP start/target years 2025 / 2040 | 102 | ✅ `42.../input.gms:35-36` |
| `s42_env_flow_fraction = 0.2` (scenario 1) | 98 | ✅ `42.../input.gms:38` |
| `off` mode ⇒ base protection only, 5 % | 553 | ✅ `input.gms:37`, `presolve.gms:58,81-88` |
| `~200` MAgPIE clusters | 223 | ✅ `config/default.cfg:26` (`...c200...`) |
| 7 land pools vs 5 water sectors | 921 | ✅ `core/sets.gms:250-251`, `:247` |
| Dam exception / growing-period restriction / discharge weighting | 127-131 | ✅ `total_water_aug13/realization.gms:32-38` |
| Buffer interface documented only as an interface in realization prose | 311 | ✅ `total_water_aug13/realization.gms:40-42` |
| All `file.gms:LINE` citations spot-checked (14 of them) | throughout | ✅ no drift found |
| Illustrative numbers explicitly labelled | 133, 244-252, 453-463, 482-493, 538-545, 564-575, 682-688 | ✅ each carries a "made-up / illustrative" note |

---

## Deferred (not verified — no bug claimed, no edit proposed)

1. `:346` "Range: ~64% (low GDP) to ~90% (high GDP)". The sigmoid `1/(1+e^((-22160-gdp)/37767))`
   (`presolve.gms:13,18`) gives 64.3 % at gdp = 0 and needs gdp ≈ 60.8 kUSD/cap MER to reach 90 %.
   Whether any MAgPIE region's 1995 `im_gdp_pc_mer` reaches that requires reading the module 09
   input data, which I cannot parse here. The upper bound looks high but I did not confirm it.
2. `:300`, `:580` "Agriculture … must stay within renewable water (surface)". Algebraically, once
   the buffer fires the constraint leaves agriculture only `0.01 × (exo_demand − availability)` —
   i.e. effectively zero, which is *stricter* than "within surface water", not equal to it. The
   doc's directional point (agriculture bears the scarcity burden) holds; I did not treat the
   imprecision as a bug.
3. `:555` "`mixed`: Development-state dependent (high-income countries only)". The code weights
   EFP by `im_development_state(t,i)`, a continuous 0–1 index
   (`modules/09_drivers/aug17/declarations.gms:32`), not a binary HIC flag — but
   `config/default.cfg` itself says "EFP policy only in hic regions", so the doc is restating
   upstream documentation. Flagging it would be an upstream issue, not a doc defect.
4. `:667`, `:860` `readGDX(gdx, "oq43_water", select = list(type = "marginal"), field = "level")`
   — `field=` alongside `select=` looks wrong for a parameter read, but the `gdx` package source
   is not in the pinned clone, so I could not confirm the argument contract.
5. `:764` `ground_use[,,"ground",]` uses four index positions on what is a 3-dimensional magclass
   object after the `select`; likely an off-by-one comma, but magclass indexing edge cases were
   not verified.
6. `:40-54` The `m_year(t) <= sm_fix_SSP2` branch (`presolve.gms:40-42`) forces SSP2 for
   historical years regardless of `s42_watdem_nonagr_scenario`. The doc does not mention it. This
   is an omission rather than a wrong claim; I did not score it.
7. Whether `q43_water.up = 0` / `q43_water.lo = -INF` in an actual GDX (the empirical confirmation
   of BUG-02's sign) — no `fulldata.gdx` was available in this session, so the sign rests on the
   equation orientation plus the GAMS row-activity convention, corroborated by the `abs()` in
   `magpie4::water_price()`.
