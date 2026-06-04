# Audit Report: Q4 (Land-conversion costs M39, transport costs M40, urban land M34 in the objective)

### Overall Verdict: ACCURATE
### Accuracy Score: 9/10

Audited against live GAMS at develop HEAD ee98739fd (clean working tree). All claimed defaults, cost-variable names, equations, and the M39/M40/M34/M11 chain were read from actual `.gms` this session.

---

## Defaults verified (config/default.cfg)

| Module | Claimed default | Actual (default.cfg) | Match |
|--------|-----------------|----------------------|-------|
| M39 landconversion | `calib` | `cfg$gms$landconversion <- "calib"` | ✓ |
| M40 transport | `gtap_nov12` | `cfg$gms$transport <- "gtap_nov12"` | ✓ |
| M34 urban | `exo_nov21` | `cfg$gms$urban <- "exo_nov21"` | ✓ |

## Cost-variable names verified (the high-error class — each checked in its claimed module)

| Variable | Claimed module | Actual declaration site | Module attribution correct? |
|----------|----------------|-------------------------|------------------------------|
| `vm_cost_landcon(j,land)` | M39 | `modules/39_landconversion/calib/declarations.gms:13` | ✓ M39 |
| `vm_cost_transp(j,k)` | M40 | `modules/40_transport/gtap_nov12/declarations.gms:13` | ✓ M40 |
| `vm_cost_urban(j)` | M34 | `modules/34_urban/exo_nov21/declarations.gms:13` | ✓ M34 |

Variable name `vm_cost_transp` (NOT `vm_cost_transport`) confirmed — the equation is `q40_cost_transport`, the variable is `vm_cost_transp`. Answer got this right (a known trap).

---

## Verified Claims (correct)

**(a) M39 — land-conversion costs**
- `vm_cost_landcon(j,land)` declared `calib/declarations.gms:13`. ✓ (answer cited :13)
- Equation `q39_cost_landcon(j2,land)` at `calib/equations.gms:12-15`. ✓ Formula reproduced **exactly**, including `pm_interest(ct,i2)/(1+pm_interest(ct,i2))`.
- Annuity factor `r/(1+r)` with no depreciation term. ✓ Verified in code (eq line 15).
- Module-38 contrast `(r+d)/(1+r)`: VERIFIED — `38_factor_costs/sticky_feb18/equations.gms:23` uses `(pm_interest(ct,i2) + s38_depreciation_rate)/(1+pm_interest(ct,i2))`. sticky_feb18 is the M38 default. Side-claim accurate.
- Driving variables `vm_landexpansion`/`vm_landreduction` come from Module 10: VERIFIED — declared `10_land/landmatrix_dec18/declarations.gms:20-21`. ✓
- Cost depends on TARGET land type only (cost keyed by `land`, the expanding type): consistent with equation structure. ✓
- Base establish costs: crop 12300 (`input.gms:9`), past 9840 (`:11`), forestry 1230 (`:12`), urban 12300 (`:13`). ALL VERIFIED exact, correct line numbers.
- Crop calibration via `i39_calib(t,i,"cost")` at `presolve.gms:12`; reward at `:13`; past `:14`; forestry `:15`; urban `:16`. ALL VERIFIED exact line numbers.
- Reduction reward applies only to cropland (`presolve.gms:13` is the only reward assignment; `s39_reward_crop_reduction`=7380, answer said 7380 implicitly via reward path). ✓
- primforest/secdforest/other stay zero (zeroed in `preloop.gms:8`, never reassigned in presolve). ✓ Outcome correct.

**(b) M40 — transport costs**
- `vm_cost_transp(j2,k)` declared `gtap_nov12/declarations.gms:13`. ✓
- Equation `q40_cost_transport(j2,k)` at `gtap_nov12/equations.gms:11-13`. ✓ Formula `vm_prod(j2,k)*f40_distance(j2)*f40_transport_costs(k)` reproduced **exactly**.
- Scales linearly with vm_prod (from M17), f40_distance (travel time, Nelson 2008), f40_transport_costs (GTAP-7 calibrated). ✓ All three confirmed against equation + doc comments in equations.gms:20-68.
- Pasture exception `s40_pasture_transport_costs = 0` at `input.gms:10`. ✓ (and `input.gms:30` sets `f40_transport_costs("pasture")` to it).
- `off` realization fixes `vm_cost_transp.fx(j,k)=0`: M40 has an `off` dir; claim consistent (not the default). Plausible, not the load-bearing path.
- Path to objective via `q11_cost_reg(i2)` `sum((cell(i2,j2),k), vm_cost_transp(j2,k))` at `11_costs/default/equations.gms:21`. ✓ VERIFIED — `vm_cost_transp` is on line 21.

**(c) M34 — urban land**
- Urban expansion pays `vm_cost_landcon(j,"urban")` via M39's same `q39_cost_landcon` (urban establish cost 12300). ✓ Two-channel claim correct.
- No reduction reward for urban (urban reward zeroed `preloop.gms:9`, never reassigned). ✓
- Urban total is a hard equality `q34_urban_land(i2)` at `equations.gms:30-31`: `sum(cell(i2,j2), vm_land(j2,"urban")) =e= sum((ct,cell(i2,j2)), i34_urban_area(ct,j2))`. ✓ VERIFIED exact, correct lines.
- t=1 fixing `vm_land.fx(j,"urban") = i34_urban_area(t,j)` at `presolve.gms:11` inside `if(ord(t)=1)`. ✓ VERIFIED.
- `vm_cost_urban(j)` via `q34_urban_cell` at `equations.gms:25-26`: `(v34_cost1+v34_cost2)*s34_urban_deviation_cost`. ✓ VERIFIED exact.
- `s34_urban_deviation_cost = 1e6` at `input.gms:13`. ✓ VERIFIED (1e+06).
- Characterized as a technical steering/deviation penalty, not a physical conversion cost; ≈0 in feasible unconstrained solution. ✓ Matches the in-code header comment (equations.gms:9-13: "very strong incentive not to deviate ... safeguards against infeasible outcomes"). v34_cost1/v34_cost2 are POSITIVE variables (declarations.gms:12-15) constrained by `=g=` to the absolute deviation, so the cost is ≥0 and minimized to 0 when achievable. ✓
- Both channels flow through M11 to vm_cost_glo. ✓ `vm_cost_landcon` line 20, `vm_cost_urban` line 45 of `11_costs/default/equations.gms`.

