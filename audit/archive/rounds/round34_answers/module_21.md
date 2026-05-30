# Module 21 (Trade) — Round 34 Answer

**Question**: How does Module 21 enforce regional self-sufficiency, and what distinguishes the k_trade vs k_notrade commodity split? Name the default realization, the key equations, and which modules consume vm_prod_reg and vm_supply.

---

## Default Realization

`selfsuff_reduced` — confirmed in `config/default.cfg`: `cfg$gms$trade <- "selfsuff_reduced"`.

---

## Regional Self-Sufficiency Enforcement

The `selfsuff_reduced` realization enforces self-sufficiency through a **production band** bounded below and above by two mirror equations, both operating at the **superregional** (`h`) level (not per-region `i`):

### Lower bound: `q21_trade_reg` (`equations.gms:31-35`)

```gams
q21_trade_reg(h2,k_trade)..
 sum(supreg(h2,i2),vm_prod_reg(i2,k_trade)) =g=
  m21_baseline_production(vm_supply, v21_excess_prod, f21_self_suff)
  * sum(ct,i21_trade_bal_reduction(ct,k_trade))
  - v21_import_for_feasibility(h2,k_trade);
```

The macro `m21_baseline_production` (defined in `core/macros.gms:115-119`) expands to a two-branch expression:

- **Exporters** (`f21_self_suff >= 1`): baseline = supply + excess production
- **Importers** (`f21_self_suff < 1`): baseline = supply x self-sufficiency ratio

The lower bound multiplies this baseline by `i21_trade_bal_reduction(t,k)` (the pool-allocation factor, 0-1) and subtracts `v21_import_for_feasibility` (emergency valve, non-zero only for `wood` and `woodfuel`).

### Upper bound: `q21_trade_reg_up` (`equations.gms:39-42`)

```gams
q21_trade_reg_up(h2,k_trade)..
 sum(supreg(h2,i2),vm_prod_reg(i2,k_trade)) =l=
  m21_baseline_production(vm_supply, v21_excess_prod, f21_self_suff)
  / sum(ct,i21_trade_bal_reduction(ct,k_trade));
```

Same macro, but **divided** by `i21_trade_bal_reduction` instead of multiplied — forming a symmetric band around baseline production.

### The pool-allocation mechanism

`i21_trade_bal_reduction(t,k)` controls how much of demand enters each of two pools:

- **Value = 1** (self-sufficiency pool): production must track demand via historical self-sufficiency ratios `f21_self_suff(t,h,k)` from input file `f21_trade_self_suff.cs3`. Ratios < 1 mean the region imports; ratios > 1 mean it exports. The band is tight.
- **Value = 0** (comparative advantage pool): band collapses, free global allocation by cost efficiency.

In `preloop.gms:11-19`, until `sm_fix_SSP2` the historical regime `l909090r808080` is applied; afterwards the scenario switches to `%c21_trade_liberalization%` (default `l909090r808080`). The `k_hardtrade21` subset (16 secondary and livestock products) receives a stricter reduction factor than the remaining "easy trade" commodities to prevent unrealistic regional specialization.

### Global balance: `q21_trade_glo` (`equations.gms:12-14`)

```gams
q21_trade_glo(k_trade)..
  sum(i2, vm_prod_reg(i2,k_trade)) =g=
  sum(i2, vm_supply(i2,k_trade)) + sum(ct,f21_trade_balanceflow(ct,k_trade));
```

This ensures global production covers global supply (plus exogenous balance flows) — the market-clearing condition for the comparative advantage pool.

---

## k_trade vs k_notrade

Both sets are defined in `modules/21_trade/selfsuff_reduced/sets.gms:11-21`.

### k_notrade (8 commodities) — superregional self-sufficiency via `q21_notrade`

```gams
q21_notrade(h2,k_notrade)..
  sum(supreg(h2,i2),vm_prod_reg(i2,k_notrade)) =g= sum(supreg(h2,i2), vm_supply(i2,k_notrade));
```

