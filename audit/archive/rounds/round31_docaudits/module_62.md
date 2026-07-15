# Round 31 Doc Audit — module_62.md (Material Demand)

**Auditor**: Opus 4.8 (1M) adversarial documentation auditor
**Date**: 2026-05-30
**Target doc**: `<magpie-agent>/modules/module_62.md`
**Ground truth**: `/tmp/magpie_develop_ro` (develop worktree) + `config/default.cfg`
**Realization audited**: `exo_flexreg_apr16` (verified: only realization — `ls modules/62_material/` shows just `exo_flexreg_apr16/`, `input/`, `module.gms`)

---

## Overall Verdict: ACCURATE

### Accuracy Score: 9/10

This is a high-quality doc. Every equation, formula, interface variable, parameter default, citation, and the full consumer/producer dependency set were verified against develop code and found correct. The implementation description (historical/future switch, scaling factor, bioplastic logistic growth, double-counting correction) is faithful and well-cited. The two issues found are a wrong upstream-dependency claim in the boilerplate footer (GDP) and a minor file-inventory inconsistency. No fabricated formulas, no inverted defaults, no phantom/omitted consumers, no wrong realization.

---

## Verified Claims (correct)

### Realization & structure
- **Only realization is `exo_flexreg_apr16`** (doc line 4): confirmed via `ls /tmp/magpie_develop_ro/modules/62_material/`.
- **2 equations** (`q62_dem_material`, `q62_dem_material_forestry`): confirmed `declarations.gms:29-30`, defined `equations.gms:22-30` and `34-38`.
- **1 interface output variable `vm_dem_material`**: confirmed `declarations.gms:25` (positive variable block 24-26).

### Equation formulas (exact-match verification)
- **q62_dem_material** (doc 33-42): byte-for-byte matches `equations.gms:22-30` (historical FAO × s62_historical + lastcalibyear×scaling×(1-s62_historical) + bioplastic_substrate − double_counted). ✓
- **q62_dem_material_forestry** (doc 94-99): matches `equations.gms:34-38` (= sum(ct, pm_demand_forestry)). ✓
- **Scaling factor** (doc 156-160): matches `presolve.gms:21-22` exactly (init 1; conditional ratio sum(kfo,vm_dem_food.l)/p62_dem_food_lastcalibyear). ✓
- **Logistic growth rate + curve** (doc 207-213): both lines match `preloop.gms:21-22` exactly. ✓
- **Mode 1 zeroing** (doc 192): `p62_dem_bioplastic(t,i)$(m_year(t)>2020)=0` matches `preloop.gms:25-27`; the nuance "only >2020 zeroed, ≤2020 preserved" is correct (preloop 17-18 set ≤2020 to historical pop-share). ✓
- **Historical-switch logic** (doc 374-379): matches `presolve.gms:15-19`. ✓
- **Memory update** (doc 398-402): matches `postsolve.gms:13-16`. ✓
- **Double-counting historical/future** (doc 280, 287): match `presolve.gms:30` and `presolve.gms:36`. ✓
- **begr/betr zero double-count** (doc 295-296): match `presolve.gms:44-45`. ✓

### Parameter defaults (MANDATE 3 — verified in code)
- `s62_include_bioplastic` **default 1 (ON)** (doc 12, 185, 217): confirmed `input.gms:30` `/ 1 /`. NOT inverted.
- `s62_max_dem_bioplastic` **default 0** (doc 218, 636): confirmed `input.gms:31` `/ 0 /`.
- `s62_midpoint_dem_bioplastic` **default 2050** (doc 219): confirmed `input.gms:32` `/ 2050 /`.
- `s62_historical` declared `declarations.gms:9-10` (default 1), set `presolve.gms:15-19` (doc 74, 863): confirmed.
- Default behavior = Mode 2 (constant at 2020 level): internally consistent with verified defaults (include=1, max=0). ✓

### Citations (MANDATE 16 — spot-verified in current develop)
All verified correct: `input.gms:9-12` (f62_dem_material table), `input.gms:14-20` (conversion ratio), `input.gms:22-28` (f62_hist_dem_bioplastic), `declarations.gms:11/15/25/29/30`, `presolve.gms:15-19/21-22/26-38/40-45`, `preloop.gms:15/17/18/22/25-27/30`, `postsolve.gms:13-16/15`, `equations.gms:22-30/34-38/37`, `sets.gms:17-24`.

