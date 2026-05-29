# Audit Report: Q (MAgPIE execution sequence & timestep loop)

Anchored on `core_docs/Core_Architecture.md`. Ground truth: `/tmp/magpie_develop_ro` (develop worktree) + `config/default.cfg`.

## Overall Verdict: SIGNIFICANT ERRORS (structurally excellent, but the load-bearing default-behavior claim is wrong)
## Accuracy Score: 0/10

The answer's phase scaffolding, module-80 solve description, and most file-level examples are accurate and well-cited. But its single most load-bearing claim about the timestep loop — that the food-demand intersolve coupling iterates per timestep ("typically 2-5 iterations") — describes a NON-DEFAULT mechanism as if it were the default. Combined with three Major misattributions/confabulations, the severity-weighted score caps at 0. (Score formula: 4·1 + 2·3 + 1·2 = 12 → max(0, 10-12) = 0.)

---

## Mechanical checks
- **M1** (file:line citations present): PASS — multiple `modules/NN/realization/file.gms:NN`-style citations.
- **M2** (active realization stated): PASS for M80 (`nlp_apr17` default) and M15 (single realization). FAIL in substance for M15: did not flag `s15_elastic_demand = 0` (the omission that produced Bug-1).
- **M3** (variable prefixes valid): PASS.
- **M4/M5** (epistemic badges/depth): PASS — answer carries a 🟡 epistemic-status block and explicitly declares docs-only.
- **M6** (closing source statement): PASS.

---

## Verified Claims (correct against code)

- **Pre-loop dispatch from main.gms**: `$batinclude "./modules/include.gms" [phase]` per phase across all modules; phase order sets → declarations → input → equations → scaling, then `start`/`preloop` from `core/calculations.gms`. CONFIRMED (`main.gms`, `core/calculations.gms:11,13`, `modules/include.gms`).
- **Model declaration**: `model magpie / all - m15_food_demand /;` at `main.gms:279` — EXACT match incl. the cited line 279. CONFIRMED.
- **`m15_food_demand` is a separately-coupled model**: declared `modules/15_food/anthro_iso_jun22/declarations.gms:207`; solved separately in intersolve. CONFIRMED.
- **preloop runs ONCE before the loop**: `core/calculations.gms` runs `start`/`preloop` in PREPROCESSING section, before `loop(t...)`. CONFIRMED.
- **Module 14 input**: `f14_yields(t_all,j,kve,w)` ← `lpj_yields.cs3`; `m_fillmissingyears` in input phase. EXACT match (`14_yields/managementcalib_aug19/input.gms:35-37,43`). CONFIRMED.
- **Module 14 preloop = FAO-calibrated yields**: CONFIRMED (`14_yields/managementcalib_aug19/preloop.gms:35-38`).
- **Module 80 default = `nlp_apr17`**: CONFIRMED (`config/default.cfg:2282`).
- **M80 solve**: `solve magpie USING nlp MINIMIZING vm_cost_glo;` (`80_optimization/nlp_apr17/solve.gms:33`). CONFIRMED.
- **`vm_cost_glo` provided by Module 11**: declared `11_costs/default/declarations.gms:9`, defined `q11_cost_glo` `equations.gms:10`. CONFIRMED.
- **Fallback retry loop**: 4 strategies (CONOPT4 default → CONOPT4 optfile=1 → CONOPT4 optfile=2 "increasing largest allowable value" → CONOPT3), `s80_resolve_option`/`s80_counter`, `until (modelstat<=2 or s80_counter>=s80_maxiter)`, on failure dump `fulldata.gdx` + abort. CONFIRMED (`80_optimization/nlp_apr17/solve.gms`).
- **`s80_maxiter` default = 30**: CONFIRMED (`80_optimization/nlp_apr17/input.gms:9`).
- **`lp_nlp_apr17` adds LP/CPLEX warmstart + secondary `vm_landdiff` minimization**: CONFIRMED (`lp_nlp_apr17/solve.gms:20-21,76,196`).
- **`nlp_ipopt` uses Ipopt + declares `ipopt.opt`/`ipopt.op2` in preloop**: CONFIRMED (`nlp_ipopt/solve.gms:13`, `nlp_ipopt/preloop.gms:9-10`). `nlp_apr17` preloop declares `conopt4.opt` (`nlp_apr17/preloop.gms:9`). CONFIRMED.
- **Postsolve carry-forward**: `pcm_land(j,land) = vm_land.l(j,land);` — EXACT match (`10_land/landmatrix_dec18/postsolve.gms:9`). CONFIRMED.
- **Postsolve equation diagnostics example**: `oq52_emis_co2_actual(t,i,emis_oneoff,"level") = q52_emis_co2_actual.l(i,emis_oneoff);` — EXACT match (`52_carbon/normal_dec17/postsolve.gms:10`). CONFIRMED.
- **Postsolve runs OUTSIDE/after the while loop, once per timestep; then `Execute_Unload "fulldata.gdx";`**: CONFIRMED (`core/calculations.gms`).
- **Only Module 80 does solve-phase work**: no other module has a `solve.gms` at all (only 80's four realizations). CONFIRMED (mild framing nit: "stubs" — they don't exist rather than being empty stubs; not a bug).
- **Default timestep range 1995-2100**: `c_timesteps = coup2100` (`config/default.cfg:133`) = `y1995..y2100` (`core/sets.gms:188`). CONFIRMED (see Bug-6 on "5-year" framing).
- **Module 22 is the (sole) presolve_ini user**: CONFIRMED — M22 `area_based_apr22/presolve_ini.gms` is the ONLY `presolve_ini.gms` in the tree (`find` over all modules returns exactly one). The answer's "canonical user" framing is correct (it understates: it's the only one).

