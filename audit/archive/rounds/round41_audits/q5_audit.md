# Audit Report: Q5 (Module 22 — Conservation / Protected-Area Constraints)

**Round**: 41
**Auditor**: Opus (semantic-validation flywheel)
**Ground truth**: live GAMS at `<magpie-root>/modules/` + `config/default.cfg`, develop HEAD ee98739fd (clean)
**Answer audited**: `audit/archive/rounds/round41_answers/q5_answer.md`

---

## Overall Verdict: MOSTLY ACCURATE
## Accuracy Score: 8/10

The answer is structurally excellent. Every load-bearing claim — the sole realization, the two key defaults, the `pm_land_conservation` declaration + dimensions, the four core consumers, M10's purely transitive role, the `q35_natveg_conservation` `=g=` aggregate, and the `v35_secdforest.lo` per-age-class bound — is verified correct against current code. The single substantive defect is a missing default-state caveat: Module 13 is listed as a direct consumer of `pm_land_conservation` with equal standing alongside M35/M29/M31/M32, but the M13 read is gated behind `c13_croparea_consv = 1`, whose default is **0** — so M13 does NOT read the parameter in a default run. One Minor dimension imprecision on `p22_wdpa_baseline` rounds out the deductions.

---

## Mechanical Checks (M1–M6)

| Check | Result | Notes |
|---|---|---|
| **M1** File:line citations present | PASS | Many `module_XX.md:NN` doc citations + GAMS-relative paths (`equations.gms:52`, `presolve.gms:172-180`, etc.). This is a docs-only answer so 🟡 doc citations dominate, which is consistent with M5. |
| **M2** Active realization stated | PASS | States `area_based_apr22` is the sole realization and therefore default; M35 `pot_forest_may24` and M10 `landmatrix_dec18`-equivalent equations correctly used. |
| **M3** Variable prefixes valid | PASS | `pm_land_conservation`, `vm_land`, `v35_secdforest`, `pcm_land`, `p22_*`, `p35_*`, `q35_*`, `q10_*`, `q29_*` all correct prefixes. |
| **M4** Epistemic badges present | PASS | Every claim carries 🟡 (documented). Honest and uniform — the answer explicitly states no `.gms` files were opened. |
| **M5** Confidence tier matches depth | PASS | All claims 🟡 and the closing statement confirms docs-only; no claim is over-tagged 🟢. |
| **M6** Closing source statement | PASS | Closes with a Source Statement block listing module_22.md / module_35.md / land_balance_conservation.md / default.cfg, with verification dates. |

All six mechanical checks pass.

---

## Verified Claims (correct)

