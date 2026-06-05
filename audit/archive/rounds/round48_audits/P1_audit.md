## Audit Report: R48-P1 (Carbon conservation when land is converted)

### Overall Verdict: MOSTLY ACCURATE
### Accuracy Score: 8/10

Auditor: Opus, Round 48. Ground truth: MAgPIE working tree == origin/develop @ ee98739fd (authoritative). All citations below were read THIS session.

---

### Verified Claims (correct):

- **Central accounting equation `q52_emis_co2_actual`**: quoted verbatim and correct. `modules/52_carbon/normal_dec17/equations.gms:16-19` —
  `vm_emissions_reg(i2,emis_oneoff,"co2_c") =e= sum((cell(i2,j2),emis_land(emis_oneoff,land,c_pools)), (pcm_carbon_stock(j2,land,c_pools,"actual") - vm_carbon_stock(j2,land,c_pools,"actual"))/m_timestep_length);`. The answer's formula, sign convention (prev>cur → positive → emission; prev<cur → sequestration), units (mio tC = Tg C → Tg C/yr), and the `/m_timestep_length` annualization are all correct.

- **`vm_carbon_stock` declared in Module 56, NOT 52**: correct. `modules/56_ghg_policy/price_aug22/declarations.gms:34` (`positive variables vm_carbon_stock(j,land,c_pools,stockType)`). Matches the G2 regression anchor.

- **`pcm_carbon_stock` is the previous-timestep stock, stored by Module 56**: correct on the mechanism. Declared at `declarations.gms:19`; stored at end of solve in `modules/56_ghg_policy/price_aug22/postsolve.gms:8` (`pcm_carbon_stock(j,land,ag_pools,stockType) = vm_carbon_stock.l(...)`), initialized in `preloop.gms:10-11`. The answer's "Module 56 stores the solved vm_carbon_stock as pcm_carbon_stock" is verified (postsolve). (Citation nit on the line number — see Bug P1-B1.)

- **Three carbon pools `c_pools /vegc,litc,soilc/`**: correct, `core/sets.gms:324-325` (exact).

- **21 emission slots = 7 land × 3 pools (`emis_oneoff`)**: correct, `core/sets.gms:315-318` (emis_oneoff has exactly 21 members). Land types listed (crop, past, forestry, primforest, secdforest, urban, other) match `core/sets.gms` and the `emis_land` mapping.

- **Populator equations** (all default realizations, all verified):
  - `q35_carbon_primforest` `modules/35_natveg/pot_forest_may24/equations.gms:42-44` with `m_carbon_stock(vm_land,fm_carbon_density,"primforest")` — exact.
  - `q35_carbon_secdforest` `equations.gms:49-51` using blended `p35_carbon_density_secdforest` — exact.
  - `q35_carbon_other` `equations.gms:53-55` — exact.
  - `q29_carbon` `modules/29_cropland/detail_apr24/equations.gms:38-42` (header line 38, `vm_carbon_stock(...,"crop",...)` line 39); aggregates `vm_carbon_stock_croparea` (+ fallow + treecover). Answer's "line 39" and "aggregates vm_carbon_stock_croparea from Module 30" correct.
  - `q31_carbon` `modules/31_past/endo_jun13/equations.gms:22-24`, `m_carbon_stock(vm_land,fm_carbon_density,"past")` — answer's "equations.gms:24" lands on the populate line. Correct.
  - `q32_carbon` `modules/32_forestry/dynamic_may24/equations.gms:108-109` (see Bug P1-B3 on the named density).
  - urban fixed to zero: `vm_carbon_stock.fx(j,"urban",ag_pools,stockType) = 0` at `modules/34_urban/exo_nov21/presolve.gms:8` — exact.
  - soilc slice via `q59_carbon_soil` `modules/59_som/cellpool_jan23/equations.gms:61-64`, `v59_som_pool + vm_land*i59_subsoilc_density` — exact.

