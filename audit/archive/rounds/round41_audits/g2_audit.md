# Audit Report: G2 (vm_carbon_stock computation in M52 + entry into GHG-policy cost in M56)

**Round**: 41 | **Regression anchor**: G2 (citation/chain anchor; §1.5 latent-doc-bug IMMUTABLE anchor)
**Auditor model**: Opus 4.8 (1M)
**Ground truth**: live GAMS at `modules/`, develop HEAD `ee98739fd` (clean)
**Answer audited**: `audit/archive/rounds/round41_answers/g2_answer.md` (docs-only answer)

---

## Overall Verdict: ACCURATE

## Accuracy Score: 9/10

`score = max(0, 10 − 4·crit − 2·major − 1·minor) = 10 − 1 = 9` (1 Minor).

---

## drift_observed: FALSE

The answer's spine matches the G2 expected answer on every load-bearing element:
- **Declaration site**: M56 `price_aug22/declarations.gms:34` (NOT M52) ✓
- **Populator set**: M29, M31, M32, M34, M35, M59 ✓ (exactly the expected set; M34 via `.fx`=0)
- **Reader**: M52 `q52_emis_co2_actual` at `normal_dec17/equations.gms:16-19` ✓
- **M56 chain**: `q56_emis_pricing_co2` → `v56_emis_pricing` → `q56_emission_cost_oneoff` → `v56_emission_cost` → `q56_emission_costs` → `vm_emission_costs(i)` ✓

No divergence. Anchor stable.

---

## Mechanical checks

| # | Check | Result | Evidence |
|---|---|---|---|
| M1 | File:line citations present | ✅ PASS | Dozens of `modules/XX/realization/file.gms:NN` citations |
| M2 | Active realization stated | ⚠️ PARTIAL | Answer names realizations in citations (`price_aug22`, `normal_dec17`, `detail_apr24`) and these ARE the defaults, but never explicitly says "this is the default realization." All cited realizations verified active in `config/default.cfg`. Not a content bug; minor M2 softness. |
| M3 | Variable prefixes valid | ✅ PASS | `vm_carbon_stock`, `pcm_carbon_stock`, `fm_carbon_density`, `vm_emissions_reg`, `v56_emis_pricing`, `v56_emission_cost`, `vm_emission_costs`, `im_pollutant_prices`, `pm_interest` — all prefixes correct |
| M4 | Epistemic badges present | ✅ PASS | 🟡 on every section |
| M5 | Confidence tier matches depth | ✅ PASS | All claims tagged 🟡 (documented); answer explicitly states "No raw .gms files were read" (line 245) — honest. Tier is conservative (everything verified TRUE against code this audit), but honesty-correct. |
| M6 | Closing source statement | ✅ PASS | Lines 239-245: "Based on module_52.md / module_56.md documentation" with verification dates |

---

## Verified Claims (correct)

1. **Declaration site** — "declared in Module 56's `declarations.gms:34`" (answer line 11).
   → CONFIRMED: `modules/56_ghg_policy/price_aug22/declarations.gms:34: vm_carbon_stock(j,land,c_pools,stockType)  Carbon stock in vegetation soil and litter ... (mio. tC)`. Grep across ALL `declarations.gms` in `modules/` finds it ONLY in M56 (M30 declares the distinct `vm_carbon_stock_croparea`, not `vm_carbon_stock`). **Not declared in M52** — correct.

2. **POPULATOR SET (the §1.5 anchor)** — answer claims M29, M31, M32, M34, M35, M59 (lines 16-21).
   → CONFIRMED EXACTLY. Open-paren grep `vm_carbon_stock(` for LHS `=e=` definitions + `.fx` bounds:
     - M29 cropland: `detail_apr24/equations.gms:39` (active) + `simple_apr24/equations.gms:30` — `"crop"` pool ✓
     - M31 past: `endo_jun13/equations.gms:23` (active, `=e=`) + `static/presolve.gms:15` (`.fx`) — `"past"` ✓
     - M32 forestry: `dynamic_may24/equations.gms:108` — `"forestry"` ✓
     - M35 natveg: `pot_forest_may24/equations.gms:43,50,54` — `"primforest"`, `"secdforest"`, `"other"` ✓
     - M59 som: `cellpool_jan23/equations.gms:62` (active) + `static_jan19/equations.gms:12,18,22` — `"soilc"` slice ✓
     - **M34 urban**: `exo_nov21/presolve.gms:8` (active) + `static/presolve.gms:10`: `vm_carbon_stock.fx(j,"urban",ag_pools,stockType) = 0;` — populates via BOUND, fixed to 0. Answer correctly states "urban carbon (fixed to 0)" (line 19). ✓
   - M52 and M56 lines (`equations.gms:19` / `:22`) carry `vm_carbon_stock` on the **RHS** of the `(pcm − vm_carbon_stock)` subtraction → READERS, correctly NOT counted as populators. ✓
   - Answer correctly excludes M30 (separate `vm_carbon_stock_croparea`, folded in by M29) and M58 peatland.

