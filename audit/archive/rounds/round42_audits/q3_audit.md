# Audit Report: Q3 (Cropland Soil-Nitrogen Budget in Module 50)

**Round**: 42 | **Auditor**: Opus | **Ground truth**: develop @ ee98739fd (clean)
**Answer audited**: `audit/archive/rounds/round42_answers/q3_answer.md`

---

## Overall Verdict: ACCURATE
## Accuracy Score: 10/10

The answer is code-faithful on every load-bearing claim. All equation bodies, variable names, realization names, and file:line citations were verified against the live `.gms` source and match. The TOP-PRIORITY wrong-realization hypothesis is **FALSE** — `macceff_aug22` IS Module 50's default (and only) realization. Part (c) is handled with above-average precision: the answer correctly recognizes that the surplus *variable* (`v50_nr_surplus_cropland`) is module-internal and is NOT exported to M51, and that M51 instead consumes the efficiency variables — a trap a naive answerer would fall into.

One Informational-tier terminology slip ("free variable" for a GAMS `positive variable`); it does not change the score (raw_severity_weighted = 0 → 10/10).

---

## TOP-PRIORITY VERIFICATION: M50 default realization

**VERIFIED M50 DEFAULT REALIZATION: `macceff_aug22`** (the only realization).

- `config/default.cfg:1479` → `cfg$gms$nr_soil_budget <- "macceff_aug22"    # def = macceff_aug22`
- `ls modules/50_nr_soil_budget/` → only `macceff_aug22/` + `input/` (no other realization dir).

The name reads MACC-related, but it is genuinely Module 50's realization (the "macceff" refers to MACC-curve mitigation of the SNUpE/NUE efficiency, applied inside M50's presolve — see `declarations.gms:43-46`, `i50_maccs_mitigation_transf`). **No wrong-realization Critical. The answer is correct.**

---

## Verified Claims (correct)

**(a) Balance equation + inputs + outputs**

- `q50_nr_bal_crp(i2)`: `vm_nr_eff(i2) * v50_nr_inputs(i2) =g= sum(kcr,v50_nr_withdrawals(i2,kcr))` — EXACT match. `modules/50_nr_soil_budget/macceff_aug22/equations.gms:14-16`. Cited 14-16. ✓ `=g=` structure (inputs×efficiency ≥ withdrawals) faithful.
- `q50_nr_inputs(i2)` (eq:22-32): all 8 terms match the answer's code block verbatim — `vm_res_recycling(i2,"nr")`, `sum((cell,kcr,w), vm_area*f50_nr_fix_area(kcr))`, fallow term, `vm_manure_recycling(i2,"nr")`, `sum(kli, vm_manure(i2,kli,"stubble_grazing","nr"))`, `vm_nr_inorg_fert_reg(i2,"crop")`, `sum(cell, vm_nr_som_fertilizer(j2))`, `sum(ct,f50_nitrogen_balanceflow(ct,i2))`, `v50_nr_deposition(i2,"crop")`. Cited 22-32. ✓ The mapping of these to fixation/deposition/fertilizer/residue/manure categories is correct. NOT a fabricated expanded form — the set-based sums are preserved exactly as in code.
- `q50_nr_withdrawals(i2,kcr)` (eq:36-43): `(1-sum(ct,f50_nr_fix_ndfa(...))) * (vm_prod_reg*fm_attributes + vm_res_biomass_ag + vm_res_biomass_bg) - vm_dem_seed*fm_attributes` — EXACT. Cited 36-43. ✓ NDFA and seed-subtraction explanations correct.
- `q50_nr_surplus(i2)` (eq:46-49): `v50_nr_surplus_cropland(i2) =e= v50_nr_inputs(i2) - sum(kcr, v50_nr_withdrawals(i2,kcr))` — EXACT. Cited 46-49. ✓
- `vm_nr_inorg_fert_reg(i,land_ag)` declared `declarations.gms:10` (positive var) ✓; `vm_nr_eff(i)` line 12 ✓; `v50_nr_surplus_cropland(i)` line 16 ✓; `v50_nr_deposition(i,land)` line 20 ✓.
- `q50_nr_deposition(i2,land)` (eq:88-90): `v50_nr_deposition =e= sum((ct,cell), i50_atmospheric_deposition_rates*vm_land)`. Answer cited 88-90 for a "separate deposition equation." ✓
- `q50_nr_cost_fert` (eq:94-97): `vm_nr_inorg_fert_costs =e= sum(land_ag, vm_nr_inorg_fert_reg)*s50_fertilizer_costs`. Cited 94-97. ✓ Default `s50_fertilizer_costs = 738` USD17MER/tN confirmed at `input.gms:29` (`/ 738 /`). ✓

