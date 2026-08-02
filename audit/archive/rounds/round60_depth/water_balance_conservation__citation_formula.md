# R60 depth audit — `cross_module/water_balance_conservation.md` — lens: citation_formula

**Auditor lens**: enter from the exact `file:line` citations; mechanically check existence, range, and token
presence; then check equation-formula fidelity and every derived-quantity formula the doc states.

**Ground truth**: MAgPIE `develop` read-only worktree (referred to below as `$DEV`; HEAD `2c02843ec`,
"Merge pull request #919 from alexkoberle/dyn_reg_tau"). magpie4 claims checked against the renv-SHA-pinned
clone recorded in `project/version_pins.json` (magpie4 **2.76.4**, sha `43970cd4`).

**Claims verified**: 58 · **Bugs**: 9 (1 Critical, 5 Major, 3 Minor)

---

## Headline result for the lens

**Zero citation drift.** All **30** `file:line` citations in this document resolve, in current `develop`, to
exactly the content claimed — including the four blocks quoted verbatim as GAMS. That is an unusually clean
citation record for this corpus, and it should be recorded as such so the flywheel does not re-litigate it.

Citations checked and passing (module 42 = `all_sectors_aug13`, module 43 = `total_water_aug13`, both
confirmed as the `config/default.cfg` defaults):

| Doc line | Citation | Verdict |
|---|---|---|
| 14, 168, 222, 355, 886, 959 | `43…/equations.gms:10-11` | ✅ `q43_water(j2)` header + body |
| 35 | `43…/equations.gms:17-18` | ✅ prose naming the 5 `wat_dem` sectors |
| 112 | `43…/equations.gms:19-20` | ✅ prose naming the 4 `wat_src` sources |
| 45, 326, 891 | `42…/equations.gms:10-14` | ✅ `q42_water_demand` header + body |
| 333, 958 | `42…/equations.gms:16-17` | ✅ `q42_water_cost` |
| 424 | `42…/equations.gms:14` | ✅ livestock term |
| 69 | `42…/presolve.gms:40-54` | ✅ SSP `if/elseif` block |
| 89 | `42…/presolve.gms:87-88` | ✅ `vm_watdem.fx("ecosystem",j)` |
| 344 | `42…/presolve.gms:12-22` | ✅ irrigation-efficiency block |
| 76 | `42…/input.gms:9` | ✅ `s42_watdem_nonagr_scenario / 2 /` |
| 96 | `42…/input.gms:22` | ✅ `s42_env_flow_scenario / 2 /` |
| 101 | `42…/input.gms:35-36` | ✅ `s42_efp_startyear / 2025 /`, `s42_efp_targetyear / 2040 /` |
| 552 | `42…/input.gms:122` | ✅ `$setglobal c42_env_flow_policy off` |
| 122 | `43…/preloop.gms:8` | ✅ `im_wat_avail(t,"surface",j)` |
| 153 | `43…/preloop.gms:10-12` | ✅ the three zeroed sources |
| 258, 896, 960 | `43…/presolve.gms:14-16` | ✅ buffer, **character-exact** to the doc's quote |
| 368 | `43…/presolve.gms:8-11` | ✅ `v43_watavail.fx` block |
| 127 | `43…/realization.gms:9-42` | ✅ LPJmL description (basin runoff, growing period, dams, discharge weight) |
| 311 | `43…/realization.gms:40-42` | ✅ buffer-interface sentence only, exactly as the doc's hedge says |
| 138 | `43…/input.gms:9-12` | ✅ `$setglobal c43_watavail_scenario cc` + options |

The bugs below are therefore **not** citation defects. They are (a) two inverted-sign formulas for derived
GDX quantities, (b) a fabricated magpie4 API, (c) a wrong populator set, and (d) three missing default-state
caveats — i.e. exactly the classes that survive a clean citation pass.

---

## BUG 1 — 🟠 Major — `formula` — equation-level "surplus" has the sign inverted

**Doc** `cross_module/water_balance_conservation.md:211`

> 2. **Surplus variable**: `oq43_water.level` = available - withdrawals (≥ 0)

