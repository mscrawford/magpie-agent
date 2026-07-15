# Round 31 Doc Audit — module_13.md (Technological Change / tc)

**Auditor**: Opus 4.8 (1M) adversarial doc-vs-code audit
**Target**: `<magpie-agent>/modules/module_13.md`
**Ground truth**: `/tmp/magpie_develop_ro` (develop worktree) + `config/default.cfg`
**Date**: 2026-05-30

---

## Overall Verdict: MOSTLY ACCURATE (one Critical consumer-set error)

module_13.md is an unusually high-quality doc: equations transcribed verbatim, input.gms switch citations all line-exact, defaults all correct, the exo realization and the Module 41 contrast box both verified. The one serious problem is a **phantom consumer**: Module 38 (Factor Costs) is claimed to consume `vm_tau` in four separate locations, but `vm_tau` does not appear anywhere in Module 38's code. This is the R20-anchor wrong-consumer-set class and is also a MANDATE 17 violation (transitive chain tau→yield→prod→cost presented as a direct read). Remaining issues are Minor citation-range overshoot and a Verification-Summary count mismatch.

**Accuracy score**: 6/10 (one Critical = -4).

---

## Default realization & key config — VERIFIED

| Claim | Code | Verdict |
|---|---|---|
| Default realization `endo_jan22` | `config/default.cfg:293` `cfg$gms$tc <- "endo_jan22"` | ✓ |
| Alternative `exo` exists | `modules/13_tc/exo/` dir present | ✓ |
| `s13_max_gdp_shr` default `Inf` | `input.gms:11` `/ Inf /` | ✓ |
| `s13_ignore_tau_historical` default `1` | `input.gms:10` `/ 1 /` | ✓ |
| `c13_croparea_consv` default `0` | `input.gms:12` `/ 0 /` | ✓ |
| `c13_croparea_consv_tau_increase` default `1` | `input.gms:13` `/ 1 /` | ✓ |
| `s13_croparea_consv_tau_factor` default `0.8` | `input.gms:14` `/ 0.8 /` | ✓ |
| `s13_croparea_consv_shr` default `0` | `input.gms:16` `/ 0 /` | ✓ |
| `s13_croparea_consv_start/target` = 2025/2030 | `input.gms:18-19` | ✓ |
| `c13_tccost` default `medium` | `input.gms:65` `$setglobal c13_tccost  medium` | ✓ |

---

## Equations — VERIFIED (5/5)

declarations.gms:17-23 declares exactly 5 equations: `q13_cost_tc`, `q13_tech_cost`, `q13_tech_cost_sum`, `q13_tau`, `q13_tau_consv`. All five formulas in the doc are transcribed verbatim from `equations.gms`:
- q13_cost_tc — doc cites `equations.gms:20-23`; code 20-23 ✓ verbatim.
- q13_tech_cost — doc cites `40-42`; code 40-42 ✓ verbatim.
- q13_tech_cost_sum — doc cites `44-45`; code 44-45 ✓ verbatim.
- q13_tau — doc cites `52-58`; code is lines 52-53 (see Bug B2, range overshoot).
- q13_tau_consv — doc cites `59-60`; code 59-60 ✓ verbatim, including the `$(c13_croparea_consv_tau_increase = 1 OR sum(ct, m_year(ct)) < s13_croparea_consv_start)` guard.

---

## Interface variables — input side VERIFIED, output side has phantom

**Inputs (all verified):**
- `pm_interest(t_all,i)` ← Module 12 `select_apr20/declarations.gms:9` ✓ (default realization confirmed `select_apr20`, `config/default.cfg:240`).
- `pcm_land(j,land)` ← Module 10, read at `presolve.gms:8-9` ✓ (`pc13_land(i,"pastr")=sum(cell(i,j),pcm_land(j,"past"))`).
- `pm_land_conservation(t,j,land,consv_type)` ← Module 22 `area_based_apr22/declarations.gms:15` (exact signature) ✓; read at `presolve.gms:40` ✓.
- `im_gdp_pc_ppp_iso`, `im_pop_iso` ← Module 09 `aug17/declarations.gms` ✓; read at `presolve.gms:26` ✓.