- **Sole realization + default**: `ls modules/22_land_conservation/` shows only `area_based_apr22/` and `input/`. Single-realization, so it is the default by construction. ✅ (`modules/22_land_conservation/area_based_apr22/`)
- **`c22_base_protect = "WDPA"`**: `config/default.cfg:723` → `cfg$gms$c22_base_protect <- "WDPA"`. ✅
- **`c22_protect_scenario = "none"`**: `config/default.cfg:755` → `cfg$gms$c22_protect_scenario <- "none"`. ✅
- **`c22_base_protect_noselect = "WDPA"` / `c22_protect_scenario_noselect = "none"`**: `default.cfg:724,756`. ✅
- **M22 has NO optimization equations**: confirmed — there is no `equations.gms` in the realization dir; files are `declarations / input / preloop / presolve_ini / realization / sets`. ✅
- **`pm_land_conservation(t,j,land,consv_type)`**: declared `modules/22_land_conservation/area_based_apr22/declarations.gms:15` with exactly those four dimensions, units "mio. ha". ✅
- **`consv_type = {protect, restore}`**: `sets.gms:26-27`. ✅
- **`land` set includes primforest/secdforest/other/past**: `core/sets.gms:251` → `/ crop, past, forestry, primforest, secdforest, urban, other /`. ✅
- **`land_natveg = {primforest, secdforest, other}`**: `core/sets.gms:262-263`. The aggregate constraint sums over exactly these three. ✅
- **Protection cap formula** `min(p22_conservation_area, pcm_land)`: `presolve_ini.gms:54-55` (set then capped where it exceeds `pcm_land`). ✅ (the answer's `min(...)` is a faithful paraphrase of the two-line set-then-clip).
- **Restoration = max(0, conservation_area − pcm_land)**: matches the presolve_ini logic at lines 66-111 (restoration is the excess of target over current area, then clipped to restore potentials). ✅
- **M35 `q35_natveg_conservation`** (`=g=` aggregate): `modules/35_natveg/pot_forest_may24/equations.gms:19-22` — `sum(land_natveg, vm_land(j2,land_natveg)) =g= sum((ct,land_natveg), pm_land_conservation(ct,j2,land_natveg,"protect"))`. Exact match including the `"protect"` slice and `ct` summation. ✅
- **`v35_secdforest.lo` per-age-class bound**: `presolve.gms:177` (historical) and `:179` (non-historical with `(1-s35_natveg_harvest_shr)` floor) — `max(pm_land_conservation(t,j,"secdforest","protect") * p35_protection_dist(j,ac_sub), pc35_secdforest_natural(j,ac_sub))`. Exact. The harvest-share floor caveat the answer adds is real. ✅
- **`p35_protection_dist`** = age-class share of secdforest: `presolve.gms:172-173`. ✅
- **M35 restoration equations** `q35_secdforest_restoration` / `q35_other_restoration`: `equations.gms:24-33`, both `=g=` against `p35_land_restoration`. ✅ (answer's cited range `equations.gms:24-33` is exact.)
- **`p35_land_restoration` derived from `pm_land_conservation(...,"restore")`**: `presolve.gms:186` (secdforest) and `:225` (other). ✅
- **M29 `q29_land_snv`**: `modules/29_cropland/detail_apr24/equations.gms:49-52` — SNV constraint adds `sum((ct,land_snv,consv_type), pm_land_conservation(ct,j2,land_snv,consv_type))` on top of the per-area SNV share. ✅ (answer cited `equations.gms:52`, the exact line of the conservation term.)
- **M31 consumes via `vm_land.lo(j,"past")`**: `modules/31_past/endo_jun13/presolve.gms:9` — `vm_land.lo(j,"past") = sum(consv_type, pm_land_conservation(t,j,"past",consv_type))`. ✅ Confirms the answer's claim that `past` gets WDPA-baseline protection AND that M31 is a real consumer.
- **M32 reads `pm_land_conservation(t,j,"other","restore")`**: `modules/32_forestry/dynamic_may24/presolve.gms:20` — subtracts the other-land restoration target when computing afforestation potential `p32_aff_pot`. ✅ (answer's framing "limits plantation siting in conservation areas" is a reasonable gloss on this restoration-reservation logic.)
- **M10 `q10_land_area`** is `=e=` and does NOT read `pm_land_conservation`: `modules/10_land/landmatrix_dec18/equations.gms:13-15` — `sum(land, vm_land(j2,land)) =e= sum(land, pcm_land(j2,land))`. Open-paren grep `pm_land_conservation(` across `10_land/` returns zero matches. ✅ The answer's "M10 constrained transitively, not directly; does not read pm_land_conservation" is exactly right.
- **`q35_min_forest` / `q35_min_other` (NPI/NDC floors)**: `equations.gms:78-82`, both `=g=` against `p35_min_forest` / `p35_min_other`. ✅
- **`c35_ad_policy = "npi"` default**: `config/default.cfg:1141`. ✅ The answer correctly states NPI is on by default and is additive to (independent of) M22's PA constraints.
- **Input filenames**: `wdpa_baseline.cs3` (`input.gms:59`) and `consv_prio_areas.cs3` (`input.gms:67`) — exact. ✅
- **`p22_*` internal parameters** in the summary table — all exist with the cited dimensions: `p22_conservation_area(t,j,land)` (decl:14), `p22_add_consv(t,j,consv22_all,land)` (decl:17), `p22_secdforest_restore_pot(t,j)` (decl:18), `p22_country_weight(i)` (decl:21). ✅
- **Restoration priority order secdforest → pasture → other**: consistent with presolve_ini.gms:71-111 (secdforest restore computed first, then pasture deductions, then other gets the residual). ✅ (broadly faithful; the exact ordering logic is intricate but the answer's summary is defensible.)

---

## Bugs Found

### Bug Q5-B1 — Module 13 listed as a direct consumer without its default-OFF caveat

- **Bug ID**: Q5-B1
- **Severity**: 🟠 **Major**
- **Class**: Class 4 (conceptual / behavioral — "described as active when OFF by default"); maps to the §1 Major trigger "Missing default-state caveat (mechanism described as if always active when it's OFF by default)".
- **Trigger matched**: §1 Major — *"Missing default-state caveat (mechanism described as if always active when it's OFF by default — `s42_pumping`, `s56_pollutant_prices` ON only with non-default config)."*
- **Claim in answer**:
  > "5. **Module 13 (TC)** — adjusts TC expectations based on the share of cropland in conservation areas (`presolve.gms:40`)."
  (listed as direct consumer #5, with the four genuinely-default consumers, no caveat)
  and in the summary table: *"`pm_land_conservation` … Binding conservation targets passed to M13, M29, M31, M32, M35."*
- **Reality in code**: The M13 read at `modules/13_tc/endo_jan22/presolve.gms:40` is inside `if(c13_croparea_consv = 1, ...)` (block opens at `presolve.gms:38`). The default is `c13_croparea_consv = 0` (`config/default.cfg:309` → `cfg$gms$c13_croparea_consv <- 0`; realization default `modules/13_tc/endo_jan22/input.gms:12` → `/ 0 /`). **In a default run, Module 13 does NOT read `pm_land_conservation`.** Listing it un-caveated alongside the four unconditional consumers misrepresents the default consumer set: a reader auditing "who reacts to conservation targets" would wrongly include M13's TC-expectation adjustment in default behavior.
- **File evidence**:
  - `modules/13_tc/endo_jan22/presolve.gms:38` → `if(c13_croparea_consv = 1,`
  - `modules/13_tc/endo_jan22/presolve.gms:40` → `p13_cropland_consv_shr(t,j)$(pcm_land(j,"crop") > 0) = sum(consv_type, pm_land_conservation(t,j,"crop",consv_type))/pcm_land(j,"crop");`
  - `config/default.cfg:309` → `cfg$gms$c13_croparea_consv <- 0      # def = 0`
  - `modules/13_tc/endo_jan22/input.gms:12` → `... (0=no 1=yes) / 0 /`
- **Anchor reference**: Resembles the §1 Major default-state-caveat anchor (`s42_pumping` ON only with non-default config). Not Critical: the four core consumers ARE correct and unconditional, M10's transitivity is correct, and the user would not edit the wrong file — they would merely overstate the default reach of conservation into the TC module. Tie-break consideration: between Major and Minor, this fires the explicit Major trigger ("mechanism described as if always active when OFF by default"), so Major stands (not downgraded — the trigger is a verbatim Major listing, not an ambiguous boundary).

### Bug Q5-B2 — `p22_wdpa_baseline` dimension cited as `wdpa_cat22` instead of `base22`

- **Bug ID**: Q5-B2
- **Severity**: 🟡 **Minor**
- **Class**: Class 3 (suffix/dimension imprecision) / borderline Class 12 (content-level mismatch).
- **Trigger matched**: §1 Minor — *"Wrong detail, but a careful reader wouldn't be misled into action."* (`tier_uncertainty: false` — the index set is a documented superset, recoverable.)
- **Claim in answer** (summary table): `p22_wdpa_baseline | M22 internal | (t,j,wdpa_cat22,land) | WDPA observed trends 1995–2020`.
- **Reality in code**: `modules/22_land_conservation/area_based_apr22/declarations.gms:13` → `p22_wdpa_baseline(t,j,base22,land)`. The parameter is declared over **`base22`** (= `{none, WDPA, WDPA_I-II-III, WDPA_IV-V-VI}`, `sets.gms:10-11`), not `wdpa_cat22`. `wdpa_cat22(base22)` is the populated subset (`sets.gms:13-14`, drops `none`), so the answer named the active-members subset rather than the declared index set. A careful reader checking declarations.gms would find `base22` and reconcile easily; the conceptual content (WDPA category × land trend) is right.
- **File evidence**:
  - `modules/22_land_conservation/area_based_apr22/declarations.gms:13` → `p22_wdpa_baseline(t,j,base22,land)`
  - `modules/22_land_conservation/area_based_apr22/sets.gms:10-14` (`base22` superset; `wdpa_cat22(base22)` subset).
- **Anchor reference**: Mild analogue of the R16 LUH2-vs-LUH3 Minor anchor (declared value vs documented/effective value differ but a careful reader checks both). Minor.

---

## Latent Doc Bugs (§1.5) — record independent of answer score

The answer relied on `module_22.md` and `module_35.md` doc claims (it is docs-only). I cross-checked the load-bearing doc-backed claims against code; the answer reproduced the code correctly on all the spine items (consumer set, declaration, equation/bound names, defaults). I therefore found **no `doc_error_answerer_beat_it`** on the spine: where the answer is right, the docs it cited appear consistent with code.

One item to flag for the doc-fix pass, since it surfaced through the answer and should be corrected at the doc layer too if the doc carries it:

- **M13 default-OFF caveat** (the basis of Bug Q5-B1). If `module_22.md` (the cited consumer-list source, `module_22.md:509-548`/`600-609`) lists Module 13 in the direct-consumer set without the `c13_croparea_consv = 0` default caveat, that doc line should gain the caveat so the next answerer does not reproduce Q5-B1. This is the actionable doc fix even though the bug manifested in the answer (the answer mirrored the doc's framing). Classed under §1.5 only IF the doc lacks the caveat; verify the doc text in Step 5. (Severity to a future reader: Major, same default-state-caveat basis.)

No other latent doc bugs detected. `pm_land_conservation` declaration/consumer attribution in the docs (hand-validated R35–R37 per the task note) remains consistent with current code at HEAD ee98739fd.

---

## Missing Nuances

- **M13's read is on the `"crop"` slice**, which is itself only nonzero when conservation priority areas overlap cropland — a second reason its default contribution is null (compounding the `c13_croparea_consv = 0` gate). Minor; not scored.
- **M32's interaction is restoration-reservation, not a `vm_land.lo` floor**: M32 subtracts `pm_land_conservation(t,j,"other","restore")` from its afforestation-potential pool (`presolve.gms:20`), i.e. it reserves other-land restoration away from NPI/NDC afforestation, rather than imposing a protection floor on plantations. The answer's gloss ("limits plantation siting in conservation areas") is directionally right but slightly mischaracterizes the mechanism (it is about not double-counting restorable other-land, not protecting existing plantations). Not a scored bug — the net effect (less land available for afforestation where restoration is committed) is correctly conveyed.
- **`q35_natveg_conservation` operates on the aggregate** `sum(land_natveg, vm_land)`, so it does NOT by itself pin individual pools; the per-pool pinning comes from the separate `vm_land.lo`/`v35_secdforest.lo` bounds (presolve.gms:162, 177-179, 201). The answer does describe both the aggregate equation AND the per-pool bounds ("Way 1 / Way 2"), so this nuance is actually covered well — noted as a strength.

---

## Summary

A strong, honest, docs-only answer that gets the entire load-bearing spine right: sole realization `area_based_apr22` (verified default by construction), the two priority defaults (`c22_base_protect = "WDPA"`, `c22_protect_scenario = "none"`), the `pm_land_conservation(t,j,land,consv_type)` declaration and dimensions, `consv_type = {protect, restore}`, the four unconditional consumers (M35, M29, M31, M32) with the correct equations/bounds, M10's purely transitive role (`q10_land_area` `=e=`, never reading the parameter), and the M35 `q35_natveg_conservation` `=g=` aggregate plus `v35_secdforest.lo` per-age-class distribution. Citations to GAMS-relative line ranges that I spot-checked (`equations.gms:19-22`, `:24-33`, `:49-52`; M31 `presolve.gms:9`; M32 `presolve.gms:20`; M10 `equations.gms:13-15`) all landed on the correct content.

Two deductions: **(Major)** Module 13 is presented as a direct consumer without noting its read is gated behind the default-OFF switch `c13_croparea_consv = 0`, overstating the default consumer set; **(Minor)** `p22_wdpa_baseline` cited over `wdpa_cat22` rather than its declared `base22` index. Score = 10 − 2(Major) − 1(Minor) = **8/10**, verdict **Mostly Accurate**.

**Verified `pm_land_conservation` consumer set** (open-paren grep, `.l`/`.lo` ignored, HEAD ee98739fd):
- **Declared + populated**: M22 (`22_land_conservation/area_based_apr22/declarations.gms:15`; populated in `presolve_ini.gms`).
- **Read unconditionally (DEFAULT run)**: M35 (`35_natveg/pot_forest_may24/equations.gms:22` + `presolve.gms` 149/162/174/177/179/186/189/197-198/201/221/225/228-229), M29 (`29_cropland/detail_apr24/equations.gms:52`; also `simple_apr24/equations.gms:41`), M31 (`31_past/endo_jun13/presolve.gms:9`), M32 (`32_forestry/dynamic_may24/presolve.gms:20`).
- **Read CONDITIONALLY, OFF by default**: M13 (`13_tc/endo_jan22/presolve.gms:40` + `exo/presolve.gms:16`), gated by `c13_croparea_consv = 1` (default 0, `config/default.cfg:309`).
- **Does NOT read it**: M10 (constrained only transitively via `vm_land.lo` set by the modules above, satisfied within `q10_land_area` `=e=`).