**Reality.** `oq43_water` is a *parameter* `oq43_water(t,j,type)`
(`modules/43_water_availability/total_water_aug13/declarations.gms:23`), so `.level` is not valid syntax; the
level slice is written in postsolve as
`oq43_water(t,j,"level") = q43_water.l(j)` (`…/postsolve.gms:13`).

GAMS normalizes an equation by moving *all* variable terms to the left. `q43_water` has variables on both
sides (`sum(wat_dem,vm_watdem…) =l= sum(wat_src,v43_watavail…)`), so the stored row is
`demand − availability =l= 0`, and the equation level is **withdrawals − availability**, which is **≤ 0** —
the negative of the surplus the doc describes.

**Reproducible evidence** (minimal analogue, run with the GAMS on this machine, 51.4.0):

```gams
variables obj;  positive variables d, a, s;
equations objdef, water, req;
objdef .. obj =e= 1*d + 100*s;
water  .. d =l= a;          $ mirrors q43_water: variables on BOTH sides
req    .. d + s =g= 10;
model m /all/;
a.fx = 4;   solve m using lp minimizing obj;   display water.l, water.m, water.up;
a.fx = 20;  solve m using lp minimizing obj;   display water.l, water.m, water.up;
```

Listing output:

```
Equation Listing:   water..  d - a =L= 0 ;         <-- GAMS normalization
CASE1 scarce  (a=4) :  water.L = 0.000    water.M = -99.000   water.Up = 0.000
CASE2 abundant(a=20):  water.L = -10.000  water.M =   0.000   water.Up = 0.000
```

In CASE 2 availability is 20 and withdrawals are 10; the doc predicts `+10`, GAMS reports **−10**.

**Proposed fix** — replace doc:211 with:

> 2. **Surplus**: the GDX parameter `oq43_water(t,j,"level")` (= `q43_water.l`, written in
>    `modules/43_water_availability/total_water_aug13/postsolve.gms:13`) is the *normalized row activity*
>    `withdrawals − availability`, so it is **≤ 0**; surplus is its negation. `oq43_water(t,j,"upper")` is 0.

---

## BUG 2 — 🟠 Major — `formula` — water shadow price is negative, not positive

**Doc** `cross_module/water_balance_conservation.md:212` and `:675`

> 3. **Shadow price only when binding**: `oq43_water.marginal` > 0 only if constraint tight

> ```r
> high_value_water <- which(shadow_price > 0.01)  # >$0.01/m³
> ```

**Reality.** MAgPIE **minimizes** `vm_cost_glo` (`modules/80_optimization/nlp_apr17/solve.gms:34`:
`solve magpie USING nlp MINIMIZING vm_cost_glo;`). For a `=l=` row in a minimization, the GAMS equation
marginal is **≤ 0**. The same minimal model above returns `water.M = -99.000` in the binding case and `0.000`
in the slack case — never positive.

This is corroborated inside the pinned reporting layer: magpie4's `water_price()` reads
`readGDX(gdx,"oq43_water",…)[, , "marginal"]` and immediately applies
`p_water_cell <- abs(p_water_cell)` (`.cache/sources/magpie4/R/water_price.R:25` and `:32`) — the absolute
value exists precisely because the raw marginal is negative.

**Why this matters concretely**: the doc's own diagnostic at line 675, run on the raw
`oq43_water[,,"marginal"]` it tells the reader to read at line 667, returns **zero** water-scarce cells in
every run — a silent false negative in a diagnostic whose whole purpose is to find scarcity.

