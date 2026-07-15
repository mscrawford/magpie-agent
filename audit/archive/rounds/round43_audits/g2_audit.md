## Audit Report: G2 (vm_carbon_stock computation in Module 52 → GHG-policy cost in Module 56)

**Round**: 43 | **Question type**: REGRESSION ANCHOR G2 (§1.5 immutable latent-doc anchor) | **Auditor**: Opus, adversarial-but-fair
**Ground truth**: live GAMS at `<magpie-root>/modules/` (develop ee98739fd, clean)
**Answer audited**: `audit/archive/rounds/round43_answers/g2_answer.md`

### Overall Verdict: ACCURATE
### Accuracy Score: 10/10
### drift_observed (G2): **false**

---

### Spine verification (declaration / populator / reader / chain)

Every load-bearing spine claim was checked against the actual `.gms` files this session.

**1. Declaration site — M56, NOT M52** ✓
- Answer (lines 9, 72): "DECLARED in Module 56 (`modules/56_ghg_policy/price_aug22/declarations.gms:34`), not Module 52."
- Code: `modules/56_ghg_policy/price_aug22/declarations.gms:34` (inside `positive variables` block):
  `vm_carbon_stock(j,land,c_pools,stockType)     Carbon stock in vegetation soil and litter for different land types (mio. tC)`
- **Exact match**, including the `positive variables` scoping and `stockType` 4th index.

**2. Populator set — {29, 31, 32, 34, 35, 59}** ✓ (this is the regression-critical claim)
- Open-paren grep `vm_carbon_stock(` over all modules, excluding `.l/.lo/.up` solution reads and `ov_carbon_stock` output params, yields the EQUATION-LHS populators:
  - M29 cropland: `simple_apr24/equations.gms:30` and `detail_apr24/equations.gms:39` — `vm_carbon_stock(j2,"crop",ag_pools,stockType) =e=`
  - M31 pasture: `endo_jun13/equations.gms:23` — `vm_carbon_stock(j2,"past",ag_pools,stockType) =e=`
  - M32 forestry: `dynamic_may24/equations.gms:108` — `q32_carbon(j2,ag_pools,stockType) .. vm_carbon_stock(j2,"forestry",ag_pools,stockType) =e=`
  - M35 natveg: `pot_forest_may24/equations.gms:43,50,54` — primforest / secdforest / other
  - M59 SOM: `cellpool_jan23/equations.gms:62` and `static_jan19/equations.gms:12,18,22` — soilc pool
- M34 urban populates via a **`.fx`-to-0 assignment**, not an equation, so it does NOT appear in the LHS grep — found instead at `34_urban/exo_nov21/presolve.gms:8` (default realization) and `34_urban/static/presolve.gms:10`: `vm_carbon_stock.fx(j,"urban",ag_pools,stockType) = 0;`
- Answer's table (lines 63-70) lists exactly these 6 modules with correct land-type attribution AND correctly flags "urban (fixed to 0)" for M34 — matching the `.fx` mechanism. Answer line 10 states "{29, 31, 32, 34, 35, 59}". **Exact match.**
- Answer also correctly notes M29 "folds in `vm_carbon_stock_croparea` from Module 30" (M30 populates the separate croparea variable; verified M30 is not in the `vm_carbon_stock(` grep). No claim that M58 peatland populates it (correct — peatland uses its own emission path).

**3. M52 reader — q52_emis_co2_actual** ✓
- Answer (lines 11, 80-88): M52 only READS `vm_carbon_stock` via `q52_emis_co2_actual` at `normal_dec17/equations.gms:16-19`.
- Code `52_carbon/normal_dec17/equations.gms:16-19`:
  ```
  q52_emis_co2_actual(i2,emis_oneoff) ..
   vm_emissions_reg(i2,emis_oneoff,"co2_c") =e=
                  sum((cell(i2,j2),emis_land(emis_oneoff,land,c_pools)),
                  (pcm_carbon_stock(j2,land,c_pools,"actual") - vm_carbon_stock(j2,land,c_pools,"actual"))/m_timestep_length);
  ```