**(b) Organic inputs from M18 + M59**

- M18 default `flexreg_apr16` (`config/default.cfg:622`). ✓
- `q18_res_recycling_nr(i2)` (eq:90-96): `vm_res_recycling(i2,"nr") =e= sum(kcr, v18_res_ag_recycling(i2,kcr,"nr") + vm_res_ag_burn(i2,kcr,"nr")*(1-f18_res_combust_eff(kcr)) + vm_res_biomass_bg(i2,kcr,"nr"))` — EXACT. Cited 90-96. ✓ The three-pathway decomposition (AG recycling / burn-ash N / BG residues) is correct.
- M59 default `cellpool_jan23` (`config/default.cfg:1916`). ✓
- `q59_nr_som(j2)` (eq:69-75): `vm_nr_som(j2) =e= sum(ct,i59_lossrate(ct))/m_timestep_length*1/15 * (sum((ct,land_from), p59_carbon_density*vm_lu_transitions(...,"crop")) - v59_som_target(j2,"crop"))` — EXACT. Cited 69-75. ✓ C:N = 15:1 and 15%/yr convergence correct.
- `q59_nr_som_fertilizer` (eq:81-84): `=l= vm_nr_som(j2)` ✓; `q59_nr_som_fertilizer2` (eq:88-91): `=l= vm_landexpansion(j2,"crop")*s59_nitrogen_uptake` ✓. Answer cited the pair as 81-91 (fair span). Default `s59_nitrogen_uptake = 0.2` tN/ha at `input.gms:9` (`/ 0.2 /`); answer rendered as "200 kg N/ha" — identical, conversion correct. ✓
- Entry into M50: `sum(cell(i2,j2), vm_nr_som_fertilizer(j2))` at eq:30. ✓
- `vm_manure` / `vm_manure_recycling` correctly attributed to Module 55 (AWMS); both DECLARED in default realization `ipcc2006_aug16/declarations.gms:19,21` (`config/default.cfg:1593` → `awms <- "ipcc2006_aug16"`). ✓

**(c) Surplus computation + downstream fate — handled with above-average precision**

- `v50_nr_surplus_cropland` is a `v50_` (module-internal) variable. Confirmed it appears ONLY in M50 (declarations + `q50_nr_surplus`) — NOT consumed by M51 or any other module. The answer's claim "the surplus feeds Module 51 via the efficiency variables, not the surplus variable directly" is CORRECT and avoids the obvious trap. ✓
- M51 default `rescaled_jan21` (`config/default.cfg:1550`). ✓
- M51 reads `vm_nr_eff`, `vm_nr_eff_pasture`, `vm_nr_inorg_fert_reg(i,"crop")`, `vm_nr_inorg_fert_reg(i,"past")`, `vm_manure_recycling`, `vm_manure_confinement`, `vm_manure` — verified in `modules/51_nitrogen/rescaled_jan21/equations.gms`. The answer's list of the three M50→M51 hand-off variables (`vm_nr_eff`, `vm_nr_eff_pasture`, `vm_nr_inorg_fert_reg`) is exactly right (lines 197-200). ✓
- Emission formula `N_loss = N_inorg_fert / (1 - SNUpE_base) × (1 - SNUpE) × emission_factor` faithfully generalizes `q51_emissions_inorg_fert` (eq:30-39: `vm_nr_inorg_fert_reg / (1-s51_snupe_base) * (1-vm_nr_eff) * i51_ef_n_soil`). ✓ Citations `equations.gms:26,34,46,59` all land on the rescaling-factor lines (man_crop / inorg_fert-crop / resid / som) — EXACT. ✓
- Cost path: `vm_nr_inorg_fert_costs` → M11 objective. Correct (M50 `q50_nr_cost_fert` produces it; standard cost-aggregation routing). ✓

