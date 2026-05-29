# Round 30 doc audit — Core_Architecture.md

**Auditor**: Opus (adversarial doc auditor)
**Date**: 2026-05-29
**Target**: `core_docs/Core_Architecture.md`
**Ground truth**: `/tmp/magpie_develop_ro` @ `ee98739fd` (Merge PR #887, develop, worktree clean)
**Config**: `/tmp/magpie_develop_ro/config/default.cfg`

## Overall verdict: ACCURATE (9.5/10)

Core_Architecture.md is a high-level structural overview. Nearly every load-bearing, code-checkable
claim verified correct against current develop. **0 confirmed bugs.** 4 items deferred (not cleanly
code-verifiable, or false-positive risk). This doc is unusually clean — consistent with it being a
stable architectural overview rather than a fast-drifting interface-variable doc.

---

## Claims verified CORRECT

### Section 1 / Summary — overview counts
- "46 independent modules" — CONFIRMED. `ls -d modules/*/` = 46 dirs; `modules/include.gms` includes 46 `module.gms`.
- "12 world regions" — CONFIRMED. `core/sets.gms:20-21` set `i / CAZ, CHA, EUR, IND, JPN, LAM, MEA, NEU, OAS, REF, SSA, USA /` (12).
- "200 cluster cells" — CONFIRMED. `core/sets.gms:57-69` set `j` runs to `USA_183*USA_200`; input config uses `...c200...` cellular file.
- "5-year time steps" — CONFIRMED. `t_all` is 5-year periods (`sets.gms:154-159`).
- "12 distinct phases" — CONFIRMED (see §2.2 below).

### Section 2.1 — main.gms entry-point line citations (ALL exact)
Verified each against `/tmp/magpie_develop_ro/main.gms`:
- "Module Setup (lines 193-253)" — setglobals at 193-252 (line 253 blank, 254 = END comment). Essentially correct (off-by-one trivial).
- "Core Macros (line 257)" — `$include "./core/macros.gms"` @ 257. ✓
- "Core Sets (line 261)" — `$include "./core/sets.gms"` @ 261. ✓
- "Module Sets (line 262)" — `$batinclude "./modules/include.gms" sets` @ 262. ✓
- "Core Declarations (line 266)" — `$include "./core/declarations.gms"` @ 266. ✓
- "Module Declarations (line 267)" — @ 267. ✓
- "Data Import (line 271)" — `$batinclude ... input` @ 271. ✓
- "Equations Definition (line 275)" — `$batinclude ... equations` @ 275. ✓
- "Model Definition (line 279)" — `model magpie / all - m15_food_demand /;` @ 279. ✓
- "Variable Scaling (line 291)" — `$batinclude ... scaling` @ 291. ✓
- "General Calculations (line 295)" — `$include "./core/calculations.gms"` @ 295. ✓

### Section 2.2 / 5.1 — phase list (12 phases)
Phases listed: sets, declarations, input, equations, scaling, start, preloop, presolve_ini, presolve, solve, intersolve, postsolve = 12.
- sets/declarations/input/equations/scaling — batincluded in `main.gms:262,267,271,275,291`. ✓
- start/preloop/presolve_ini/presolve/solve/intersolve/postsolve — batincluded in `core/calculations.gms:13,15,52,54,76,81,87`. ✓
- Annotations ("preloop = ONCE before loop", "presolve_ini e.g. 22_land_conservation bounds", "solve = 80_optimization", "intersolve = 15_food coupling") all consistent with code.

### Section 3.2 — core sets (verified against core/sets.gms)
- `i` 12 regions w/ exact member names — `sets.gms:20-21`. ✓
- `j` 200 clusters — `sets.gms:57-69`. ✓
- `iso` ISO countries — `sets.gms:37-55`. ✓
- `cell(i,j)` mapping — `sets.gms:71-83`. ✓
- `t_all` "All time periods (1965-2150)" — `sets.gms:154-159` y1965..y2150. ✓
- `t` "default 1995-2100" — `sets.gms:188` coup2100 = y1995..y2100 (default). ✓
- `t_past` configured — `sets.gms:177-183`. ✓ `ct`/`pt` dynamic — `sets.gms:218-219`. ✓
- `land` pools crop/past/forestry/primforest/secdforest/urban/other — `sets.gms:251` exact 7. ✓
- `w / rainfed, irrigated /` — `sets.gms:241`. ✓
- `nutrients` dm/ge/nr/p/k — `sets.gms:288-289`. ✓
- `kall` products incl. crops + livestock + residues + timber — `sets.gms:228-235`. ✓
- Livestock members `livst_rum, livst_pig, livst_chick, livst_egg, livst_milk` — `sets.gms:233` exact. ✓
- `ac` "5-year intervals" — `sets.gms:269-275` (ac0..ac300, acx). ✓ (doc does not enumerate, so no MANDATE-11 truncation risk).

### Section 4.2 — full 46-module list
Every module number + name matches `modules/include.gms` and `ls modules/`, including `71_disagg_lvst`.

### Section 5.2 — time-step execution pseudo-code
Matches `core/calculations.gms` precisely:
- start/preloop before loop (13,15); `ct(t)=no; pt(t)=no` clear (33-34); `loop(t...)` (40);
  `ct(t)=yes; pt(t)=yes$(ord(t)=1); pt(t-1)=yes$(ord(t)>1)` (43-45); presolve_ini→presolve (52,54);
  `sm_intersolve=0; while(sm_intersolve=0, ...)` (57-59); load_gdx (62); solve (76); `sm_intersolve=1` (79);
  intersolve (81); postsolve (87); `Execute_Unload "fulldata.gdx";` (92); restart `put_utility 'save'` (99). ✓

### Section 6 — naming conventions (prefixes verified to EXIST in code)
- `vm_` interface var — e.g. `vm_land` `modules/10_land/*/declarations.gms`. ✓
- `pm_` interface param — 84 files contain `pm_`. ✓
- `v##_` internal var — `v32_cost_hvarea` etc. `modules/32_forestry/dynamic_may24/declarations.gms:64`. ✓
- `p##_` internal param — `p32_aff_pol` `:14`. ✓
- `q##_` equations — `q11_cost_glo`, `q11_cost_reg`. ✓
- `f##_` file params — `f14_fao_yields_hist` etc. ✓
- `i##_` input params — `i14_calib_yields_hist` etc. ✓
- `o##_` output params — `o15_kcal_regr_initial`, `o60_glo` (8 unique). ✓
- `m_` macros — `m_year`, `m_annuity_*` `core/macros.gms`. ✓
- `s_`/`sm_` scalars — `s_use_gdx` (`main.gms:187`), `sm_intersolve` (`core/declarations.gms:9`). ✓
- `c_` config switches — convention real (`c_timesteps`, `c_past` in main.gms). ✓
- `_reg` / `_glo` suffixes — present in 15 / 5 declarations.gms files respectively. ✓
- (`x_` — see deferred #1)

### Section 7.1 — model definition
`model magpie / all - m15_food_demand /` @ `main.gms:279`. `m15_food_demand` model block exists @ `modules/15_food/anthro_iso_jun22/declarations.gms:207`. Description "all equations except food demand model" correct. ✓

### Section 7.2 — solver options (lines 281-287)
`iterlim=1000000, reslim=1000000, sysout=Off, limcol=0, limrow=0, decimals=3, savepoint=1` — exact match `main.gms:281-287`. ✓

### Section 9.3 — dynamic sets
`h2(h)=yes; i2(i)=yes; j2(j)=yes;` — `core/sets.gms:121-128`. ✓

### Section 10 — config / restart
- §10.1 example `$setglobal land landmatrix_dec18` / `yields managementcalib_aug19` — match `main.gms:194,198` (also default.cfg:354). ✓
- §10.2 `$setglobal c_timesteps coup2100` / `c_past till_2015` — match `main.gms:182,183`. ✓
- §10.3 `$if set RESTARTPOINT $goto %RESTARTPOINT%` — `main.gms:8` exact. ✓

---

## DEFERRED (not flagged — code-unverifiable or false-positive risk)

1. **`x_` prefix ("Critical output parameters"), §6 line 244.** No live variable in develop uses
   `x_` / `x##_` / `xm_` (rg: `x[0-9][0-9]_...` = 0 unique; `xm_` = 0 unique; positive control
   `o[0-9][0-9]_...` = 8). HOWEVER this prefix is ALSO documented in the agent's own `Data_Flow.md:70`
   ("eXtremely important outputs") and MAgPIE's README references a "Coding Etiquette" that
   traditionally defines o_/x_ output prefixes. Absence of current usage ≠ fabricated convention;
   `x_` is plausibly a reserved/rarely-used prefix. Per audit rule ("claimed convention does not
   exist" is highest-risk false positive; false positives worse than misses), NOT flagged. If a
   future maintainer wants to tighten: note `x_` is reserved/currently-unused in develop, rather than
   delete it.

2. **§2.1 step "12. Time Loop Execution" has no line number; the loop lives in
   `core/calculations.gms` (included at step 11, `main.gms:295`), not directly in main.gms.** This is
   a pedagogical flattening: main.gms IS the entry point and transitively drives the loop via the
   calculations.gms include. Not a code error; would only be a Minor structural-precision nit.
   Optional clarification, not a bug.

3. **§8.1 "IMAGE: Socioeconomic projections".** MAgPIE drivers are SSP-based; "IMAGE" as the
   socioeconomic source is a prose data-provenance claim not statically verifiable from GAMS code
   (belongs to preproc/mrdrivers domain). Not code-checkable here.

4. **§11 dependency chains** ("All modules depend on 09_drivers,10_land"; "14→17→70";
   "35→32→73"; "52→56→57"). Directionally plausible (spot-checked: `32_forestry` references
   natveg-domain vars; `73_timber` references forestry-domain vars). "depend on" is fuzzy and these
   are architectural generalizations, not falsifiable interface-set claims. Not flagged.

---

## Notes on method
- All line numbers re-verified in CURRENT develop (worktree clean @ ee98739fd), per MANDATE 16.
- Absence claims (`x_`) confirmed with rg + positive control (`o##_`). The `find -exec grep +` cross-check
  was unreliable here (batch truncation, the documented hazard) — rg results are the trustworthy ones
  and were consistent across invocations.
- No phantom/omitted consumer-set bugs: this doc makes no specific `vm_FOO consumed by {set}` claims to
  diff (its §11 chains are generalizations, not enumerated consumer sets), so MANDATE 13/17 had no
  concrete target to falsify.
