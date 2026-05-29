# Audit Report: Q4 (Module 37 Labor Productivity — Default State, Non-Default Pathway, Cost-Objective Feed-Through)

**Round**: R28
**Auditor**: Opus (adversarial)
**Verification worktree**: `/tmp/magpie-develop-r28/` @ `ee98739fd` (clean origin/develop)
**Answer file**: `magpie-agent/audit/archive/rounds/round28_answers/q4_answer.md`

---

### Overall Verdict: MOSTLY ACCURATE
### Accuracy Score: 8/10

The answer nails the high-stakes axis the question targets: it correctly leads with the **`off` default**, states `pm_labor_prod = 1` everywhere, is explicit about what is NOT active by default, and correctly gates the entire heat-stress mechanism behind the non-default `exo` + `sticky_labor` combination. No wrong-default, no non-default-as-active, no invented names, no wrong cost attribution. The single content defect is a **non-verbatim `q38_ces_prodfun` GAMS block** quoted as if it were the code — and that defect is **inherited verbatim from module_38.md §3.1**, so a latent doc bug is recorded and the doc must be fixed this session.

---

### Mechanical checks

| # | Check | Result | Note |
|---|---|---|---|
| M1 | File:line citations present | PASS | Many exact citations (off/preloop.gms:8, sticky_feb18/presolve.gms:8-10, equations.gms:15/15-47/10, declarations.gms:16) |
| M2 | Active realization stated | PASS | Leads with `off` (M37) and `sticky_feb18` (M38), both flagged as default; non-defaults clearly marked |
| M3 | Variable prefixes valid | PASS | `pm_labor_prod`, `vm_cost_prod_crop`, `vm_cost_glo`, `v11_cost_reg`, `s38_ces_elast_*`, `f37_labor_prod` all correct prefixes |
| M4 | Epistemic badges | PARTIAL | §"Source Confidence" carries 🟢/🟡; body claims mostly unbadged (Informational, not scored) |
| M5 | Confidence tier matches depth | PASS | sticky_labor CES explicitly tagged "🟡 Documented without file:line" — honest |
| M6 | Closing source statement | PASS | "All factual identifiers ... copied directly from documentation"; per-claim source map provided |

---

### Verified Claims (correct against code)

