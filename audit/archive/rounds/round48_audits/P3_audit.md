# Audit Report: R48-P3 (Land-balance conservation: q10_land_area, transition matrix, area conservation across timesteps)

### Overall Verdict: ACCURATE
### Accuracy Score: 10/10

Auditor: Opus (Round 48). Ground truth read THIS session from working tree == origin/develop @ ee98739fd.
Default realization of module 10 = `landmatrix_dec18` (verified `config/default.cfg:232`; it is also the ONLY realization — `ls modules/10_land/` shows just `landmatrix_dec18/` + `input/`). The answer correctly states this.

---

### Mechanical checks (M1–M6)
| Check | Result | Note |
|---|---|---|
| M1 file:line present | PASS | Many exact citations (equations.gms:13-15, 19-21, 23-25, 30-33, 35-38, 50-54; postsolve.gms:9; declarations.gms:11). |
| M2 active realization stated | PASS | States `landmatrix_dec18` is the only realization — correct. |
| M3 variable prefixes valid | PASS | `vm_land`, `pcm_land`, `vm_lu_transitions`, `vm_landexpansion`, `vm_landreduction`, `vm_landdiff_natveg`, `vm_landdiff_forestry`, `f10_land` — all valid prefixes, all exist in code. |
| M4 epistemic badges per claim | PARTIAL | Body has no inline 🟢/🟡 badges; only the footer carries a 🟡. Indicator only (Informational), not a content bug. |
| M5 confidence tier matches depth | PASS | Answer is honestly tagged 🟡 (docs-based) and does not over-claim 🟢 code verification. |
| M6 closing source statement | PASS | "🟡 Based on: cross_module/land_balance_conservation.md (primary) and modules/module_10.md (supplementary)." |

---

### Verified Claims (correct):