---

## Bugs Found

### Bug Q-B1 — Intersolve coupling described as default; "2-5 iterations" per timestep
- **Severity**: 🔴 Critical
- **Class**: 4 (conceptual pseudo-code) / default-state
- **Trigger**: "Active mechanism claimed when actually OFF by default" (the `s42_pumping` anchor).
- **Claim in answer**: "iterates until Module 15 sets `sm_intersolve = 1`. ... Module 15 (food demand) checks convergence ... If not converged, it updates demand parameters and resets `sm_intersolve = 0`, triggering another solve. Convergence typically takes 2-5 iterations."
- **Reality in code**: `s15_elastic_demand` defaults to **0** (`config/default.cfg:414`; `15_food/anthro_iso_jun22/input.gms:66`). The intersolve re-iteration block is gated by `if (s15_elastic_demand = 1 AND m_year(t) > sm_fix_SSP2, ...)` (`intersolve.gms:30`). With the default, that block is skipped, `sm_intersolve` stays at the core-set value 1, and the `while(sm_intersolve = 0)` loop runs **exactly once** — MAgPIE is NOT re-solved per timestep by default. The answer presents the elastic-demand coupling as the operative per-timestep behavior with no default-OFF caveat. Also, the iteration cap is `s15_maxiter = 10` (`input.gms:70`, `config:422`), not "2-5".
- **File evidence**: `modules/15_food/anthro_iso_jun22/input.gms:66` (`s15_elastic_demand ... / 0 /`); `intersolve.gms:30` (gate); `config/default.cfg:414`.
- **Root cause**: `doc_error` — `Core_Architecture.md:231-232` asserts "Module 15 iterates ... (typically 2-5 iterations)" with no default caveat; the Core-Architecture-anchored answer reproduced it. (module_15.md:14,482,758 has the correct caveat but was not consulted.) See latent doc bug L1.
- **Anchor reference**: `s42_pumping` Critical anchor (mechanism claimed active when OFF by default).