---

## Bugs Found

### Bug Q4-B1
- **Severity**: Minor
- **Class**: 12 (content-level citation mismatch) / 10 (file:line)
- **Trigger**: §1 Minor — "Stale package/realization citation that's recoverable (correct concept, findable in a different location)"; tie-broken DOWN from Major because the variable name is correct and the body text cites the equation correctly.
- **Claim in answer**: Register table (line 147): `vm_cost_urban(j)` | "Declaration file" = "`modules/34_urban/exo_nov21/scaling.gms:8` (scaled); declared in `exo_nov21/equations.gms:25-26`".
- **Reality in code**: `vm_cost_urban(j)` is DECLARED in `modules/34_urban/exo_nov21/declarations.gms:13` (positive variables block). `scaling.gms:8` only sets `vm_cost_urban.scale(j) = 1e3` (a scale statement, not a declaration). `equations.gms:25-26` is the DEFINING EQUATION `q34_urban_cell`, not the declaration. So the table's "Declaration file" column misattributes the declaration site for the M34 row — inconsistent with the M39/M40 rows in the same table, which correctly point to `declarations.gms`.
- **File evidence**: `modules/34_urban/exo_nov21/declarations.gms:13` — `vm_cost_urban(j)          Technical adjustment costs` (under `positive variables`). `scaling.gms:8` — `vm_cost_urban.scale(j) = 1e3;`.
- **Mitigation**: Body text (line 122) correctly says "equation `q34_urban_cell` (`equations.gms:25-26`)". Only the register table's declaration column is wrong, and the variable name itself is right, so a reader is misled only about WHERE the declaration lives — recoverable by a one-line grep.
- **Anchor reference**: none directly; mildest end of the citation-drift family (cf. R20 citation-drift anchor, but that was 13 drifted citations of materially different content; this is a single mis-typed citation-target with the variable name intact).

### Bug Q4-B2
- **Severity**: Informational
- **Class**: 10 (file:line, off-by-one)
- **Trigger**: §1 Informational / §1 Minor boundary — "Off-by-few line citation where adjacent lines say similar things"; tie-broken DOWN to Informational (off by one line, content is the same parameter block).
- **Claim in answer**: line 89 cites `f40_distance(j2)` data at `input.gms:15-21`.
- **Reality in code**: the `f40_distance` parameter block spans `gtap_nov12/input.gms:14-21` (declaration header at line 15, opening `/` at 16). Off by one at the start. The `f40_transport_costs` citation `input.gms:23-28` (line 90) is correct.
- **File evidence**: `modules/40_transport/gtap_nov12/input.gms:14` — `f40_distance(j) Transport distance to urban center (min)`; block closes line 21.
- **Note**: trivial; would not mislead. Recorded for completeness only.

`score = max(0, 10 - 4·0 - 2·0 - 1·1 - 0·1) = 9`. (B1 = 1 Minor; B2 = Informational, weight 0.)

---

## Missing Nuances (not scored — answer was not obligated to cover)

- The body says urban primforest/secdforest/other "are initialized to zero in `preloop.gms:8` and never overwritten." Precise mechanism: `preloop.gms:8` zeros `i39_cost_establish` for the FULL `land` set (not selectively those three); presolve then overwrites crop/past/forestry/urban only, leaving the other three at zero. The OUTCOME stated is correct; the phrasing slightly implies selective zeroing of only those three. Not a bug (conclusion is right), but a more precise reader might want the full-set zeroing noted.
- The answer does not mention that `vm_land.fx(j,"urban")` at t>1 has `.lo=0, .up=Inf` (presolve.gms:13-15), i.e. the cell value is genuinely free post-t1 and only steered by the penalty — the answer says "can deviate, subject to strong punishment costs," which captures this correctly.
- `vm_carbon_stock.fx(j,"urban",...) = 0` (presolve.gms:8) — urban carries no carbon stock; out of scope for a cost question, fine to omit.

---

## Summary

A strong, code-faithful answer. Every load-bearing element verified exact against live GAMS: all three defaults, all three cost-variable names (including the `vm_cost_transp` vs `vm_cost_transport` trap), all three defining equations (formulas reproduced verbatim), the annuity factor, the parameter values (12300/9840/1230/12300; 1e6 deviation cost), the M10-sourced driving variables, the two-channel urban treatment, and the M11 objective aggregation. No hallucinated variables, no wrong equation names, no wrong module attribution, no wrong defaults — the entire high-error cost-attribution surface is clean.

The only deductions are citation hygiene in the closing register table (one mis-attributed declaration site for `vm_cost_urban`, Minor) and one off-by-one input.gms range (Informational). Both are recoverable and do not affect the substantive answer.

No latent doc bugs surfaced: the answer's claims that were checkable against code all held, and the docs it relied on (module_39/40/34.md) produced correct variable names, equations, and defaults. No `doc_error_answerer_beat_it` recorded.

**Score: 9/10 — Accurate.**
