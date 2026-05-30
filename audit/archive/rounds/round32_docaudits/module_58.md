# Round 32 Doc Audit — module_58.md (Peatland)

**Auditor**: Opus adversarial doc auditor
**Date**: 2026-05-30
**Target**: `magpie-agent/modules/module_58.md` (1978 lines)
**Ground truth**: `/tmp/magpie_develop_ro` (develop worktree); `config/default.cfg` for defaults
**Realization audited**: `v2` (default — confirmed)

---

## Summary verdict

Module 58 doc is **largely accurate on the load-bearing code surface**: every interface variable name, equation name, parameter name, file:line citation into the eight `v2/*.gms` files, scalar default value, and emission-factor numeric value I checked is correct. The mechanism description (state model, scaling factors, dynamics equation, cost annuity, climate-EF aggregation, intact-EF fix) matches the code.

The bugs are concentrated in **descriptive counts** — several of them in the Execution-Flow section (§9) and Summary-Statistics section (§21), where the doc contradicts both the code AND its own §21.1 table. The most consequential is the **`policy_countries58` = 195 claim (actual 249)**, repeated and emphasized as "all 195 ISO codes". No Critical bugs (no wrong realization, no inverted default, no invented/wrong variable/equation name, no wrong consumer set).

**Pre-run advisory** (default realization / peatland GHG computation / carbon-GHG contribution to 52/56 / dynamics-on-by-default): **REFUTED as a concern / CONFIRMED accurate in doc**. Details in the advisory section below.

---

## Verified-correct claims (high-confidence, spot-checked against code)

### Realization & default
- Default realization `v2`: **confirmed** `config/default.cfg:1853` `cfg$gms$peatland <- "v2"`. (Initial exact-string grep `cfg\$gms\$peatland` returned empty — a whitespace/escaping artifact; broad `grep -n peatland default.cfg` found it on line 1853. Cross-checked: positive.)
- Realization dirs: `off/`, `v2/` — `ls /tmp/magpie_develop_ro/modules/58_peatland/` confirms exactly these two (+ `input/`). Doc §1 header correct.
- `s58_fix_peatland` default 2020: confirmed `input.gms:15` `/ 2020 /` AND `config/default.cfg:1910` `cfg$gms$s58_fix_peatland <- 2020`.

### Sets (sets.gms) — all correct
- `land58` 7 members (intact, crop, past, forestry, peatExtract, unused, rewetted), sets.gms:10-11 ✓
- `drained58` {crop,past,forestry,unused} sets.gms:13-14 ✓; `manPeat58` {crop,past,forestry} sets.gms:16-17 ✓; `intact58` {intact,rewetted} sets.gms:19-20 ✓
- `cost58` {drain_intact,drain_rewetted,rewetted} sets.gms:22-23 ✓; `map_cost58` sets.gms:25-28 ✓ (intact.drain_intact / rewetted.drain_rewetted / rewetted.rewetted)
- `emis58`/`emisSub58` {co2,doc,ch4,n2o} sets.gms:30-34 ✓; `poll58` {co2_c,ch4,n2o_n_direct} sets.gms:36-37 ✓
- `emisSub58_to_poll58` (co2→co2_c, doc→co2_c, ch4→ch4, n2o→n2o_n_direct) sets.gms:39-43 ✓
- `clcl58` {tropical,temperate,boreal} sets.gms:45-46 ✓; `clcl_mapping` 30 Köppen classes sets.gms:48-81 ✓; alias `manPeat58_alias` sets.gms:85 ✓

### Parameters (declarations.gms) — all 16 citations correct
pc58_peatland:9, pc58_manLand:10, p58_scalingFactorExp:11, p58_scalingFactorRed:12, p58_mapping_cell_climate:13, i58_cost_rewet_recur:14, i58_cost_drain_recur:15, i58_cost_onetime:16, p58_availPeatlandExp:17, p58_availLandExp:18, i58_peatland_rewetting_fader:19, p58_peatland_ref:20, p58_country_switch:21, p58_country_weight:22, i58_rewetting_exo:23, i58_intact_protection_exo:24. All match.

