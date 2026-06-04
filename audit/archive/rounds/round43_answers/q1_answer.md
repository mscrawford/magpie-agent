# Q1 Answer: How MAgPIE solves — Module 80, interest rate discounting, and factor costs in the objective

---

## (a) Module 80 default realization, solver, and recursive-dynamic vs. intertemporal

### Default realization: `nlp_apr17`

Confirmed in `config/default.cfg`: `cfg$gms$optimization <- "nlp_apr17"`.

`nlp_apr17` is a **pure solver-orchestration module** — it defines zero model equations. Its entire job is to invoke GAMS's NLP solver on the pre-assembled model object `magpie` (declared in `main.gms` as `model magpie / all - m15_food_demand /`, which includes all equations from all other active module realizations).

**Solver invoked**: CONOPT4 (nonlinear gradient-based).

Primary solve statement (`modules/80_optimization/nlp_apr17/solve.gms:34`):
```gams
solve magpie USING nlp MINIMIZING vm_cost_glo;
```

CONOPT4 option: `Tol_Optimality = s80_toloptimal` (default `1e-08`, from `nlp_apr17/input.gms:12`).

On failure (`modelstat > 2`), a `repeat` loop cycles through four recovery strategies (CONOPT4 defaults → CONOPT4 custom optfile → CONOPT4 relaxed variable limits → CONOPT3), up to `s80_maxiter = 30` attempts (`nlp_apr17/input.gms:9`, `nlp_apr17/solve.gms:48-92`).

**Recursive-dynamic, not intertemporal.** Each 5-year timestep is solved independently. Module 11 aggregates costs *within* the current timestep into `vm_cost_glo` and Module 80 minimizes that scalar. There is no forward-looking NPV objective, no Bellman equation, and no anticipation of future states. Module 11's documentation explicitly records: "Module 11 does NOT apply discount rates to future costs. Each time step is optimized independently (recursive dynamic, not forward-looking)" (`modules/module_11.md` §8.4, §12.5).

---

## (b) Module 12 (interest rate) and discounting of the objective

### What Module 12 computes

Module 12 has **no equations** — it is a parameter-calculation module that runs only in `preloop`. Its sole output is `pm_interest(t,i)`, a regional-and-timestep-specific annual interest rate (fraction per year) calculated in `modules/12_interest_rate/select_apr20/preloop.gms:23-26`.

Default mode (`c12_interest_rate = "gdp_dependent"`): linear interpolation between
- `s12_interest_lic = 0.10` (LIC, 10%) and
- `s12_interest_hic = 0.04` (HIC, 4%)

based on `im_development_state(t,i)` (0–1 per-capita GDP index from Module 09), with a fader `f12_interest_fader(t)` that transitions from historical to policy rates over 2025–2050.

### How pm_interest enters the objective — through cost-module annuitization, not Module 11 directly

`pm_interest` does NOT appear as a term in Module 11's `q11_cost_reg` or `q11_cost_glo`. Instead, it enters `vm_cost_glo` **indirectly through the cost modules that annuitize capital investments**. The key ones in the default configuration are:

**Module 38 (Factor Costs, `sticky_feb18`)** — the most important consumer for the global cost total. `pm_interest` enters the capital-cost equation (`modules/38_factor_costs/sticky_feb18/equations.gms:23`):

```gams
q38_cost_prod_capital(i2) ..
  vm_cost_prod_crop(i2,"capital")
    =e= (sum((cell(i2,j2), kcr), v38_investment_immobile(j2,kcr))
       + sum((cell(i2,j2)),       v38_investment_mobile(j2)))
       * sum(ct, (pm_interest(ct,i2) + s38_depreciation_rate) / (1 + pm_interest(ct,i2)));
```

The annuitization factor `(r + d) / (1 + r)` (where `r = pm_interest`, `d = s38_depreciation_rate = 0.05`) converts the investment stock into a per-period cost equivalent. The resulting `vm_cost_prod_crop(i,factors)` then enters `q11_cost_reg` via `sum(factors, vm_cost_prod_crop(i2,factors))` (`modules/11_costs/default/equations.gms:15`).

`pm_interest` also appears in `presolve.gms:25-26` of `sticky_feb18`, where it divides the per-ton capital need to convert an annuitized cost back into the equivalent capital stock:

```
p38_capital_need(t,i,kcr,"mobile")   = i38_fac_req × share_capital / (pm_interest + s38_depreciation_rate) × (1 - s38_immobile)
p38_capital_need(t,i,kcr,"immobile") = i38_fac_req × share_capital / (pm_interest + s38_depreciation_rate) × s38_immobile
```

Other modules that annuitize via `pm_interest` and therefore pass discounted costs into `vm_cost_glo` (each routes through Module 11):
- Module 29 (`vm_cost_cropland` → `q11_cost_reg` line `equations.gms:43`)
- Module 32 (`vm_cost_fore` → `q11_cost_reg` line `equations.gms:33`) — Faustmann rotation discount
- Module 39 (`vm_cost_landcon` → `q11_cost_reg` line `equations.gms:20`)
- Module 41 (`vm_cost_AEI` → `q11_cost_reg` line `equations.gms:29`)
- Module 56 (`vm_emission_costs`, `vm_reward_cdr_aff` → `q11_cost_reg` lines `equations.gms:26-27`) — CDR reward annuity
- Module 58 (`vm_peatland_cost` → `q11_cost_reg` line `equations.gms:42`)

