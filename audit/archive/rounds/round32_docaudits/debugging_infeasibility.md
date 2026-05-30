# Doc Audit: agent/helpers/debugging_infeasibility.md (Round 32)

**Auditor**: Opus adversarial doc-auditor
**Date**: 2026-05-30
**Ground truth**: /tmp/magpie_develop_ro (GAMS develop) + config/default.cfg
**Doc**: /Users/turnip/Documents/Work/Workspace/magpie/magpie-agent/agent/helpers/debugging_infeasibility.md

## Verdict: MOSTLY ACCURATE (lower band)

This doc is unusually accurate on its highest-stakes content — every slack-variable name, every penalty value, the equation constraint types, and the modelstat mechanics check out against current develop. The bugs are concentrated in the "Dangerous Configurations" tables (lines 79, 81, 89, 132-133), where two config switches are mischaracterized and a set of safe/dangerous thresholds is unsupported by code and contradicts the model's own defaults. The R29 pre-run advisory ("13 slack variables") is REFUTED — it was based on a stale doc version.

Score estimate: ~7/10 (1 Major + 2 Minor + caveats).

---

## Claims verified CORRECT (no bug)

### Slack-variable table (lines 101-108) — ALL 5 names + penalties CORRECT
Literal `grep` (authoritative; rg gave a misleading prefix-stripped display here — a live instance of the "cross-check rg with grep" rule):

| Doc claim | Code evidence | Verdict |
|---|---|---|
| `v73_prod_heaven_timber`, M73, $1M/tDM | `modules/73_timber/default/declarations.gms:24`; penalty `s73_free_prod_cost / 1e+06 /` `input.gms:17` | OK |
| `v44_bii_missing`, M44, $1M/unit | `modules/44_biodiversity/bii_target/declarations.gms:13`; `s44_cost_bii_missing / 1e+06 /` `input.gms:13` | OK |
| `v32_land_missing`, M32, $1M/ha | `modules/32_forestry/dynamic_may24/declarations.gms:66`; `s32_free_land_cost / 1e+06 /` `input.gms:33` | OK |
| `v21_import_for_feasibility`, M21, $1,500/tDM, wood/woodfuel only | `modules/21_trade/selfsuff_reduced/declarations.gms`; `s21_cost_import / 1500 /` `input.gms:18`; restricted to `k_import21 = / wood, woodfuel /` `input.gms:13` via `.fx(h,k_trade)=0; .up(h,k_import21)=Inf` `preloop.gms:36-38` | OK — "(only!)" is CORRECT for the default realization |
| `v29_fallow_missing`, M29, $615/ha | `modules/29_cropland/detail_apr24/declarations.gms`; `s29_fallow_penalty / 615 /` `input.gms:34` | OK (note: `s29_cost_treecover_recur` is also 615, a co-located look-alike, but the fallow value is independently 615 — not a confusion) |

All slack-bearing realizations are the DEFAULTS: timber=`default`, biodiversity=`bii_target`, forestry=`dynamic_may24`, cropland=`detail_apr24`, trade=`selfsuff_reduced` (all verified in config/default.cfg). So every table row is active in a default run.

### Note slack variables (line 99) — all 4 names CORRECT
`v32_ndc_area_missing` (`32_forestry/dynamic_may24/declarations.gms`), `v29_treecover_missing` (`29_cropland/detail_apr24`), `v30_betr_missing` (`30_croparea/{simple,detail}_apr24`), `v38_relax_CES_lp` (`38_factor_costs/sticky_labor/declarations.gms:23`). All literal grep hits.

### Equations + constraint types — CORRECT
- `q10_land_area` `=e=` strict equality (`modules/10_land/landmatrix_dec18/equations.gms:13-15`: `sum(land,vm_land(j2,land)) =e= sum(land,pcm_land(j2,land))`). Doc line 53 CORRECT.
- `q43_water` `=l=` per-cluster cap, no transfer term (`modules/43_water_availability/total_water_aug13/equations.gms:10-11`). Doc line 122 "hard cap, no inter-cluster transfer" CORRECT.
- `q60_bioenergy_reg(i2)` `=g=` regional floor (`modules/60_bioenergy/1st2ndgen_priced_feb24/equations.gms:46-47`; default bioenergy=`1st2ndgen_priced_feb24`). Doc line 127 "hard floor — each region MUST produce" CORRECT.
- `q21_notrade` exists in default trade (`modules/21_trade/selfsuff_reduced/equations.gms:18`). `oq21_notrade` marginal output exists (`declarations.gms:47`).
- Output params `oq10_land_area`, `oq43_water`, `ov_land` all exist (postsolve.gms/declarations.gms). Doc Step-3 readGDX targets are real.

