# Round 36 doc audit — module_41.md (Area Equipped for Irrigation)

**Target doc**: `magpie-agent/modules/module_41.md`
**Ground truth**: `/tmp/magpie_develop_ro/modules/41_area_equipped_for_irrigation/` + `config/default.cfg`
**Auditor**: Opus (highest capability), adversarial doc audit
**Date**: 2026-05-30

## Overall Verdict: MOSTLY ACCURATE
## Accuracy estimate: ~8.5/10

The doc is unusually accurate on the load-bearing facts: default realization, equation formulas, variable names, equation counts, the vast majority of file:line citations, the depreciation default (0), and the cross-module relationships are all correct and verified in code. The errors are concentrated in two low-harm areas: (1) a wrong scaling-factor value (`10e4` vs code `1e4`) presented as code-verified, and (2) a systematically off-by-one file-line-count table in §17. Neither would cause a wrong high-stakes code edit, hence no Critical.

---

## Pre-run advisory verification (REQUESTED)

> "Verify default realization (likely endo_apr13; also has 'static' - LEAD with the default). R33 confirmed M41 reads vm_area: sum(kcr, vm_area(j,kcr,'irrigated')) =l= vm_AEI. Verify vm_AEI producer/consumer sets with BOTH 'name(' AND 'name.' greps + positive control."

**CONFIRMED on all points:**

1. **Default realization = `endo_apr13`** — `config/default.cfg`: `cfg$gms$area_equipped_for_irrigation <- "endo_apr13"    # def = endo_apr13`. Doc LEADS with endo_apr13 (line 7-8). ✅ Correct.
2. **M41 reads vm_area** in q41_area_irrig: `endo_apr13/equations.gms:11` and `static/equations.gms:11` both `sum(kcr, vm_area(j2,kcr,"irrigated")) =l= vm_AEI(j2)`. ✅ Confirmed.
3. **vm_AEI producer/consumer sets** (both `vm_AEI(` and `vm_AEI.` greps + positive control run):
   - **Populated/bounded by M41 only**: `static/presolve.gms:9` (`.fx`), `endo_apr13/presolve.gms:11` (`.lo`), read back via `.l` in postsolve. vm_AEI is M41's own decision variable.
   - **Direct consumers OUTSIDE M41**: ONLY `modules/30_croparea/detail_apr24/equations.gms:82` (`q30_rotation_max_irrig`: `- vm_AEI(j2) * sum(ct,i30_rotation_rules(...))`). The DEFAULT M30 realization `simple_apr24` lists `vm_AEI` in `not_used.txt` (does NOT consume it).
   - Comprehensive sweep `rg -n 'vm_AEI' modules/ core/ -g '*.gms' | grep -v 41_area_equipped` → single hit (M30 detail_apr24:82). Positive control: `rg -c 'vm_area' modules/30_croparea/simple_apr24/equations.gms` → 10 (search works).
   - **vm_cost_AEI consumer**: ONLY M11 `default/equations.gms:29` (`+ vm_cost_AEI(i2)` in cost aggregation).

   Doc's "Used by: Module 30 (constraint on irrigated cropland)" (line 282, 619) is the q41_area_irrig economic relationship (constraint is DEFINED in M41, bounds M30's vm_area) — accurate as the documented relationship. The doc does NOT mention the additional `detail_apr24`-only rotation-constraint read, but its core claim (vm_AEI bounds irrigated cropland) holds for all realizations. NOT flagged as a bug (see Deferred for the missing-nuance note).

---

## Verified-correct claims (high-confidence)