**Proposed fix** — at doc:212 write "`oq43_water(t,j,"marginal")` is **< 0** where the constraint binds and
0 where it is slack (GAMS sign convention for `=l=` under minimization); magpie4's `water_price()` reports
`abs()` of it". At doc:675 use `which(abs(shadow_price) > 0.01)` (or read via `magpie4::water_price(gdx,
level = "cell")`, which already takes the absolute value).

---

## BUG 3 — 🟠 Major — `other` — `water_demand()` is not a magpie4 function; units are km³, not mio. m³

**Doc** `cross_module/water_balance_conservation.md:607` (repeated at `:842`)

> ```r
> watdem <- water_demand(gdx, level="cell", water_source=FALSE)
> ```

**Reality.** There is no `water_demand` anywhere in magpie4 2.76.4 (sha `43970cd4`) — not in `R/`, not in
`NAMESPACE`, not in `man/`. The function is **`water_usage()`**
(`.cache/sources/magpie4/R/water_usage.R:30-32`), whose signature is
`water_usage(gdx, file, level, users, sum, seasonality, abstractiontype, digits)` — there is no
`water_source` argument. Two further consequences in the same code block:

- `water_usage()` returns **km³/yr** and `water_avail()` returns **km³** (`R/water_avail.R:46`,
  `x <- x / 1000`), so the doc's printed unit `"mio. m³"` (doc:618) and its tolerance
  `stopifnot(max_violation < 0.01)` (doc:622, doc:847) are off by 10³.
- The scarce/abundant cutoffs at doc:650 (`surplus < 1`) and doc:654 (`surplus > 100`) inherit the same
  1000× error.

**Proposed fix** — replace both `water_demand(gdx, level="cell", water_source=FALSE)` calls with
`water_usage(gdx, level = "cell", users = "sectors", sum = FALSE, seasonality = "grper")`, relabel the units
as km³, and rescale the tolerance/cutoffs (0.01 mio. m³ → 1e-5 km³).

---

## BUG 4 — 🔴 Critical — `attribution_populate` — `vm_prod(j,kli)` attributed to modules 17 and 70; the populator is module 71

**Doc** `cross_module/water_balance_conservation.md:420`, `:430`, `:910`

> ### 6.5 Module 17 (Production) and Module 70 (Livestock)
> …
> - `vm_prod(j,kli)`: Livestock production from Module 17 (Mt DM/yr)
> …
> | 17, 70 | Livestock production (contributes to agricultural demand) | vm_prod(j,kli) |

**Reality** (role map `audit/integrated/depth_rolemap.json` → `vm_prod`:
`declared_in 17_production`, `populated_by [30, 31, 71, 73]`, `read_by [17,18,31,38,40,42,71,73]`; confirmed
by both-endpoints grep):

- **DECLARED** in `modules/17_production/flexreg_apr16/declarations.gms:9` (`vm_prod(j,k)`).
- The **`kli` slice is POPULATED by module 71** (`disagg_lvst`, default `foragebased_jul23` per
  `config/default.cfg`): `modules/71_disagg_lvst/foragebased_aug18/equations.gms:38`
  (`vm_prod(j2,kli_rum) =e= sum(kforage,v71_prod_rum(…))`) and `:45` (`vm_prod(j2,kli_mon) =l= …`); the
  default realization carries the same pair at `modules/71_disagg_lvst/foragebased_jul23/equations.gms:23`
  and `:56`.
- Module 17 only **READS** it: `modules/17_production/flexreg_apr16/equations.gms:11`,
  `vm_prod_reg(i2,k) =e= sum(cell(i2,j2), vm_prod(j2,k));`.
- **Module 70 has zero contact with `vm_prod`.** `rg -n "vm_prod\(" $DEV/modules/70_livestock/` → exit 1
  (no match); `rg -n "vm_prod\." $DEV/modules/70_livestock/` → exit 1 (no match, so no solution-level
  `.l/.lo` read either). Positive control on the same directory:
  `rg -c "vm_prod_reg" $DEV/modules/70_livestock/fbask_jan16/equations.gms` → `6`. Module 70 works entirely
  on the **regional** `vm_prod_reg(i,kap)`.

**Harm** (R20 anchor — wrong producer set in an authoritative summary table): a reader tracing or modifying
how livestock production drives agricultural water demand is sent to module 70, where the variable does not
occur, and is never told about module 71 — which is absent from this document entirely, including from the
§11.3 "Module Roles" table.

**Proposed fix** — retitle §6.5 to "Module 71 (Livestock Disaggregation) and Module 17 (Production)" and
rewrite doc:430 as: "`vm_prod(j,kli)`: cell-level livestock production — **declared** in
`modules/17_production/flexreg_apr16/declarations.gms:9`, **populated** by module 71
(`modules/71_disagg_lvst/foragebased_jul23/equations.gms:23,56`; default realization `foragebased_jul23`),
**read** here by module 42. Module 70 does not touch `vm_prod`; it operates on the regional `vm_prod_reg`."
Change the §11.3 row from `17, 70` to `71 (17 declares)`.

---

## BUG 5 — 🟠 Major — `default_value` — pumping costs presented without the `s42_pumping = 0` default

**Doc** `cross_module/water_balance_conservation.md:333-336` (and §10.2, `:829-832`)

> **Pumping Costs** (`modules/42_water_demand/all_sectors_aug13/equations.gms:16-17`):
> ```gams
> vm_water_cost(i) =e= sum(cell(i,j), vm_watdem("agriculture",j)) * ic42_pumping_cost(i);
> ```

**Reality.** `s42_pumping` defaults to **0** — `modules/42_water_demand/all_sectors_aug13/input.gms:39`
(`s42_pumping … / 0 /`) and `config/default.cfg:1418` (`cfg$gms$s42_pumping <- 0   # def = 0`). Presolve sets
`ic42_pumping_cost(i) = 0` unconditionally
(`modules/42_water_demand/all_sectors_aug13/presolve.gms:26`) and only overwrites it inside
`if ((s42_pumping = 1), …)` (`…/presolve.gms:29-35`). So in **every default run `vm_water_cost(i) = 0`** and
this equation contributes nothing.