### Modelstat mechanics (lines 44, 140-143) — CORRECT
`modules/80_optimization/nlp_apr17/solve.gms:102` (default optimization=`nlp_apr17`):
`if ((p80_modelstat(t) > 2 and p80_modelstat(t) ne 7), ... abort "no feasible solution found!")`.
- Line 44 "first timestep with value > 2 (and ≠ 7)" — CORRECT.
- Lines 140-143 "MAgPIE tolerates modelstat=7 (doesn't abort)" — CORRECT (abort explicitly excludes 7).
- `p80_modelstat` is the right object name (`declarations.gms:9`).

### Food-slack absence (line 109) — CORRECT
`grep -rIn` for `_missing|_heaven|for_feasibility|slack` across modules 15/16/17 returned EMPTY; positive control (`q15_*`/`vm_dem_food` in module 15) passed. `import_for_feasibility` is confined to module 21 only and restricted to wood/woodfuel. The "Critical gap: food/feed/crop production have NO slack" claim is well-founded.

### GSN_HalfEarth (line 80) — CORRECT
`GSN_HalfEarth` is a valid `c22_protect_scenario` member (`modules/22_land_conservation/area_based_apr22/sets.gms:19`; default conservation realization = `area_based_apr22`). Line 118 "config switch, not a scalar" also correct (default.cfg:755 `c22_protect_scenario <- "none"`).

### Config switches exist with stated defaults
`s22_conservation_start`=2025, `s32_aff_plantation`=0, `s13_max_gdp_shr`=Inf, `c60_2ndgen_biodem`=R34M410-SSP2-NPi2025, `s42_watdem_nonagr_scenario`=2, `s42_irrig_eff_scenario`=2 — all present in default.cfg. Doc's stated defaults (Inf for s13; safe≥2025 for s22) consistent.

---

## R29 ADVISORY — REFUTED

The pre-run advisory said: *"debugging_infeasibility.md:99 said '13 slack variables' but the table lists 5."*
Current doc line 99 reads: *"MAgPIE has **several** slack variables ... The table below lists the **main** high-penalty safety valves; it is **not exhaustive** (e.g. `v32_ndc_area_missing`, `v29_treecover_missing`, `v30_betr_missing`, and the CES relaxation `v38_relax_CES_lp` also exist)."*
There is no "13" count and no inconsistency: the doc explicitly hedges the table as non-exhaustive and names the additional slacks (all 4 verified real). The advisory was generated against a stale/earlier doc revision. **No count bug exists.** verify_cmd: `grep -n "13 slack\|several slack\|slack variab" debugging_infeasibility.md` -> only "several slack variables" at :99.

---

## BUGS FOUND

### BUG 1 (Major) — `s13_max_gdp_shr` mischaracterized
- **doc_line**: debugging_infeasibility.md:79
- **Claim**: "`s13_max_gdp_shr` at finite values | Caps agricultural GDP share — documented infeasibility trigger"
- **Reality**: `s13_max_gdp_shr` = "Maximum tech cost as share of regional GDP" (`modules/13_tc/endo_jan22/input.gms:11`, default Inf). It caps the COST OF TECHNOLOGICAL CHANGE (R&D / yield-improvement investment) as a fraction of regional GDP — NOT "agricultural GDP share". Used in `endo_jan22/presolve.gms:21,26` to bound `s13_max_gdp_shr * GDP` as an upper limit on TC expenditure. Capping TC investment can indeed cause infeasibility (yield targets become unreachable), so the "infeasibility trigger" half is directionally fine; the parameter SEMANTICS are wrong.
- **Class**: Wrong parameter semantics / module characterization (MANDATE 6).
- **Trigger**: §1 Major "right concept area, wrong description of what the switch governs" (would mislead a user about which lever they are pulling).
- **verify_cmd**: `grep -rn "s13_max_gdp_shr" /tmp/magpie_develop_ro/modules/13_tc/` -> `input.gms:11: s13_max_gdp_shr  Maximum tech cost as share of regional GDP / Inf /`; `presolve.gms:26: ... * s13_max_gdp_shr`
- **confirmed**: true
- **proposed_fix**: Replace line 79 cell with: ``| `s13_max_gdp_shr` at finite values | Caps technological-change (TC) investment cost as a share of regional GDP; a tight cap can make yield targets unreachable — documented infeasibility trigger |``