| Doc claim | Doc line | Code evidence | Verdict |
|---|---|---|---|
| Default realization `endo_apr13` | 7-8 | `config/default.cfg` def line | ✅ |
| q41_area_irrig formula (both realiz.) | 38-39, 812-813 | endo & static `equations.gms:10-11` exact | ✅ |
| q41_cost_AEI formula | 62-66, 819-823 | `endo_apr13/equations.gms:19-23` exact (whitespace aside) | ✅ |
| `vm_AEI(j)` positive var, declarations.gms:19 | 274 | `endo_apr13/declarations.gms:19` | ✅ |
| `vm_cost_AEI(i)` var, declarations.gms:15 | 284 | `endo_apr13/declarations.gms:15` | ✅ |
| `pc41_AEI_start(j) = f41_irrig("y1995",...)` preloop.gms:9 | 134 | `endo_apr13/preloop.gms:9` | ✅ |
| `vm_AEI.lo = pc41_AEI_start / (1-s41_dep)**m_timestep_length` presolve.gms:11 | 107 | `endo_apr13/presolve.gms:11` | ✅ |
| `pc41_AEI_start(j)=vm_AEI.l(j)` postsolve.gms:8 | 162 | `endo_apr13/postsolve.gms:8` | ✅ |
| `p41_AEI_start(t,j)=pc41_AEI_start(j)` presolve.gms:8 | 173 | `endo_apr13/presolve.gms:8` | ✅ |
| `vm_AEI.fx(j)=f41_irrig(...)` static presolve.gms:9 | 193 | `static/presolve.gms:9` | ✅ |
| `vm_cost_AEI.fx(i)=0` static presolve.gms:11 | 204 | `static/presolve.gms:11` | ✅ |
| s41_AEI_depreciation default 0, input.gms:11 | 84,126,415,778 | `endo_apr13/input.gms:11` `/ 0 /` | ✅ |
| `$setglobal c41_initial_irrigation_area LUH3` input.gms:8 | 144 | `endo_apr13/input.gms:8` | ✅ |
| t_ini41 = y1995..y2015 (sets.gms:9-10) | 147-149 | `endo_apr13/sets.gms:9-10` | ✅ |
| aei41 = LUH3, Mehta2024_Siebert2013, Mehta2024_Meier2018 (sets.gms:12-13) | 137-139 | `endo_apr13/sets.gms:12-13` | ✅ |
| f41_c_irrig table input.gms:14-18, $include line 16 | 99,262,481 | `endo_apr13/input.gms:14-18` | ✅ |
| `pc41_unitcost_AEI(i)=f41_c_irrig(t,i)` presolve.gms:14 | 100 | `endo_apr13/presolve.gms:14` | ✅ |
| 2 equations endo / 1 equation static | 24,803 | declarations.gms q41 grep: endo {q41_area_irrig, q41_cost_AEI}; static {q41_area_irrig} | ✅ |
| equation declarations endo:22-25 / static:16-18 | 806-807 | endo eqns block 22-25; static 16-18 | ✅ |
| oq41_cost_AEI endo-only | 677 | `rg oq41_cost_AEI static/` → no match (EXIT 1) | ✅ |
| ov_*/oq41_* postsolve lines 11-18 (marg/level) | 656,661,672,677 | `endo_apr13/postsolve.gms:11-26` exact mapping | ✅ |
| vm_cost_AEI used by M11 (aggregated into total costs) | 292,623 | `11_costs/default/equations.gms:29` | ✅ |
| pm_interest from M12 | 304 | `12_interest_rate/select_apr20/declarations.gms:9` `pm_interest(t_all,i)` | ✅ |
| cell(i,j) core set; m_timestep_length core macro | 308,312 | `core/sets.gms:71`; `core/macros.gms:51` | ✅ |
| static @limitation "No irrigation...not equipped...in the past" realization.gms:12 | 217-218 | `static/realization.gms:12` exact | ✅ |
| Authors Anne Biewald, Markus Bonsch, Christoph Schmitz | 900 | `module.gms:15` | ✅ |
| Convergence to European level by 2050 realization.gms:21 | 247-248 | `endo_apr13/realization.gms:21` | ✅ |

Mechanical checks: M1 ✅ (abundant file:line); M2 ✅ (leads with default endo_apr13, notes static); M3 ✅ (all prefixes valid: vm_, pc41_, p41_, s41_, f41_, c41_, pm_); M4/M6 N/A (doc, not Q&A answer).

---

## Bugs found

### BUG module_41-B1 — scaling factor value wrong (`10e4` vs code `1e4`)
- **Severity**: Major (tier_uncertainty: true — borderline Minor; scaling factors affect solver numerics only, not model results)
- **Class**: 12 (content-level citation mismatch) / "wrong number"
- **Trigger**: §1 Major — "Right concept, wrong number (... default value off by a moderate factor)"; also content-mismatch at a cited line.
- **Doc lines**: module_41.md:693 and :698
- **Claim in doc** (line 693, presented as code at the cited site `endo_apr13/scaling.gms:8`):
  ```
  vm_cost_AEI.scale(i) = 10e4;
  ```
  and (line 698) "Variable values ~ millions of USD, **scaling by 10^5** brings closer to order of magnitude 1".
