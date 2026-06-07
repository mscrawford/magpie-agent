# Round 49 — Adversarial Verification: modification_safety_guide.md

Target: `/Users/turnip/Documents/Work/Workspace/magpie/magpie-agent/cross_module/modification_safety_guide.md`
Ground truth: `/tmp/magpie_develop_ro` (develop worktree, read-only)
Verifier posture: default skepticism; both negative/consumer claims confirmed twice + positive control.

---

## BUG-1 — UPHELD (consumer_set, MANDATE 17 direct-vs-transitive)

**Doc claim (lines 353-357):** diagram routes `vm_prod_reg(i,kall)` from Module 17 to Module 21 (Trade) → Module 16 (Demand) → Module 11 (Costs) → Module 73 (Timber) → "9 other modules".

**Severity:** Major (latent doc error; contradicts the doc's own §3.2 table and Appendix B).

### Step A — Mechanical citation check (citation_ok = TRUE)
```
$ test -f .../17_production/flexreg_apr16/declarations.gms  -> EXISTS
$ wc -l .../declarations.gms                                -> 27  (line 10 in range)
$ sed -n '10p'  -> " vm_prod_reg(i,kall)   Regional aggregated production (mio. tDM per yr)"
```
Line 10 contains the claimed identifier `vm_prod_reg(i,kall)`. PASS.

### Step C — Independent re-derivation of the consumer set
grep BOTH forms across the whole module tree, excluding producer 17:
```
$ rg -l 'vm_prod_reg\(' /tmp/magpie_develop_ro/modules/
   50_nr_soil_budget, 20_processing, 21_trade(3 realiz), 18_residues(2),
   16_demand, 70_livestock(2), 38_factor_costs(2), 71_disagg_lvst(2), 17(decl+eq)
$ rg -l 'vm_prod_reg\.' /tmp/magpie_develop_ro/modules/   (.l/.lo/.up/.fx/.m)
   17_production/postsolve.gms, 71_disagg_lvst/preloop.gms (x2)
   -> adds NO new module (17 is producer; 71 already in set)

Distinct module numbers (both forms, minus 17): 16 18 20 21 38 50 70 71  -> COUNT = 8
```
This is EXACTLY the set the doc's own recompute note (line 338, 2026-05-24) records:
"vm_prod_reg reaches 16, 18, 20, 21, 38, 50, 70, 71". §3.2 table (line 335) = "8 modules";
Appendix B (line 1082) = "8". The diagram is the only place that disagrees.

### Negative claims (highest-risk false positives) — confirmed twice + positive control
**11_costs does NOT read vm_prod_reg:**
```
rg 'vm_prod_reg\(' 11_costs/  -> NO MATCH
rg 'vm_prod_reg\.' 11_costs/  -> NO MATCH
rg 'vm_prod_reg'   11_costs/  -> NO MATCH (bare)
POSITIVE CONTROL: rg 'vm_cost_processing' 11_costs/ -> default/equations.gms (search works)
```
**73_timber does NOT read vm_prod_reg:**
```
rg 'vm_prod_reg\(' 73_timber/ -> NO MATCH
rg 'vm_prod_reg\.' 73_timber/ -> NO MATCH
rg 'vm_prod_reg'   73_timber/ -> NO MATCH (bare)
POSITIVE CONTROL: rg 'vm_prod\b' 73_timber/ -> default/equations.gms, module.gms (search works)
```
So 73_timber consumes `vm_prod` (cell-level), not `vm_prod_reg` — auditor's "indirect/timber path" rationale is correct. 11_costs reads `vm_cost_*` aggregates, not `vm_prod_reg`.

### Proposed-fix sanity: each of the 8 named modules truly references vm_prod_reg
```
16 YES(16_demand) 18 YES(18_residues) 20 YES(20_processing) 21 YES(21_trade)
38 YES(38_factor_costs) 50 YES(50_nr_soil_budget) 70 YES(70_livestock) 71 YES(71_disagg_lvst)
```
No 9th consumer exists (re-counted: 8). The proposed fix introduces no phantom.

**VERDICT: UPHELD.** corrected_set = the 8 real consumers {16_demand, 18_residues, 20_processing, 21_trade, 38_factor_costs, 50_nr_soil_budget, 70_livestock, 71_disagg_lvst}. Remove 11_costs and 73_timber from the arrow and drop the "9 other modules" tail. Matches auditor's proposed_fix exactly.

---

## BUG-2 — NOT_REVIEWABLE (other: parameter default value) — citation PASS, value confirmed

**Doc claim (line 478):** `c56_pollutant_prices | Default: SSP2-NPi2025`.
**Severity:** Minor (stale string; concept right, exact scenario token incomplete).

### Step A — Mechanical citation check (citation_ok = TRUE)
```
$ sed -n '1713p' config/default.cfg
  cfg$gms$c56_pollutant_prices <- "R34M410-SSP2-NPi2025"     # def = R34M410-SSP2-NPi2025
$ wc -l config/default.cfg -> 2425  (1713 in range)

$ sed -n '84p' modules/56_ghg_policy/price_aug22/input.gms
  $setglobal c56_pollutant_prices  R34M410-SSP2-NPi2025
$ wc -l input.gms -> 117  (84 in range, and doc cites range 84-117)
```
Both cited lines exist, in range, and contain the real default `R34M410-SSP2-NPi2025`.
Doc's `SSP2-NPi2025` is a substring missing the `R34M410-` scenario-protocol prefix. Auditor's reality_in_code reproduces exactly.

**VERDICT: NOT_REVIEWABLE** (value/prose class; citation already validated in Step A → pass to fixer unchanged). corrected value = `R34M410-SSP2-NPi2025`.

---

## Summary
- BUG-1: UPHELD — vm_prod_reg has exactly 8 direct consumers; diagram falsely adds 11_costs + 73_timber + inflated tail. Re-derived set matches doc's own line 338/335/1082. Negatives confirmed 2 methods + positive control.
- BUG-2: NOT_REVIEWABLE (value), citation_ok — default is `R34M410-SSP2-NPi2025`, doc has truncated `SSP2-NPi2025`.
Both fixes safe to apply as the auditor proposed.