### BUG 2 (Major) — `s56_cprice_red_factor` safe/dangerous thresholds fabricated and contradict default
- **doc_line**: debugging_infeasibility.md:89 (and reinforced at :81, :138)
- **Claim**: line 89 "`s56_cprice_red_factor` | 56 | Safe range 0-0.5 | Dangerous > 0.8 with early start"; line 81 "Very high `s56_cprice_red_factor` ... Aggressive carbon price + no CDR option".
- **Reality**: `s56_cprice_red_factor` = "Reduction factor for CO2 price (-)", **default 1** (`modules/56_ghg_policy/price_aug22/input.gms:66`, confirmed default.cfg:1620 `<- 1`). It is a flat multiplier on the CO2 price: `im_pollutant_prices(...) = im_pollutant_prices(...) * s56_cprice_red_factor` (`price_aug22/preloop.gms:67`), applied across all years (no "start year" coupling on this line). The directional intuition (higher factor -> higher price -> more infeasibility risk) is correct, but: (a) the model's DEFAULT value 1 sits inside the doc's "dangerous (>0.8)" band, so the table implies default runs are dangerously configured, which is false; (b) the specific thresholds 0-0.5 / >0.8 have no code basis (fabricated numbers); (c) "with early start year" attributes a year-dependence this multiplier does not have.
- **Class**: Fabricated parameter range + missing default-state caveat (Bug class 6/13-adjacent).
- **Trigger**: §1 Major "Right concept, wrong number (parameter range / default off)"; also "Missing default-state caveat".
- **verify_cmd**: `grep -rn "s56_cprice_red_factor" /tmp/magpie_develop_ro/modules/56_ghg_policy/` -> `input.gms:66: ... Reduction factor for CO2 price (-) / 1 /`; `preloop.gms:67: im_pollutant_prices(...) = ...*s56_cprice_red_factor;` and `grep s56_cprice_red_factor config/default.cfg` -> `<- 1 # def = 1`
- **confirmed**: true
- **proposed_fix**: Replace line 89 cell with: ``| `s56_cprice_red_factor` | 56 | 1 (default = full scenario CO2 price) | Values >1 amplify the CO2 price above the scenario path, increasing infeasibility risk; values <1 reduce it. There is no code-based "safe/dangerous" cutoff — risk depends on the scenario price path. |`` And soften line 81 to: ``| `s56_cprice_red_factor` > 1 (price amplified above scenario) with limited CDR | Aggressive carbon price + limited CDR option |``

### BUG 3 (Minor) — `c21_trade_liberalization = "autarky"` and `"free"` are not valid options
- **doc_line**: debugging_infeasibility.md:132 (and fix at :133)
- **Claim**: line 132 "Cause: `c21_trade_liberalization = "autarky"` or low self-sufficiency ratios"; line 133 fix "Use 'regionalized' or 'free' trade settings".
- **Reality**: valid `c21_trade_liberalization` values are `l909090r808080` (default), and per the in-code comment `"regionalized"`, `"globalized"`, `"fragmented"` (`modules/21_trade/selfsuff_reduced/input.gms:8-9`). "autarky" appears only as a comment word in the non-default bilateral realization (`selfsuff_reduced_bilateral22/preloop.gms:87`), never as an accepted switch value; `"free"` is not an accepted value either. Setting `c21_trade_liberalization = "autarky"` / `"free"` would not select a defined regime. The conceptual point (tight trade -> regional infeasibility) is sound, and `"regionalized"`/`"fragmented"` (lines 91, 133) ARE valid.
- **Class**: Invalid config-value string / advisory drift (Bug class 13-adjacent / advisory).
- **Trigger**: §1 Minor "wrong detail; a careful reader would check valid options" (loose advisory prose, not a load-bearing variable/equation). Tie-breaker pulls to Minor.
- **verify_cmd**: `grep -rn "autarky" /tmp/magpie_develop_ro/modules/21_trade/` -> only `selfsuff_reduced_bilateral22/preloop.gms:87` (comment); `grep -n "options are" modules/21_trade/selfsuff_reduced/input.gms` -> `options are "regionalized" and "globalized" and "fragmented"`
- **confirmed**: true
- **proposed_fix**: Line 132: replace `c21_trade_liberalization = "autarky"` with `c21_trade_liberalization = "fragmented"` (or "low trade liberalization, e.g. `fragmented`"). Line 133: replace "Use 'regionalized' or 'free' trade settings" with "Use a more liberal setting such as `regionalized` or `globalized`".