**Outputs:**
- `vm_tau(j,tautype)` declared `declarations.gms:13` ✓. **Real consumer**: Module 14 only (`14_yields/managementcalib_aug19/equations.gms:16`, `nl_fix.gms`). **Module 38 is NOT a consumer** → Bug B1 (Critical).
- `vm_tech_cost(i)` declared `declarations.gms:10` ✓. Consumer: Module 11 (`11_costs/default/equations.gms`) ✓ — correctly stated.

---

## Bugs Found

### B1 — Critical — Phantom consumer: Module 38 does not consume `vm_tau`

- **Severity**: Critical
- **Trigger**: §1 "Wrong module attribution" / R20 anchor (wrong consumer set on a load-bearing interface variable). Also MANDATE 17 (direct vs transitive consumer).
- **Class**: 15 (latent doc error — wrong consumer set) / 2-adjacent.
- **Doc lines**: `module_13.md:152`, `:155`, `:371`, `:439` (also implied at `:13`, `:442`).
  - `:152` Outputs table: ``| `vm_tau(j,tautype)` | Module 14 (Yields), Module 38 (Factor Costs) | ...``
  - `:155` ``"...linking intensification investments (Module 13) to yield improvements (Module 14) and production costs (Module 38)..."``
  - `:371` ``"Module 38 (Factor Costs): Receives `vm_tau` to adjust production costs"``
  - `:439` ``"Provides to: Modules 11 (costs), 14 (yields), 38 (factor costs)"``
- **Reality in code**: `vm_tau` appears ONLY in Module 13 (self) and Module 14 (yields). Module 38 (`factor_costs`) contains zero references to `vm_tau` (or even the word "tau") in any of its three realizations (`per_ton_fao_may22`, `sticky_feb18` [default], `sticky_labor`). M38's default `sticky_feb18` computes factor costs from `vm_prod_reg`/`vm_prod` and labor/capital requirements (`sticky_feb18/equations.gms:15-44`), not from tau. The intensity↔cost interaction noted in `endo_jan22/realization.gms:34-36` is a forward *pointer* ("can be found instead in [38_factor_costs]"), not a `vm_tau` data dependency. The true path is transitive: `vm_tau` → `vm_yld` (M14) → `vm_prod` → factor costs (M38); MANDATE 17 forbids presenting this as M38 directly "receiving `vm_tau`".
- **File evidence**: `modules/38_factor_costs/sticky_feb18/equations.gms:15-44` (no tau; uses vm_prod_reg/vm_prod). Absence: zero `vm_tau` matches across `modules/38_factor_costs/`.
- **verify_cmd**:
  - `grep -rc "vm_tau" /tmp/magpie_develop_ro/modules/38_factor_costs/ | grep -v ":0$"` → `ZERO vm_tau matches across all M38 files` (printed by fallback echo; grep produced no nonzero-count lines).
  - Positive control: `grep -rc "vm_prod_reg" /tmp/magpie_develop_ro/modules/38_factor_costs/ | grep -v ":0$"` → `sticky_feb18/equations.gms:1`, `per_ton_fao_may22/equations.gms:3`, `sticky_labor/not_used.txt:1` (search dir valid).
  - Full consumer set: `rg --no-ignore -l "vm_tau" /tmp/magpie_develop_ro/modules/` → only `13_tc/*` and `14_yields/managementcalib_aug19/{equations,nl_fix}.gms`.
- **confirmed**: true.
- **Proposed fix**: Remove Module 38 as a `vm_tau` consumer everywhere and (optionally) replace with a labeled transitive note.
  - `:152` Consumer cell → `Module 14 (Yields)`.
  - `:155` → ``"...is the central mechanism linking intensification investments (Module 13) to yield improvements (Module 14). (Production costs in Module 38 respond only indirectly, via `vm_yld`→`vm_prod`, not via `vm_tau` directly.)"``
  - `:371` → delete the "Module 38 ... Receives `vm_tau`" line, or rewrite as: ``"Module 38 (Factor Costs): NOT a direct consumer of `vm_tau`; factor costs respond to intensification only transitively through `vm_yld` (M14) → `vm_prod`."``
  - `:439` Provides-to list → `Modules 11 (costs), 14 (yields)`.
  - Also fix the Verification-Summary "Critical Role" framing at `:155` accordingly.