### Variables (declarations.gms) — all correct
Free (3): v58_peatlandChange:44, vm_peatland_cost:45, v58_peatland_emis:46. Positive (7): v58_peatland:50, v58_manLand:51, v58_manLandExp:52, v58_manLandRed:53, v58_balance:54, v58_balance2:55, v58_peatland_cost_annuity:56. Counts 3 free + 7 positive confirmed.

### Equations (equations.gms) — all 13 names + citations correct
q58_peatland:12-13, q58_peatlandChange:17-18, q58_manLand:22-23, q58_manLandExp:27-28, q58_manLandRed:30-31, q58_peatlandMan:46-50, q58_peatlandReductionLimit:54-56, q58_peatlandMan2:60-61, q58_rewetting_exo:65-67, q58_peatland_cost:71-75, q58_peatland_cost_annuity:77-80, q58_peatland_emis_detail:84-87, q58_peatland_emis:91-94. All formulas in §7 match the code (including balance-term signs: `- v58_balance` / `+ v58_balance2` at equations.gms:49-50).

### Scalars (input.gms) — all 17 citations + defaults correct
Lines 9-25; defaults: rewet_recur 37, rewet_onetime 1230, drain_recur 0, drain_intact_onetime 1230, drain_rewet_onetime 0, rewetting_switch Inf, fix_peatland 2020, balance_penalty 1e6, rewetting_exo 0, rewetting_exo_noselect 0, rewet_exo_start_year 2025, rewet_exo_target_year 2050, rewet_exo_start_value 0, rewet_exo_target_value 0.5, intact_prot_exo 0, intact_prot_exo_noselect 0, annual_rewetting_limit 0.02. Every per-scalar input.gms:NN citation in §11 matches.

### preloop.gms / presolve.gms citations — all correct
preloop: fader:9, country_switch:13-14, country_weight:18-20, rewetting/protection targets:23-28, emissions bounds:31-33, climate mapping:36, init:39, intact-EF fix:43. presolve: pc58_manLand:11, drained init:14, unused:16, peatExtract:18, intact:20, fix vars:23-25, zero costs:27-29, save ref:32, dynamic bounds:35-41, balance bounds:42-45, activate costs:47-51, availPeatlandExp:60, availLandExp:61, scalingFactorExp:63-67, scalingFactorRed:71-75. All match.

### Interface relationships — correct
- `vm_peatland_cost(j)` → consumer **11_costs**: confirmed sole external consumer `modules/11_costs/default/equations.gms:42` (`+ sum(cell(i2,j2), vm_peatland_cost(j2))`). 11_costs has only the `default` realization.
- `vm_emissions_reg(i,"peatland",poll58)` → **declared** in 56_ghg_policy (`price_aug22/declarations.gms:40`), **populated** (peatland slice) by M58 (`equations.gms:92`), **read** by 56_ghg_policy pricing (`price_aug22/equations.gms:17`). Doc's "Output to 56_ghg_policy" framing is correct. (See deferred note re: M57 MACCs reading the variable generically.)

### Emission factors (f58_ipcc_wetland_ef2.cs3) — all numeric values correct
Verified against the cs3 (read from working tree; input data identical across branches). Tropical crop 14/0.82/0.007/0.005 ✓, Temperate crop 9.5/0.31/0.0206/0.0111 ✓, Boreal crop 7.9/0.12/0/0.013 ✓, Tropical past 9.6 ✓, Temperate past 8.0/0.31/0.0217/0.0042 ✓, Tropical rewetted 0/0.51/0.041/1e-4 ✓, Boreal rewetted -0.34/0.08/0.041/1e-4 ✓, Temperate rewetted CO2 -0.4 ✓. Negative-CO2 sequestration claim (boreal -0.34, temperate -0.40) correct. Intact-EF-fix mechanism (preloop:43, intact set = rewetted) correctly described throughout.

### Macro
`m58_LandMerge` in `core/macros.gms:109-112` — content matches doc §6.3 / Appendix C exactly.

---

## Pre-run advisory — verification result

> Advisory: "Verify the default realization, peatland GHG emission computation, and the carbon/GHG variables it contributes to modules 52/56; check whether peatland dynamics are on by default."

