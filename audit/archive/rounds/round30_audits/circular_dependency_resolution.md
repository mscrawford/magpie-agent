# Audit Report: R30 — Circular Dependency Resolution (Land/Carbon, M10↔M56)

**Question (anchored on `cross_module/circular_dependency_resolution.md`)**: Give one concrete circular dependency between MAgPIE modules and explain the exact within-timestep resolution mechanism.

**Ground truth**: `/tmp/magpie_develop_ro` (develop worktree), `config/default.cfg`.

---

### Overall Verdict: SIGNIFICANT ERRORS (lower band of Mostly-Accurate thesis, dragged by two Major supporting-detail errors)
### Accuracy Score: 5/10

The answer's **central thesis is correct and well-supported**: the land/carbon loop is broken within a timestep because `pcm_carbon_stock` is a *parameter* (frozen from t-1), while only `vm_carbon_stock` is free; the feedback operates across timesteps via the postsolve update. That spine is verified against code. The score is pulled down by two Major errors in the supporting detail — a G2-class producer/consumer mis-attribution and a code-block that misrenders the postsolve assignment's index sets — plus one Minor cost-chain shortcut.

---

### Verified Claims (correct)

- **Realizations** (M8): `landmatrix_dec18` (M10), `normal_dec17` (M52), `price_aug22` (M56) are each the sole realization and match `config/default.cfg`. ✓ (`default.cfg`: `cfg$gms$land`, `cfg$gms$carbon`, `cfg$gms$ghg_policy`.)
- **`q56_emis_pricing_co2` snippet** — matches code verbatim: `modules/56_ghg_policy/price_aug22/equations.gms:19-22`. Citation `equations.gms:19-22` is exact. ✓
- **`q10_land_area` snippet** — matches code verbatim: `modules/10_land/landmatrix_dec18/equations.gms:13-15`. Citation exact. ✓
- **Loop-breaker thesis**: `pcm_carbon_stock` IS a parameter (`price_aug22/declarations.gms:19`, in the `parameters` block); `vm_carbon_stock` IS a `positive variable` (`declarations.gms:34`). The within-timestep asymmetry (constant − variable)/timestep is correctly characterized. ✓ This is the heart of the question and it is right.
- **`vm_land` ownership**: declared in M10 (`landmatrix_dec18/declarations.gms:19`); the `land` set has exactly **7** members (`crop, past, forestry, primforest, secdforest, urban, other`, `core/sets.gms:251`). "Seven land pools" ✓.
- **`im_pollutant_prices` loaded in preloop** ✓ (`price_aug22/preloop.gms:37-43`, exogenous trajectory).
- **M10 postsolve** `pcm_land(j,land) = vm_land.l(j,land)` — present at `landmatrix_dec18/postsolve.gms:9`. ✓
- **Cost reaches the objective via M11** ✓ — `vm_emission_costs(i2)` enters `q11_cost_reg` (`11_costs/default/equations.gms:26`) → `vm_cost_glo` (`q11_cost_glo`, line 10).
- **Module-doc citations** the answer leaned on are accurate: `module_56.md:82-85` (renders `q56_emis_pricing_co2` correctly), `module_10.md:36,39` (`q10_land_area` at `equations.gms:13-15`).
- **Type 1 (Temporal Feedback)** classification matches `circular_dependency_resolution.md` §2.1. ✓
- `c56_carbon_stock_pricing` default = `actualNoAcEst` (the answer used the `%...%` macro faithfully; did not misstate a default). ✓

---

### Bugs Found