- **Soil-carbon convergence (`v59_som_pool`)**: equation `modules/59_som/cellpool_jan23/equations.gms:46-52` matches the answer's `lossrate*target + (1-lossrate)*legacy` structure (legacy = previous carbon density mapped through `vm_lu_transitions`). The `lossrate = 1 - 0.85^(yeardiff)` (15%/yr) claim is verified exactly: `i59_lossrate(t)=1-0.85**m_yeardiff(t)` at `modules/59_som/cellpool_jan23/preloop.gms:45` (code comment confirms 15%/yr → 44%/5yr, 80%/10yr, 96%/20yr; answer's "~20 years" consistent).

- **`fm_carbon_density` from LPJmL `lpj_carbon_stocks.cs3`, read by Module 52**: correct. `table fm_carbon_density(t_all,j,land,c_pools)` … `$include "./modules/52_carbon/input/lpj_carbon_stocks.cs3"` at `modules/52_carbon/normal_dec17/input.gms:16-18`. Answer's range 16-20 brackets it (the table/`$ondelim`/`$include`/`$offdelim`/`;` block spans 16-20). Correct.

- **Chapman-Richards growth at `core/macros.gms:18`**: correct and precise. Line 18 is `$macro m_growth_vegc(S,A,k,m,ac) S + (A-S)*(1-exp(-k*(ac*5)))**m;` — the vegc Chapman-Richards macro. Good precision.

- **Age-class density interfaces `pm_carbon_density_secdforest_ac`, `pm_carbon_density_other_ac`, `pm_carbon_density_plantation_ac`**: all three exist as real M52 declarations (`modules/52_carbon/normal_dec17/declarations.gms:9,11,12`). No confabulation.

- **`q56_emis_pricing_co2` re-computes the stock change with the priced `stockType`**: correct. `modules/56_ghg_policy/price_aug22/equations.gms:19-22` uses `vm_carbon_stock(...,"%c56_carbon_stock_pricing%")` for the current stock. The answer correctly identifies the `stockType`-substitution as the only difference from `q52_emis_co2_actual`.

- **`c56_carbon_stock_pricing` default = `actualNoAcEst`**: correct. `config/default.cfg:1817` and `modules/56_ghg_policy/price_aug22/input.gms:90`. Answer's explanation (excludes afforestation establishment to avoid double-counting with CDR rewards) is consistent with the code design.

- **Cost chain into objective**: `q56_emission_cost_annual` (eq 29-33) + `q56_emission_cost_oneoff` (eq 45-52) → `v56_emission_cost` → `q56_emission_costs` (eq 56-58) → `vm_emission_costs(i)`. Answer's chain diagram and the `equations.gms:29-52` range are correct; one-off emissions get the `pm_interest` annuity treatment (the answer simplified but did not misstate).

- **`vm_emissions_reg` declared in Module 56**: correct, `modules/56_ghg_policy/price_aug22/declarations.gms:40`.

- **PR #869 secdforest carbon-density blend**: verified. `p35_carbon_density_secdforest` blended in `modules/35_natveg/pot_forest_may24/presolve.gms:244-252` — weighted average of FRA-calibrated `pm_carbon_density_secdforest_ac` and uncalibrated Braakhekke `pm_carbon_density_secdforest_ac_uncalib`, weighted by natural-origin area share `pc35_secdforest_natural/pc35_secdforest`. Answer's Step 7 description is accurate, including the crucial note that the conservation accounting is unchanged (only the density input is more accurate).

- **Framing: stock-flow accounting, not a strict conservation law**: correct and well-stated; matches `cross_module/carbon_balance_conservation.md §1` and the code design (no balance constraint on total C; the invariant is that every stock loss registers as a positive emission).

---

### Bugs Found:

- **Bug ID**: R48-P1-B1
- **Severity**: Minor
- **Class**: 10 (Stale/wrong file:line citation)
- **Trigger**: "File:line citation drift to adjacent but different content" (§1 Major trigger) — downgraded via tie-breaker (see below).
- **Claim in answer**: Summary table row "Previous-period stock preserved … `pcm_carbon_stock(j,land,c_pools,"actual")` | M56 `declarations.gms:34`".
- **Reality in code**: `pcm_carbon_stock` is declared at `modules/56_ghg_policy/price_aug22/declarations.gms:19`. Line 34 is the declaration of `vm_carbon_stock` (a different, but adjacent and identically-shaped, variable in the same declarations block). The answer cited line 34 correctly for `vm_carbon_stock` in Step 2 but reused it for `pcm_carbon_stock` in the summary.
- **File evidence**: `modules/56_ghg_policy/price_aug22/declarations.gms:19` (`pcm_carbon_stock(j,land,c_pools,stockType) … (mio. tC)`) vs `:34` (`vm_carbon_stock(j,land,c_pools,stockType)`).
- **Tier reasoning**: between Minor and Major. The citation points to a *different variable name*, which argues Major (R20 anchor: 5-20 line drift = Major). But it is a single citation, 15 lines up in the SAME declarations block, both variables have identical signatures, and the correct pcm mechanism is otherwise fully described (incl. postsolve storage). A reader lands on the right file and right block. Tie-breaker pulls down → **Minor**. `tier_uncertainty: true`.

- **Bug ID**: R48-P1-B2
- **Severity**: Minor
- **Class**: 10 (Stale/wrong file:line citation — line-range truncation)
- **Trigger**: "File:line citation drift to adjacent but different content (would mislead a careful reader)" — truncated range; downgraded via tie-breaker.
- **Claim in answer**: "mapped through `emis_land(emis_oneoff,land,c_pools)` (`core/sets.gms:332–335`)".
- **Reality in code**: The `emis_land` set declaration spans `core/sets.gms:332-354` (opens at 332, all 21 mappings run through the closing `/` at 354). `332-335` captures only the opening and the first 3 mappings (crop_vegc/litc/soilc), truncating 18 of 21. The set's *functional* content (21 mappings, 7 land × 3 pools) is described correctly in prose; only the line range is understated. A reader lands on the correct set in the correct file.
- **File evidence**: `core/sets.gms:332` (`emis_land(emis_oneoff,land,c_pools) Mapping between land and carbon pools`) through `:354` (closing `/`).
- **Anchor reference**: weaker analogue of the R16 suffix-truncation anchor, but for a *citation range* not a set enumeration — the answer did NOT truncate the set's described content, only the cited lines. Hence Minor, not the Critical R16 anchor. **Root cause is the boundary doc** (see latent doc bug below); recorded as an answer bug because the truncation appears in the answer text.
- `tier_uncertainty: true`.

---

### Latent doc bugs (record independent of the answer score, §1.5):

- **Doc bug ID**: R48-P1-DOC1
- **Root cause tag**: `doc_error` (boundary-doc citation truncation; the answer inherited it rather than beating it)
- **Severity (by future-reader harm)**: Minor
- **Doc**: `cross_module/carbon_balance_conservation.md` cites `emis_land` set at `core/sets.gms:332-335` (line 325 and §4.3 mapping block). Actual extent is `core/sets.gms:332-354`. A future answerer will re-inherit the truncated range (as this answer did).
- **Fix this session (validate-semantic Step 5)**: update the two `core/sets.gms:332-335` references in `carbon_balance_conservation.md` to `core/sets.gms:332-354`.
- **Note**: This is NOT the classic §1.5 "answerer beat the doc" case (answer-correct-despite-wrong-doc); it is the inverse (answer reproduced a wrong doc citation). Recorded here so the doc gets fixed and the truncation does not recur downstream. The doc's load-bearing *semantic* claims (q52 equation `equations.gms:16-19`, `vm_carbon_stock` declared at `declarations.gms:34`, pools at `sets.gms:324-325`, stock-flow-not-conservation framing) were all spot-checked and are CORRECT vs code.

---

### Missing Nuances:

- **`pcm`/`vm_carbon_stock` populated over `ag_pools` for vegc+litc, soilc handled separately by M59**: the answer correctly splits the work (M35/29/31/32/34 do above-ground via `m_carbon_stock`/`m_carbon_stock_ac`, which sum only `ag_pools`; M59 does the soilc slice). It does not explicitly note that `m_carbon_stock` (`core/macros.gms:99-101`) sums *only* `ag_pools` (vegc, litc) and that `pcm_carbon_stock` is stored in postsolve over `ag_pools` while soilc flows through M59's own initialization (`modules/59_som/cellpool_jan23/preloop.gms:30-35`). Not an error — the answer's per-pool attribution table is correct — just an under-explained mechanism. (Informational, not scored.)
- **Module 32 density chain**: the equation multiplies `v32_land × p32_carbon_density_ac` (a module-local parameter at `modules/32_forestry/dynamic_may24/declarations.gms:19`); `p32_carbon_density_ac` is derived from the M52-provided `pm_carbon_density_plantation_ac`. The answer named the upstream M52 interface (`pm_carbon_density_plantation_ac`, which is real and correct as the plantation density source) rather than the local parameter that literally appears in the equation. Because the answer's M32 table row carries no file:line citation and names a real variable, this is at most an imprecision (see B3 note below), not a confabulation.

- **Note (sub-bug-threshold, M32)**: the Step 2 table says Module 32 = "Plantation age-class area × `pm_carbon_density_plantation_ac`". The equation `q32_carbon` (`equations.gms:108-109`) uses `v32_land × p32_carbon_density_ac`. `pm_carbon_density_plantation_ac` (M52 `declarations.gms:12`) is the real upstream source feeding the local `p32_carbon_density_ac`, so the named variable exists and is causally correct. No file:line was attached to this row, and no false equation was written. Judged Informational (below Minor threshold), not counted in the score.

---

### Mechanical checks:
- **M1** (file:line citations present): PASS — many concrete `modules/XX/realization/file.gms:NN` citations.
- **M2** (active realization stated): PASS — answer covers default realizations throughout (normal_dec17, price_aug22, cellpool_jan23, pot_forest_may24, detail_apr24, endo_jun13, exo_nov21); all confirmed default in `config/default.cfg`.
- **M3** (variable prefixes valid): PASS — `vm_`, `pcm_`, `pm_`, `fm_`, `v59_`, `p35_`, `q52_`, `q56_`, etc. all consistent with usage in code.
- **M4** (epistemic badges present): PASS — 🟡 badges throughout (appropriately, since produced docs-only).
- **M5** (confidence tier matches depth): PASS — all 🟡 (documented), consistent with docs-only production; the line-number caveat at the end is honest.
- **M6** (closing source statement): PASS — closes with a Sources block listing the docs consulted.

---

### Summary:

A strong, well-structured answer that gets the entire carbon-conservation accounting chain right: the central stock-change equation `q52_emis_co2_actual` (verbatim and correctly located), the producer/consumer distinction for `vm_carbon_stock` (declared in M56, populated by the land modules + M59, read by M52 — fully consistent with the G2 anchor), the three pools, the 21 emission slots, the pricing chain through M56 into the objective, the soil-carbon convergence dynamics, and the (correct) framing that this is stock-flow accounting rather than a hard conservation law. The Chapman-Richards citation (`core/macros.gms:18`) was impressively precise. No invented variables, no fabricated equations, no wrong defaults, correct realizations throughout.

Two Minor citation imprecisions cost 2 points: (B1) `pcm_carbon_stock` cited at the `vm_carbon_stock` declaration line (34 instead of 19, same block), and (B2) the `emis_land` set's line range truncated to 332-335 instead of 332-354 — the latter inherited from the boundary doc (latent doc bug DOC1, to be fixed this session). Both are recoverable (right file, right block/set) and neither would lead a user to a wrong action. The M32 density-name choice is a sub-threshold imprecision (real upstream interface named instead of the local parameter; no false equation).

**Score = max(0, 10 - (4·0 + 2·0 + 1·2)) = 8/10. Verdict: MOSTLY ACCURATE.**