3. **M52 reader equation** — `q52_emis_co2_actual` at `equations.gms:16-19` (answer lines 84, 213).
   → CONFIRMED EXACT. `modules/52_carbon/normal_dec17/equations.gms:16-19`:
     ```
     q52_emis_co2_actual(i2,emis_oneoff) ..
       vm_emissions_reg(i2,emis_oneoff,"co2_c") =e=
       sum((cell(i2,j2),emis_land(emis_oneoff,land,c_pools)),
       (pcm_carbon_stock(j2,land,c_pools,"actual") - vm_carbon_stock(j2,land,c_pools,"actual"))/m_timestep_length);
     ```
   Formula reproduced verbatim in answer (lines 86-91). Declaration at `declarations.gms:30` (answer line 83) — CONFIRMED.

4. **M56 pricing chain (Path B, direct read)** — `q56_emis_pricing_co2` at `equations.gms:19-22` reading stocks directly, bypassing the annual-only `q56_emis_pricing` (answer Part 4, lines 122-135).
   → CONFIRMED EXACT. `equations.gms:19-22` uses `"%c56_carbon_stock_pricing%"` for the current-stock slice (not hardcoded `"actual"`). `q56_emis_pricing` (line 15) is indexed over `emis_annual` only; `q56_emis_pricing_co2` (line 19) over `emis_oneoff` — disjoint set slices writing the same `v56_emis_pricing`. Answer's architectural read (one-off CO2 does NOT flow through `q56_emis_pricing`) is accurate and insightful. ✓

5. **`c56_carbon_stock_pricing` default = `actualNoAcEst`** (answer lines 133, 194).
   → CONFIRMED: `input.gms:90: $setglobal c56_carbon_stock_pricing  actualNoAcEst` and `config/default.cfg:1817: ... <- "actualNoAcEst"`. Rationale (excludes afforestation-establishment carbon to avoid double-counting with CDR reward) is consistent with code structure. ✓

6. **Cost chain `q56_emission_cost_oneoff` → `q56_emission_costs`** (answer Part 5).
   → CONFIRMED: `q56_emission_cost_oneoff` (eq at `equations.gms:45-52`) computes `v56_emission_cost = sum(pollutants, v56_emis_pricing × m_timestep_length × sum(ct, im_pollutant_prices × pm_interest/(1+pm_interest)))` — annuity-due factor, formula reproduced correctly. `q56_emission_costs` (eq at `:56-58`): `vm_emission_costs(i2) =e= sum(emis_source, v56_emission_cost(i2,emis_source))`. ✓

7. **`c56_emis_policy` default = `reddnatveg_nosoil`** (answer line 186).
   → CONFIRMED: `input.gms:86: $setglobal c56_emis_policy  reddnatveg_nosoil`. ✓

8. **M56 preloop initialization of `pcm_carbon_stock` from `fm_carbon_density`** (answer lines 41, 204).
   → CONFIRMED: `preloop.gms:10: pcm_carbon_stock(j,land,ag_pools,stockType) = fm_carbon_density("y1995",j,land,ag_pools)*pcm_land(j,land);` and `:11: vm_carbon_stock.l = pcm_carbon_stock`. Answer cites `preloop.gms:10` ✓. Postsolve store `pcm_carbon_stock = vm_carbon_stock.l` confirmed at `postsolve.gms:8` (answer line 25 "stores ... at the end of each timestep"). ✓

9. **Chapman-Richards / litter macros** (answer Part 2b, lines 51, 60) and start.gms age-class density lines (17/28/48, 20/31/51) — these are M52-internal density computations feeding the populators, cited from `module_52.md`. Not independently re-verified line-by-line this audit (peripheral to the G2 spine), but consistent with `module_52.md:138,220,308` which were cross-checked and align with code. No red flags.

---

## Bugs Found

### G2-B1
- **Severity**: Minor
- **Class**: 10 (Stale/loose file:line citation)
- **Trigger** (§1 Minor): "Off-by-few line citation where adjacent lines say similar things."
- **Claim in answer**: "Step 1: One-off emission costs (q56_emission_cost_oneoff, **equations.gms:35-52**)" (answer line 145, repeated line 220).
- **Reality in code**: The `q56_emission_cost_oneoff` equation **statement** begins at `equations.gms:45` (`q56_emission_cost_oneoff(i2,emis_oneoff) ..`) and runs to line 52. Lines 35-44 are the `*'` documentation comment block (one-off-vs-yearly discounting rationale). A reader jumping to line 35 lands on comment prose, not the equation.
- **File evidence**: `modules/56_ghg_policy/price_aug22/equations.gms:45-52` (equation); `:35-44` (preceding comment block).
- **Note**: The answer adopts a comment-inclusive citation convention throughout (it also cites `q56_emis_pricing` as 12-17 [eq at 15-17] and `q56_emission_costs` as 54-58 [eq at 56-58]). For those two the comment lead-in is 2-3 lines and the span still lands the reader adjacent to the equation; for the oneoff equation the lead-in is 10 lines, which is the only one loose enough to mislead a careful reader. The cited content is still the RIGHT equation's documentation (not drift to a different/wrong equation), so this is Minor, not Major. **tier_uncertainty: false** (clearly below the Major "drift to materially different content" threshold).

