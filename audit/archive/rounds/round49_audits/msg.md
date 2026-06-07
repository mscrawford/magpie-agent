# Audit Report: R49 (vm_land consumer set — modification_safety_guide.md)

## Overall Verdict: MOSTLY ACCURATE
## Accuracy Score: 7/10

Ground truth: develop worktree `/tmp/magpie_develop_ro` at HEAD `ee98739fd` (matches the commit anchor the answer and module_10.md cite — docs are CURRENT, not stale).

---

## Ground-truth derivation (whole-tree greps + positive/negative controls)

**Equation-form reads** `rg "vm_land(" modules/ --include="*.gms"` (excl. producer 10_land):
29, 30, 31, 32, 34, 35, 50, 59 = 8 modules.

**Solution-level reads** `rg "vm_land\." modules/` (.l/.lo/.up/.fx/.m, presolve/postsolve, excl. 10_land):
22, 31, 32, 34, 35, 59 = 6 modules.

**Bare-symbol / macro-arg reads** (`vm_land` passed whole to a macro): 58_peatland (`m58_LandMerge(vm_land,...)` in `v2/equations.gms:23`).

**Union (the actual direct consumer set, excl. 10_land):**
`22, 29, 30, 31, 32, 34, 35, 50, 58, 59` = **10 modules**.

Final whole-tree confirmation (filter out `vm_land_*` derivatives): identical 10-module set.

**Negative control (false-positive exclusions):**
- `39_landconversion`: only `vm_landexpansion` / `vm_landreduction` (`calib/equations.gms:13-14`). NOT a vm_land consumer.
- `80_optimization`: only `vm_landdiff` (`lp_nlp_apr17/solve.gms`, `module.gms:15`). NOT a vm_land consumer.
- `11, 13, 14, 44, 56, 71`: ZERO bare `vm_land` references (only `vm_land_*` / `pcm_land` / `pm_land_start` / `vm_cost_land_transition`). Confirmed via explicit grep returning "NO MATCHES".
- `core/macros.gms:13`: a comment EXAMPLE only — not a consumer.

**Default-realization check (config/default.cfg):** land_conservation=area_based_apr22, cropland=detail_apr24, croparea=simple_apr24, past=endo_jun13, forestry=dynamic_may24, urban=exo_nov21, natveg=pot_forest_may24, nr_soil_budget=macceff_aug22, peatland=v2, som=cellpool_jan23. All consumer reads above are present in the DEFAULT realization of each module.

**Critical detail — module 22 (`area_based_apr22`) has NO equations.gms** (files: declarations, input, preloop, presolve_ini, realization, sets). It consumes vm_land EXCLUSIVELY at solution level: `vm_land.lo(j,"crop")` in `presolve_ini.gms:86,97,108`. A `vm_land(` equation grep returns ZERO for module 22; only the `.lo` (MANDATE-20) grep catches it.

---

## Verified Claims (correct)

- **Doc consumer set is accurate AND complete.** `modification_safety_guide.md:54-55` (and `module_10.md:315-316`, Appendix B:1078) list exactly `22, 29, 30, 31, 32, 34, 35, 50, 58, 59`. This is the verified ground-truth set. No phantoms, no omissions. The answer reproduced it correctly.
- **Count = 10, EXTREME risk** (`modification_safety_guide.md:46`). Correct.
- **Exclusions correct.** 11 (vm_cost_land_transition), 39 (vm_landexpansion/reduction), 13/44/56 (pcm_land), 14/71 (pm_land_start), 80 (vm_landdiff) — all verified to NOT read vm_land. `module_10.md:317-318` states these with commit anchor ee98739fd, which IS the current develop HEAD.
- **pcm_land population:** `postsolve.gms:9` `pcm_land(j,land) = vm_land.l(j,land)`; declared `declarations.gms:11`. Both confirmed.
- **Per-module equation citations** (via land_balance_conservation.md): 29 `detail_apr24/equations.gms:12`, 31 `endo_jun13/equations.gms:17`, 32 `dynamic_may24/equations.gms:55-56`, 34 `exo_nov21/equations.gms:31`, 35 `pot_forest_may24/equations.gms:11,13`, 50 `macceff_aug22/equations.gms:79,90`, 59 `cellpool_jan23/equations.gms:33,63`. All accurate to default realizations; answer correctly used defaults.
- **Epistemic framing** (🟡 documented, not independently code-verified this session) honestly disclosed; provided a re-verify command.

---

## Bugs Found