**Bug R30-B1**
- **Severity**: Major
- **Class**: 15 (latent-doc-class manifesting in the answer) / producer-consumer mis-attribution (cf. G2 anchor)
- **Trigger**: "Wrong variable prefix / module attribution that misleads about behavior" (Major). Considered Critical via the R20/G2 producer-consumer anchor; **tie-breaker pulls to Major** because the central mechanism is correct and the question is about resolution, not carbon-stock provenance.
- **Claim in answer**: data-flow box — "Module 10 `vm_land` → **Module 52 calculates `vm_carbon_stock`**"; variable table — "`vm_carbon_stock(...)` | variable | Current carbon stocks **(Module 52**, consumed by 56)".
- **Reality in code**: `vm_carbon_stock` is DECLARED in **Module 56** (`price_aug22/declarations.gms:34`), POPULATED (LHS of `=e=`) by **M29, M31, M32, M35, M59** (`29_cropland/{simple,detail}_apr24/equations.gms`, `31_past/endo_jun13/equations.gms:23`, `32_forestry/dynamic_may24/equations.gms:108`, `35_natveg/pot_forest_may24/equations.gms:43-54`, `59_som/{cellpool_jan23,static_jan19}/equations.gms`). **M52 only READS it** via `q52_emis_co2_actual` (`52_carbon/normal_dec17/equations.gms:16-19`). Confirmed twice: M52 `declarations.gms` has no `vm_carbon_stock` (positive control: `q52_emis_co2_actual` found at line 30).
- **File evidence**: `modules/56_ghg_policy/price_aug22/declarations.gms:34`; `modules/52_carbon/normal_dec17/equations.gms:16-19`.
- **Anchor reference**: G2 carbon-stock propagation anchor (`flywheel_rubric.md` §1.5, §6). This is the exact "M52 calculates vm_carbon_stock" misconception the G2 regression guards.

**Bug R30-B2**
- **Severity**: Major
- **Class**: 12 (content-level citation mismatch) + 4 (formula/code rendered inexactly, presented as code)
- **Trigger**: "Citation points at content materially different from what's at the cited line" (Major).
- **Claim in answer**: a fenced GAMS block, introduced as "Module 56's `postsolve.gms` runs:", citing `postsolve.gms:8`:
  ```gams
  pcm_carbon_stock(j,land,c_pools) = vm_carbon_stock.l(j,land,c_pools);
  ```
- **Reality in code** (`price_aug22/postsolve.gms:8`):
  ```gams
  pcm_carbon_stock(j,land,ag_pools,stockType) = vm_carbon_stock.l(j,land,ag_pools,stockType);
  ```
  Two material discrepancies: (a) **`ag_pools` not `c_pools`** — `ag_pools(c_pools) = /vegc, litc/` (above-ground only, `price_aug22/sets.gms:209`); the M56 postsolve does NOT update `soilc`. The `soilc` pool's `pcm_carbon_stock` is set in `59_som/cellpool_jan23/preloop.gms:30-35` (preloop, static across timesteps in the default som realization) — NOT in this line. (b) The **`stockType` 4th dimension is dropped**. Copying the answer's version into the model would over-write soilc (which M59 owns) and fail to compile on the dimension mismatch.