---

## Bugs Found

### Q3-B1
- **Severity**: Informational
- **Class**: 1 (GAMS prefix/terminology) — borderline, recorded at the lowest tier
- **Trigger**: §1 Informational ("Style or doc issue, not a content error"); no Major/Minor trigger fires because the variable is correctly named, correctly attributed, and the answer's substantive meaning is right.
- **Claim in answer**: "The model optimizes `vm_nr_inorg_fert_reg` (inorganic fertilizer) upward…" framed as "a free variable" (line 32) and "the only free optimization variable in the budget" (line 62).
- **Reality in code**: `vm_nr_inorg_fert_reg(i,land_ag)` is declared under `positive variables` (`declarations.gms:9-10`), not GAMS `free variables`. In GAMS, "free variable" is a specific type (unbounded, can go negative); a positive variable is bounded ≥ 0.
- **File evidence**: `modules/50_nr_soil_budget/macceff_aug22/declarations.gms:9-10` — `positive variables\n vm_nr_inorg_fert_reg(i,land_ag) ...`
- **Why not higher**: The answer's INTENT — "the only endogenous/optimized decision variable in the budget, vs. the exogenous organic inputs" — is correct and stated explicitly several times. A reader would not edit code wrongly. Tie-breaker (§1) pulls DOWN; this is a terminology slip, not a content error. `tier_uncertainty: true` (Informational vs Minor).

---

## Missing Nuances (not bugs)

- The answer focuses on cropland (as asked) and only lightly touches the parallel pasture budget (`q50_nr_bal_pasture`, `q50_nr_inputs_pasture`, `q50_nr_surplus_pasture`). Appropriate scoping; not penalized.
- `f50_nitrogen_balanceflow` is described as a correction for "structurally unrealistic SNUpE values"; the code comment frames it as a generic balance-flow correction term. Minor interpretive gloss, well within docs; not a bug.

---

## Latent doc bugs (§1.5)

**None.** `module_50.md` was the answerer's primary source; I cross-checked its equation blocks and citations (lines 32, 60, 83-96, 111-127, 135-144, 162-167) against live code — every one matches the current `.gms`. The doc is code-faithful; the answer reproduced it faithfully. No `doc_error_answerer_beat_it` to record. (The "free variable" slip is in the ANSWER's prose, not in `module_50.md`, which says "endogenous optimization variable" / "optimization variable" — line 16, 24, 104 — correctly.)

---

## Mechanical checks

| Check | Result | Note |
|---|---|---|
| M1 (file:line present) | PASS | Many exact `modules/XX/real/equations.gms:NN` citations |
| M2 (active realization stated) | PASS | States `macceff_aug22` default for M50; also `flexreg_apr16` (M18), `cellpool_jan23` (M59), `rescaled_jan21` (M51) |
| M3 (prefixes valid) | PASS | `vm_*`, `v50_*`, `f50_*`, `s50_*`, `s59_*`, `i59_*` all consistent with code |
| M4 (epistemic badges) | PASS | Every block tagged 🟡 (docs-only, honest about no raw `.gms` read) |
| M5 (tier matches depth) | PASS | 🟡 consistently matched to doc-citation; no 🟢 over-claim despite not reading code |
| M6 (closing source statement) | PASS | "Primary source: module_50.md…" closing block present |

---

## Summary

A 10/10 answer. Every equation (`q50_nr_bal_crp`, `q50_nr_inputs`, `q50_nr_withdrawals`, `q50_nr_surplus`, `q50_nr_cost_fert`, `q18_res_recycling_nr`, `q59_nr_som`, `q59_nr_som_fertilizer`/`2`, M51 emission equations), every variable, every realization name, and every file:line citation verified against live develop @ ee98739fd and matches. The top-priority wrong-realization hypothesis is disproven: `macceff_aug22` is M50's genuine (and only) default realization. Part (c) is notably precise — it correctly distinguishes the module-internal surplus variable from the efficiency variables M51 actually consumes, dodging the "surplus is exported" trap. Sole blemish: "free variable" used loosely for a GAMS `positive variable` (Informational; substantive meaning correct). No doc fixes required.
