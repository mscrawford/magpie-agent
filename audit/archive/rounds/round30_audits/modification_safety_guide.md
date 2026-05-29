# Audit Report: Round 30 — Highest-centrality modules / what breaks if you change M10 or M11

**Question (anchored on `cross_module/modification_safety_guide.md`)**: Which MAgPIE modules are highest-centrality and riskiest to modify, and why? What downstream interfaces break if I change module 10 (land) or module 11 (costs)?

**Ground truth**: develop worktree `/tmp/magpie_develop_ro` + `config/default.cfg`. Whole-tree greps (find+grep and rg), each isolated, with positive controls.

---

## Overall Verdict: SIGNIFICANT ERRORS
## Accuracy Score: 3/10

raw_severity_weighted = 4·1 (Critical) + 2·1 (Major) + 1·1 (Minor) = 7 → score = max(0, 10 − 7) = **3**.

The Critical is partially mitigated (counts + 18-module union correct, two entries hedged), but the trigger (wrong consumer sets on a modification-safety question, R20 anchor) fires squarely. Per the immutable R20 anchor a wrong consumer set is Critical even when adjacent facts are right; the tie-breaker (pick-lower) applies only to genuine two-tier ambiguity, and the harm here (user sent to wrong files + misses real consumers on the exact question asked) clears the Critical bar. Not downgraded. Final = **3/10**.

---

## What the answer got RIGHT (verified in code)

- **Centrality top-4 + ranks** (M11=28/1/27, M10=17/15/2, M56=16/13/3, M32=16/5/11; M17 rank 7, 14 conns): matches `Module_Dependencies.md` §1.2 and the structural reality. Not independently re-derivable from a single grep, but internally consistent and doc-cited. ✓
- **Realizations**: M10 = `landmatrix_dec18` (only realization; default per `config/default.cfg:232`); M11 = `default` (only realization; `config/default.cfg:236`). ✓ (M2 satisfied.)
- **M10 declares `pcm_land`**: YES — `modules/10_land/landmatrix_dec18/declarations.gms:11`. The answer's "five interface variables incl. pcm_land" is correct on the declaration. ✓
- **`vm_land` consumer set (10 modules: 22,29,30,31,32,34,35,50,58,59)**: EXACT match to whole-tree grep (`\bvm_land\b`, excl 10_land). ✓ This is the load-bearing set and it is right.
- **`land` set = 7 types** (crop, past, forestry, primforest, secdforest, urban, other): `core/sets.gms:250-251`. ✓
- **`q10_land_area` formula** `sum(land, vm_land(j2,land)) =e= sum(land, pcm_land(j2,land))`: verbatim match, `modules/10_land/landmatrix_dec18/equations.gms:13-15`. Set-based sum preserved (MANDATE 10 ✓).
- **Equation names** `q10_transition_to`, `q10_transition_from`, `q11_cost_glo`, `q11_cost_reg`: all exist, correctly named. ✓
- **18-module union touched by any M10 interface var** (11,13,14,22,29,30,31,32,34,35,39,44,50,56,58,59,71,80): EXACT match to the code union across all 9 M10 interface vars. ✓
- **`q11_cost_glo`** `vm_cost_glo =e= sum(i2, v11_cost_reg(i2))`: verbatim, `modules/11_costs/default/equations.gms:10`. ✓
- **M11 = pure aggregator, no input data / no parameters / two equations**: confirmed — `modules/11_costs/default/` has no `input.gms`; declarations are 2 vars + 2 eqs + `ov*/oq*` output params only. ✓
- **q11_cost_reg: 32 terms, 31 positive + 1 negative (`- vm_reward_cdr_aff`)**: EXACT — 1 head term + 30 leading-`+` + 1 leading-`-`; the sole negative is `vm_reward_cdr_aff` (`equations.gms:27`). ✓
- **`vm_reward_cdr_aff` is the only legitimate negative; M56 design**: declared M56; correct. ✓
- **27 upstream provider modules feed q11_cost_reg**: distinct declaring modules of the 32 terms = exactly 27 (10,13,18,20,21,29,30,31,32,34,35,38,39,40,41,42,44,50,54,56,57,58,59,60,70,71,73). ✓
- **`vm_cost_glo` = objective, exactly 1 downstream consumer (the solver / M80)**: `solve magpie USING nlp MINIMIZING vm_cost_glo` in M80 (`nlp_apr17/solve.gms:34`, etc.); `vm_cost_glo` consumed only by 80_optimization. ✓
- **Hard-failure (M10/infeasibility) vs silent-failure (M11/free-lunch) asymmetry**: conceptually sound; missing-cost = implicit zero = unbounded exploitation is the correct mechanism. ✓
- **`vm_lu_transitions` tracks GROSS between-type transitions, not net stock differences**: CORRECT per `module_10_notes.md:13,15` and the equation structure — and it **beat a wrong doc** (see latent bug L1).