Compounding it: even with `s42_pumping = 1`, `…/presolve.gms:32-34` multiplies by `s42_multiplier` for every
`m_year(t) > s42_multiplier_startyear` (= 1995), and `s42_multiplier` defaults to **0**
(`input.gms:41`, `config/default.cfg:1426`). Both switches must be changed before pumping costs are non-zero
after 1995. §10.2's "SAFE: Pumping costs … Affects agricultural production costs" names both switches but
does not say either is off.

This is the rubric's named Major trigger ("Missing default-state caveat … `s42_pumping`").

**Proposed fix** — insert before the code block at doc:334: "⚠️ **Inactive by default.** `s42_pumping = 0`
(`config/default.cfg:1418`) ⇒ `ic42_pumping_cost(i) = 0` (`…/presolve.gms:26`) ⇒ `vm_water_cost(i) = 0` in a
default run. Activating it requires `s42_pumping = 1` **and** a non-zero `s42_multiplier` (default 0), which
otherwise re-zeroes the cost for every year after `s42_multiplier_startyear` = 1995." Mirror the caveat in
§10.2.

---

## BUG 6 — 🟠 Major — `default_value` — EFP ramp and Smakhtin flows presented as the operative default; `c42_env_flow_policy` is `off`

**Doc** `cross_module/water_balance_conservation.md:99`, `:101-102`, `:534`, `:552-556`

> - **Scenario 2**: LPJmL Smakhtin algorithm (cell-specific) - DEFAULT
> **Environmental Flow Protection (EFP) Policy** … Linear ramp-up from 2025 (0%) to 2040 (100%)
> 1. EFP policy ramps up 2025-2040 (linear increase from 0% to 100%)
> **Policy Modes** … `off` … `on` … `mixed` …

**Reality.** `s42_env_flow_scenario = 2` is indeed the default, but it is **gated by a second switch the doc
never marks**: `c42_env_flow_policy` defaults to **`off`**
(`modules/42_water_demand/all_sectors_aug13/input.gms:122`; `config/default.cfg:1373`,
`cfg$gms$c42_env_flow_policy <- "off"   # def = "off"`). Chain in a default run:

1. `p42_efp(t_all,"off") = 0;` — `…/preloop.gms:15`
2. `$else` branch → `i42_env_flow_policy(t,i) = p42_efp(t,"off")*shr + p42_efp(t,"off")*(1-shr) = 0` —
   `…/presolve.gms:81-82`
