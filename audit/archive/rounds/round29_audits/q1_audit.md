# Audit Report: Q1 (Land-area conservation & double-counting prevention)

**Round**: R29
**Worktree**: /tmp/magpie-develop-r29/ @ ee98739fd
**Question**: How does MAgPIE enforce conservation of total land area, what prevents double-counting when land moves between uses (exact constraint name + equality/inequality, variables, transition matrix relation, pools, is land lost/created)?

### Overall Verdict: MOSTLY ACCURATE (lower band)
### Accuracy Score: 7/10

**Score derivation (§4 formula, binding):** 1 Major (B1) + 1 Minor (B2) → 10 − 2(1) − 1(1) = **7**. No Critical (B1 tie-broken down from Critical to Major — see B1).

---

### Verified Claims (correct):

1. **`q10_land_area` is `=e=` strict equality**, `equations.gms:13-15`. Answer quotes it verbatim; code matches exactly:
   `sum(land, vm_land(j2,land)) =e= sum(land, pcm_land(j2,land));` — `modules/10_land/landmatrix_dec18/equations.gms:13-15`. ✓ Equality (not inequality) confirmed.
2. **LHS `vm_land(j,land)` (variable), RHS `pcm_land(j,land)` (parameter)** — declarations.gms:11,19. ✓
3. **`pcm_land` recursive update via `postsolve.gms:9`**: `pcm_land(j,land) = vm_land.l(j,land);` — exact line match. ✓
4. **7-pool land set, `core/sets.gms:250-251`**: `/ crop, past, forestry, primforest, secdforest, urban, other /`. Answer lists all 7, cites 250-251. ✓ (Answer table orders urban/other swapped vs the set literal `...urban, other`; immaterial — set is unordered here.)
5. **`q10_transition_from` (`equations.gms:23-25`)**: row/source fixing — `sum(land_to, vm_lu_transitions(j,land_from,land_to)) =e= pcm_land(j,land_from)`. Answer's "total outflow from any source = prior-period area" is correct. ✓ Citation line-exact.
6. **`q10_transition_to` (`equations.gms:19-21`)**: column/destination fixing — `sum(land_from, ...) =e= vm_land(j,land_to)`. Answer's "total inflow to any destination = current-period area" correct. ✓ Citation line-exact. Row/column semantics not inverted.
7. **`vm_lu_transitions(j,land_from,land_to)`, 7×7 = 49 entries** — declarations.gms:23. ✓
8. **`q10_landexpansion` off-diagonal column sum (`equations.gms:30-33`)** and **`q10_landreduction` off-diagonal row sum (`equations.gms:35-38`)**, both `=e=`, with `$(not sameas(land_from,land_to))` guard. Answer quotes verbatim; line-exact. ✓
9. **`q10_landdiff` (`equations.gms:50-54`)**: `vm_landdiff =e= sum((j2,land), vm_landexpansion + vm_landreduction) + vm_landdiff_natveg + vm_landdiff_forestry`. Line-exact; components attributed to M35 (natveg) / M32 (forestry) — `vm_landdiff_natveg` declared in `35_natveg/pot_forest_may24/declarations.gms`, `vm_landdiff_forestry` in `32_forestry/dynamic_may24/declarations.gms`. ✓
10. **Presolve transition restrictions (`presolve.gms`)**: `vm_lu_transitions.fx(j,"primforest","forestry")=0` (line 13), `vm_lu_transitions.fx(j,land_from,"primforest")=0` (line 20), `.up(j,"primforest","primforest")=Inf` (line 21), `primforest→other`/`secdforest→other` fixed to 0 (lines 16-17). All four factual restriction statements correct. Answer's block citation `presolve.gms:10-23` brackets `@code`(10)…`@stop`(23). ✓
11. **`start.gms:8`**: `pm_land_start(j,land) = f10_land("y1995",j,land);` — line-exact. ✓ (Answer §6 wrote `start.gms:8` — correct; the file actually has `pm_land_start = f10_land(...)`. Note answer §6 text says "initialized from LUH2"; module_10.md:223 also says LUH2, consistent with doc.)
12. **Net-not-gross limitation**, `realization.gms:11`: "This realization only accounts for net land use transitions." Answer §7 note matches. ✓
13. **`landmatrix_dec18` is default + only realization** — `config/default.cfg:232` `cfg$gms$land <- "landmatrix_dec18"`; module.gms lists only this realization. Answer names it consistently. ✓
14. **No invented names**: every variable cited (`vm_land`, `pcm_land`, `vm_lu_transitions`, `vm_landexpansion`, `vm_landreduction`, `vm_landdiff`, `vm_landdiff_natveg`, `vm_landdiff_forestry`, `pm_land_start`, `f10_land`, `vm_cost_land_transition`) exists in code. ✓