**Key point**: `pm_interest` acts as an *intra-timestep* annuitization rate that converts capital stocks into period costs. It does NOT discount costs across timesteps. There is no inter-timestep NPV calculation anywhere in the model.

---

## (c) How Module 38 factor costs enter the global objective

### The chain: M38 → M11 → vm_cost_glo → solver

**Step 1 — Module 38 produces `vm_cost_prod_crop(i,factors)`.**

Default realization `sticky_feb18` uses four equations:

1. `q38_cost_prod_labor(i2)` — labor cost: production volume × per-ton labor requirement × wage-scaling ratio / productivity gain (`equations.gms:15-17`).

2. `q38_cost_prod_capital(i2)` — capital cost: annuitized sum of immobile + mobile investments via `(pm_interest + s38_depreciation_rate) / (1 + pm_interest)` (`equations.gms:21-24`).

3. `q38_investment_immobile(j2,kcr)` — `=g=` constraint: cellular immobile investment must cover the shortfall between required immobile capital and existing stock (`equations.gms:33-36`). Variables: `v38_investment_immobile(j,kcr)`.

4. `q38_investment_mobile(j2)` — `=g=` constraint: pooled mobile investment covers remaining shortfall (`equations.gms:41-44`). Variables: `v38_investment_mobile(j)`.

Output variable: `vm_cost_prod_crop(i,factors)` with `factors = {labor, capital}`, unit mio USD17MER/yr (`declarations.gms:16`).

**Step 2 — Module 11 aggregates `vm_cost_prod_crop` into the regional cost.**

Equation `q11_cost_reg` (`modules/11_costs/default/equations.gms:15-47`) sums 32 cost terms. The factor-cost term:

```gams
q11_cost_reg(i2) .. v11_cost_reg(i2) =e=
  sum(factors, vm_cost_prod_crop(i2,factors))
  + ... [31 other terms] ...
;
```

`vm_cost_prod_crop` is documented as the **largest single contributor** to `v11_cost_reg`, typically 40–60% of total (`module_11.md` §15.2).

**Step 3 — Module 11 aggregates regional costs into `vm_cost_glo`.**

```gams
q11_cost_glo .. vm_cost_glo =e= sum(i2, v11_cost_reg(i2));
```

(`modules/11_costs/default/equations.gms:10`)

**Step 4 — Module 80 minimizes `vm_cost_glo`.**

```gams
solve magpie USING nlp MINIMIZING vm_cost_glo;
```

(`modules/80_optimization/nlp_apr17/solve.gms:34`)

The solver sees one scalar objective variable. All 32 cost components — including factor costs — are simultaneously visible to the optimizer via the constraint structure that links production decisions to cost variables.

---

## Summary table

| Question | Answer | Key names | Doc citation |
|---|---|---|---|
| Default M80 realization | `nlp_apr17` | — | `module_80.md` §Realization:nlp_apr17 |
| Solver invoked | CONOPT4 (primary); CONOPT3 (fallback) | `s80_toloptimal`, `s80_maxiter` | `module_80.md` solve sequence, `nlp_apr17/solve.gms:34` |
| Per-timestep or intertemporal | Per-timestep (recursive dynamic) | `vm_cost_glo` minimized each t | `module_11.md` §8.4, §12.5; `module_80.md` overview |
| Interest rate output | `pm_interest(t,i)` | `s12_interest_lic=0.10`, `s12_interest_hic=0.04` | `module_12.md` §2 |
| How pm_interest enters objective | Via annuitization in cost modules (M38, M29, M32, M39, M41, M56, M58); NOT as a direct M11 term | `(pm_interest + s38_depreciation_rate) / (1 + pm_interest)` | `module_38.md` §2.1.2 (`equations.gms:23`) |
| Factor cost variable | `vm_cost_prod_crop(i,factors)` | `v38_investment_immobile`, `v38_investment_mobile` | `module_38.md` §2.2 |
| Factor cost equations | 4 (`q38_cost_prod_labor`, `q38_cost_prod_capital`, `q38_investment_immobile`, `q38_investment_mobile`) | — | `module_38.md` §2.1 (`equations.gms:15-44`) |
| Entry point into M11 | `sum(factors, vm_cost_prod_crop(i2,factors))` first term in `q11_cost_reg` | — | `module_11.md` §2.2 (`equations.gms:15`) |
| Entry point into solver | `vm_cost_glo` via `q11_cost_glo` then `solve ... MINIMIZING vm_cost_glo` | — | `module_11.md` §2.1 (`equations.gms:10`); `module_80.md` (`nlp_apr17/solve.gms:34`) |

---

## Doc I wished existed

The docs correctly state that `pm_interest` is an "annuitization rate, not an inter-timestep discount rate" (module_12.md §7 Limitations), but no single document explicitly maps *all* the cost-module paths through which `pm_interest` reaches `vm_cost_glo`, including the double appearance in M38 (once in `presolve.gms` to set capital-need parameters, once in `equations.gms:23` to annuitize investment). A short cross-module note — perhaps in `cross_module/` — titled "interest rate transmission path" would be useful for auditors.

---

## Source statement

🟡 Based on module documentation only (docs-only answer per task specification):
- `modules/module_80.md` (verified 2026-05-16)
- `modules/module_12.md` (verified 2025-10-13)
- `modules/module_11.md` (verified 2026-05-16)
- `modules/module_38.md` (verified 2026-05-23 R3)
- `config/default.cfg` (default realization confirmations cited in doc headers)

No `.gms` files were opened. All equation text is reproduced from doc citations; line numbers were verified at last-sync date. Code changes since last sync (if any) may have shifted line numbers.