- **M37 default = `off`**: `config/default.cfg:1214` → `cfg$gms$labor_prod <- "off"`. ✓
- **M37 realizations are exactly {`off`, `exo`}**: `ls modules/37_labor_prod/` → `off/`, `exo/`. ✓ ("exo" correctly identified as the only non-default.)
- **`off` action `pm_labor_prod(t,j) = 1;`**: `modules/37_labor_prod/off/preloop.gms:8` — exact statement, exact line. ✓
- **`pm_labor_prod` producing module + name**: declared in M37 (`off/declarations.gms:9`, `exo/declarations.gms:9`) as `pm_labor_prod(t,j) labor productivity factor (1)`. Producer = Module 37, exact name confirmed. ✓
- **`exo` slice expression**: `exo/preloop.gms:8` = `pm_labor_prod(t,j) = f37_labor_prod(t,j,"%c37_labor_rcp%","%c37_labor_metric%","%c37_labor_intensity%","%c37_labor_uncertainty%");`. Answer's quote matches (line 8 correct). ✓
- **Config globals** `c37_labor_rcp / _metric / _intensity / _uncertainty / _prod_scenario`: `exo/input.gms:8,13-16`. ✓ Scenario paths (cc/nocc/nocc_hist) are exo-only logic (`exo/preloop.gms:9-11`, `input.gms:8`). ✓
- **Data file + dimensions**: `f37_labourprodimpact.cs3`, table `f37_labor_prod(t_all,j,rcp37,metric37,intensity37,uncertainty37)` (`exo/input.gms:18,20`); sets `rcp37/metric37/intensity37/uncertainty37` (`exo/sets.gms:9-19`). ✓
- **M38 default = `sticky_feb18`**: `config/default.cfg:1235` → `cfg$gms$factor_costs <- "sticky_feb18"`. ✓
- **sticky_feb18 aborts if `pm_labor_prod != 1`**: `sticky_feb18/presolve.gms:8-10` = `if (smax(j, pm_labor_prod(t,j)) <> 1 OR smin(j, pm_labor_prod(t,j)) <> 1, abort "This factor cost realization cannot handle labor productivities != 1");`. Exact lines, exact mechanism. ✓ (Consequence "check always passes under off" is correct.)
- **`sticky_labor` is the realization that consumes non-unit `pm_labor_prod`**: ✓ (sticky_feb18 aborts; CES + pm_labor_prod live only in sticky_labor).
- **`vm_cost_prod_crop(i,factors)`, factors = {labor,capital}, mio USD17MER/yr, declared sticky_feb18/declarations.gms:16**: declaration line 16 exact; `factors / labor, capital /` (`sticky_labor/sets.gms:15-16`, `sticky_feb18/sets.gms`). ✓
- **q38_cost_prod_labor @ sticky_feb18 equations.gms:15-17; q38_cost_prod_capital @ 21-24**: exact line ranges. ✓
- **sticky_feb18 q38_cost_prod_labor divides by `pm_productivity_gain_from_wages` and does NOT contain `pm_labor_prod`**: `equations.gms:16` has `* (1/pm_productivity_gain_from_wages(ct,i2)) *`; no `pm_labor_prod` present. ✓
- **`s38_ces_elast_subst` default 0.3**: `sticky_labor/input.gms:16` = `/ 0.3 /`; CES `_par = (1/_subst) - 1` (`sticky_labor/preloop.gms:9`). Answer uses `_par` in the equation and `_subst` for the 0.3 value — both names real, used correctly. ✓
- **q11_cost_glo @ equations.gms:10** = `vm_cost_glo =e= sum(i2, v11_cost_reg(i2));` — exact, line 10. ✓ `vm_cost_glo` is the minimized objective. ✓
- **q11_cost_reg @ equations.gms:15-47**, first RHS term = `sum(factors,vm_cost_prod_crop(i2,factors))` — exact, line 15 correct, term-1 claim correct. ✓
- **M11 single realization `default`**: `ls modules/11_costs/` → `default/` only. ✓
- **`pm_productivity_gain_from_wages` from Module 36**: declared `modules/36_employment/exo_may22/declarations.gms`. ✓ (matches answer's chain).

---

### Bugs Found

#### Q4-B1 — Non-verbatim `q38_ces_prodfun` quoted as GAMS code

- **Bug ID**: Q4-B1
- **Severity**: **Major**
- **Class**: 4 (Conceptual pseudo-code presented as actual code)
- **Trigger** (§1 Major): "Right concept, wrong [detail]" + Pattern-4 fenced-GAMS fidelity; first Critical trigger that could fire ("Fabricated formula presented as the code's actual implementation") does **not** fire — the formula is a *simplified real* equation, not fabricated; equation name, variable names, and overall CES structure are all correct.
- **Claim in answer** (§3, fenced ```gams block, lines 56-62):
  ```gams
  (1 - i38_ces_shr(j2,kcr)) * (pm_labor_prod(j2) * pm_productivity_gain_from_wages(i2)
                               * v38_laborhours_need(j2,kcr))**(-s38_ces_elast_par)
  ```
- **Reality in code** (`modules/38_factor_costs/sticky_labor/equations.gms:22`):
  ```gams
  (1 - i38_ces_shr(j2,kcr))*(sum(ct, pm_labor_prod(ct,j2) * sum(cell(i2,j2), pm_productivity_gain_from_wages(ct,i2))) * v38_laborhours_need(j2,kcr))**(-s38_ces_elast_par)
  ```
  The answer (a) drops the `sum(ct, ...)` time-current selector, (b) drops the `sum(cell(i2,j2), ...)` j2→i2 region mapping, (c) writes `pm_labor_prod(j2)` instead of `pm_labor_prod(ct,j2)`, and (d) leaves `i2` as a free/undefined index (in real code `i2` exists only inside the `cell(i2,j2)` sum). As written it is not valid GAMS.
- **File evidence**: `/tmp/magpie-develop-r28/modules/38_factor_costs/sticky_labor/equations.gms:19-23` (full equation verified verbatim).
- **Anchor reference**: R16 Major — "agent fabricated an expanded `q10_land_area` equation by enumerating set members instead of preserving the set-based sum ... would mislead a reader about how the code reads, but not into a wrong code edit." Same class, inverse direction (collapsed sums vs expanded). The economic substance (effective labor = `pm_labor_prod × productivity_gain × laborhours`) the answer states in prose is correct; only the quoted index structure is wrong.
- **Root cause**: `doc_error` inherited — see Q4-D1. The answer reproduced module_38.md §3.1's block faithfully; it did NOT independently mis-derive. (Not `answerer_confabulation`: the doc handed it the simplified block.)
- **tier_uncertainty**: false (R16 anchor pins this class at Major).

---

### Latent doc bugs (recorded independent of answer score; FIX this session per §1.5 / class 15)

#### Q4-D1 — module_38.md §3.1 quotes a non-verbatim `q38_ces_prodfun`

- **Class**: 15 (latent doc error) / Bug_Taxonomy Pattern 4.
- **Severity (by future-reader harm)**: **Major**. A reader copying the doc's fenced GAMS block writes invalid GAMS (free `i2`, missing `ct`/`cell` sums) and misunderstands the time/region aggregation. NOT Critical: equation name, all variable names, realization attribution, and default-vs-alt framing are correct — no wrong-realization or wrong-attribution cascade.
- **Doc line**: `magpie-agent/modules/module_38.md:242-248` (the ```gams block under "### 3.1 CES production function").
  ```gams
  + (1 - i38_ces_shr(j2,kcr)) * (pm_labor_prod(j2) * pm_productivity_gain_from_wages(i2)
                                 * v38_laborhours_need(j2,kcr))**(-s38_ces_elast_par)
  ```
- **Code line**: `modules/38_factor_costs/sticky_labor/equations.gms:22` (see Q4-B1 for the verbatim form).
- **Why it matters for the flywheel**: this is the exact failure mode §1.5 was written to catch — Q4's answerer *trusted the bad doc and reproduced it* (this round it cost a Major; an unfixed doc will keep costing it). The doc's own hedge "(conceptual; verify against `sticky_labor/equations.gms` before quoting)" sits on the *Y = A[...]* math form at line 251, NOT on the fenced GAMS block at 242-248, which is presented as actual code.
- **Suggested fix**: replace the §3.1 fenced GAMS block with the verbatim `equations.gms:19-23` text (including `sum(ct, ...)` and `sum(cell(i2,j2), ...)`), add a `:19-23` file:line per MANDATE 16, and either keep the conceptual `Y = A[...]` form clearly under its existing "(conceptual)" label or move it below the verbatim block. The same simplified block appears nowhere else in the doc (grep `pm_labor_prod(j2)`), so this is a single-site fix.

---

### Non-bugs considered and dismissed

- **"200 MAgPIE cells"** (answer §1): `j` is the cluster set; 200 is the standard default but config-dependent. Inherited from module_37.md (lines 388, 458) which uses the same convention. Contextual, does not alter mechanism understanding → Informational, not counted.
- **"10% drop in labor productivity yields ~3% shift toward capital"** (§3 line 65): a 🔵 economic gloss on σ = 0.3, explicitly framed as interpretation, not quoted as code. Heuristic and roughly right in spirit; not a code claim → not scored. (Mirrors module_38.md:265's analogous gloss.)
- **Omission of exo `nocc`/`nocc_hist` lines 9-11 from the §2 quote**: the answer quotes only the line-8 slice but explicitly enumerates the scenario switch under §1 "What is NOT active." Acceptable abstraction, not a bug.

---

### Missing Nuances

- The answer's chain diagram labels the `v11_cost_reg` step `equations.gms:15-47` (correct) but the §4 prose cites `q11_cost_reg` at `equations.gms:15` only; both are fine since 15 is the equation's first line.
- The answer does not mention that in `sticky_labor` the labor-productivity effect enters the **cost** only indirectly (via the CES constraint setting `v38_laborhours_need`), since `sticky_labor`'s own `q38_cost_prod_labor` (equations.gms:39-41) is `vm_prod × v38_laborhours_need × pm_hourly_costs` and contains neither `pm_labor_prod` nor `pm_productivity_gain_from_wages`. The answer's §3 framing ("CES forces higher factor requirements → raises both slices of vm_cost_prod_crop") is correct in mechanism, but a sharper answer would have noted the cost equation itself is productivity-free in sticky_labor (the effect is fully routed through the requirement variables). Minor descriptive incompleteness, not an error → not scored.

---

### Scoring

```
raw_severity_weighted = 4·(0 critical) + 2·(1 major) + 1·(0 minor) + 0·(informational) = 2
score_0_10 = max(0, 10 - 2) = 8
```

- Critical: 0  | Major: 1 (Q4-B1) | Minor: 0 | Informational: 0
- Latent doc bugs: 1 (Q4-D1, Major by future-reader harm; does NOT reduce the answer score; fix this session).

**doc_quality classification**: Q4's only answer-scoring bug (Q4-B1) is rooted in a doc error (Q4-D1), NOT answerer confabulation → Q4 STAYS IN the `doc_quality_mean` set.

---

### Summary

Q4 is a strong, correctly-gated answer (8/10, Mostly Accurate). Every high-stakes fact is right and verified against code: `off` default, `pm_labor_prod = 1`, the sticky_feb18 abort guard, the full M38→M11 cost chain, and the variable/equation/realization names. The lone defect is a simplified `q38_ces_prodfun` quoted as GAMS — and it is **inherited from module_38.md §3.1**, the precise "answerer trusts a wrong doc" pattern §1.5 exists to break. Fix module_38.md:242-248 to the verbatim `sticky_labor/equations.gms:19-23` this session so the next round's answerer doesn't reproduce it.