### Commodity set count (MANDATE 11)
- **"39 commodities"** (doc 449): confirmed — `sed -n '19,23p' sets.gms | tr ',' '\n' | grep -c non-empty = 39`. Exact. Set members (tece, maiz, trce, rice_pro, soybean, ... res_nonfibrous) match `sets.gms:19-23`. ✓

### Dependency set (MANDATE 13 + 17 — full enumeration, two methods)
- **Downstream consumer = Module 16 ONLY** (doc 343-346): confirmed by `grep -rn vm_dem_material` AND `rg -rln vm_dem_material` — only `62_material/` own files + `16_demand/sector_may15/equations.gms:24,36,46,54,87`. No core/ refs. Module 16 default = `sector_may15` (`config/default.cfg:608`). ✓
- **Upstream M15** via `vm_dem_food.l` (doc 324-327): confirmed `presolve.gms:22`, `postsolve.gms:15` — read via `.l` level (doc correctly notes this). ✓
- **Upstream M73** via `pm_demand_forestry` (doc 329-332): declared `modules/73_timber/default/declarations.gms:11`; timber default = `default` (`config/default.cfg:2205`). ✓ (Note: code indexes `(t_ext,i,kforestry)`; doc says `(t,i,kforestry)` — trivial.)
- **Upstream M09** via `im_pop` (doc 334-337): declared `modules/09_drivers/*/declarations.gms:11` as `im_pop(t_all,i)`; used `preloop.gms:17,18,22`. ✓

### Input data files
- All three files (`f62_dem_material.cs3`, `f62_bioplastic2biomass.csv`, `f62_hist_dem_bioplastic.csv`) confirmed in `modules/62_material/input/files` manifest (doc 826-828, 247). ✓

---

## Bugs Found

### Bug 62-B1 — Footer over-claims GDP as an upstream dependency
- **Severity**: Minor
- **Trigger**: "Recommendation/claim that contradicts code" → wrong dependency claim; footer metadata (a careful reader doing modification-safety reasoning could be misled, but the body is correct and no destructive edit follows). Tie-breaker pulls below Major.
- **Class**: 15 (latent doc error) / dependency-set inaccuracy.
- **Doc line**: module_62.md:899
- **Claim in doc**: "**Depends on**: Module 09 (drivers) for population **and GDP**"
- **Reality in code**: Module 62 consumes only `im_pop` (population) from Module 09. There is NO GDP reference anywhere in the module. The doc body itself (lines 334-337) correctly lists only `im_pop`; the footer adds "and GDP" with no code basis.
- **File evidence**: `rg -in 'gdp' /tmp/magpie_develop_ro/modules/62_material/` → EXIT 1 (no match) across the entire module tree, case-insensitive. Positive control: `rg im_pop preloop.gms` returns lines 17,18,22 (search works in that dir). `im_pop` declared `modules/09_drivers/.../declarations.gms:11`.
- **verify_cmd**: `rg -in 'gdp' /tmp/magpie_develop_ro/modules/62_material/ ; echo EXIT:$?` → `EXIT:1`
- **Confirmed**: true (two methods: per-realization-dir `NO_GDP_REFERENCE` + whole-tree EXIT 1; positive control on im_pop passed).
- **Proposed fix**: Change "**Depends on**: Module 09 (drivers) for population and GDP" → "**Depends on**: Module 09 (drivers) for population (`im_pop`); Module 15 (food) for `vm_dem_food.l`; Module 73 (timber) for `pm_demand_forestry`". (Minimal fix: drop "and GDP".)