### Bug Q-B2 — `sm_intersolve` control flow inverted; `load_gdx.gms` omitted from loop
- **Severity**: 🟠 Major (tier_uncertainty: true — net outcome is described correctly)
- **Class**: 4 (conceptual pseudo-code)
- **Trigger**: "Citation/structure drift to materially different content."
- **Claim in answer**: pseudocode `while(sm_intersolve = 0, solve; intersolve);` and "iterates until Module 15 sets `sm_intersolve = 1`."
- **Reality in code** (`core/calculations.gms:57-83`): the body is `[$include load_gdx.gms]; solve; sm_intersolve=1; intersolve;`. The **core** sets `sm_intersolve=1` UNCONDITIONALLY (calc.gms:79) right after solve; Module 15 then sets it BACK to **0** (`intersolve.gms:125`) to CONTINUE iterating (when not converged & under maxiter). So the flag-setting direction is reversed (M15 sets 0-to-continue, not 1-to-exit), and the answer's reproduced pseudocode omits both the core `sm_intersolve=1;` line and the in-loop `$include "./core/load_gdx.gms"`.
- **File evidence**: `core/calculations.gms:57,59,79`; `modules/15_food/anthro_iso_jun22/intersolve.gms:125,129,133`.
- **Root cause**: `doc_error` (Core_Architecture.md:222-226 carries the same simplification) reproduced by the answerer.

### Bug Q-B3 — Fabricated set member `f35_forest_lost_share(i,"fires")`
- **Severity**: 🟠 Major (tier_uncertainty: true)
- **Class**: 12 (content-level mismatch) / MANDATE 12 (exact set-member labels)
- **Trigger**: invented set member presented as code.
- **Claim in answer**: `p35_disturbance_loss_secdf(t,j,ac) = pc35_secdforest(j,ac) * f35_forest_lost_share(i,"fires")`.
- **Reality in code**: the `driver_source` set members are `{overall, deforestation, shifting_agriculture, wildfire}` (`35_natveg/pot_forest_may24/sets.gms:11-15`). **"fires" is not a member.** The default first branch uses `"shifting_agriculture"` (presolve.gms:14), and drops the `sum(cell(i,j),...)` and `*m_timestep_length_forestry` factors and uses `ac_sub` (not `ac`). `module_35.md:172,211-212` correctly uses `"shifting_agriculture"` / lists `wildfire` — the answer changed a correct doc label into a non-existent one.
- **File evidence**: `modules/35_natveg/pot_forest_may24/sets.gms:11-15`, `presolve.gms:14`; correct doc at `magpie-agent/modules/module_35.md:172`.
- **Root cause**: `answerer_confabulation`.
- **Anchor reference**: R16 q10_land_area set-expansion Major.
- **Note**: the user's own global instructions flag this exact mislabeling sensitivity ("disturbance rates labeled 'wildfire'", NOT "fire").

### Bug Q-B4 — presolve_ini wrongly attributed `vm_land.lo(j,land_natveg)` bound-setting
- **Severity**: 🟠 Major (tier_uncertainty: true)
- **Class**: 12 / MANDATE 17 (one-hop / direct-vs-transitive; phase+module misattribution)
- **Trigger**: attributing an action to the wrong phase/module.
- **Claim in answer**: "[presolve_ini] Module 22 (land conservation) is the canonical user, setting `vm_land.lo(j,land_natveg)` from `pm_land_conservation(t,j,land,"protect")`."
- **Reality in code**: M22 `presolve_ini.gms` COMPUTES the `pm_land_conservation(t,j,land,"protect"/"restore")` parameter (and references only `vm_land.lo(j,"crop")`, lines 86,97,108). The natveg `vm_land.lo` floors derived from `pm_land_conservation(...,"protect")` are applied in **Module 35's `presolve.gms`** (lines 162 primforest, 201 secdforest, 231 other) — a different PHASE (presolve, not presolve_ini) and a different MODULE (35, not 22). There is no `vm_land.lo(j,land_natveg)` set-indexed assignment anywhere.
- **File evidence**: `modules/22_land_conservation/area_based_apr22/presolve_ini.gms:54,86,97,108`; `modules/35_natveg/pot_forest_may24/presolve.gms:162,201,231`.
- **Root cause**: `answerer_confabulation` (the doc says only "22_land_conservation sets bounds"; the answer invented the specific variable + source + phase).
- **Anchor reference**: R24 Q4-B3 (M30→M29→M52 mislabeled as direct) Major.