---

### Bugs Found:

#### Bug Q1-B1 — `vm_landreduction` consumer set over-attributed (35 and 59 do not consume it)

- **Bug ID**: Q1-B1
- **Severity**: Major
- **Class**: 6 (Hardcoded counts/set drift) / consumer-set attribution
- **Trigger** (§1 Major): "Fabricated count for a set/parameter/realization list" — the consumer set claimed for `vm_landreduction` includes two modules that do not read it.
- **Claim in answer** (§4): "Both [`vm_landexpansion` and `vm_landreduction`] are `=e=` (strict equality). These variables are consumed by modules 35, 39, 58, and 59."
- **Reality in code**:
  - `vm_landexpansion` (the M10 var) IS consumed by 35, 39, 58, 59 — `35_natveg/pot_forest_may24/equations.gms:197,222`, `39_landconversion/calib/equations.gms:13`, `58_peatland/v2/equations.gms:28` (macro arg to `m58_LandMerge`), `59_som/cellpool_jan23/equations.gms:91`. ✓ for expansion.
  - `vm_landreduction` is consumed ONLY by 39 and 58 — `39_landconversion/calib/equations.gms:14`, `58_peatland/v2/equations.gms:31`. It has ZERO references in `35_natveg/` and `59_som/` (full-tree grep, all forms, both empty). The answer attributes reduction to 35 and 59, which is wrong.
- **File evidence**:
  - `modules/39_landconversion/calib/equations.gms:14` — `- vm_landreduction(j2,land)*sum((ct,cell(i2,j2)), i39_reward_reduction(...))`
  - `modules/58_peatland/v2/equations.gms:31` — `m58_LandMerge(vm_landreduction,vm_landreduction_forestry,"j2")`
  - `grep -rn vm_landreduction modules/35_natveg/` → empty; `modules/59_som/` → empty.
  - (peatland default = `v2`, `config/default.cfg:1853`; so 58's consumption is on the active realization.)
- **Root cause**: `doc_error`. The answer faithfully reproduced a wrong doc claim. Both docs list reduction with the same set as expansion:
  - `cross_module/land_balance_conservation.md:228` — "`vm_landreduction(j,land)` → To modules 35, 39, 58, 59"
  - `modules/module_10.md:344` — "Reduction = land lost to other types … Used by modules 35, 39, 58, 59 for impacts" (the line bundles expansion+reduction under one consumer list).
- **Anchor reference**: Resembles the R20 wrong-consumer-set anchor (Critical when a refactor would MISS a real consumer). Here the error is *over-inclusion* (claims 2 non-consumers), so a refactor of `vm_landreduction` would waste effort checking 35/59 but would NOT miss a real consumer. Lower harm than the R20 omission case → **Major** (tie-breaker pulls down from Critical; over-attribution misleads about behavior but does not cause a wrong/missed edit). `tier_uncertainty: true`.
- **Doc fix** (apply this session per §1.5 Step 5): split the bundled consumer list so reduction reflects its true {39, 58} set.
  - `cross_module/land_balance_conservation.md:228`: change `vm_landreduction(j,land)` → "To modules 39, 58" (and the §5.1 prose at lines 227-228 likewise). Optionally annotate: expansion → 35, 39, 58, 59; reduction → 39, 58.
  - `modules/module_10.md:344`: change "Used by modules 35, 39, 58, 59 for impacts" so it does not apply the expansion set to reduction; reduction is used by 39, 58. (module_10.md:227-228 / 302-304 also assert `vm_landreduction → 58, 39, …`; verify those rows: 58_peatland and 39_landconversion are correct, but any 35/59 reduction claim is wrong — line 301 lists `35_natveg | vm_land, vm_landexpansion, vm_lu_transitions` which is correctly expansion-only; line 299 lists `59_som | vm_land, pm_land_start, vm_landexpansion, vm_lu_transitions` correctly expansion-only. So the module_10.md *table* is already right; only the §2 prose line 344 over-bundles.)

#### Bug Q1-B2 — Interpretive gloss: `primforest→other` / `secdforest→other` "handled by Module 35's internal age-class dynamics"

- **Bug ID**: Q1-B2
- **Severity**: Minor
- **Class**: 4 (Conceptual pseudo-code / unverified mechanism gloss)
- **Trigger** (§1 Minor): "Wrong detail, but a careful reader wouldn't be misled into action." The *fact* (these two transitions fixed to 0) is correct; the appended causal gloss is not grounded in M10 code.
- **Claim in answer** (§5, 3rd bullet): "No direct primforest → other or secdforest → other: these within-natveg transitions are handled by Module 35's internal age-class dynamics, not via Module 10's transition matrix."
- **Reality in code**: `presolve.gms:16-17` fixes `vm_lu_transitions.fx(j,"primforest","other")=0` and `.fx(j,"secdforest","other")=0` with the comment "Conversions within natveg are not allowed" — i.e., these are *prohibited*, full stop. The code does NOT say the flow is rerouted through M35's age-class dynamics. Separately, primforest→secdforest is NOT fixed to 0 (it is a free variable in M10's matrix), so the natveg-internal flow that IS active actually runs *through* M10's matrix, contradicting the spirit of the gloss. The "handled by M35 not via M10's matrix" framing is an interpretation, not code truth for the →other pair.
- **File evidence**: `modules/10_land/landmatrix_dec18/presolve.gms:15-17` (comment + two `.fx`); absence of any `vm_lu_transitions.fx(j,"primforest","secdforest")` in presolve.gms (primforest→secdforest unrestricted).
- **Root cause**: `doc_error` (partly). `cross_module/land_balance_conservation.md:207` makes a parallel gloss ("primforest → secdforest and other → secdforest transitions are handled internally by Module 35"), and the doc matrix (lines 142-149) marks primforest→secdforest as "M35". The answer adapted this gloss but reassigned it to the →other pair. Mild confabulation on top of a doc gloss. Low stakes — the headline fact (these transitions blocked) is right.
- **Anchor reference**: none exact; closest is the general Pattern-4 conceptual-gloss family.
- **Doc note**: `land_balance_conservation.md:207` claim that primforest→secdforest is "handled internally by Module 35 … not through Module 10's transition matrix" is itself questionable — primforest→secdforest is an *unrestricted* `vm_lu_transitions` entry (presolve fixes only →primforest, →other, primforest→forestry). Flag for a future targeted check; not fixed here as it is outside the answer's exact wording and needs an M35 deep-read to adjudicate.

