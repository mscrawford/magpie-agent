# Audit Report: Q5 (MAgPIE Infeasibility — causes, diagnosis, fixes, slack variables)

**Round**: R29 | **Worktree**: `/tmp/magpie-develop-r29/` @ `ee98739fd` (origin/develop) | **Auditor**: Opus adversarial

### Overall Verdict: MOSTLY ACCURATE
### Accuracy Score: 8/10

**Headline**: The R11 FABRICATED slack variable is GONE. All 6 slack variables and both named switches the answer presents as authoritative EXIST in code with exact names. Verified each against declarations.gms / input.gms in the clean worktree. The constraint claims (q10 hard equality, q43 ag-no-buffer, q21_notrade, q60 hard floor, no food slack) are all correct. Three Minor index/citation imprecisions; no Critical, no Major.

---

## Slack-variable & switch existence ledger (the #1 job)

| Identifier | Type | Status | File:line (worktree) |
|---|---|---|---|
| `v73_prod_heaven_timber(j,kforestry)` | slack | ✅ EXISTS | `modules/73_timber/default/declarations.gms:24` |
| `v44_bii_missing(i,biome44)` | slack | ✅ EXISTS | `modules/44_biodiversity/bii_target/declarations.gms:13` |
| `v32_land_missing(j)` | slack | ✅ EXISTS | `modules/32_forestry/dynamic_may24/declarations.gms:66` |
| `v32_ndc_area_missing(j)` | slack | ✅ EXISTS | `modules/32_forestry/dynamic_may24/declarations.gms:79` |
| `v21_import_for_feasibility(h,k_trade)` | slack | ✅ EXISTS | `modules/21_trade/selfsuff_reduced/declarations.gms:20` |
| `v29_fallow_missing(j)` | slack | ✅ EXISTS | `modules/29_cropland/detail_apr24/declarations.gms:45` |
| `s56_cprice_red_factor` | switch | ✅ EXISTS | `modules/56_ghg_policy/price_aug22/input.gms:66` |
| `s32_free_land_cost` (=1e6) | switch | ✅ EXISTS | `modules/32_forestry/dynamic_may24/input.gms:33` |
| `s73_free_prod_cost` (=1e6) | scalar | ✅ EXISTS | `modules/73_timber/default/input.gms:17` |
| `s44_cost_bii_missing` (=1e6) | scalar | ✅ EXISTS | `modules/44_biodiversity/bii_target/input.gms:13` |
| `i29_fallow_penalty(t)` (from `s29_fallow_penalty`=615) | param | ✅ EXISTS | `modules/29_cropland/detail_apr24/declarations.gms:34`; input.gms:34 |
| `s21_cost_import` (=1500) | scalar | ✅ EXISTS | `modules/21_trade/selfsuff_reduced/input.gms:18` |

**NOT-FOUND / fabricated: NONE.** Contrast with R11, which fabricated a slack variable. This answer fabricates nothing.

**Default-realization check** (all the realizations the answer used ARE the config defaults):
- M32 `dynamic_may24` ✓, M29 `detail_apr24` ✓, M21 `selfsuff_reduced` ✓, M44 `bii_target` ✓, M73 `default` ✓, M10 `landmatrix_dec18` ✓, M43 `total_water_aug13` ✓, M60 `1st2ndgen_priced_feb24` ✓, M80 `nlp_apr17` ✓, M57 `on_aug22` ✓, M58 `v2` ✓ (verified `grep cfg$gms$* config/default.cfg`).

---

## Constraint-claim verification