- **Reality in code**: `endo_apr13/scaling.gms:8` = `vm_cost_AEI.scale(i) = 1e4;` (= 10,000 = 10^4, NOT 10^5). `10e4` evaluates to 100,000 = 10^5, so both the quoted value and the magnitude prose are 10× too large vs code.
- **File evidence**: `modules/41_area_equipped_for_irrigation/endo_apr13/scaling.gms:8: vm_cost_AEI.scale(i) = 1e4;`
- **verify_cmd**: `rg -n 'vm_cost_AEI\.' /tmp/magpie_develop_ro/modules/41_area_equipped_for_irrigation/endo_apr13/scaling.gms` → `8:vm_cost_AEI.scale(i) = 1e4;` (also full cat -n of scaling.gms confirms line 8 `1e4`, line 10 `q41_cost_AEI.scale(i) = 1e4;`)
- **confirmed**: true
- **Proposed fix**: In the code block at module_41.md:693 replace `vm_cost_AEI.scale(i) = 10e4;` with `vm_cost_AEI.scale(i) = 1e4;`. At line 698 replace "scaling by 10^5 brings closer to order of magnitude 1" with "scaling by 10^4 brings closer to order of magnitude 1".

### BUG module_41-B2 — §10 omits the second scaling statement `q41_cost_AEI.scale(i) = 1e4`
- **Severity**: Minor
- **Class**: 6 (count/completeness drift) — descriptive incompleteness of a section that purports to document scaling.
- **Trigger**: §1 Minor — "Wrong detail, but a careful reader wouldn't be misled into action".
- **Doc lines**: module_41.md:690-702 (§10 "Scaling")
- **Claim in doc**: §10 documents only `vm_cost_AEI.scale(i)` as the scaling applied (source line cited: `endo_apr13/scaling.gms:8`).
- **Reality in code**: `endo_apr13/scaling.gms` has THREE relevant lines: `:8 vm_cost_AEI.scale(i) = 1e4;`, `:9 *q41_area_irrig.scale(j) = 1e-2;` (commented out), `:10 q41_cost_AEI.scale(i) = 1e4;` (active equation scaling). The doc omits the active `q41_cost_AEI.scale` (line 10).
- **File evidence**: `modules/41_area_equipped_for_irrigation/endo_apr13/scaling.gms:10: q41_cost_AEI.scale(i) = 1e4;`
- **verify_cmd**: `cat -n /tmp/magpie_develop_ro/modules/41_area_equipped_for_irrigation/endo_apr13/scaling.gms` → 10 lines; line 10 = `q41_cost_AEI.scale(i) = 1e4;`
- **confirmed**: true
- **Proposed fix**: After the `vm_cost_AEI.scale` block in §10, add: "The equation `q41_cost_AEI` is also scaled (`endo_apr13/scaling.gms:10`: `q41_cost_AEI.scale(i) = 1e4;`); a third scaling line for `q41_area_irrig` is present but commented out (`scaling.gms:9`)."

### BUG module_41-B3 — §17 file-line-count table systematically off by one
- **Severity**: Minor (tier_uncertainty: true — borderline Informational; pure metadata in a "Summary of File Locations" section, no reader acts on it)
- **Class**: 6 (hardcoded counts drift)
- **Trigger**: §1 Minor — wrong detail, not action-misleading; contradicts the doc's own "100+ citations verified" quality claim.
- **Doc lines**: module_41.md:961-987 (§17), plus the contradicted "9 lines" at :972
- **Claim in doc vs reality** (all files end with a trailing newline, so `wc -l` = true last-line number):

  | File | Doc says | Actual (wc -l) |
  |---|---|---|
  | module.gms | 21 | 20 |
  | endo realization.gms | 40 | 39 |
  | endo sets.gms | 15 | 14 |
  | endo declarations.gms | 35 | 34 |
  | endo input.gms | 26 | 25 |
  | endo equations.gms | 24 | 23 |
  | endo preloop.gms | 10 | 9 |
  | endo presolve.gms | 15 | 14 |
  | endo postsolve.gms | 28 | 27 |
  | endo scaling.gms | 9 | **10** |
  | static realization.gms | 23 | 22 |
  | static sets.gms | 15 | 14 |
  | static declarations.gms | 27 | 26 |
  | static input.gms | 16 | 15 |
  | static equations.gms | 17 | 16 |
  | static presolve.gms | 12 | 11 |
  | static postsolve.gms | 23 | 22 |

  16 of 17 are +1 too high; scaling.gms is -1 (doc 9, actual 10).