- **Default/only realization**: `landmatrix_dec18`. ✅ `config/default.cfg:232` (`cfg$gms$land <- "landmatrix_dec18"`); only realization dir present.
- **`q10_land_area` structure**: `sum(land, vm_land(j2,land)) =e= sum(land, pcm_land(j2,land));` ✅ EXACT match `modules/10_land/landmatrix_dec18/equations.gms:13-15`. `=e=` strict equality, LHS variable sum over `land`, RHS previous-timestep parameter `pcm_land`. Cited lines exact.
- **7 land types**: `crop, past, forestry, primforest, secdforest, urban, other`. ✅ `core/sets.gms:250-251`. All 7 members correct (answer's display order swaps the last two `urban`/`other` — immaterial to `sum(land,...)`; see Bug-1, Informational).
- **`q10_transition_to`**: `sum(land_from, vm_lu_transitions(j2,land_from,land_to)) =e= vm_land(j2,land_to);` ✅ EXACT `equations.gms:19-21`. Column-sum = current area. Cite exact.
- **`q10_transition_from`**: `sum(land_to, vm_lu_transitions(j2,land_from,land_to)) =e= pcm_land(j2,land_from);` ✅ EXACT `equations.gms:23-25`. Row-sum = previous area. Cite exact.
- **Equation NAMES exist in the DEFAULT realization** (explicit task check): `q10_land_area`, `q10_transition_to`, `q10_transition_from`, `q10_landexpansion`, `q10_landreduction` all declared `declarations.gms:27-31` and defined `equations.gms` — ✅ in `landmatrix_dec18` (not borrowed from another realization; module 10 has no other realization).
- **`q10_landexpansion`/`q10_landreduction`** (off-diagonal in/outflows): ✅ EXACT `equations.gms:30-33` and `35-38`, including the `$(not sameas(land_from,land_to))` diagonal exclusion.
- **`pcm_land` chaining (postsolve)**: `pcm_land(j,land) = vm_land.l(j,land);` ✅ EXACT `postsolve.gms:9`. Correct `.l` solution-level read; correctly explained as RHS constant for next timestep.
- **`pcm_land` declaration**: ✅ `declarations.gms:11` (answer cites declarations.gms:11). Correct.
- **Forbidden-transition `.fx()` bounds (presolve)**: all four restrictions verified in `presolve.gms`:
  - `vm_lu_transitions.fx(j,"primforest","forestry") = 0;` — line 13 ✅
  - `vm_lu_transitions.fx(j,"primforest","other") = 0;` — line 16 ✅
  - `vm_lu_transitions.fx(j,"secdforest","other") = 0;` — line 17 ✅
  - `vm_lu_transitions.fx(j,land_from,"primforest") = 0;` (primforest one-way decline) — line 20 ✅, with `vm_lu_transitions.up(j,"primforest","primforest") = Inf;` persistence — line 21 ✅
  (Answer's block cite `presolve.gms:10-23` brackets the actual `@code…@stop` block; the four named bounds are at 13/16/17/20-21. Loose but correct content; see Bug-2, Informational.)
- **Net-vs-gross note**: `realization.gms:11` "@limitations This realization only accounts for net land use transitions." ✅ EXACT. `vm_landdiff_natveg` (M35 `pot_forest_may24/declarations.gms:79`) and `vm_landdiff_forestry` (M32 `dynamic_may24/declarations.gms:67`) feed `q10_landdiff` (`equations.gms:50-54`) ✅ — names and structure verified.
- **`vm_landexpansion` consumers → modules 35, 39, 58, 59** and **`vm_landreduction` → 39, 58**: ✅ VERIFIED CORRECT against code (default realizations): expansion consumed in `35_natveg/pot_forest_may24/equations.gms`, `39_landconversion/calib/equations.gms`, `58_peatland/v2/equations.gms:28` (via `m58_LandMerge` macro), `59_som/cellpool_jan23/equations.gms`; reduction in `39_landconversion/calib/equations.gms` and `58_peatland/v2/equations.gms:31`. Module 32 does NOT consume the Module-10 vars — it uses its own `vm_landexpansion_forestry`/`vm_landreduction_forestry`. (Auditor note: a naive substring grep `vm_landexpansion` falsely implicates M32 via `vm_landexpansion_forestry`; an exact-paren grep `vm_landexpansion\(` falsely DROPS M58 because it passes the bare symbol into a macro. Both traps checked and resolved — answer's list matches the true set.)
- **`q10_cost` $1/ha gross-change cost** and **49 (7×7) transitions per cell**: ✅ `equations.gms:42-44` (`* 1`); 7 land types ⇒ 7×7; `vm_lu_transitions(j,land_from,land_to)` with `alias(land,land_from)`/`alias(land,land_to)` (`landmatrix_dec18/sets.gms:19-20`).

---

### Bugs Found:

- **Bug ID**: R48-P3-B1
- **Severity**: Informational
- **Class**: (none of 1–14 cleanly; closest is style/ordering — not a content error)
- **Trigger**: §1 Informational — "Style or doc issue, not a content error." (tie-breaker pulls down)
- **Claim in answer**: land-type table and expanded equation list the order `...secdforest, other, urban` (Section 1 table; Section 2 expansion).
- **Reality in code**: `core/sets.gms:251` order is `crop, past, forestry, primforest, secdforest, urban, other` — last two swapped vs answer.
- **File evidence**: `core/sets.gms:250-251` — `/ crop, past, forestry, primforest, secdforest, urban, other /`.
- **Impact**: zero — all 7 members are present and correct; `sum(land, …)` is order-independent. Display ordering only.

- **Bug ID**: R48-P3-B2
- **Severity**: Informational (tier_uncertainty: true — Informational vs Minor)
- **Class**: 10 (file:line citation) — borderline
- **Trigger**: §1 Informational tie-breaker (vs §1 Minor "off-by-few line citation where adjacent lines say similar things").
- **Claim in answer**: Section 3 — "`pcm_land` initialized from LUH2 historical data (`f10_land("y1995",j,land)`) via `start.gms:8`."
- **Reality in code**: `start.gms:8` assigns **`pm_land_start`** (`pm_land_start(j,land) = f10_land("y1995",j,land);`); `pcm_land` is assigned at **`start.gms:11`** (`pcm_land(j,land) = pm_land_start(j,land);`). The two-line chain (8→11) sits in one initialization block.
- **File evidence**: `modules/10_land/landmatrix_dec18/start.gms:8` and `:11`.
- **Impact**: minimal — the substantive claim (pcm_land ultimately receives the y1995 `f10_land` value) is CORRECT, and the named source (`f10_land("y1995",…)`) and file are correct; only the precise assignment line for `pcm_land` is one step further (line 11). A reader landing on line 8 finds the same block / same source one line up. Scored Informational (matches the doc, which also cites `start.gms:8` / `8-12` — `module_10.md:200,363`). Not a doc error worth flagging: the doc's block-range `start.gms:8-12` covers both lines.

---

### Missing Nuances (not scored):
- No inline 🟢/🟡 epistemic badges on individual body claims (only the footer). M4 partial — Informational, consistent with the answer being honestly framed as a 🟡 docs-based synthesis.
- `pm_land_start` (the intermediate) is itself a directly-consumed interface parameter (`14_yields`, `71_disagg_lvst` read it per `module_10.md:318`); the answer collapses the `f10_land → pm_land_start → pcm_land` chain to a single hop. Acceptable simplification for a conservation-mechanism question.

### Latent doc errors (§1.5): NONE.
The answer relied on `cross_module/land_balance_conservation.md` and `module_10.md`. Every load-bearing doc claim the answer inherited — `q10_land_area` form + cite (doc:14, 93-98), the `sum(land,…)` structure, `pcm_land` postsolve update (doc:119), presolve restrictions (doc:186-201), and the expansion/reduction consumer lists (`land_balance_conservation.md:227-228`, `module_10.md:344`) — was VERIFIED CORRECT against code this session. In particular the consumer lists (the §1.5 / R20-anchor risk surface) are accurate: expansion→{35,39,58,59}, reduction→{39,58}. No `doc_error_answerer_beat_it`, no propagated doc error.

### Summary:
A near-perfect docs-only answer. All five named equations (`q10_land_area`, `q10_transition_to`, `q10_transition_from`, `q10_landexpansion`, `q10_landreduction`) exist in the default `landmatrix_dec18` realization with exactly the cited structure, operator (`=e=`), and line numbers; the `pcm_land` postsolve chain (`postsolve.gms:9`) and the four forbidden-transition `.fx()` bounds (`presolve.gms:13-21`) are correct; the consumer lists are correct. The conservation logic is explained accurately and at the right depth: aggregate equality (`q10_land_area`) + doubly-balanced transition matrix (`q10_transition_to`/`q10_transition_from`) + recursive `pcm_land` chaining + bound-fixed forbidden transitions. Crucially, the answer presents the verbatim set-based `sum(land,…)` form as the code and clearly LABELS the member enumeration as "Expanded, the equation reads:" — so it does NOT repeat the R16 Major anchor (which fabricated an enumerated form AS the code). The only blemishes are two Informational items: a cosmetic last-two set-member swap, and a one-step-loose `start.gms:8` citation for `pcm_land` (assigned at :11) whose substance is correct. Score: 10 − 0 = 10/10.

---
Auditor verification footer: read THIS session @ ee98739fd — `config/default.cfg:232`; `modules/10_land/landmatrix_dec18/{equations,declarations,presolve,postsolve,start,realization,sets}.gms`; `core/sets.gms:248-267`; `modules/32_forestry/dynamic_may24/{equations}.gms`; `modules/35_natveg/pot_forest_may24/declarations.gms`; `modules/58_peatland/v2/equations.gms`; `modules/59_som/cellpool_jan23/equations.gms` (existence); consumer census via exact-paren AND substring grep cross-check; `cross_module/land_balance_conservation.md`; `modules/module_10.md`.