### BUG 4 (Minor) — `v38_relax_CES_lp` listed without non-default caveat
- **doc_line**: debugging_infeasibility.md:99
- **Claim**: note lists "the CES relaxation `v38_relax_CES_lp` also exist[s]" alongside the other slacks (which are all default-active).
- **Reality**: `v38_relax_CES_lp` exists ONLY in the non-default factor_costs realization `sticky_labor` (6 files); the DEFAULT factor_costs realization is `sticky_feb18` (default.cfg:1235), which contains ZERO references to it (positive controls: `vm_cost_prod` found in 4 sticky_feb18 files; `v38_relax_CES_lp` found in 6 sticky_labor files). So in a default run this slack does not exist. The other note slacks (`v32_ndc_area_missing`, `v29_treecover_missing`, `v30_betr_missing`) ARE in default realizations. Listing `v38_relax_CES_lp` without the "non-default realization" caveat could send a user looking for a variable absent from their default GDX. (MANDATE 4 — capability vs default.)
- **Class**: Missing default-state caveat (Bug class 13-adjacent).
- **Trigger**: §1 Minor — the note is explicitly hedged ("not exhaustive", "also exist", i.e. "exists in the codebase"), so a careful reader is not misled into action; but the default-absence is worth a parenthetical. Tie-breaker to Minor.
- **verify_cmd**: `grep -rl "v38_relax_CES_lp" .../sticky_feb18/ | wc -l` -> 0; `.../sticky_labor/ | wc -l` -> 6; `grep cfg$gms$factor_costs config/default.cfg` -> `sticky_feb18`
- **confirmed**: true
- **proposed_fix**: In line 99, change "and the CES relaxation `v38_relax_CES_lp` also exist" to "and the CES relaxation `v38_relax_CES_lp` (only in the non-default `sticky_labor` factor-costs realization) also exist".

---

## DEFERRED (not code-verifiable / low-confidence — NOT edited)

1. line 78 "SSP3 + PkBudg650 | High population + tight carbon budget = impossible" — an empirical scenario-combination claim about run outcomes, not checkable from a single GAMS file; plausible but not code-verifiable here.
2. line 91 "Safe range '\"regionalized\"'" for `c21_trade_liberalization` — "regionalized" is a valid option but NOT the default (default is `l909090r808080`). The doc says "Safe range", not "default", so it is defensible; flagging the default mismatch would risk over-reach. Left as-is.
3. readGDX object names in the diagnostic snippets (lines 29-35, 48, 59-61) use the solver-variable names (`v73_...`, `ov_land`, `oq10_land_area`). Whether `readGDX(gdx,"v73_prod_heaven_timber")` vs `"ov73_prod_heaven_timber"` is the right call is an R-runtime/gdx2 behavior question, not a GAMS-code fact; the GAMS objects all exist, so I did not flag the R usage. Low confidence either way.
4. line 109 penalty-tier ordering and "$1M/..." dollar formatting are USD17MER per the input.gms units; the doc writes plain "$" — a units-precision nuance, not a code error.

---

## Method notes / grep-reliability log
- rg displayed `v*`-prefixed names with the prefix stripped (showed `ln`/`oln`) on the slack-variable probes; literal `grep -rn` showed the true names (`v73_prod_heaven_timber`, etc.). Confirms the repo guidance to cross-check rg with grep. All slack-name verdicts rest on literal grep + reading declarations.gms.
- Several compound/looped commands truncated when an internal grep exited 1; all absence claims (BUG 4 CES-lp; food-slack absence) were re-run isolated with `wc -l` counts and positive controls.