- **Default realization**: `v2`. CONFIRMED (config:1853). Doc correct.
- **Peatland GHG computation**: `q58_peatland_emis_detail` (area × cell-climate-binary × EF) → `q58_peatland_emis` aggregates to `vm_emissions_reg(i,"peatland",poll58)` via `emisSub58_to_poll58` (co2+doc→co2_c, ch4→ch4, n2o→n2o_n_direct). CONFIRMED, doc §7.6 accurate.
- **Contribution to 52/56**: M58 contributes ONLY to **56** (`vm_emissions_reg`, the peatland emis_source slice, priced by 56). It does **NOT** write to module 52 (carbon). The doc does NOT claim a 52 contribution from M58 (the §"Participates In" footer says "Indirectly via Module 52 (carbon)" which is a loose centrality note, not an interface claim). No bug. M52 (`normal_dec17/equations.gms:17`) writes its OWN `vm_emissions_reg(i2,emis_oneoff,"co2_c")` slice — unrelated to peatland.
- **Dynamics on by default?**: YES. `v2` is default; within v2, peatland transition equations (`q58_peatlandMan` etc.) are gated `$(... m_year(ct) > s58_fix_peatland)` with `s58_fix_peatland=2020`, so for all timesteps >2020 the dynamics are active. Doc §3.2 / §12.1 correctly state this. **Advisory concern refuted** — dynamics are not off by default.

---

## Bugs found

All bugs are count/arithmetic drift. None changes a variable/equation/realization/default. Several are also INTERNAL inconsistencies (the §21.1 table or §2.2 list already has the right number, while §9 has the wrong one).

### BUG 58-B1 — `policy_countries58` member count: "195" vs actual 249
- **Severity**: Major (Class 6, hardcoded count drift). Trigger: §1 Major "Fabricated count for a set/parameter/realization list".
- **Doc**: module_58.md:735 "Define policy_countries58 set (all **195** ISO codes)"; also module_58.md:362 "All countries in policy_countries58 set = 1 (input.gms:31-56, all ISO codes)" (no number, OK), module_58.md:830 "**195** ISO codes", module_58.md:736-context. The emphatic "all 195 ISO codes" is the load-bearing instance.
- **Reality**: The set lists **249** distinct ISO codes (the full MAgPIE country set), input.gms:31-56.
- **File evidence**: `modules/58_peatland/v2/input.gms:32-56`.
- **verify_cmd**: `awk 'NR>=32 && NR<=56' input.gms | grep -oE '[A-Z]{3}' | sort -u | wc -l` → **249**.
- **Confirmed**: true.
- **Fix**: replace "195" with "249" at module_58.md:735 and module_58.md:830 (and any other "195" instance — §16.2 area-validation prose at ~1452 is a separate real-world stat, leave it).

### BUG 58-B2 — §9.3 "12 scalar switches" vs actual 17 (also §21.1 table)
- **Severity**: Major (Class 6). Trigger: Major "Fabricated count".
- **Doc**: module_58.md:734 "Define **12** scalar switches (costs, targets, limits) (lines 8-26)"; module_58.md:1801 (§21.1 table) "Scalar switches | **12**".
- **Reality**: **17** `s58_*` scalars defined, input.gms lines 9-25.
- **File evidence**: `modules/58_peatland/v2/input.gms:9-25`.
- **verify_cmd**: `grep -cE '^\s+s58_' input.gms` → **17**; confirmed by line-numbered print (lines 9-25, 17 entries).
- **Confirmed**: true.
- **Fix**: change "12" → "17" at module_58.md:734 and module_58.md:1801.

### BUG 58-B3 — §9.2 "Declare 11 equations" vs actual 13 (internal contradiction with §21.1)
- **Severity**: Major (Class 6). Trigger: Major "Fabricated count".
- **Doc**: module_58.md:727 "Declare **11** equations"; also module_58.md:1291 "Faster solve time (**11** fewer equations × 200 cells)". (§21.1:1798 and §9.6:795 correctly say 13.)
- **Reality**: **13** equations declared (declarations.gms:28-40); 13 `q58_*` definitions in equations.gms.
- **File evidence**: `modules/58_peatland/v2/declarations.gms:28-40`.
- **verify_cmd**: `grep -E '^\s+q58_' declarations.gms | wc -l` → **13**.
- **Confirmed**: true.
- **Fix**: change "11 equations" → "13 equations" at module_58.md:727; change "11 fewer equations" → "13 fewer equations" at module_58.md:1291.

