# Doc Audit: core_docs/Query_Patterns_Reference.md

**Round 50 doc-audit sweep**
**Auditor**: adversarial doc auditor (Opus, highest capability)
**Ground truth**: `/tmp/magpie_develop_ro` (develop worktree) + `config/default.cfg`
**Date**: 2026-06-06

---

## Scope & character of the doc

`Query_Patterns_Reference.md` is primarily a **methodology / response-pattern** guide (5 patterns: parameterized-vs-implemented detection, cross-module tracing, temporal mechanism, calculate/model/simulate handler, debugging decision tree). Most content is prose advice and *labeled illustrative* examples ("Conceptually", "Response Pattern", "Warning Signs / RED FLAGS"). However it embeds a substantial set of **concrete, code-checkable claims** inside its worked examples — interface variable/equation names, four hard `file:line` citations, set names, a parameter default, a decay formula, and a numeric convergence table. These were all enumerated and verified.

The doc is unusually accurate. The four hard file:line citations are all EXACT against current develop, the G2 carbon-stock producer-vs-consumer distinction is stated correctly (M59 populates the soilc pool, M52 only reads `vm_carbon_stock`), and the parameter default it flags is correct. **One** code-derivable numerical error was found (a single entry in the convergence table), with internal evidence (the formula one line above contradicts it).

---

## Verified claims (correct)

### Realizations / defaults
- cropland default = `detail_apr24` — `config/default.cfg:795` ✓ (`rg 'gms\$cropland'`)
- carbon default = `normal_dec17` — `config/default.cfg:1556` ✓
- som default = `cellpool_jan23` — `config/default.cfg:1916` ✓
- All three realization dirs exist (`ls`): `29_cropland/{detail_apr24,simple_apr24}`, `52_carbon/normal_dec17`, `59_som/{cellpool_jan23,static_jan19}`.
- RED FLAG #4 example `s29_treecover_target = 0` (qpat:73) — `config/default.cfg:849 cfg$gms$s29_treecover_target <- 0 # def = 0` ✓ CONFIRMED.

### Pattern 2 — tree-cover → SOM → carbon chain (qpat:108-124)
- `v29_treecover(j,ac)` — declared `modules/29_cropland/detail_apr24/declarations.gms:40` ✓
- `q29_treecover` aggregates to `vm_treecover(j)` — `modules/29_cropland/detail_apr24/equations.gms:83-84` ✓ **EXACT** (doc cites :83-84; code at 83-84).
- `vm_treecover` declared `declarations.gms:39` ✓
- `i59_cratio_treecover = 1.0` (doc) — code `i59_cratio_treecover = 1;` at `modules/59_som/cellpool_jan23/preloop.gms:82` ✓ (1 == 1.0).
- Formula `vm_treecover × i59_cratio_treecover` — `modules/59_som/cellpool_jan23/equations.gms:26` ✓
- M59 POPULATES soilc pool of `vm_carbon_stock(j,land,"soilc",stockType)` — `modules/59_som/cellpool_jan23/equations.gms:62` (eq `q59_carbon_soil`, LHS at line 62) ✓ **EXACT**.
- M52 READS `vm_carbon_stock` in `q52_emis_co2_actual` — `modules/52_carbon/normal_dec17/equations.gms:16-19` ✓ **EXACT**. Doc's statement "it does not aggregate SOM into the stock" is consistent with the G2 anchor (M52 = reader, not populator).