---

### Missing Nuances (not bugs):

- Answer omits `q10_cost` / `vm_cost_land_transition` (`equations.gms:42-44`, the 1 USD/ha gross-change penalty). Reasonable omission — it is a stabilizer, not a conservation/double-counting mechanism. Not scored.
- Answer omits explicit "this is the only realization" statement (M2). Single-realization module, so stakes are nil; not scored.
- Inline epistemic badges (M4) are absent on individual claims (only the Sources block carries 🟢). Informational at most; not separately scored given the strong file:line grounding.

---

### Latent doc bugs recorded (doc_errors_latent[]):

1. **`vm_landreduction` consumer over-attribution** — `cross_module/land_balance_conservation.md:228` and `modules/module_10.md:344` claim reduction is consumed by {35, 39, 58, 59}; true set is {39, 58}. Root cause of Q1-B1. FIX this session (Step 5). Severity to a future reader: Major (over-inclusion; a reader would believe M35/M59 read landreduction). This is `doc_error` (the answer reproduced it, did NOT beat it — so it also lowered the answer score; not a `doc_error_answerer_beat_it`).
2. **primforest→secdforest "handled by M35 not M10's matrix"** — `land_balance_conservation.md:207` + matrix lines 142-149. primforest→secdforest is an unrestricted M10 transition entry; the gloss may misdescribe the mechanism. Flag for targeted verification (needs M35 read); not auto-fixed.

---

### Summary:

Spine of the answer is correct and well-cited: `q10_land_area` is the named `=e=` strict-equality conservation constraint (lines 13-15, verbatim correct); the double-counting interlock via `q10_transition_from` (row sum = prior area) + `q10_transition_to` (column sum = current area) is described accurately with correct row/column semantics and line-exact citations; the 7-pool set, off-diagonal expansion/reduction, `q10_landdiff`, presolve restrictions, recursive `pcm_land` update, and net-not-gross limitation are all verified against the worktree. Two bugs: (B1, Major) the `vm_landreduction` consumer set wrongly includes modules 35 and 59 (true set: only 39 and 58) — inherited verbatim from a wrong doc claim (root_cause `doc_error`), fixed this session; (B2, Minor) an unsupported "handled by Module 35's age-class dynamics" causal gloss on the →other transition prohibition. **Score = 10 − 2(Major B1) − 1(Minor B2) = 7/10.** Verdict: Mostly Accurate (lower band).