---

## Latent doc-bug check (§1.5 — THE G2 anchor)

**Result: NO latent populator-set doc bug. The R26 regression remains FIXED.**

The answer is docs-only (line 245). Both source docs state the populator set **correctly and explicitly**, matching code exactly:

- `module_52.md:424`: *"Provider: Modules 29 (Cropland, crop pool), 31 (Pasture), 32 (Forestry), 34 (Urban, fixed to 0), 35 (Natural Vegetation), and 59 (SOM, soilc pool for all land types) populate `vm_carbon_stock` by land type. Module 30 populates the separate `vm_carbon_stock_croparea`, which Module 29 folds in; Module 58 (peatland) does NOT populate it."* → matches code (incl. M34-via-.fx and M30/M58 exclusions).
- `module_56.md:583` and `module_56.md:1037-1044`: identical correct list (29, 31, 32, 34, 35, 59), M34 urban fixed to 0, croparea via `vm_carbon_stock_croparea`, peatland excluded.
- `module_52.md:267-273` and `module_56.md:600-619`: per-module populator file:line citations spot-checked against code — M29 `detail_apr24/equations.gms` (doc:41 / code eq LHS at 39, within block), M31 `endo_jun13/equations.gms` (doc:24 / code:24 exact), M35 `pot_forest_may24/equations.gms` (doc:44 / code:43-44 exact for `=e=`). Accurate.

This is the post-R26 recovered state described in the rubric §1.5 anchor (R22 found the list wrong → R23 declined the fix → R26 regressed to 7 → fix applied → recovered). The fix has held. **No `doc_error_answerer_beat_it` bug to record.** Had the docs still carried the wrong list, the answer (which copied the docs) would have inherited it — so the docs being correct is exactly why the answer scored well here.

---

## Missing Nuances

1. **M2 softness**: The answer never says "`price_aug22` / `normal_dec17` / `detail_apr24` are the default realizations." They ARE (verified in `config/default.cfg`), and the answer cites them, but a reader on a non-default realization wouldn't be warned. Low-stakes for G2 (the spine is realization-stable), but a one-line "all realizations cited are the config defaults" would close M2 cleanly.

2. **M31 dual populator path**: The active `endo_jun13` realization populates `vm_carbon_stock("past")` via an `=e=` equation (`equations.gms:23`), but M31's `static` realization populates it via `.fx` (`presolve.gms:15`). The answer's generic "Pasture: pasture carbon" is correct for the default but doesn't flag this realization-dependent mechanism. Not a bug (default is `endo_jun13` → equation path), just an unstated nuance.

3. **`pcm_carbon_stock` declaration site** not stated. The answer correctly treats it as the lagged companion populated in M56 postsolve, but doesn't cite where the `pcm_` parameter is declared. Peripheral; the answer's behavioral description is correct.

---

## DOC BUGS TO FIX

**None.** The populator-set claims in `module_52.md` (lines 424, 267-273) and `module_56.md` (lines 583, 616, 1037-1044) are correct versus code. The §1.5 anchor's previously-wrong list is fixed and has held. No doc edits required this round.

(G2-B1 is an ANSWER citation looseness, not a doc bug — `module_56.md`'s own equation citations are accurate.)

---

## Summary

A strong, accurate G2 answer. Every load-bearing claim — declaration in M56 (not M52), the full populator set {29,31,32,34,35,59} including the easily-missed M34-via-`.fx` and the M59 `soilc` slice, the M52 reader equation, and the full M56 pricing chain with the direct `q56_emis_pricing_co2` carbon-stock read and `actualNoAcEst` default — is confirmed against live code at HEAD `ee98739fd`. The answer's architectural insight (one-off CO2 bypasses the annual `q56_emis_pricing` and is priced directly off stocks) is correct and well-explained. Only deduction is one Minor citation-span looseness (`q56_emission_cost_oneoff` cited as 35-52; equation proper is 45-52, lines 35-44 are comments). **drift_observed: false** — the anchor is stable. The §1.5 latent-doc-bug surface is clean (docs carry the correct populator list; the R26 regression fix has held). **Score: 9/10.**