### Pattern 1 — parameterized-vs-implemented detection (qpat:9-74)
- Sets `tillage59`, `inputs59` exist — `modules/59_som/cellpool_jan23/sets.gms:13,16` ✓
- `f59_cratio_tillage` exists — `modules/59_som/cellpool_jan23/input.gms:49` ✓
- `i59_cratio`, `i59_cratio_treecover` exist — `declarations.gms:15,17` ✓
- Tillage hardcoding pattern `i59_tillage_share(i,tillage59)=0;` then `i59_tillage_share(i,"full_tillage")=1;` — `modules/59_som/cellpool_jan23/preloop.gms:52-53` ✓ **EXACT** (doc cites :52-53 at qpat:46). Matches RED FLAG #2 (qpat:65-67) and the worked response (qpat:46).
- RED FLAG #3 comment `*' So far it just tracks the subsystem due to missing data` — actual code comment `modules/59_som/cellpool_jan23/preloop.gms:48` is `*' So far it just tracks the subsystem component due to missing data for the other categories`. Close paraphrase of a real comment; used as an illustrative warning-sign, not a citation. Not a bug.

### Pattern 3 — temporal mechanism (qpat:130-171)
- `q59_som_target_noncropland` — `modules/59_som/cellpool_jan23/equations.gms:31` (decl :29) ✓
- `q59_som_target_cropland` — `equations.gms:20` (decl :28) ✓
- `f59_topsoilc_density` — `input.gms:77`, used in equations ✓
- `vm_lu_transitions(j,land_from,land_to)` — declared `modules/10_land/landmatrix_dec18/declarations.gms:23`, used `equations.gms:20,24,33,38` ✓. Doc's `vm_lu_transitions(j,"secdforest","crop")` is a valid instantiation of the signature. "Location: Module 10 (Land), used in Module 59" ✓ — M59 reads the transition matrix (via local alias `n`) at `modules/59_som/cellpool_jan23/equations.gms` (see comment :55 "land-use transition matrix of the current timestep is used").
- Formula `i59_lossrate(t) = 1 - 0.85^timestep_length` (qpat:153) — code `i59_lossrate(t)=1-0.85**m_yeardiff(t);` at `modules/59_som/cellpool_jan23/preloop.gms:45` ✓ (`m_yeardiff` = years between timesteps = "timestep length"; conceptual rendering is faithful).
- "15% annual movement toward equilibrium" (qpat:152) ✓ (1 − 0.85 = 0.15).
- "20 years: 96% of gap closed" (qpat:157) — `1 − 0.85^20 = 0.961` ✓; "~20 years (96% convergence)" (qpat:169) ✓.
- "10 years: 80% of gap closed" (qpat:156) — `1 − 0.85^10 = 0.803` ✓.

### Pattern 4 — calculate/model/simulate handler (qpat:177-371)
The appendix examples are explicitly *conceptual* (teaching parameterization-vs-mechanistic). Attributions spot-checked against code:
- Example 3 — Module 52 = MECHANISTIC Chapman-Richards growth ✓. `modules/52_carbon/normal_dec17/realization.gms` references the Chapman-Richards growth model; `input.gms` has `f52_growth_par(clcl,chap_par,forest_type)` (the `chap_par` = Chapman parameters), calibrated per region via bisection (`preloop.gms`). Standard C-R form `A(1-exp(-k·age))^m` is correct as an illustrative formula.
- Example 1 — Module 51 = PARAMETERIZED IPCC emission factors ✓. `modules/51_nitrogen/rescaled_jan21/` loads `f51_ef*` from `.cs3` (input.gms `$include .../f51_ef_reg.cs3`); equations apply `i51_ef(...)`. (rg garbled "ef"→"ln" in tool output; substance is the IPCC-EF structure.)
- Example 4 — Module 42 water demand exists (`all_sectors_aug13` default) with `demand × area` structure ✓ (conceptual, no default claim made).
- The "*' So far it just tracks..." and "wildfire/disturbance" examples are generic warning-sign templates, not module-specific citations.

### Pattern 5 — debugging decision tree (qpat:374-409)
- GAMS `modelstat` codes 3=UNBOUNDED, 4=INFEASIBLE, 13=ERROR — standard GAMS semantics (general knowledge, not MAgPIE-specific). Correct. `.m`/`.lo`/`.up` usage and conservation checks are generic advice; not code-checkable claims about specific identifiers.

---

## Bugs found

### BUG qpat-B1 — 5-year SOM convergence percentage inconsistent with the formula