### Bug 62-B2 — File Structure Summary omits `scaling.gms`, miscounts realization files
- **Severity**: Informational
- **Trigger**: Hardcoded-count / file-inventory completeness (Bug class 6 tendency, but reader not misled into action — scaling.gms is fully commented boilerplate). Lower tier per tie-breaker.
- **Class**: 6 (hardcoded counts drift) — informational instance.
- **Doc line**: module_62.md:812-823 (and the "Source files read: 9/9 ✓" checklist at 834-843)
- **Claim in doc**: lists 9 files as the realization's structure — `module.gms, realization.gms, sets.gms, declarations.gms, input.gms, equations.gms, preloop.gms, presolve.gms, postsolve.gms` — and asserts "Source files read: 9/9 ✓".
- **Reality in code**: The `exo_flexreg_apr16/` realization directory contains 9 `.gms` files: sets, declarations, input, equations, **scaling**, preloop, presolve, postsolve, realization. `module.gms` lives one level up in `62_material/` (not in the realization dir). The doc's enumerated list includes `module.gms` but **omits `scaling.gms`** entirely. So the count "9" is right only by coincidence (one parent-dir file swapped for one omitted realization file); total `.gms` files associated with the module = 10.
- **File evidence**: `ls modules/62_material/exo_flexreg_apr16/` shows `scaling.gms` (507 bytes). `scaling.gms` content (lines 8-9) is two commented-out `.scale` assignments — no active code.
- **verify_cmd**: `wc -l /tmp/magpie_develop_ro/modules/62_material/exo_flexreg_apr16/*.gms` → lists scaling.gms (9 lines); `Read scaling.gms` → lines 8-9 both prefixed `*` (commented).
- **Confirmed**: true.
- **Proposed fix**: Add `scaling.gms` to the file list (note it is commented-out boilerplate: `*q62_dem_material.scale(...)`), and clarify that `module.gms` is the parent-dir module selector while the realization dir holds 9 phase files. E.g. add a 10th bullet "`scaling.gms` (10 lines): variable scaling factors — currently all commented out (inactive)" and update "Source files read: 9/9" → "10/10 (incl. scaling.gms boilerplate)".

---

## Missing Nuances (NOT scored as bugs)

- **`min()` cap on lastcalibyear substrate** (`presolve.gms:31`): `p62_bioplastic_substrate_lastcalibyear(i,kall) = min(p62_bioplastic_substrate(t,i,kall), f62_dem_material(t,i,kall))`. The doc's double-counting section (lines 272-300) describes the subtraction correctly but never mentions that the stored historical substrate is capped at the FAO material demand. Not an error in any stated claim — an omission. Not flagged.
- **`realization.gms:13-14` citation scope** (doc 175): the bulleted justification list at doc 175-179 attaches percentages (~5-10% vs ~85-90%) and "income elasticities not justified" to this citation; the code at 13-14 only states "minor importance of non-bioenergy material usage". The core quoted justification IS present; the percentages are the doc's gloss (flagged illustrative elsewhere). Loose but not a false claim. Not flagged.
- **`rice` vs `rice_pro`** (doc 444): illustrative parenthetical "(tece, maiz, rice, soybean, etc.)" uses `rice` where the set member is `rice_pro`. Clearly an "etc." example, not presented as the authoritative set (the full set is correctly described as 39 members). MANDATE-12-adjacent but in explicitly-illustrative context. Not flagged.

---

## Deferred (not code-verifiable here)

- Input-data temporal coverage claims: historical material demand "y1965-y2010" (doc 47/140/354) and historical bioplastic "y1965-y2020" (doc 363). The y-range is stated in the `presolve.gms:9` comment ("y1965 to y2010") and the bioplastic y2020 cutoff is consistent with code, but the actual first/last years in `f62_dem_material.cs3` / `f62_hist_dem_bioplastic.csv` require reading the binary/cs input files (not present in worktree — only the `files` manifest). Cannot confirm exact span.
- Magnitude claims (~5-10% material share, ~85-90% food/feed, conversion ratios, typical Mio tDM totals): all explicitly labeled illustrative/pedagogical in the doc; not real-data claims, not code-checkable.
- "Centrality: Medium" / "🟡 MEDIUM RISK" (doc 897, 907): cross-doc judgment, points to `core_docs/Module_Dependencies.md`; not a module-62 code claim.

---

## Mechanical checks
- M1 (file:line citations present): PASS (60+ full-path-style citations, all spot-checked correct).
- M3 (variable prefixes valid): PASS (vm_/pm_/im_/s62_/p62_/f62_/q62_ all correctly prefixed).
- Realization stated + matches default: PASS (single realization, correctly named).

## Summary
module_62.md is accurate and well-cited. All equations, formulas, defaults (incl. the s62_include_bioplastic=1 ON-by-default, NOT inverted), citations, the 39-commodity set count, and the full dependency set (consumer = M16 only; upstream M09/M15/M73) verify against develop. Two issues: (B1, Minor) footer wrongly lists "GDP" as an M09 dependency — module 62 reads only im_pop; (B2, Informational) File Structure Summary omits scaling.gms and lists parent-dir module.gms in its place. Score 9/10.