### B2 — Minor — Citation range overshoot for q13_tau

- **Severity**: Minor
- **Trigger**: §1 Minor "Off-by-few line citation where adjacent lines say similar things" (citation drift into adjacent comment block).
- **Class**: 10 (stale/imprecise file:line citation).
- **Doc line**: `module_13.md:103` `*Source*: modules/13_tc/endo_jan22/equations.gms:52-58`.
- **Reality in code**: `q13_tau` occupies lines 52-53 only (52 = `q13_tau(j2,tautype)..`, 53 = the `=e=` body). Lines 54-58 are a blank line plus the comment preamble for the *next* equation (`q13_tau_consv`). The cited range 52-58 overshoots by 5 lines into unrelated content.
- **File evidence**: `equations.gms:52-53` (equation); `:55-57` are the `q13_tau_consv` doc-comment.
- **verify_cmd**: `awk 'NR>=52 && NR<=53 {print NR": "$0}' /tmp/magpie_develop_ro/modules/13_tc/endo_jan22/equations.gms` → 52: `q13_tau(j2,tautype)..`, 53: `vm_tau(j2,tautype) =e= sum(...);`.
- **confirmed**: true.
- **Proposed fix**: change `:103` citation to `modules/13_tc/endo_jan22/equations.gms:52-53`.

### B3 — Informational — Verification-Summary interface-variable count mismatch

- **Severity**: Informational
- **Trigger**: §1 Informational (metadata/footer count not acted upon) — borderline Minor (Pattern 6 count drift), tie-broken down because it is in the non-load-bearing Verification Summary footer.
- **Class**: 6 (hardcoded counts drift).
- **Doc line**: `module_13.md:418` `- **Interface variables verified**: 6/6 (vm_tau, vm_tech_cost, v13_tau_core, v13_tau_consv, pm_interest, pcm_land, pm_land_conservation)`.
- **Reality**: the parenthetical lists 7 names, not 6; and the line conflates module-13-internal variables (`v13_tau_core`, `v13_tau_consv`) with interface (`vm_*`) and imported (`pm_*`) variables under one "interface variables" label.
- **File evidence**: N/A (internal count inconsistency).
- **verify_cmd**: manual count of the parenthetical list = 7 entries vs stated "6/6".
- **confirmed**: true.
- **Proposed fix**: change `6/6` to `7/7` (or drop the count); optionally relabel as "interface + imported + internal variables verified".

---

## Advisory check (pre-run flag) — REFUTED (no bug)

> Pre-run advisory: "R30 verified module 13's TC mechanism is a GDP-share cap on `vm_tech_cost.up` via `s13_max_gdp_shr` (presolve.gms:21-26). Ensure module_13.md describes this correctly, not as a generic 'GDP drives adoption rate'."

module_13.md describes this **correctly**. `:143` labels `im_gdp_pc_ppp_iso` as a "GDP per capita **cap** on tech investments"; `:276-288` gives the constraint as `vm_tech_cost.up(i) = sum((i_to_iso(i,iso),ct), im_gdp_pc_ppp_iso(ct,iso) * im_pop_iso(ct,iso)) * s13_max_gdp_shr`, matching `presolve.gms:25-26` verbatim, and frames it as a cap to "avoid unrealistically high endogenous investments." The doc nowhere states "GDP drives adoption rate." Confirmed against `presolve.gms:21-33`. No bug; advisory concern already satisfied.

---

## Spot-checked claims that are CORRECT (sample)