3. `ic42_env_flow_policy(i) = 0` — `…/presolve.gms:85`
4. `vm_watdem.fx("ecosystem",j) = i42_env_flows_base(t,j)*(1-0) + i42_env_flows(t,j)*0` — `…/presolve.gms:87-88`
5. `i42_env_flows_base(t,j) = s42_env_flow_base_fraction * sum(wat_src, im_wat_avail(t,wat_src,j))` with
   `s42_env_flow_base_fraction = 0.05` — `…/presolve.gms:58`, `input.gms:37`

So by default the ecosystem sector takes a **flat 5% of available water in every cell and every year**, the
2025→2040 fader never leaves zero, and the cell-specific Smakhtin values `i42_env_flows` (from
`lpj_envflow_grper.cs2`, `input.gms:111-117`) are multiplied by zero and **never enter the model**. The doc
states the correct `off` behaviour once, in passing, at doc:553 — but marks "DEFAULT" only on scenario 2 and
presents the ramp (§2.3, §7.4) and "full EFP" (§7.5, doc:569) as the operating regime.

**Proposed fix** — at doc:99 append: "(scenario switch only — see the EFP policy gate below)". At doc:101
insert: "⚠️ **Off by default**: `c42_env_flow_policy = off` (`config/default.cfg:1373`). With `off`,
`i42_env_flow_policy = 0` and `vm_watdem.fx("ecosystem",j)` = `s42_env_flow_base_fraction` (0.05) × available
water; the 2025-2040 fader and the Smakhtin values `i42_env_flows` are inactive. Everything below describes
`c42_env_flow_policy = on|mixed`." Mark `off` as DEFAULT in the §7.4 policy-modes list.

---

## BUG 7 — 🟡 Minor — `formula` — module 42 equations quoted without their names and with the equation aliases rewritten

**Doc** `cross_module/water_balance_conservation.md:47-49`, `:328-330`, `:335`, `:426`, and `:71`

> ```gams
> vm_watdem("agriculture",j) * v42_irrig_eff(j) =e=
>   sum(kcr, vm_area(j,kcr,"irrigated") * ic42_wat_req_k(j,kcr))
>   + sum(kli, vm_prod(j,kli) * ic42_wat_req_k(j,kli) * v42_irrig_eff(j));
> ```

**Reality.** The code (`modules/42_water_demand/all_sectors_aug13/equations.gms:10-14`) reads:

```gams
q42_water_demand("agriculture",j2) ..
 vm_watdem("agriculture",j2) * v42_irrig_eff(j2) =e=
   sum(kcr, vm_area(j2,kcr,"irrigated") *
   ic42_wat_req_k(j2,kcr))
 + sum(kli, vm_prod(j2,kli) * ic42_wat_req_k(j2,kli) * v42_irrig_eff(j2));
```

The algebra is faithful, but every module-42 block drops the equation header and rewrites the equation-domain
aliases `j2`/`i2` as `j`/`i`. Consequently **`q42_water_demand` and `q42_water_cost` are named nowhere in the
document** (`grep -n "q42_" cross_module/water_balance_conservation.md` → no match), while `q43_water` appears
14 times — including in §11.2 "Critical Equations", which lists the module-42 equation by prose description
only. Related: doc:71 puts a non-existent placeholder `ssp_scenario` inside a ```gams fence where the code has
string literals `"ssp1"`/`"ssp2"`/`"ssp3"` (`…/presolve.gms:41,45,48,51`).

**Proposed fix** — restore the `q42_water_demand("agriculture",j2) ..` and `q42_water_cost(i2) ..` headers and
the `j2`/`i2` aliases in all four blocks; add the equation names to the §11.2 list; label doc:70-72 as
pseudocode or use one concrete literal (`"ssp2"`, the default).

---

## BUG 8 — 🟡 Minor — `mechanism` — the infeasibility buffer has no on/off switch

**Doc** `cross_module/water_balance_conservation.md:722` and `:806-808`

> - **Solution**: Reduce demands, increase water availability, or enable buffer
> **⚠️ DANGER: Changing infeasibility buffer** … **Test**: Run without buffer to check if demands sustainable

**Reality.** The buffer is unconditional code, not a configurable feature:
`modules/43_water_availability/total_water_aug13/presolve.gms:13-16` is a bare assignment whose only guard is
the `$( … > 0)` condition on the shortfall itself. There is no scalar, no `$setglobal`, and no `config/default.cfg`
entry controlling it — the module's only config entries are the realization and `c43_watavail_scenario`
(`config/default.cfg:1425-1432`). "Enable buffer" and "run without buffer" both describe controls that do not
exist; suppressing it requires editing `presolve.gms`.

**Proposed fix** — at doc:722 drop "or enable buffer" (the buffer is always on). At doc:808 write: "**Test**:
the buffer has no switch — to test sustainability without it you must comment out
`modules/43_water_availability/total_water_aug13/presolve.gms:14-16` in a scratch copy, and expect
infeasibility wherever exogenous demand exceeds surface water."

---

## BUG 9 — 🟡 Minor — `mechanism` — "no feedback from Module 43 to Module 41" contradicts the LP coupling

**Doc** `cross_module/water_balance_conservation.md:414`

> - No feedback from Module 43 water constraint to Module 41 investment

**Reality.** The default realization is `endo_apr13` (`config/default.cfg`,
`cfg$gms$area_equipped_for_irrigation <- "endo_apr13"   # def = endo_apr13`), where `vm_AEI(j)` is an
endogenous decision variable in the **same LP** as `q43_water`, coupled through irrigated area:

- `modules/41_area_equipped_for_irrigation/endo_apr13/equations.gms:10-11` —
  `q41_area_irrig(j2) .. sum(kcr, vm_area(j2,kcr,"irrigated")) =l= vm_AEI(j2);`
- `modules/41_area_equipped_for_irrigation/endo_apr13/equations.gms:19-23` — `q41_cost_AEI(i2)` charges for
  every hectare of AEI expansion.
- `modules/42_water_demand/all_sectors_aug13/equations.gms:12-13` — the same `vm_area(j2,kcr,"irrigated")`
  drives `vm_watdem("agriculture",j2)`, which `q43_water` bounds.

So a binding water constraint suppresses irrigated area in the current time step and thereby removes the
payoff for paying `q41_cost_AEI` — current-period feedback exists and is direct. What is genuinely absent is
**foresight**: MAgPIE is recursive-dynamic, so the AEI decision cannot anticipate *future* scarcity. The doc
states the same indirect-shadow-price mechanism for module 30 two sections earlier (doc:390-392), so the
claim is also internally inconsistent.

**Proposed fix** — replace doc:414 with: "No *anticipatory* feedback: AEI expansion responds to the current
time step's water shadow price (`vm_AEI` and `q43_water` are solved jointly, coupled by
`modules/41_area_equipped_for_irrigation/endo_apr13/equations.gms:11`), but MAgPIE's recursive-dynamic solve
means it cannot anticipate future scarcity — hence stranding risk under a drying trajectory."

---

## Deferred (not bugs — flagged as unverifiable or out of scope)

1. **Irrigation-efficiency range "~64-90%"** (doc:55, doc:346). The sigmoid
   `1/(1+2.718282**((-22160-im_gdp_pc_mer("y1995",i))/37767))` (`…/presolve.gms:18`) has a floor of 0.6425 at
   GDPpc = 0, matching "~64%", but the upper end depends on `im_gdp_pc_mer` values that live in gitignored
   module-09 input data; not checkable in the worktree. No edit proposed.