### Bug R49-B1 — Solution-level dimension wrongly declared "unanswerable"
- **Severity**: Major
- **Class**: 4 (conceptual pseudo-code / mischaracterization) — borderline 12
- **Trigger** (§1 Major): "The claim is wrong in a way that misleads about behavior, but won't directly cause damaging action."
- **Claim in answer**: "The documentation does not enumerate whether any external consumer module reads `vm_land.l` or `vm_land.lo` in its own presolve/postsolve — this would require direct code inspection and is not addressed in the current AI docs. That is the one dimension of the question the documentation cannot answer."
- **Reality in code**: The question EXPLICITLY foregrounded solution-level reads ("or via solution-level attributes such as vm_land.l/.lo in presolve/postsolve"). The answer had everything needed to answer it: **module 22 (already in the listed 10) is a solution-level-ONLY consumer** (`vm_land.lo(j,"crop")` in `area_based_apr22/presolve_ini.gms:86,97,108`; it has no equations.gms). Modules **31, 32, 34, 35, 59** also read `vm_land.l/.lo/.fx/.up` in presolve/postsolve (e.g. `32_forestry/dynamic_may24/presolve.gms:19`, `35_natveg/.../presolve.gms:40,130,157`, `59_som/.../postsolve.gms:9`). The documented 10-set therefore ALREADY fully accounts for solution-level reads — the consumer set is complete on exactly the dimension the answer claimed it could not verify. By punting, the answer (a) declines to answer the literal question and (b) implies the set might be incomplete on this dimension when it is not.
- **File evidence**: `/tmp/magpie_develop_ro/modules/22_land_conservation/area_based_apr22/presolve_ini.gms:86,97,108`; whole-tree `vm_land.` grep → {22,31,32,34,35,59}.
- **Anchor reference**: aligns with MANDATE 20 (solution-level `.l/.lo` reads) — the answer cited the MANDATE-relevant risk but then asserted the docs "cannot answer" it, which is the inverse of the correct conclusion.

### Bug R49-B2 — Module 22 mechanism mischaracterized as an equation read
- **Severity**: Minor
- **Class**: 12 (content-level mismatch)
- **Trigger** (§1 Minor): "Wrong detail, but a careful reader wouldn't be misled into action or misunderstanding."
- **Claim in answer**: table row — "22_land_conservation | Reads `vm_land(j,land)` to enforce protected-area lower bounds".
- **Reality in code**: module 22's default realization reads `vm_land.lo(j,"crop")` (a solution-level attribute) in `presolve_ini.gms`, not `vm_land(j,land)` in any equation (it has no equations.gms). The `vm_land(j,land)` notation implies an equation read that does not exist. The high-level role (conservation/protected-area bounds) is correct, so impact is limited.
- **File evidence**: `/tmp/magpie_develop_ro/modules/22_land_conservation/area_based_apr22/presolve_ini.gms:86,97,108`; `vm_land(` grep on module 22 → zero hits.

### Bug R49-B3 — Module 30 mechanism mischaracterized
- **Severity**: Informational
- **Class**: 12 (content-level mismatch)
- **Trigger** (§1 Informational): style/precision; a careful reader checks code.
- **Claim in answer**: table row — "30_croparea | Reads `vm_land(j,"crop")` as an available area bound".
- **Reality in code**: `simple_apr24/equations.gms:23` uses `vm_land(j2,"crop")` as the SCALING BASE for the bioenergy-tree (betr) area-target equation: `vm_land(j2,"crop") * sum(ct,i30_betr_target(ct,j2)) - vm_area(j2,"betr","rainfed")`. It is not a generic "available area bound." Module 30 IS a correct consumer; only the mechanism gloss is off.
- **File evidence**: `/tmp/magpie_develop_ro/modules/30_croparea/simple_apr24/equations.gms:23`.

---

## Latent doc bugs (rubric §1.5)

**None.** The load-bearing doc claim the answer relied on — the 10-module consumer set in `modification_safety_guide.md:54-55` and `module_10.md:315-316` — is fully correct vs code (verified by whole-tree union grep + negative controls). The exclusion note `module_10.md:317-318` and its anchor `ee98739fd` are also correct (anchor = current HEAD). No `doc_error_answerer_beat_it` to record: the answer did not beat a wrong doc; both doc and answer-core are right. Bugs B1-B3 are answerer-side framing/mechanism errors, not doc errors.

---

## Missing Nuances

- The answer could have AFFIRMATIVELY answered the solution-level part: "Yes — solution-level reads are already covered: module 22 is a presolve-only (`vm_land.lo`) consumer, and 31/32/34/35/59 read `vm_land.l/.lo` in addition to their equation reads. The 10-set is complete including these." Instead it declared the dimension unanswerable (B1).
- Module 32's `presolve.gms:19` reads `vm_land.l/.lo` for the **past** land type (afforestation-potential pattern, analogous to the MANDATE-20 `vm_area.l` near-miss) — a nice confirming detail the answer omitted (32 is already listed, so not a completeness gap).

---

## Summary

The answer's central conclusions are correct: the safety guide's 10-module vm_land consumer set (`22, 29, 30, 31, 32, 34, 35, 50, 58, 59`) is accurate AND complete vs develop HEAD ee98739fd, with no phantom consumers and no omissions, and the excluded modules (11/13/14/39/44/56/71/80) genuinely consume other Module-10 variables. Citations to the default realizations are accurate. The score is held to 7 by one Major framing error: the answer declared the solution-level (`vm_land.l/.lo`) dimension — which the question explicitly asked about — to be undocumented/unanswerable, when in fact the documented 10-set already fully captures it (module 22 is a solution-level-only consumer; five others read solution-level attributes too). Two mechanism mischaracterizations (modules 22 and 30) share that same equation-vs-solution-level blind spot.

Score: 10 − 2 (1 Major) − 1 (1 Minor) − 0 (1 Informational) = **7**.