- **File evidence**: `wc -l` over all files in `/tmp/magpie_develop_ro/modules/41_area_equipped_for_irrigation/{,endo_apr13/,static/}*.gms`; trailing-newline confirmed via `tail -c 1 | xxd` (0a) for module.gms, realization.gms, equations.gms, static/postsolve.gms.
- **verify_cmd**: `wc -l module.gms endo_apr13/*.gms static/*.gms` (in module dir) → counts above; `awk 'END{print NR}' endo_apr13/scaling.gms` → 10.
- **confirmed**: true
- **Proposed fix**: Update §17 line counts to the "Actual" column above (note scaling.gms is 10 lines, not 9). Lower-priority cosmetic fix; alternatively drop exact line counts (they drift on every code edit) in favor of "~N lines".

---

## Deferred (not code-verifiable here, or judgment-call missing-nuance — DO NOT edit)

- **M30 detail_apr24 rotation read of vm_AEI** (`30_croparea/detail_apr24/equations.gms:82`, `q30_rotation_max_irrig`): a genuine additional direct equation-level consumer of vm_AEI that exists ONLY in the non-default `simple_apr24`... correction: only in non-default `detail_apr24` (default is `simple_apr24`, which has vm_AEI in `not_used.txt`). The doc's "Used by Module 30" claim describes the q41_area_irrig constraint (defined in M41) and is accurate; the rotation-constraint read is an undocumented nuance, NOT a doc error. Optional enhancement, not a bug.
- **f41_c_irrig.csv "~10 regions" / region count** (doc §6.2 line 475) and **avl_irrig.cs3 cell/dimension claims** (§6.1): input data files are NOT materialized in the read-only develop worktree (only `input/files` manifests present). Cannot verify column counts. Doc's "~10 MAgPIE regions" and "~200 cells" are conventional MAgPIE approximations, plausible but unverified here.
- **s41_AEI_depreciation unit** (doc §5.1 line 417 "Fraction per year (0-1)" vs code comment `(USD17PPP per USD17PPP)`): both describe a dimensionless ratio; the formula `(1-s41)**m_timestep_length` treats it per-year. Reasonable interpretation, not a clear error.
- **Cost-data / convergence prose, World Bank 1995 attribution, Mehta/Siebert/Meier citations**: match realization.gms / sets.gms comments; bibliographic correctness of the @keys is out of code-audit scope.
- **"zero errors" / "Changes Since Last Verification: None" closing meta-claims** (lines 1008, 1063): overclaims given B1-B3, but these are documentation meta-statements, not code-checkable interface facts. Not recorded as interface bugs.
- **Doc's "Used by: Module 30" framing vs MANDATE-17 strictness**: the q41_area_irrig constraint is DEFINED in M41 (M41 reads M30's vm_area), so the "M30 uses vm_AEI" framing is economic shorthand. Standard MAgPIE doc convention; the parallel M42 entry (line 627) correctly labels M42 as indirect-via-M30. Not flagged.

---

## Summary

module_41.md is solid on all load-bearing facts (default realization, both equation formulas, variable/parameter names, equation counts, depreciation default 0, M11/M30/M12 relationships, ~95% of file:line citations all verified in develop). Three low-harm code-verifiable errors: (B1, Major) scaling value `10e4`+"10^5" should be `1e4`+"10^4" at scaling.gms:8; (B2, Minor) §10 omits the active `q41_cost_AEI.scale(i)=1e4` at scaling.gms:10; (B3, Minor) §17 file-line counts systematically off by one. No Critical: no wrong default, no inverted boolean, no invented variable/equation, no wrong consumer SET that would misdirect a modification.