- **Severity**: Minor (tier_uncertainty: true — Major is defensible)
- **Class**: 6 (hardcoded counts/values drift) / numeric error
- **Trigger**: §1 Major "right concept, wrong number" vs §1 Minor "wrong detail, careful reader not misled into action" — tie-breaker pulls down to Minor.
- **Doc line**: qpat:155
- **Claim in doc**:
  ```
  Formula: i59_lossrate(t) = 1 - 0.85^timestep_length   (line 153)
  Rates:
  - 5 years: 44% of gap closed                          (line 155)  ← WRONG
  - 10 years: 80% of gap closed                         (line 156)  ✓
  - 20 years: 96% of gap closed                         (line 157)  ✓
  ```
- **Reality in code**: With `i59_lossrate = 1 − 0.85^t` (the formula stated one line above, matching `preloop.gms:45`), the gap-closed fraction at 5 years is `1 − 0.85^5 = 0.556 = 56%`, NOT 44%. The value `44%` is the **remaining** gap (`0.85^5 = 0.444`). The 10-year (80.3%) and 20-year (96.1%) entries are correctly reported as gap-*closed*; only the 5-year entry was computed as gap-*remaining*, making the table internally inconsistent.
- **File evidence**: `modules/59_som/cellpool_jan23/preloop.gms:45` (`i59_lossrate(t)=1-0.85**m_yeardiff(t);`)
- **verify_cmd**: `python3 -c "print(1-0.85**5, 1-0.85**10, 1-0.85**20)"` → `0.5563 0.8031 0.9612` (5yr = 55.6%, not 44%; 10yr/20yr match doc).
- **confirmed**: true (arithmetic from the code-stated formula; internal inconsistency with lines 156-157 corroborates).
- **proposed_fix**: replace qpat:155 `- 5 years: 44% of gap closed` with `- 5 years: 56% of gap closed`.

**Why not higher**: This sits inside an illustrative "Response Structure" template for a methodology pattern, not a direct behavioral claim about a named variable/equation, and the correct value is one line above (the formula). A careful reader would recompute and catch it. **Why not Informational**: it is a wrong number a less-careful answerer could copy verbatim into a convergence-speed claim (off by ~12 percentage points at 5yr), so it crosses the "wrong detail" threshold above style. Tie-breaker → Minor.

---

## Deferred (not code-verifiable / not edited)

- The convergence "rates" are presented under a "Typical: 60-80% of natural level" equilibrium and "~20 years" practical-equilibrium framing. The 60-80% cropland SOM range (qpat:164) is a representative empirical range (depends on `i59_cratio` per crop/region/cell), not a single code constant — cannot be pinned to one line; left as illustrative.
- Pattern 4 conceptual formulas (`emissions = N_input × fixed_EF × NUE_adjustment`, `demand = water_per_ha × crop_area`, `C(age)=A(1-exp(-k·age))^m`) are explicitly labeled illustrative/conceptual; attributions verified above, but the exact algebraic forms are pedagogical and not claimed as verbatim code, so not flagged.
- Pattern 5 generic conservation/debugging advice (`.m > 0`, "compare to historical 2015 FAO") is methodology, not a code claim.

---

## Summary

22 load-bearing code-checkable claims verified. The doc is highly accurate: all four hard `file:line` citations are EXACT against current develop (29 equations.gms:83-84, 59 equations.gms:62, 52 equations.gms:16-19, 59 preloop.gms:52-53), all realization defaults correct, the G2 carbon-stock producer(M59)-vs-consumer(M52) distinction stated correctly, `s29_treecover_target=0` default confirmed, and `vm_lu_transitions`/`i59_lossrate`/Chapman-Richards attributions all verified. **One** numeric error: qpat:155 "5 years: 44% of gap closed" should be 56% (44% is the remaining gap; contradicts the formula on qpat:153 and the consistent 10yr/20yr entries). Minor (Major defensible).