Must be produced within the super-region; no global pool. Members: `oilpalm` (FAOSTAT complications), `foddr`, `pasture` (too bulky), `res_cereals`, `res_fibrous`, `res_nonfibrous` (residues), `begr`, `betr` (bioenergy — traded in REMIND, not MAgPIE).

Note: this is **superregional** self-sufficiency (`h`), not per-region (`i`). Production can be reallocated among individual regions within a super-region to meet the aggregate constraint.

### k_trade (38 commodities) — subject to the production band

All crops, processed products, livestock products, fish, and forestry products. Within this set, `k_hardtrade21` (16 items: secondary products + all livestock) receives a higher trade balance reduction factor, restricting international trade further and preventing extreme specialization.

The key distinction is **where market clearing occurs**:
- `k_notrade`: enforced at super-region level; no global pool at all.
- `k_trade`: lower and upper production bounds (self-sufficiency pool) plus a global production constraint (comparative advantage pool); the two pools blend according to `i21_trade_bal_reduction`.

---

## All Key Equations (default `selfsuff_reduced`, 9 total)

| Equation | Dimension | Purpose |
|---|---|---|
| `q21_trade_glo` | `(k_trade)` | Global production >= global supply + balance flows |
| `q21_notrade` | `(h,k_notrade)` | Superregional production >= supply for non-tradables |
| `q21_trade_reg` | `(h,k_trade)` | Lower production bound (min self-sufficiency) |
| `q21_trade_reg_up` | `(h,k_trade)` | Upper production bound (max self-sufficiency) |
| `q21_excess_dem` | `(k_trade)` | Global excess demand from importing super-regions |
| `q21_excess_supply` | `(h,k_trade)` | Distributes excess demand to exporters via `i21_exp_shr` |
| `q21_cost_trade_tariff` | `(h)` | Superregional tariff costs -> `vm_cost_trade_tariff` |
| `q21_cost_trade_margin` | `(h)` | Superregional transport margin costs -> `vm_cost_trade_margin` |
| `q21_cost_trade_feasibility` | `(h)` | Emergency import penalty -> `vm_cost_trade_feasibility` |

Note: The three cost equations replace the former combined pair (*q21_cost_trade_reg* + *q21_cost_trade*) removed in PR #866.

---

## Which Modules Consume vm_prod_reg and vm_supply

These are **interface variables consumed by Module 21**, not provided by it.

### vm_prod_reg(i,k) — provided by Module 17 (Production)

Module 21 reads `vm_prod_reg` in every trade balance equation (`q21_trade_glo`, `q21_notrade`, `q21_trade_reg`, `q21_trade_reg_up`, `q21_cost_trade_tariff`, `q21_cost_trade_margin`). From Module 21's perspective this is an upstream input.

Within the model as a whole, `vm_prod_reg` is produced by Module 17 and consumed by Module 21 to enforce trade balances. The Cycle C5 circular dependency (Module 16 -> Module 21 -> Module 17 -> Module 16) means all three are solved simultaneously in one GAMS SOLVE statement.

### vm_supply(i,k) — provided by Module 16 (Demand)

Module 21 reads `vm_supply` in `q21_trade_glo`, `q21_notrade`, `q21_trade_reg`, `q21_trade_reg_up`, `q21_excess_dem`, `q21_cost_trade_tariff`, `q21_cost_trade_margin`. This is the regional demand signal that self-sufficiency constraints are anchored to.

The module docs note that `vm_supply` is provided by Module 16 and `vm_prod_reg` is provided by Module 17 (`modules/21_trade/selfsuff_reduced/declarations.gms` cross-verified with Module 17 `equations.gms:17` and Module 16 `equations.gms`).

---

## Epistemic Status

🟡 **Documented** — Based on `magpie-agent/modules/module_21.md`, which was verified against the full `selfsuff_reduced` source file set including `declarations.gms`, `equations.gms`, `preloop.gms`, `presolve.gms`, `sets.gms`, `input.gms`, `scaling.gms`, and `core/macros.gms:115-119`, as well as `config/default.cfg:644-708` and Module 11 consumption at `modules/11_costs/default/equations.gms:30-32`. No raw GAMS code was read in this session per task instructions.

Source: `magpie-agent/modules/module_21.md`