- **File evidence**: `modules/56_ghg_policy/price_aug22/postsolve.gms:8`; `modules/56_ghg_policy/price_aug22/sets.gms:209` (`ag_pools` definition); `modules/59_som/cellpool_jan23/preloop.gms:30-35` (soilc init).
- **Note**: This is a faithful reproduction of a doc error (see latent doc bug L1) — root cause `doc_error_answerer_beat_it` is too generous since the answer reproduced it; classified `doc_error` (answerer inherited the doc's wrong rendering).

**Bug R30-B3**
- **Severity**: Minor
- **Class**: 17-adjacent (one-hop shortcut in a flow diagram)
- **Trigger**: "Wrong detail, but a careful reader wouldn't be misled into action" (Minor).
- **Claim in answer**: data-flow box — "Module 56 `v56_emission_cost` → Module 11 aggregates into `vm_cost_glo`".
- **Reality in code**: M11 reads **`vm_emission_costs(i)`** (the regional aggregate produced by `q56_emission_costs`, `equations.gms:56-58`), NOT the per-source intermediate `v56_emission_cost`; and it routes through `v11_cost_reg` (`q11_cost_reg:26`) before `vm_cost_glo` (`q11_cost_glo:10`). The answer's own variable table lists the chain correctly (`v56_emission_cost` = per-source cost; `vm_cost_glo` = objective), so the diagram is a shortcut, not a contradiction.
- **File evidence**: `modules/11_costs/default/equations.gms:10,26`; `modules/56_ghg_policy/price_aug22/equations.gms:56-58`.

---

### Latent Doc Bugs (recorded regardless of answer score — `cross_module/circular_dependency_resolution.md`)

**L1 (Critical by future-reader harm)** — lines **110-111**. The "Code Evidence" block:
```gams
* Module 52, postsolve.gms:
pcm_carbon_stock(j,land,c_pools) = vm_carbon_stock.l(j,land,c_pools);
```
attributes the postsolve update to **Module 52** (it is **Module 56**, `price_aug22/postsolve.gms:8`) AND renders the index sets as `c_pools` (no `stockType`) when code uses `ag_pools,stockType`. A future reader trusting this would (a) look in the wrong module for the lag update and (b) copy a statement that mis-handles soilc and fails to compile. This is the source of answer Bug B2; the answer corrected the module attribution but inherited the set/dimension error. Root cause: `doc_error`.

**L2 (Major)** — lines **96-99** (Type-1 diagram) and **110**: the doc uses the variable name **`pcm_carbon_density`**, which **does not exist** anywhere in the code (confirmed: zero hits; positive control `fm_carbon_density` present in `price_aug22/preloop.gms`). The real lagged variable is `pcm_carbon_stock`. Invented variable name in a doc. The answer beat this (used `pcm_carbon_stock` throughout). Root cause: `doc_error_answerer_beat_it`.

**L3 (Minor)** — Appendix A, lines **967-968**: `pcm_carbon_stock(j,land,c_pools,stockType)` updated in `modules/56_ghg_policy/price_aug22/postsolve.gms:8` — module (56) and file:line (postsolve.gms:8) are **correct here**, but the pool set should be `ag_pools` (the postsolve updates only above-ground pools). 4-dim arity correct; set name imprecise. Root cause: `doc_error`.

**Note on doc structural quality**: `circular_dependency_resolution.md` opens with the "26 circular dependencies" framing (Executive Summary, §8.2) where 22 of 26 are explicitly "Inferred"/"Suspected" and "not fully documented" — the answer wisely did NOT lean on that count. Section 3.4's `vm_carbon_stock(j,"forestry","vegc","actual")` is attributed to "[56]" in the chain diagram (line 382) — same M52-vs-M56 confusion family as L1, but the answer did not cite §3.4. Not separately scored; flagged for the doc-fix pass.

---

### Missing Nuances
- The answer never states `soilc` is handled separately (M59, static in default `cellpool_jan23`); the postsolve lag it describes covers only above-ground pools. This is the root of B2 and would have been the precise version of the mechanism.
- `c56_carbon_stock_pricing` default (`actualNoAcEst`) is not stated; the macro form is faithful but a reader can't tell which `stockType` slice is priced by default.

---

### Summary
Central mechanism (lagged-parameter loop break + cross-timestep postsolve feedback) is **correct and verified**. Two Major supporting-detail errors — the G2-class "M52 calculates vm_carbon_stock" mis-attribution (B1) and the postsolve code-block with wrong index sets `c_pools`/missing `stockType` (B2) — plus a Minor cost-chain shortcut (B3). Both Majors trace to errors in the anchoring doc (`circular_dependency_resolution.md` L1-L3), which should be fixed this session: correct the M52→M56 postsolve attribution, replace `c_pools`→`ag_pools,stockType` in the code block, and eliminate the non-existent `pcm_carbon_density` name. Score: 10 − 2 − 2 − 1 = **5/10**.
