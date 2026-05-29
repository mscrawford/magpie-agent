## Audit Report: R29 Q7 / G2 (vm_carbon_stock computation in M52 + entry into M56 GHG-policy cost)

### Overall Verdict: MOSTLY ACCURATE
### Accuracy Score: 8/10

(raw_severity_weighted = 4·0 critical + 2·0 major + 1·2 minor = 2 → 10 − 2 = 8. Profile: 0 Critical, 0 Major, 2 Minor citation-range imprecisions; all load-bearing facts correct. Per §7 verdict table, 1-2 Minor bugs sit at the Accurate/Mostly-Accurate boundary; tagged MOSTLY ACCURATE since two citations need tightening.)

**Worktree audited**: `/tmp/magpie-develop-r29/` @ HEAD (ee98739fd; verified via `.git` pointer, modules/52_carbon + modules/56_ghg_policy present).
**Defaults confirmed**: `cfg$gms$ghg_policy <- "price_aug22"`, `cfg$gms$carbon` → only `normal_dec17` realization exists (config/default.cfg). Both M52 and M56 are effectively single-realization (only `<real>/` + `input/`), so there is no realization-ambiguity to flag (M2 satisfied implicitly).

### drift_observed: **false**

This anchor regressed R22→R23→R26 (answerer trusting a wrong doc populator list), recovered to 9 at R27. R29 answer holds the recovery: the declaration site is correct, the populator set is correct AND more precise than the rubric summary, and the producer-vs-reader distinction is explicit. No regression.

---

### Verified Claims (correct):

**1. Declaration site (the historical G2 trap) — CORRECT.**
`vm_carbon_stock(j,land,c_pools,stockType)` is declared in **Module 56**, `price_aug22/declarations.gms:34` (under `positive variables`). Verified by direct Read of the file — line 34 exact. Answer's central §1/§6 claim ("declared in M56, not M52; M52 reads it, land modules populate it") is fully correct. `pcm_carbon_stock` co-declared at declarations.gms:19 (answer says "also declared in Module 56" — correct). `vm_emission_costs(i)` decl:39, `v56_emis_pricing` decl:41, `v56_emission_cost` decl:42 — all confirmed.

**2. Populator set — CORRECT and code-accurate at the DEFAULT realizations.**
Authoritative roster from `grep -rln vm_carbon_stock modules/` + `find -exec grep -l` on equations.gms, then per-module Read at each DEFAULT realization:
- **M29** (detail_apr24, default): writes `vm_carbon_stock(j2,"crop",ag_pools,stockType) =e= vm_carbon_stock_croparea(j2,ag_pools) + ...` (equations.gms:39-40). POPULATOR (crop, ag pools). ✓
- **M30** (simple_apr24, default — NOT detail): defines `vm_carbon_stock_croparea(j2,ag_pools)` (equations.gms:50; decl:20), which M29 folds in. Answer's §2 description of M30's role is mechanistically correct (contributes via the helper var, M29 aggregates). ✓
- **M31** (endo_jun13, default): `vm_carbon_stock(j2,"past",ag_pools,stockType) =e= ...` (equations.gms:23). POPULATOR. ✓
- **M32** (dynamic_may24, default): `q32_carbon(j2,ag_pools,stockType) .. vm_carbon_stock(j2,"forestry",ag_pools,stockType) =e= m_carbon_stock_ac(...)` (equations.gms:108). POPULATOR (forestry, ag_pools = vegc+litc). ✓
- **M34** (exo_nov21, default): `vm_carbon_stock.fx(j,"urban",ag_pools,stockType) = 0;` (presolve.gms:8). Fixes urban carbon to 0 (populates via bound, not `=e=`). Answer "Urban (fixed to 0)" — correct. ✓
- **M35** (pot_forest_may24, default): writes vm_carbon_stock for "primforest" (eq:43), "secdforest" (eq:50), "other" (eq:54). POPULATOR. ✓
- **M59** (cellpool_jan23, default): `vm_carbon_stock(j2, land,"soilc",stockType)` (equations.gms:62). POPULATOR (soilc pool, all land). ✓
- **M58 (Peatland) NOT a populator** — absent from the grep -rln list; answer's true-negative claim confirmed. ✓