- **q10_land_area hard equality, no slack** ✅ `10_land/landmatrix_dec18/equations.gms:13-15`: `sum(land, vm_land(j2,land)) =e= sum(land, pcm_land(j2,land));` — answer quotes it verbatim. Confirmed `=e=`.
- **q43_water inequality, agriculture NOT buffered** ✅ `43_water_availability/total_water_aug13/equations.gms:10-11`: `sum(wat_dem,vm_watdem(wat_dem,j2)) =l= sum(wat_src,v43_watavail(wat_src,j2));`. The 1% groundwater buffer for exogenous demand is real: `presolve.gms:14-16` adds `(...)*1.01` `$(...>0)` to `v43_watavail.fx("ground",j)`. Answer's "1% safety margin, exogenous only, ag not buffered" is EXACTLY right.
- **q21_notrade** ✅ `21_trade/selfsuff_reduced/equations.gms:19`: `sum(supreg(h2,i2),vm_prod_reg(i2,k_notrade)) =g= sum(supreg(h2,i2), vm_supply(i2,k_notrade));` (answer cited 18-19; equation body is line 19).
- **q21_trade_reg with v21 slack** ✅ `equations.gms:31-35`; slack `- v21_import_for_feasibility(h2,k_trade)` on line 35.
- **v21 covers wood/woodfuel ONLY (NOT food)** ✅ DECISIVE: `k_import21(k_trade) / wood, woodfuel /` at `selfsuff_reduced/input.gms:13`; `preloop.gms:37-38` set `.lo/.up` only on `k_import21` (all other `k_trade` fixed to 0 at `preloop.gms:36`). Answer's emphasized claim is verified.
- **q60_bioenergy_reg hard floor, no slack, default c60_biodem_level=1** ✅ `60_bioenergy/1st2ndgen_priced_feb24/equations.gms:46-47`: `sum(kbe60, v60_2ndgen_bioenergy_dem_dedicated(i2,kbe60)) =g= sum(ct,i60_bioenergy_dem(ct,i2))*c60_biodem_level;`. Default `c60_biodem_level / 1 /` (input.gms:37). No slack present — correct.
- **NO food/feed/crop-production slack (by design)** ✅ Consistent with all module evidence; no `*_for_feasibility` / `*_missing` / `*_heaven` variable exists on the food balance or crop-production side. Answer's "critical gap" framing is accurate.
- **p80_modelstat diagnostic ">2 and ≠7"** ✅ `80_optimization/nlp_apr17/declarations.gms:9` declares `p80_modelstat(t)`; `solve.gms:98` `if ((p80_modelstat(t) <= 2)` and `solve.gms:102` `if ((p80_modelstat(t) > 2 and p80_modelstat(t) ne 7)` — the answer's failure-detection rule maps EXACTLY to code. Modelstat=7 "continues" claim confirmed.
- **M10 transition restrictions** ✅ `landmatrix_dec18/presolve.gms:13` `vm_lu_transitions.fx(j,"primforest","forestry") = 0;` and `:20` `vm_lu_transitions.fx(j,land_from,"primforest") = 0;` — both citations exact.
- **q44_bii_target** ✅ `bii_target/equations.gms:22-23`; penalty actually accrues in `q44_cost` (line 28-29) via `s44_cost_bii_missing` — answer cited q44_bii_target for the constraint (correct) and the table maps the penalty to it (minor: the cost lives in q44_cost, but the answer's table column is "what it relaxes", so this is fine).
- **q32_cost_total slack costs** ✅ `dynamic_may24/equations.gms:21-27`; `v32_land_missing * s32_free_land_cost` (line 25) + `v32_ndc_area_missing * s32_free_land_cost` (line 26). Answer's "same s32_free_land_cost for both" verified.
- **q32_aff_pol** ✅ `dynamic_may24/equations.gms:74-75`: `sum(ac_est, v32_land(j2,"ndc",ac_est)) + v32_ndc_area_missing(j2) =e= sum(ct, p32_aff_pol_timestep(ct,j2));`. Exact.
- **M73 q73_prod_wood / q73_prod_woodfuel carry v73 slack** ✅ `q73_prod_wood(j2)` at line 43 (slack at :50), `q73_prod_woodfuel(j2)` at line 52 (slack at :61); slack cost in `q73_cost_timber` at line 30.
- **M57 division-by-zero & 1/(1-mit) blowup** ✅ `57_maccs/on_aug22/equations.gms:40,50` divide by `s57_implicit_emis_factor` (→ div-by-zero if 0); lines `38,48` divide by `(1 - im_maccs_mitigation(...))` (→ blowup as mitigation→1). Answer's TWO citations (40,50 for implicit factor; 38,48 for maxmac) are BOTH exactly right. `s57_implicit_emis_factor / 0.01 /`, `s57_maxmac_* / -1 /` (input.gms:14-19).
- **M58 peatland combos** ✅ All four named switches exist in `58_peatland/v2/input.gms`: `s58_rewetting_switch / Inf /` (:14), `s58_rewetting_exo / 0 /` (:17), `s58_annual_rewetting_limit / 0.02 /` (:25), `s58_rewet_exo_target_value / 0.5 /` (:22). Answer's "default rate 0.02/yr, ≥1.0 target unreachable by 2050" verified against the 0.02 default. (Note: answer wrote `s58_rewetting_exo` — code has both `s58_rewetting_exo` and `s58_rewetting_exo_noselect`; the named one exists.)

---

## Bugs Found

### Q5-B1 (Minor)
- **Severity**: Minor | **Class**: 1 (GAMS prefix/index confusion) | **Trigger**: §1 Minor — "wrong detail, careful reader not misled into action"
- **Claim in answer**: line 92 — "`v21_import_for_feasibility(h,k_notrade)` which **only covers wood and woodfuel**"
- **Reality in code**: the variable is declared `v21_import_for_feasibility(h,k_trade)` (`declarations.gms:20`) and appears in `q21_trade_reg` indexed `(h2,k_trade)`, restricted to `k_import21={wood,woodfuel}` via preloop bounds. The index label `k_notrade` is wrong (should be `k_trade`).
- **Why Minor not Major**: wood and woodfuel ARE members of `k_notrade` too (`sets.gms:21`), and the substantive claim ("only wood/woodfuel") is CORRECT and decisively verified via `k_import21`. The mislabel is internally inconsistent with the same answer's own correct usage two lines later, but doesn't mislead about behavior.

### Q5-B2 (Minor)
- **Severity**: Minor | **Class**: 3 (suffix/index truncation) | **Trigger**: §1 Minor
- **Claim in answer**: line 155 — `q60_bioenergy_reg(h2,k_trade)..`
- **Reality in code**: `q60_bioenergy_reg(i2)..` (`1st2ndgen_priced_feb24/equations.gms:46`). The equation is indexed over regions `i2` only, not `(h2,k_trade)`. The RHS the answer shows (`sum(kbe60,...) =g= sum(ct,i60_bioenergy_dem)*c60_biodem_level`) is otherwise correct.
- **Why Minor**: the equation exists with the right name and the mechanism/floor description is correct; only the declared index tuple in the code block is wrong. A reader copying the block would get a GAMS compile error and self-correct, not make a wrong modeling decision.

### Q5-B3 (Informational — tie-breaker pulled down from Minor)
- **Severity**: Informational | **Class**: 10 (imprecise file:line citation) | **Trigger**: §1 Minor "off-by-few line citation where adjacent lines say similar things" fired, but §1 tie-breaker ("when between two tiers, pick the lower") pulls to Informational because the equation NAMES are correct and the citation is in a metadata table column, not a load-bearing claim. `tier_uncertainty: true`.
- **Claim in answer**: line 177 (table) — `v73_prod_heaven_timber ... q73_prod_wood, q73_prod_woodfuel (equations.gms:35-53)`
- **Reality in code**: `q73_prod_wood` is at line **43** and `q73_prod_woodfuel` at **52** (`73_timber/default/equations.gms`); the slack-cost term is in `q73_cost_timber` at line **30**. The cited range "35-53" starts ~8 lines early (lands in the q73_cost_timber descriptive comments) but does cover q73_prod_woodfuel's opening.
- **Why Minor**: equation names correct, range overlaps the actual equations; a careful reader finds them. Tie-breaker pulls toward the lower tier.

---

## Latent doc bugs (§1.5) — tested `agent/helpers/debugging_infeasibility.md`

The doc is **substantially correct on every slack identifier** (`v73_prod_heaven_timber`, `v44_bii_missing`, `v32_land_missing`, `v21_import_for_feasibility`, `v29_fallow_missing` all present and correctly attributed, line 101-107). No fabricated slack variable in the doc — the R11 fabrication has been remediated upstream. Two doc imperfections, both of which the **answer corrected** (`doc_error_answerer_beat_it`, do NOT lower the answer score; fix the doc this session per validate-semantic Step 5):

### Q5-DOC1 (Minor, doc_error_answerer_beat_it)
- **Doc line 99**: "MAgPIE has **13 slack variables** with high penalty costs." The same section's table then lists exactly **5**.
- **Code reality**: the doc's own table of 5 (`v73_prod_heaven_timber`, `v44_bii_missing`, `v32_land_missing`, `v21_import_for_feasibility`, `v29_fallow_missing`) is the right enumeration; `v32` actually contributes TWO (`v32_land_missing` + `v32_ndc_area_missing`), so a defensible count is 6 distinct slack variables. "13" is unsupported — no enumeration in the repo backs it.
- **Answerer beat it**: answer line 173 says "**5 documented slack variables**" and the body separately surfaces `v32_ndc_area_missing` as a 4th table row (effectively 6). The answer did NOT reproduce "13".
- **Severity**: Minor (a count, not a wrong identifier; future-reader harm is low — they'd see the 5-row table and notice the mismatch). Class 6 (hardcoded count drift). **Fix the doc**: change "13" → "6" (or "5 primary; 6 counting v32_ndc_area_missing separately") to match the table.

### Q5-DOC2 (Informational, doc_error_answerer_beat_it)
- **Doc line 107**: `v29_fallow_missing | 29 | $615/ha | Fallow land target gap`. States a fixed $615/ha penalty.
- **Code reality**: the cost coefficient is `i29_fallow_penalty(t)` (time-indexed param, `declarations.gms:34`), set from scalar `s29_fallow_penalty / 615 /` (`input.gms:34`) in presolve. So $615 IS the default, but it is a scenario/time-settable penalty, not a hardcoded constant like the $1e6 slacks.
- **Answerer beat it**: answer line 184 correctly characterizes it as "`i29_fallow_penalty(t)` — a scenario-specific penalty" and explicitly flags it as a "soft penalty, not hard infeasibility prevention".
- **Severity**: Informational (the doc's $615 is the correct default; only the "fixed vs settable" nuance is lost). No doc fix strictly required; optionally annotate "$615/ha default (`s29_fallow_penalty`, settable)".

**No latent bug rises to Critical**: unlike the G2 anchor (wrong producer/consumer SET → refactor miss), these are a count typo and a penalty-nuance, not a wrong-identifier or wrong-attribution that would send a future reader to the wrong file/variable.

---

## Missing Nuances (not scored)

- The answer's M16 food-balance framing ("Module 16 demand supply-closure") is correct in spirit but the answer itself flags (line 235) that it did not pin the exact binding closure equation in M16. Honest disclaimer; not a bug.
- Answer attributes the v44 penalty to `q44_bii_target` in the slack table; the cost is actually realized in `q44_cost` (`equations.gms:28-29`). The constraint that the slack relaxes IS q44_bii_target, so the table's "what it relaxes" column is right — noted for completeness, not scored.
- `s56_cprice_red_factor` is a CO2-price multiplier (`preloop.gms:67` multiplies `im_pollutant_prices(...,"co2_c",...)` by it). Answer calls it "amplifies carbon prices" — technically it's a reduction factor (name) used as a multiplier; default behavior depends on its value. Answer's "keep ≤0.5 for early start" is advisory and matches the doc's table. Not scored.

---

## Summary

The single most important R29 verification — does any named slack variable or switch NOT exist — returns **clean**: all 12 named identifiers exist with exact names at the cited modules, every one in the **default** realization. The R11 fabricated-slack failure mode is fully remediated, in both the answer and the underlying doc. The answer's constraint mechanics (q10 hard `=e=`, q43 ag-unbuffered with the real 1% exogenous groundwater margin, q21_notrade, q21 v21-slack restricted to `k_import21={wood,woodfuel}`, q60 hard floor, no food slack, p80_modelstat `>2 and ne 7`) are all verified verbatim or near-verbatim against code. Three Minor blemishes (two wrong index tuples in code blocks: `v21(...,k_notrade)`→`k_trade`, `q60_bioenergy_reg(h2,k_trade)`→`(i2)`; one off-by-8 citation range on the M73 equations). Two latent doc imperfections (a "13 slack variables" count vs a 5-row table; a "$615/ha" fixed-penalty framing), both beaten by the answer and worth a quick doc fix this session, neither Critical.

**Mechanical formula** (§4): `score = 10 − [4·Critical + 2·Major + 1·Minor + 0·Informational]`.
- Critical: 0 | Major: 0 | Minor: 2 (B1, B2 — both unambiguous wrong-index labels) | Informational: 1 (B3, tie-breaker).
- raw_severity_weighted = 4·0 + 2·0 + 1·2 + 0·1 = **2** → **score = 10 − 2 = 8**.

I deliberately do NOT override the formula upward despite the decisive correctness on the load-bearing question — the rubric's stability mechanism (§8: mechanical formula, decision-tree triggers, tie-breaker pulls down) is the whole point of the flywheel. Two clear Minor index-label bugs = −2. The answer earns **8/10** (Mostly Accurate, upper band: 2 bugs, no Major, no structural error). The latent doc bugs are recorded separately (§1.5) and do not affect this score.

**Final: 8/10** — Mostly Accurate. No Critical, no Major, 2 Minor (+1 Informational, tier_uncertainty on B3). Zero fabricated identifiers — R11 failure mode fully remediated.