### Bug Q-B5 — Age-class shift formula hardcoded `ac-1`, dropped guard
- **Severity**: 🟡 Minor
- **Class**: 4 (conceptual pseudo-code)
- **Claim in answer**: `p35_secdforest(t,j,ac) = pc35_secdforest(j,ac-1)` (5-year shift).
- **Reality in code** (`35_natveg/pot_forest_may24/presolve.gms:94`): `p35_secdforest(t,j,ac)$(ord(ac) > s35_shift) = pc35_secdforest(j,ac-s35_shift);` — shift is by scalar `s35_shift` with a `$(ord(ac) > s35_shift)` guard. Concept (age advancement) correct; literal `ac-1` and dropped conditional are imprecise.
- **Root cause**: `answerer_style_or_framing`.

### Bug Q-B6 — "5-Year Steps" header overstates uniform stepping
- **Severity**: 🟡 Minor
- **Class**: 11/range
- **Claim in answer**: header "The Timestep Loop (5-Year Steps, Default 1995-2100)".
- **Reality in code**: `coup2100` = `y1995,...,y2060,y2070,y2080,y2090,y2100` (`core/sets.gms:188`) — 5-year through 2060, then **10-year** to 2100. The loop is set-driven (`loop(t...)`), not fixed 5-year.
- **Root cause**: `answerer_style_or_framing`.

---

## Latent doc bugs (fix regardless of answer score)

### L1 — Core_Architecture.md §5.2 presents per-timestep food-demand iteration as default ("2-5 iterations")
- **Doc location**: `core_docs/Core_Architecture.md:231-232` ("the WHILE loop ... Module 15 iterates between food demand and the optimizer until convergence (typically 2-5 iterations)"); reinforced by line 225 ("15_food sets sm_intersolve").
- **Code reality**: `s15_elastic_demand` defaults to **0** (`config/default.cfg:414`, `15_food/anthro_iso_jun22/input.gms:66`); intersolve coupling gated by `if (s15_elastic_demand = 1 AND m_year(t) > sm_fix_SSP2)` (`intersolve.gms:30`). With defaults the while loop runs ONCE; no per-timestep re-solve. Cap is `s15_maxiter = 10`, not 2-5.
- **Severity (future-reader harm)**: **Critical** — this doc note is what produced the answer's Critical Bug-1. Fix: add "By default `s15_elastic_demand = 0`, so the WHILE loop executes exactly once per timestep; the 1..10-iteration coupling runs only when elastic demand is enabled."
- **Root cause**: `doc_error` (answer did NOT beat it — it reproduced it).
- **Note**: `module_15.md` (lines 14, 482, 758, 760, 929) already states the default-0 caveat and the 10-iteration cap correctly — Core_Architecture.md is the out-of-sync doc.

### L2 — Core_Architecture.md §5.2 pseudocode mis-states who sets sm_intersolve and omits load_gdx + the unconditional core reset
- **Doc location**: `core_docs/Core_Architecture.md:222-226`.
- **Code reality** (`core/calculations.gms:57-83`): loop body is `$include load_gdx.gms; [batinclude] solve; sm_intersolve=1 (CORE, unconditional); [batinclude] intersolve`. Module 15 sets `sm_intersolve=0` to CONTINUE (`intersolve.gms:125`), not `=1` to exit. The doc's "15_food sets sm_intersolve" obscures that the core sets it to 1 and M15 only flips it back to 0.
- **Severity (future-reader harm)**: **Major** — misleads on loop-termination mechanics.
- **Root cause**: `doc_error`.

---

## Summary

Structurally one of the stronger execution-sequence answers: phase order, M80 solve/fallback, `vm_cost_glo` attribution, M14 input/preloop, and the `pcm_land`/`oq52_emis_co2_actual` postsolve examples are all exact-verified against develop. The score is nonetheless 0 because (a) the answer's central timestep-loop claim — that the food-demand coupling iterates 2-5×/timestep — is FALSE for the default config (`s15_elastic_demand = 0`), an `s42_pumping`-class Critical; and (b) three Major confabulations/misattributions (fabricated `"fires"` set member; `vm_land.lo(j,land_natveg)` mis-attributed to M22 presolve_ini instead of M35 presolve; inverted `sm_intersolve` flow + omitted `load_gdx`). Two latent doc bugs in `Core_Architecture.md:222-232` (the source of the Critical and one Major) must be fixed regardless; `module_15.md` already has the correct default caveat, so the fix is to bring Core_Architecture.md §5.2 into line with it.