Pool split validated: `ag_pools(c_pools) / vegc, litc /` (M56 sets.gms:210); soilc handled by M59 — answer's vegc/litc-vs-soilc split is correct. `stockType / actual, actualNoAcEst /` (M56 sets.gms:213).

Note: the answer lists M30 separately (7 modules) whereas the rubric §6 summary lists 5 land modules + M59. This is a *refinement*, not a discrepancy — M30 genuinely defines the croparea helper var that M29 aggregates, and the answer says so. More precise than the rubric summary; not a bug.

**3. M52 reader equation — CORRECT, formula exact.**
`q52_emis_co2_actual` declared at `normal_dec17/declarations.gms:30` (the only `q52` equation; line 35 is the `oq52` output param — answer's "one equation" claim correct), defined at `equations.gms:16-19`. The quoted formula matches byte-for-byte:
`vm_emissions_reg(i2,emis_oneoff,"co2_c") =e= sum((cell(i2,j2),emis_land(emis_oneoff,land,c_pools)), (pcm_carbon_stock(...,"actual") - vm_carbon_stock(...,"actual"))/m_timestep_length)`. Always uses stockType="actual". ✓

**4. M56 pricing chain — CORRECT, all three line citations EXACT.**
- `q56_emis_pricing_co2(i2,emis_oneoff)` at equations.gms:**19-22** (answer:19-22 ✓). Reads `vm_carbon_stock(...,"%c56_carbon_stock_pricing%")` directly, bypassing vm_emissions_reg. Formula matches exactly.
- `q56_emission_cost_oneoff(i2,emis_oneoff)` at equations.gms:**45-52** (answer:45-52 ✓). `v56_emission_cost =e= sum(pollutants, v56_emis_pricing * m_timestep_length * sum(ct, im_pollutant_prices * pm_interest/(1+pm_interest)))`. Annuity-due factor present. Formula matches.
- `q56_emission_costs(i2)` at equations.gms:**56-58** (answer:56-58 ✓). `vm_emission_costs(i2) =e= sum(emis_source, v56_emission_cost(i2,emis_source))`. ✓
- Chain `q56_emis_pricing_co2 → v56_emis_pricing → q56_emission_cost_oneoff → v56_emission_cost → q56_emission_costs → vm_emission_costs` — fully correct.
- `vm_emission_costs` consumed in M11 (`11_costs/default/equations.gms`) — answer's §4d "enters Module 11 objective" confirmed. ✓

**5. Supporting facts — CORRECT.**
- `c56_carbon_stock_pricing` default = `actualNoAcEst` (input.gms:90 `$setglobal`; default.cfg:1817). ✓
- `m_timestep_length` macro at `core/macros.gms:51`. ✓
- `c_pools / vegc, litc, soilc /` (core/sets.gms:325). ✓
- `pcm_carbon_stock` updated in M56 postsolve.gms:8 (`= vm_carbon_stock.l`). Answer §1 "updated there each timestep" ✓.
- All variable/parameter names real (no confabulation): `vm_carbon_stock_croparea` (M30 decl:20), `pm_carbon_density_secdforest_ac/_other_ac/_plantation_ac` (M52 decl:9/11/12), `fm_carbon_density` (M56 preloop:10), `pm_interest`, `im_pollutant_prices` (M56 decl:9). ✓

---

### Bugs Found:

- **Bug ID**: Q7-B1
- **Severity**: Minor
- **Class**: 10 (Stale/imprecise file:line citation)
- **Trigger**: §1.51 Minor — "Off-by-few line citation where adjacent lines say similar things."
- **Claim in answer**: §3 — "`emis_land(emis_oneoff,land,c_pools)` — set mapping ... covers `crop_vegc`, `past_litc`, `secdforest_vegc`, etc. (`core/sets.gms:332-335`)"
- **Reality in code**: `emis_land` is declared at core/sets.gms:**332**; its member block runs from 333 well past 335 (crop_vegc/litc/soilc at 333-335; `past_litc` at 338; `secdforest_vegc` at 345). The cited range 332-335 under-covers two of the three named examples.
- **File evidence**: `core/sets.gms:332` `emis_land(emis_oneoff,land,c_pools) Mapping...`; members 333+ (`crop_vegc . (crop) . (vegc)` ... `secdforest_vegc` :345).
- **Why Minor not Major**: lines 333-335 ARE emis_land members; adjacent lines are the same set mapping — a careful reader lands inside the correct set and would scroll to find the named members. Not materially different content.

- **Bug ID**: Q7-B2
- **Severity**: Minor
- **Class**: 10 (Stale/imprecise file:line citation)
- **Trigger**: §1.51 Minor — off-by-few line citation; cited content is genuinely present in the span.
- **Claim in answer**: §4c — "`im_pollutant_prices(...)` — the configured GHG price ..., constructed through the multi-stage preloop in `preloop.gms:35-124`"
- **Reality in code**: `modules/56_ghg_policy/price_aug22/preloop.gms` is **123 lines** long — line 124 does not exist. The `im_pollutant_prices` construction does span roughly preloop.gms:37-122 (assignments at 37,39,41,43,48,51,63,67,70...), so the start is right and the body is genuinely there; the end overshoots by ~2 lines past EOF.
- **File evidence**: `wc -l preloop.gms` = 123; `im_pollutant_prices` assignments grep'd at lines 37-70+.
- **Why Minor**: content described (multi-stage price construction) is real and in that span; only the end boundary is off by a couple lines / 1 past EOF. Would not mislead into wrong action.

---

### Missing Nuances (not scored):
- The answer doesn't explicitly state "price_aug22 / normal_dec17 are the default (and only) realizations." Both modules are single-realization, so M2 is satisfied implicitly, but an explicit one-liner would be cleaner. Informational only.
- §2 says M32's age-class densities are "supplied by M52"; M32 actually consumes its own `p32_carbon_density_ac` (derived upstream from M52's `pm_carbon_density_plantation_ac`). Correct in spirit (the M52 density chain feeds it), not load-bearing for the question. Not counted.
- M34's "populates" is via `.fx` bound-fixing (presolve), not an `=e=` equation — the answer's "(fixed to 0)" already conveys this; the rubric expected-set explicitly lists 34 as a populator, so consistent.
- Per the answer's own Sources note, source files were NOT read this session (line numbers from docs dated 2026-05-16 / 2025-10-13). Despite that, essentially every line citation was exact — evidence the underlying docs (`module_52.md`/`module_56.md`) are currently accurate on this chain. No `doc_error_answerer_beat_it` to record: the §1.5 latent-doc-bug mandate triggers when the answer is right but a load-bearing doc claim is WRONG vs code; here the load-bearing claims (declaration site, populator set, reader eq, pricing chain) match code, so the docs are correct, not beaten.