---

## Bugs Found

### Bug Q30-B1 — Confabulated per-variable consumer sets (CRITICAL)
- **Severity**: Critical
- **Class**: 2 (Hallucinated/mis-attributed consumer set) / aligns with R20 anchor (wrong consumer set on a modification question)
- **Trigger (§1 Critical)**: "build on a false foundation … load-bearing modification" — the question is *what breaks if I change M10*; the named consumer sets are the actionable answer and they point at the wrong modules.
- **Root cause**: `answerer_confabulation` (the docs had the CORRECT sets; the answer ignored them and invented plausible names).
- **Claim in answer** (M10 table, "Named consumers"):
  - `pcm_land` → "11, 13, 14, 39, 44, 56, 71, 80"
  - `vm_landexpansion` → "39, 52, 56 + downstream"
  - `vm_landreduction` → "52, 56"
  - `vm_lu_transitions` → "32, 39, 44"
- **Reality in code** (whole-tree grep, 2 methods + positive controls):
  - `pcm_land` consumers = **13, 22, 29, 31, 32, 34, 35, 44, 56, 58, 59, 71** (12). The answer's 11/14/39/80 are PHANTOMS for `pcm_land` (they touch M10 via *other* interfaces: 11←`vm_cost_land_transition`, 14←`pm_land_start`, 39←`vm_landexpansion/reduction`, 80←`vm_landdiff`/`vm_cost_glo`). Only 13/44/56/71 of the named set are real.
  - `vm_landexpansion` consumers = **35, 39, 58, 59**. Named 52, 56 are PHANTOMS; only 39 correct.
  - `vm_landreduction` consumers = **39, 58**. Named 52, 56 are BOTH PHANTOMS.
  - `vm_lu_transitions` consumers = **29, 35, 59**. Named 32, 39, 44 are ALL PHANTOMS.
- **File evidence**:
  - `modules/52_carbon/` and `modules/56_ghg_policy/` contain ZERO hits for `vm_landexpansion`/`vm_landreduction` (rg + find, positive control: `vm_landexpansion` IS found in `modules/39_landconversion/calib/equations.gms:13`).
  - `modules/32_forestry/`, `modules/39_landconversion/`, `modules/44_biodiversity/` contain ZERO hits for `vm_lu_transitions` (positive control: found in `modules/29_cropland/.../equations.gms`).
  - `modules/{11,14,39,80}/` contain ZERO `\bpcm_land\b` hits (positive control: `modules/29_cropland/.../presolve.gms:29` has it).
  - Correct sets per code match `cross_module/land_balance_conservation.md:227-228` and `modules/module_10.md:344,299-304` — i.e., the docs were right and available.
- **Why Critical, not Major**: directly answers a modification-safety question. A user told "`vm_lu_transitions` breaks M32/M39/M44" would (a) audit three modules that don't consume it and (b) miss M29/M35/M59 that do. For `vm_landreduction`, told "52/56" they audit two non-consumers and miss the real 39/58. This is the R20 anchor pattern (wrong consumer set → missed modules in a refactor → Critical). The counts (12/4/2/3) and the 18-module union are correct, and the `pcm_land`/`vm_landexpansion` entries carry "including"/"+downstream" hedges — mitigating, but naming hard non-consumers (52, 56, 32, 44, 80) is not excused by a hedge.
- **Anchor reference**: R20 (`pm_carbon_density_ac` wrong-consumer-set → Critical).

### Bug Q30-B2 — M52 "reads vm_land to compute vm_carbon_stock" (MAJOR)
- **Severity**: Major
- **Class**: MANDATE 17 (direct vs transitive consumer) / G2-class producer-vs-consumer confusion
- **Trigger (§1 Major)**: "wrong in a way that misleads about behavior" on a dependency claim.
- **Root cause**: `answerer_confabulation`.
- **Claim in answer** (M10 §4 cascade): "carbon balance (M52 reads `vm_land` to compute `vm_carbon_stock`)".
- **Reality**: M52 does **not** read `vm_land` (zero hits in `modules/52_carbon/`). M52 reads `vm_carbon_stock` (`modules/52_carbon/normal_dec17/equations.gms:19`) to compute CO2 *emissions* from stock change. `vm_carbon_stock` is DECLARED in M56 (`price_aug22/declarations.gms:34`) and POPULATED by land modules (29,31,32,34,35) + 59 (G2 anchor). The cascade direction (M10 → land modules → carbon stock → M52) is right; the stated mechanism ("M52 reads vm_land", "to compute vm_carbon_stock") is wrong on both halves.
- **File evidence**: `rg '\bvm_land\b' modules/52_carbon/` → none; `modules/52_carbon/normal_dec17/equations.gms:19` reads `vm_carbon_stock`; declaration site `modules/56_ghg_policy/price_aug22/declarations.gms:34`.
- **Anchor reference**: MANDATE 17 R24 Q4-B3; G2 producer/consumer distinction.