2. **`mixed` EFP mode described as "high-income countries only"** (doc:105, doc:555). Code multiplies by the
   *continuous* `im_development_state(t,i)` (`modules/09_drivers/aug17/declarations.gms:32`, "0 = low income
   country 1 = high income country"), not a binary HIC filter — but `config/default.cfg`'s own comment reads
   "(mixed): EFP policy only in hic regions", so the doc matches maintainer description. Not flagged
   (advisory drift risk).
3. **Role-map / grep discrepancy on `vm_watdem`.** `audit/integrated/depth_rolemap.json` lists
   `populated_by: ["42","43"]`. Both-endpoints grep shows module 43 only **reads** it —
   `…/43…/equations.gms:11` (equation RHS) and `…/43…/presolve.gms:15-16` (`vm_watdem.lo` on the RHS of the
   buffer assignment). Code trusted; the map's `43` is an attribute-form heuristic artifact. The doc's
   direction claim (42 produces → 43 consumes, doc:338-342, doc:361-366) is **correct**. Recorded so a future
   auditor does not "fix" a correct doc statement from the map.
4. **`1.01` described as "1% safety margin for numerical stability"** (doc:279). No comment in
   `…/presolve.gms:13-16` explains the factor; the interpretation is plausible but unverifiable from code.
5. **"Why variable if fixed? To provide shadow prices"** (doc:373-377). Rationale not stated in code.
6. **Growing-period → annual multipliers** (doc:702-705) and **LPJmL runoff-change percentages**
   (doc:511-515). Not derivable from GAMS code; explicitly framed as approximations / literature.
7. **All numeric worked examples** (§5.1, §7.1, §7.2, §7.5, §8.3). Each carries an explicit
   "*Note: Made-up numbers for illustration*" label; not audited.

---

## Reproduction notes

`$DEV` = the read-only `develop` worktree root; `$AGENT` = this repository root. Every probe was run as its
own standalone command (no `find … -exec … +` chaining), and every absence claim carries a positive control:

| Purpose | Command | Result |
|---|---|---|
| Realization names | `ls -d $DEV/modules/42_water_demand/*/ $DEV/modules/43_water_availability/*/` | `agr_sector_aug13`, `all_sectors_aug13`, `total_water_aug13` (+ `input/`) |
| Defaults | `grep -n "water_demand\|water_availability" $DEV/config/default.cfg` | `all_sectors_aug13`, `total_water_aug13` |
| Citation range | `wc -l` on all 8 cited `.gms` files | 20/12/16/52/27/21/88/132 — every cited line in range |
| Set membership | `rg -n "wat_dem\|wat_src" $DEV/core/sets.gms` | `wat_src` 4 members (`core/sets.gms:244`), `wat_dem` 5 (`core/sets.gms:247`) |
| `watdem_exo` | `cat $DEV/modules/42_water_demand/all_sectors_aug13/sets.gms` | `/ domestic, manufacturing, electricity, ecosystem /` (`sets.gms:9-10`) — agriculture excluded ✅ |
| EFP country count | python parse of `EFP_countries` vs `iso` in `core/sets.gms` | **249 vs 249** — doc:103 correct ✅ |
| Objective direction | `rg -n "MINIMIZING" $DEV/modules/80_optimization/*/solve.gms` | `solve magpie USING nlp MINIMIZING vm_cost_glo` |
| Land balance is `=e=` | `sed -n '13,15p' $DEV/modules/10_land/landmatrix_dec18/equations.gms` | `q10_land_area(j2) .. sum(land,vm_land) =e= sum(land,pcm_land)` — doc §4.2 ✅ |
| Cell count | `grep -n "cellular" $DEV/config/default.cfg:26` | `…_c200_MRI-ESM2-0-ssp245…` — "~200 cells" ✅ |
| M70 has no `vm_prod` | `rg -n "vm_prod\(" $DEV/modules/70_livestock/` | exit 1, no match |
| …solution-level too | `rg -n "vm_prod\." $DEV/modules/70_livestock/` | exit 1, no match |
| …positive control | `rg -c "vm_prod_reg" $DEV/modules/70_livestock/fbask_jan16/equations.gms` | `6` — search works in that dir |
| magpie4 `water_demand` | `rg -n "water_demand" $AGENT/.cache/sources/magpie4` | NO MATCH (whole clone) |
| …positive control | `rg -c "water_avail" $AGENT/.cache/sources/magpie4/NAMESPACE` | `1` |
| GAMS sign convention | `gams waterlevel.gms` (model above), GAMS 51.4.0 | `water.L = -10.000`, `water.M = -99.000` |

---

*Lens: citation_formula. Reported under the R60 depth-audit protocol. Severity tiers per
`audit/flywheel_rubric.md` §1; BUG 4 assigned Critical on the immutable R20 wrong-consumer/producer-set
anchor (a reader is sent to a module with zero contact with the variable, and the real populator is absent
from the document).*