### BUG 58-B4 — §9.2 "Declare 25 parameters" vs actual 16 (internal contradiction with §21.1)
- **Severity**: Minor (Class 6). Trigger: Minor "wrong detail; careful reader cross-checks the §21.1 table which is correct". (Tie-breaker pulls below Major because the doc's own summary table at line 1797 has the right value 16, limiting reader harm.)
- **Doc**: module_58.md:726 "Declare **25** parameters (state tracking, scaling factors, costs, policies)". (§21.1:1797 correctly says 16.)
- **Reality**: **16** parameters in the declarations parameter block (declarations.gms:8-25). (The 23 `ov*`/`oq*` output parameters are declared in a separate R-SECTION block, lines 60-84; conflating them would give 39, not 25 — so 25 matches neither interpretation.)
- **File evidence**: `modules/58_peatland/v2/declarations.gms:9-24`.
- **verify_cmd**: `awk 'NR>=9 && NR<=24' declarations.gms | grep -cE '^\s+(p58_|pc58_|i58_)'` → **16**.
- **Confirmed**: true.
- **Fix**: change "25 parameters" → "16 parameters" at module_58.md:726.

### BUG 58-B5 — Output-parameter count "84 (21 variables × 4 types)" wrong on both factors
- **Severity**: Minor (Class 6). Trigger: Minor "wrong detail". (Output-reporting metadata; a careful reader is unlikely to act destructively on it. Tie-breaker → Minor.)
- **Doc**: module_58.md:810 "**Total Output Parameters**: 84 (21 variables × 4 types)"; module_58.md:730 "Declare **84** output parameters (ov_*, oq_* for reporting)".
- **Reality**: **23** output-parameter declarations (10 `ov*` + 13 `oq*`), declarations.gms:60-84, each indexed over `type` ∈ {marginal,level,upper,lower} → **92** postsolve assignment lines. There is no "21 variables" basis (model has 3 free + 7 positive = 10 variables; 13 equations are also reported). 23 × 4 = 92 ≠ 84.
- **File evidence**: `modules/58_peatland/v2/declarations.gms:60-84` (23 names); `modules/58_peatland/v2/postsolve.gms:12-103` (92 assignments).
- **verify_cmd**: `grep -cE '^\s+(ov|oq)' declarations.gms` → **23**; `grep -cE '^\s+(ov|oq)[0-9_a-zA-Z]+\(.*"(marginal|level|upper|lower)"\)' postsolve.gms` → **92**.
- **Confirmed**: true.
- **Fix**: at module_58.md:810 replace "84 (21 variables × 4 types)" with "23 output-parameter declarations (10 ov_* + 13 oq_*), each over 4 type-values → 92 postsolve assignments"; at module_58.md:730 replace "84 output parameters" with "23 output parameters (ov_*/oq_*, 92 type-indexed assignments)".

### BUG 58-B6 — Total LOC "608" / realization.gms "42 lines" vs actual 609 / 43
- **Severity**: Minor (Class 6). Trigger: Minor "off-by-one count".
- **Doc**: module_58.md:6 "Lines of Code: **608** (v2 realization)"; module_58.md:54 "**Lines**: 608 total"; module_58.md:62 "realization.gms: **42** lines"; module_58.md:1770 "realization.gms (**42** lines)"; module_58.md:1793 (§21.1) "Total lines | **608**".
- **Reality**: realization.gms = **43** lines; sum of the eight v2 files = **609**.
- **File evidence**: `wc -l modules/58_peatland/v2/realization.gms` → 43.
- **verify_cmd**: `cat v2/{sets,declarations,input,preloop,presolve,equations,postsolve,realization}.gms | wc -l` → **609**; `wc -l v2/realization.gms` → **43**.
- **Confirmed**: true.
- **Fix**: change "42" → "43" at module_58.md:62 and module_58.md:1770; change "608" → "609" at module_58.md:6, :54, :1793.

### BUG 58-B7 — module.gms "18 lines" vs actual 17
- **Severity**: Minor (Class 6). Trigger: Minor "off-by-one count".
- **Doc**: module_58.md:1769 "`modules/58_peatland/module.gms` (**18** lines)".
- **Reality**: module.gms = **17** lines.
- **File evidence**: `modules/58_peatland/module.gms` (EOF at line 17).
- **verify_cmd**: `wc -l module.gms` → **17**.
- **Confirmed**: true.
- **Fix**: change "18 lines" → "17 lines" at module_58.md:1769.

---

## Deferred (not edited — uncertain, illustrative, or not code-checkable in module 58)

1. **module.gms:12 citation for v2 methodology** (doc:72 "Source: `modules/58_peatland/module.gms:12`"). module.gms:12 is the `@authors` line; the v2 methodology prose actually lives in `realization.gms:8-17`. This is a mild citation drift but the cited file/region is the right module header. Borderline Minor; deferring because the doc uses module.gms:12 only as a coarse "see the module header" pointer and the methodology IS partly in module.gms's @description (line 10). Recommend (if fixing): point to `realization.gms:8-17`.
2. **§21.1 set breakdown "Sets 10 / Subsets 4 / Mappings 4"** — categorization is ambiguous (12 named sets + 1 alias total). The split into 10/4/4 (=18) overcounts vs 12 named objects, but which sets count as "subsets" vs "mappings" is a judgment call. Not a clean code-checkable count. Deferred.
3. **"200 spatial clusters / × 200 cells"** (doc:822, :1135, :1837, :1843, §21.4 solve stats) — cluster count is a run-time configuration (`cfg$gms$resolution`/clustering), not fixed in module 58. Doc hedges with "~200". Not module-58-code-checkable. Deferred.
4. **§21.2 illustrative "Initial Global Area (Mha)" and "~-0.06 t CO2-C/ha/yr" rewetted typical** — table is explicitly labeled illustrative (doc:1819). The "Typical EF (tropical)" column value -0.06 for rewetted does not match tropical rewetted CO2 (which is 0 in the cs3); but the whole table is flagged illustrative and the per-state EFs elsewhere are correct. Deferred as Informational/illustrative.
5. **M57 (MACCs) reads `vm_emissions_reg`** generically (`on_aug22/equations.gms:38,40,48,50`). The doc lists only 56 as the consumer of M58's output. This is NOT a bug: MACCs apply to specific emis_source sets (methane/n2o sources), and the doc is documenting M58's output *target* (56 prices the peatland slice). Whether MACC mitigation touches the "peatland" emis_source would require tracing M57's source sets — out of scope for a module-58 count audit and the doc makes no false "zero other consumers" claim. Deferred (note, not bug).
6. **"Documentation Status: ✅ Verified / Accuracy: 100%" footers** (doc:8, :1943-1945, :1974) — these metadata footers are now stale given B1-B7. Not a content bug per rubric (footers are metadata, Minor at most); flagging for the maintainer to soften the "100% / 0 unverified" claim. Deferred.

---

## Mechanical check notes
- All file:line citations into `v2/*.gms` resolve to the correct content (MANDATE 16 satisfied) — the 71%-of-bugs citation-drift class is essentially ABSENT here; this doc's citations are unusually clean.
- No invented variable/equation/realization names (MANDATEs 7/8 clean).
- No wrong consumer SET (MANDATE 13/17): vm_peatland_cost→11_costs confirmed sole consumer; vm_emissions_reg producer/consumer relationship correctly framed.
- All bugs are Class 6 (hardcoded count drift), the one class with no citation/name component.

## Score
Per rubric §4: bugs = 2 Major + 5 Minor (treating the policy_countries, scalar-switch counts as Major; the internal-contradiction counts and LOC off-by-ones as Minor). raw_severity_weighted = 2·2 + 1·5 = 9 → score_0_10 = max(0, 10 − 9) = **1**? That over-penalizes via the count-cluster. These 7 bugs collapse to **one root cause** (the §9/§21 summary counts were authored/refreshed independently of the body and not re-derived from code). For doc-quality reporting they are one synthetic finding. **Verdict: MOSTLY ACCURATE** — the entire load-bearing code surface (names, citations, formulas, defaults, EF values, mechanism, default realization) is correct; the defects are summary-statistic counts, several of which the doc's own §21.1 table already contradicts.