### Bug Q30-B3 — M43 named as irrigation-demand consumer of vm_land (MINOR)
- **Severity**: Minor
- **Class**: 6/17 (module mis-number + transitive var) within a cascade summary
- **Trigger (§1 Minor)**: "wrong detail, careful reader not misled into action."
- **Root cause**: `answerer_confabulation`.
- **Claim**: "water balance (M43 irrigation demand is area-dependent)".
- **Reality**: Irrigation *demand* is Module **42** (`42_water_demand`), not 43 (`43_water_availability` = supply). And M42's irrigation water equation reads `vm_area(j2,kcr,"irrigated")` (M30), NOT `vm_land` (`modules/42_water_demand/all_sectors_aug13/equations.gms:12`). The cascade is loosely right (M10 land → M30 area → M42 water) but the module number and variable are both off. Minor because it sits in a one-line "cascade" summary, not a load-bearing table.

---

## Latent doc bugs (record regardless of answer score — §1.5)

### L1 — `modification_safety_guide.md:47` mislabels vm_lu_transitions as "(net changes only)"
- **Doc**: `cross_module/modification_safety_guide.md:47` — table row `vm_lu_transitions(j,land_from,land_to) | 3 modules | 🟠 HIGH | Transition matrix (net changes only)`.
- **Code reality**: `vm_lu_transitions` is the GROSS between-type transition matrix. `q10_transition_to/from` (`equations.gms:19-25`) and `q10_landexpansion/reduction` (`equations.gms:30-38`) compute gross flows from one land class to another (both directions). `module_10_notes.md:13,15,25` explicitly document this and flag the net/gross conflation as a recurring R15 error "in 8 locations." Line 47 is a 9th instance, in the authoritative modification reference.
- **Root cause**: `doc_error_answerer_beat_it` — the answer correctly said "gross between-type transitions, not net stock differences," beating the doc.
- **Severity (future-reader harm)**: Major. A reader trusting "net changes only" mis-models land-use-change accounting (net stock ≠ gross transitions is a real, flagged distinction). Fix: change "(net changes only)" → "(gross between-type transitions)" at line 47.
- **Fix-this-session**: yes (per §1.5 mandate, independent of the answer's score).

> Note: the per-variable CORRECT consumer sets DO exist in the docs (`land_balance_conservation.md:227-228`, `module_10.md:344,299-304`), so Q30-B1 is NOT a latent doc bug — the docs are well-maintained there; the answer simply failed to use them.

---

## Mechanical checks
- M1 (file:line): PARTIAL — answer quotes `q11_cost_glo`/`q10_land_area` GAMS blocks and cites doc sections, but gives no explicit `modules/.../equations.gms:NN`. Acceptable for a 🟡 documented answer; flagged, not scored.
- M2 (active realization): PASS (M10 landmatrix_dec18, M11 default; both noted as only/default).
- M3 (prefixes): PASS.
- M4/M5 (epistemic badges): PASS (🟡 closing block, correct tier).
- M6 (closing source statement): PASS.

---

## Missing nuances
- `pcm_land` is the *previous-timestep* land state; it is read in `q10_land_area`/`q10_transition_from` and re-set in `postsolve.gms:9`. The answer treats it purely as an "exported" var; fine for scope.
- The answer's "1 downstream consumer (the solver)" is precisely Module 80 (`solve … MINIMIZING vm_cost_glo`). Correct and worth the explicit M80 pin.

---

## Summary
Spine is strong and largely verified: realizations, the `vm_land` 10-consumer set, the 18-module union, both M10 conservation/transition equations, the full q11_cost_reg term count (32; 31+/1−), the 27 providers, and the single-consumer objective are all correct against code — and the answer correctly called the transition matrix "gross," beating a wrong doc label (latent L1). The damage is concentrated in the M10 per-variable "Named consumers" column: for `vm_landexpansion`/`vm_landreduction`/`vm_lu_transitions` (and half of `pcm_land`) the answer invented plausible-but-wrong consumer modules (52, 56, 32, 44, 80, 11, 14, 39) while the COUNTS stayed right — exactly the R20 wrong-consumer-set failure, and exactly the question the user asked. Plus a MANDATE-17 mis-attribution (M52 "reads vm_land") and a Minor M42/M43 swap. Score 3/10.