### Mechanical checks:
M1 ✓ (many file:line citations). M2 ✓ implicit (single-realization modules; cited realizations are the only ones). M3 ✓ (all prefixes valid: vm_/pm_/v56_/im_/pcm_/fm_ correct). M4/M5 partial — body lacks per-claim 🟢/🟡 badges (Sources block uses 🟡); Informational, not scored as bug. M6 ✓ (Sources block present, "Based on module docs" equivalent).

### Summary:
The answer is accurate and holds the R27 recovery on G2. The load-bearing facts that this anchor exists to protect are all correct: (1) `vm_carbon_stock` is **declared in Module 56** (`price_aug22/declarations.gms:34`), not M52; (2) the **populator set** is correct and verified at default realizations — M29(crop, via croparea helper from M30), M31(past), M32(forestry), M34(urban=0), M35(primforest/secdforest/other), M59(soilc) — with M58 correctly excluded; (3) the **producer-vs-reader distinction** is explicit (M52's `q52_emis_co2_actual` READS; land modules POPULATE); (4) the M56 pricing chain and all three M56 equation line citations are EXACT. Two Minor off-by-few citation-range imprecisions (`emis_land` range under-covers its named examples; `preloop.gms` end overshoots EOF by ~2 lines). Score = max(0, 10 − [4·0 + 2·0 + 1·2]) = **8/10**.