- 15-year research lag `(1+pm_interest)**15` — `equations.gms:23` ✓.
- Infinite-horizon annuity `r/(1+r)` (no depreciation term) — `equations.gms:42` ✓.
- Module 41 contrast `(r + s41_AEI_depreciation)/(1+r)` — `modules/41_area_equipped_for_irrigation/endo_apr13/equations.gms:23` ✓ (`endo_apr13` realization exists; scalar present).
- q13_tau_consv conditional guard text — `equations.gms:59` ✓.
- Tau bounds: `.lo` historical vs `pc13_tau`, `.up = 2*pc13_tau` — `presolve.gms:13-19` ✓.
- GDP-constraint activation `m_year(t) > sm_fix_SSP2 AND s13_max_gdp_shr <> Inf` — `presolve.gms:21` ✓.
- Initial tau load `pc13_tau(h,"crop") = fm_tau1995(h)` cited at `preloop.gms:18` — exact line ✓.
- Postsolve `pc13_tcguess = (v13_tau_core.l/pc13_tau)**(1/m_yeardiff) - 1` — `postsolve.gms:11` ✓.
- `tautype` members {pastr, crop} `sets.gms:13-14` ✓; `scen13` {low, medium, high} `sets.gms:10-11` ✓.
- exo realization: tau fixed, no equations, reads `f13_tau_scenario.csv` via magpie4 `tau(gdx,...)` — `exo/realization.gms:8-24`; no `equations.gms` in `exo/` ✓.
- `ov_tau` is the GDX output symbol used in the testing snippet — `declarations.gms:48`, `postsolve.gms` ✓.
- `vm_tech_cost` consumer = Module 11 — `11_costs/default/equations.gms` ✓.

---

## Deferred (not code-falsifiable / out of scope — NOT edited)

1. **"1995" vs "2000" initial-tau year**: module_13.md says 1995 (`:178`, `:265`). The CODE supports 1995 (`fm_tau1995`, index `"y1995"`, `preloop.gms:18`). However `endo_jan22/realization.gms:23` *prose* says "year 2000." module_13.md's "1995" is the more code-accurate choice, so NOT a doc bug — but the upstream realization.gms comment is internally inconsistent with its own filename. Flag for maintainers, no edit to module_13.md.
2. **Circular-dependency narrative** (`:446-470`): the chain `...→ pm_yields_semi_calib [14] → Feeds back to tau calculation` is a system-level conceptual narrative cross-referencing `circular_dependency_resolution.md`. M13's tau equations do NOT directly read `pm_yields_semi_calib` (M13 reads `pcm_land`, `pm_interest`, `pm_land_conservation`, GDP/pop only). The doc hedges with "(via past production patterns)" and labels the resolution as lagged/temporal. Borderline MANDATE-2 looseness but framed as narrative, not a direct-read claim — too ambiguous to flag without overreach. `pm_yields_semi_calib` does exist (M14 declarations/preloop).
3. **`endo_apr13/equations.gms` cited without full `modules/41_.../` path** (`:70`): MANDATE-16 prefers full paths, but this is a cross-module aside in a contrast box and its content is verified correct. Informational-at-most; not flagged.
4. **realization.gms:8-33 cited for the "15-year shift" claim** (`:18`): that range is the @description block, which speaks of the general implementation per Dietrich 2014 but not the literal "15 years" (that lives in `equations.gms:23/26-32`, which the doc also cites elsewhere). General-reference citation, acceptable; not flagged.

---

## Summary

3 confirmed bugs: **1 Critical** (Module 38 phantom `vm_tau` consumer, repeated in 4 locations — wrong consumer set, R20-anchor class + MANDATE 17 transitive-as-direct), **1 Minor** (q13_tau citation range 52-58 overshoots the 2-line equation into the next equation's comment block), **1 Informational** (Verification-Summary says "6/6" but lists 7 interface variables). Everything else verified accurate: all 5 equations verbatim, all input.gms switch defaults line-exact, input-side interface attributions correct, exo realization and Module 41 contrast correct. The pre-run GDP-cap advisory is REFUTED — the doc already describes the `s13_max_gdp_shr` cap on `vm_tech_cost.up` correctly.