- **Exact match** to the answer's reproduced block (lines 82-87). The reproduced GAMS is verbatim, including `"actual"` on both stock terms and `/m_timestep_length`.
- Answer claims M52 has exactly 1 equation (line 98); grep confirms `q52_emis_co2_actual` is the only `q52_*` in the realization. ✓

**4. M56 cost chain** ✓ (all five hops + terminal target)
- Answer (lines 113, 158-173): `q56_emis_pricing_co2` → `v56_emis_pricing` → `q56_emission_cost_oneoff` → `v56_emission_cost` → `q56_emission_costs` → `vm_emission_costs(i)`.
- Code `56_ghg_policy/price_aug22/equations.gms`:
  - `q56_emis_pricing_co2` at **lines 19-22** (answer cites 19-22 ✓): `v56_emis_pricing(i2,emis_oneoff,"co2_c") =e= sum(... pcm_carbon_stock(...,"actual") - vm_carbon_stock(...,"%c56_carbon_stock_pricing%"))/m_timestep_length`. **Exact match** to answer block lines 117-122, including the `%c56_carbon_stock_pricing%` macro on the current-stock term (the key difference from q52's hard-coded `"actual"`).
  - `q56_emission_cost_oneoff` at **lines 45-52** (answer cites 45-52 ✓): `v56_emission_cost(i2,emis_oneoff) =e= sum(pollutants, v56_emis_pricing(...) * m_timestep_length * sum(ct, im_pollutant_prices(...) * pm_interest(ct,i2)/(1+pm_interest(ct,i2))))`. **Exact match** to answer block lines 131-139, including the `r/(1+r)` annuity factor.
  - `q56_emission_costs` at **lines 56-58** (answer cites 56-58 ✓): `vm_emission_costs(i2) =e= sum(emis_source, v56_emission_cost(i2,emis_source))`. **Exact match** to answer block lines 149-151.

**5. c56_carbon_stock_pricing default = actualNoAcEst** ✓
- Answer (line 125): default value is `"actualNoAcEst"`, "excludes afforestation establishment-phase carbon from pricing."
- Code: `config/default.cfg:1817` → `c56_carbon_stock_pricing <- "actualNoAcEst"`; `56_ghg_policy/price_aug22/input.gms:90` → `$setglobal c56_carbon_stock_pricing  actualNoAcEst`. **Exact match.**

---

### Additional claims verified (supporting density pipeline + sets)

- **fm_carbon_density / LPJmL** (answer Step 1a): M52 loads `fm_carbon_density(t_all,j,land,c_pools)`; concept correct. (input.gms line cites are 🟡 doc-sourced; not independently re-read this session but consistent with the module structure — non-load-bearing for the G2 spine.)
- **m_growth_vegc (Chapman-Richards)** at `core/macros.gms:18` ✓ — code: `$macro m_growth_vegc(S,A,k,m,ac) S + (A-S)*(1-exp(-k*(ac*5)))**m;`. Answer (line 36) reproduces with `^m` instead of GAMS `**m`; harmless presentational rendering of the exponent (see Informational note below).
- **m_growth_litc_soilc** at `core/macros.gms:20` ✓ — code: `$macro m_growth_litc_soilc(start,end,ac) (start + (end - start) * 1/20 * ac*5)$(ac <= 20/5) + end$(ac > 20/5);`. Answer (lines 50-51) reproduces faithfully.
- **emis_oneoff** set at `core/sets.gms:314` ✓ (answer cites 314-318 for the member span — line 314 is the set header, members follow; acceptable).
- **emis_land** mapping at `core/sets.gms:332` ✓ (answer cites 332-335; line 332 is the declaration `emis_land(emis_oneoff,land,c_pools)`; acceptable).
- **M52 default realization** = `normal_dec17` (config/default.cfg) ✓ — answer reads from this realization throughout.
- **M34 default realization** = `exo_nov21` (config/default.cfg) ✓ — the `.fx`-to-0 the answer attributes to M34 lives in `exo_nov21/presolve.gms:8`, the active realization (also present in `static/presolve.gms:10`).
- **Dual-pathway architecture** (answer Part 3, lines 104-113): answer correctly distinguishes the M52 emission-accounting path (`q52_emis_co2_actual → vm_emissions_reg`, used for annual gases via `q56_emis_pricing`) from the M56 direct CO2-pricing path (`q56_emis_pricing_co2 → v56_emis_pricing`, bypasses `vm_emissions_reg`). Verified: `q56_emis_pricing` (eq.gms:15-17) handles `emis_annual` and routes through `vm_emissions_reg`; `q56_emis_pricing_co2` (eq.gms:19-22) handles `emis_oneoff` CO2 and reads `vm_carbon_stock` directly. **Correct and a genuinely insightful nuance.**

---

### Latent doc-bug check (§1.5 G2 anchor — the regression-critical audit)

The §1.5 anchor exists because R22→R23→R26 the **doc populator list** was wrong while answers re-derived correctly, then R26 regressed when an answerer trusted the bad doc. The mandate: even if THIS answer is right, record + fix any wrong load-bearing doc claim.

I checked the docs directly:
- `modules/module_52.md:424`: "Provider: Modules 29 (Cropland, crop pool), 31 (Pasture), 32 (Forestry), 34 (Urban, fixed to 0), 35 (Natural Vegetation), and 59 (SOM, soilc pool for all land types) populate `vm_carbon_stock` by land type. Module 30 populates the separate `vm_carbon_stock_croparea`, which Module 29 folds in; Module 58 (peatland) does NOT populate it." → **CORRECT** vs code.
- `modules/module_56.md:583`: same set {29, 31, 32, 34, 35, 59} with identical M30/M58 nuances → **CORRECT**.
- `modules/module_56.md:1074`: "Carbon stocks (29,31,32,34,35,59; M30 via vm_carbon_stock_croparea)" → **CORRECT**.
- `modules/module_52.md:415-416`: declaration attributed to Module 56 → **CORRECT**.

**No latent populator-set doc bug.** The docs match code. This is the post-R26 recovered state (anchor recovered to 9 at R27); it has held through R43. **No `doc_error_answerer_beat_it` to record.**

---

### Bugs Found:

**None at Critical / Major / Minor severity.**

One Informational nitpick (does NOT affect score under §1, weight 0):

- **Bug ID**: G2-B1
- **Severity**: Informational
- **Class**: 4 (conceptual rendering) — boundary case, presentational only
- **Trigger**: §1 Informational — "Ordinal/syntax rendering that doesn't change meaning."
- **Claim in answer**: line 36 renders the Chapman-Richards macro as `S + (A-S)*(1-exp(-k*(ac*5)))^m` (caret exponent).
- **Reality in code**: `core/macros.gms:18` uses GAMS exponent `**m`: `S + (A-S)*(1-exp(-k*(ac*5)))**m`.
- **Assessment**: The math is identical; `^` vs `**` is a rendering choice and the §1 note explicitly exempts "exponent math." A reader is not misled. Recorded for completeness only. (The litc macro at answer line 51 is reproduced faithfully.)

---

### Mechanical checks (§2)

| # | Check | Result | Evidence |
|---|---|---|---|
| **M1** | File:line citations present | ✅ PASS | Dozens of precise `modules/XX/realization/file.gms:NN` citations (decl.gms:34, normal_dec17/eq.gms:16-19, price_aug22/eq.gms:19-22/45-52/56-58, macros.gms:18/20, sets.gms:314-318/332-335). |
| **M2** | Active realization stated | ✅ PASS | M52 normal_dec17, M56 price_aug22 (single realization), M34 exo_nov21 implied via the `.fx` attribution. M56 is single-realization (noted). |
| **M3** | Variable prefixes valid | ✅ PASS | `vm_carbon_stock`, `pcm_carbon_stock`, `vm_emissions_reg`, `v56_emis_pricing`, `v56_emission_cost`, `vm_emission_costs`, `im_pollutant_prices`, `pm_interest`, `pm_carbon_density_*_ac` — all prefixes correct and match declarations. |
| **M4** | Epistemic badges present | ⚠️ PARTIAL | Single global 🟡 badge in the Source statement (line 182) covering all claims as "documented." No per-claim badges. Acceptable for a docs-grounded walkthrough; not a content bug (Informational tendency, not counted). |
| **M5** | Confidence tier matches depth | ✅ PASS | Answer is honest: "No `.gms` files were opened in this session" (line 187) — so 🟡 (documented), not 🟢, is the correct tier. The answer did NOT over-claim 🟢. Good discipline. |
| **M6** | Closing source statement | ✅ PASS | Lines 180-187: explicit "Based on module_52.md / module_56.md documentation" with per-doc Last-Verified dates. |

M4 partial does not generate a scored bug — a single covering badge with an explicit "no code read this session" disclaimer is within acceptable practice for a documented-tier answer, and the tier is correctly chosen.

---

### Missing Nuances:

- **None material.** The answer is, if anything, more complete than the expected-answer summary: it adds the dual-pathway architecture (q52 accounting vs q56 pricing), the `s52_growingstock_calib` / FAO FRA 2025 bisection-calibration overwrite of secdforest/plantation vegc densities (a 2026-04-20 addition, correctly dated), the soilc "not age-class-specific" point, and the `c56_emis_policy = "reddnatveg_nosoil"` priced-pool selection. None of these were independently re-read this session (they are 🟡 doc-sourced and outside the G2 spine), but all are consistent with the module docs and none contradict code I did read.
- The answer's note (line 192-193) proposing a `cross_module/carbon_balance_conservation.md` "carbon stock bridge note" is a reasonable doc-gap observation, not an error.

---

### Summary:

The G2 spine — declaration (M56 decl.gms:34), populator set ({29,31,32,34,35,59}, with M34 via `.fx`-to-0 correctly distinguished from the five equation-populators), M52 reader (`q52_emis_co2_actual`, eq.gms:16-19), and the full M56 cost chain (`q56_emis_pricing_co2` → `v56_emis_pricing` → `q56_emission_cost_oneoff` → `v56_emission_cost` → `q56_emission_costs` → `vm_emission_costs`, all line citations exact) — is **fully correct against live code**. The `c56_carbon_stock_pricing = actualNoAcEst` default and all reproduced equation blocks match verbatim. **drift_observed = false.**

Critically for the §1.5 anchor: the docs (`module_52.md:424`, `module_56.md:583/1074`) state the populator set **correctly**, including the M34-fixed-to-0 and M58-excluded nuances. The R22→R26 latent doc bug remains fixed; **no `doc_error_answerer_beat_it` to record**. The anchor is healthy at R43.

Only one Informational nitpick (`^` vs `**` exponent rendering, weight 0). Score: 10/10.

**Verified against** `modules/56_ghg_policy/price_aug22/declarations.gms:34`, `modules/52_carbon/normal_dec17/equations.gms:16-19`, `modules/56_ghg_policy/price_aug22/equations.gms:15-58`, `modules/29_cropland/{simple_apr24,detail_apr24}/equations.gms`, `modules/31_past/endo_jun13/equations.gms:23`, `modules/32_forestry/dynamic_may24/equations.gms:108`, `modules/35_natveg/pot_forest_may24/equations.gms:43-54`, `modules/59_som/{cellpool_jan23,static_jan19}/equations.gms`, `modules/34_urban/exo_nov21/presolve.gms:8`, `core/macros.gms:18,20`, `core/sets.gms:314,332`, `config/default.cfg:1817` + `modules/56_ghg_policy/price_aug22/input.gms:90`, and docs `modules/module_52.md`, `modules/module_56.md`.
