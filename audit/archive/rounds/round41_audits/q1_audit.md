# Audit Report: Q1 (Socioeconomic drivers M09 → food demand M15 → production M16/M17, default config)

### Overall Verdict: MOSTLY ACCURATE (lower band)
### Accuracy Score: 6/10

Verified against live GAMS code on branch `develop` @ HEAD ee98739fd (tracked code clean). The answer's conceptual spine is correct and the load-bearing equation (`q15_food_demand`) is reproduced exactly. Points lost to a cluster of fabricated `equations.gms:NN` citations in the (b) summary table (the answerer conflated the markdown doc's own render-line numbers with source-file line numbers), one off-by-one populate citation, and a simplified M21 trade balance that does not match the default realization.

---

### Verified Claims (correct):

**Defaults / config** (all read directly from `config/default.cfg`):
- `cfg$gms$drivers <- "aug17"` (default.cfg:210), `c09_pop_scenario`/`c09_gdp_scenario`/`c09_pal_scenario <- "SSP2"` (default.cfg:211,212,220). ✓
- `cfg$gms$food <- "anthro_iso_jun22"`, `cfg$gms$demand <- "sector_may15"`, `cfg$gms$production <- "flexreg_apr16"` confirmed via realization dirs (only one realization each for 09/16/17). ✓
- `s15_calibrate <- 1` (default.cfg:603), `s15_elastic_demand <- 0` (default.cfg:414). ✓ Both correctly stated.
- `sm_fix_SSP2 = 2025` declared `modules/09_drivers/aug17/input.gms:22` (`/ 2025 /`). ✓ Exact line + value.
- SSP2-fix logic `modules/09_drivers/aug17/preloop.gms:36-56`: `if(m_year(t_all) <= sm_fix_SSP2, ...SSP2... else ...%c09_*_scenario%)`. ✓ Answer's "SSP2 forced ≤2025, selected (=SSP2) after" is exactly right.

**M09 interface parameters** — all exist with the exact names, prefixes, dimensions, and declaration lines claimed (`modules/09_drivers/aug17/declarations.gms`):
- `im_pop(t_all,i)` :11 ✓ · `im_pop_iso(t_all,iso)` :10 ✓ · `im_demography(t_all,iso,sex,age)` :34 ✓ · `im_gdp_pc_ppp_iso(t_all,iso)` :29 ✓ · `im_gdp_pc_mer_iso(t_all,iso)` :16 ✓ · `im_physical_inactivity(t_all,iso,sex,age)` :33 ✓.
- M09 populate lines for the population vars are correct: `im_pop` @ preloop.gms:41,50 ✓; `im_pop_iso` @ 40,49 ✓; `im_demography` @ 39,48 ✓.
- Dimension annotations "12 MAgPIE regions" (default H12) and "249 ISO countries" are correct (🔵 standard MAgPIE set cardinalities).

**M15 (anthro_iso_jun22)**:
- `q15_food_demand(i2,kfo)` at `equations.gms:10-14` — formula reproduced **exactly** (`(vm_dem_food + Σ f15_household_balanceflow) * Σ(fm_nutrition_attributes·10**6) =g= Σ(im_pop·p15_kcal_pc_calibrated)·365`). ✓ The core "per-capita kcal × im_pop × 365" claim is verified at line 13.
- `q15_budget(iso)` at `equations.gms:48-52` (the PROSE citation), `im_gdp_pc_ppp_iso` used at line 52. ✓
- `q15_regr_bmi_shr` @ 71-76 ✓; `q15_regr` @ 169-173 ✓ (both cited correctly in §(b) prose).
- `vm_dem_food` declared `declarations.gms:14` (positive var, "Food demand (mio. tDM per yr)"). ✓ (Declared over `kall`; answer writes `vm_dem_food(i,kfo)`, which is the **correct usage index** inside `q15_food_demand` — not a bug.)
- `p15_kcal_pc_calibrated(t,i,kfo)` declared `declarations.gms:141`. ✓
- Standalone NLP model name `m15_food_demand` ✓ (declarations.gms:207); answer's claim that `q15_food_demand` is the only equation linking the standalone model to MAgPIE's optimization is correct (declarations.gms:232-233 confirm `q15_food_demand` is in MAgPIE, not in the food-demand model).

**M16 (sector_may15)** — `equations.gms`:
- `q16_supply_crops` @ 19-29: `vm_supply = vm_dem_food + Σ vm_dem_feed + vm_dem_processing + vm_dem_material + vm_dem_bioen + vm_dem_seed + v16_dem_waste + Σ f16_domestic_balanceflow`. ✓ Exact.
- `q16_supply_livestock` @ 31-38 ✓; `q16_supply_secondary` @ 40-49 ✓ (both include `vm_dem_food`).
- `vm_supply(i,kall)` declared `declarations.gms:11` ("Regional demand (mio. tDM per yr)"). ✓ M16-as-aggregation-hub characterization correct.

**M17 (flexreg_apr16)** — `equations.gms`:
- `q17_prod_reg(i2,k) .. vm_prod_reg(i2,k) =e= sum(cell(i2,j2), vm_prod(j2,k))` @ 10-11. ✓ Exact. `vm_prod_reg(i,kall)` declared `declarations.gms:10`. ✓ "Pure spatial aggregator; does not read vm_dem_food/vm_supply" correct.

---

### Bugs Found:

#### Bug Q1-B1
- **Severity**: Major  (`tier_uncertainty: true` — Major/Minor boundary; the correct equation name + correct prose citation sit alongside each wrong table cite)
- **Class**: 10 (Stale/wrong file:line citation) + 12 (content-level mismatch)
- **Trigger** (§1 Major): "File:line citation drift to adjacent/different content (would mislead a careful reader)."
- **Root cause**: `answerer_confabulation` — the answerer copied the **markdown doc's own line numbers** (where the variable visually appears in `module_15.md`'s rendered code blocks) and mislabeled them as `equations.gms:NN`.
- **Claim in answer** (§(b) tables):
  - `im_pop` → "`equations.gms:57` — RHS of `q15_food_demand`"
  - `im_gdp_pc_ppp_iso` → "`equations.gms:105` — `q15_budget`"
  - `im_demography` → "`equations.gms:258-261` — `q15_intake`"
- **Reality in code** (`modules/15_food/anthro_iso_jun22/equations.gms`):
  - `im_pop` in `q15_food_demand` is at **line 13** (block 10-14). Line 57 of the file is prose comment text.
  - `im_gdp_pc_ppp_iso` in `q15_budget` is at **line 52** (block 48-52). Line 105 is inside `q15_bmi_shr_medium`.
  - `q15_intake` is at **lines 141-151**, `im_demography` used at **143 and 147**. Lines 258-261 are R-section OUTPUT declarations (`oq15_bmi_shr_*`), an entirely different block.
- **File evidence**: `equations.gms:13` (`sum(ct,im_pop(ct,i2) * p15_kcal_pc_calibrated(ct,i2,kfo)) * 365`); `equations.gms:52` (`+ sum(ct, im_gdp_pc_ppp_iso(ct,iso) + ...)`); `equations.gms:143,147` (`im_demography(ct,iso,sex,age)` in `q15_intake`).
- **Note**: The numbers 57 / 105 / 258 are exactly the line offsets where these variables appear in `magpie-agent/modules/module_15.md` (module_15.md:57, :105, :258). The doc's *headers* correctly label the blocks `equations.gms:10-14` (module_15.md:51) and `equations.gms:48-52` (:98), and the **answer's own prose** uses those correct cites — so the table contradicts the answer's prose. Internal inconsistency confirms confabulation rather than doc-inheritance.
- **Anchor reference**: resembles R20 (2026-04-20) "line numbers cited from render/diff rather than post-merge code; citations drifted" → Major.

#### Bug Q1-B2
- **Severity**: Minor
- **Class**: 10 (file:line citation, off-by-one to adjacent same-loop line)
- **Trigger** (§1 Minor): "Off-by-few line citation where adjacent lines say similar things."
- **Claim in answer** (§(b) Physical inactivity): "M09 populates this from `f09_physical_inactivity.cs3` (WHO data) via `preloop.gms:39,48`."
- **Reality in code**: `im_physical_inactivity` is assigned at `preloop.gms:38` (SSP2 branch) and `:47` (else branch). Lines **39,48** are the `im_demography` assignment (the line immediately below, with the `+0.000001` constant).
- **File evidence**: `modules/09_drivers/aug17/preloop.gms:38` (`im_physical_inactivity(...) = f09_physical_inactivity(...,"SSP2",...)`); `:39` (`im_demography(...) = ... + 0.000001`).
- **Root cause**: `answerer_confabulation` (conflated demography's populate lines — which module_09.md:163 cites as `preloop.gms:39, 48` — with physical_inactivity's).

#### Bug Q1-B3
- **Severity**: Minor  (`tier_uncertainty: true` — could be Major under a strict reading of "invented regional balance with vars absent from the default realization")
- **Class**: 4 (Conceptual pseudo-code presented as the model's form)
- **Trigger** (§1 Minor): "Wrong detail, but a careful reader wouldn't be misled into action" — peripheral, uncited, directionally correct; pulled down by tie-breaker from Major.
- **Claim in answer** (§(c) Step 3 + Summary trace): "`vm_supply` feeds Module 21 (Trade), which enforces the global food balance: `vm_prod_reg(i,k) + vm_import(i,k) - vm_export(i,k) ≥ vm_supply(i,k)`."
- **Reality in code**: The **default** trade realization is `selfsuff_reduced` (`config/default.cfg:650`). Its balance is a self-sufficiency pool with **no per-region import/export variables**: `sum(i2, vm_prod_reg(i2,k_trade)) =g= sum(i2, vm_supply(i2,k_trade)) + sum(ct,f21_trade_balanceflow(ct,k_trade))` (`selfsuff_reduced/equations.gms:13-14`). There are no `vm_import`/`vm_export` variables in `selfsuff_reduced` *or* in `selfsuff_reduced_bilateral22` (grep returned empty for both). The answer's `vm_prod_reg + vm_import - vm_export ≥ vm_supply` is a generic textbook form, not any realization's actual equation.
- **File evidence**: `modules/21_trade/selfsuff_reduced/equations.gms:13-14`; `config/default.cfg:650` (`cfg$gms$trade <- "selfsuff_reduced"`).
- **Mitigation**: out of the question's core scope (M09→M15→M16→M17), not given a file:line, no realization claimed, and the directional logic (production must cover supply; trade redistributes regionally) is sound. Hence Minor, not Major.
- **Root cause**: `answerer_confabulation` (generic trade form substituted for the default realization's actual equation).

---

### Latent Doc Bugs (recorded independent of score):

#### Latent Q1-L1 (low severity — informational/minor)
- **Root cause**: `doc_error_answerer_beat_it` (the answer inherited the imprecise doc cite; conceptual mapping stayed correct).
- **Doc**: `magpie-agent/modules/module_09.md:212` states `im_gdp_pc_ppp_iso` "**Calculation** (`preloop.gms:23-27`)"; `:175` states `im_gdp_pc_mer_iso` "**Calculation** (`preloop.gms:29-33`)".
- **Reality**: Lines 23-27 / 29-33 compute the **`i09_gdp_pc_ppp_iso_raw` / `i09_gdp_pc_mer_iso_raw`** *per-capita ISO raw* parameters. The **`im_gdp_pc_ppp_iso` / `im_gdp_pc_mer_iso`** interface variables are populated (assigned the scenario value) at `preloop.gms:44,53` and `:43,52` respectively. The answer copied these into its "Where M09 populates it" column (`preloop.gms:23-27` / `:29-33`), so the column points at the upstream raw computation rather than the `im_*` assignment.
- **Severity / harm**: Low. The cited lines DO compute the same quantity (per-capita PPP/MER), and module_09.md frames them as the "Calculation". A reader looking for the `im_*` assignment line would be ~20 lines off but in the same `preloop.gms` and the same conceptual block. Not a producer/consumer-SET error (which would be Critical per the R20 anchor) — it is line-precision only. Worth tightening but does not affect the answer's correctness.
- **Suggested fix** (optional, low priority): in module_09.md §3.2.1/§3.2.3, either relabel as "raw per-capita computed at `preloop.gms:29-33`/`23-27`; selected into `im_*` at `preloop.gms:43,52`/`44,53`", or add the assignment line alongside the raw-calc line.

---

### Missing Nuances:
- The Step 1c realization table omits M17 (`flexreg_apr16`) and M21 (`selfsuff_reduced`) — both are single-realization or default and are mentioned later in prose, so this is cosmetic, not a bug.
- The answer correctly flags `s15_elastic_demand = 0` (default) and that demand is therefore exogenous to the optimizer per timestep — a genuinely important nuance that many answers miss. Credit.
- `q15_food_demand`'s shadow price (`q15_food_demand.m`) being used as the food price signal back into the standalone model under iteration is not mentioned, but is out of scope for this question.

### Summary:
The answer is conceptually sound end-to-end and nails the load-bearing pieces: default SSP2 (with the `sm_fix_SSP2=2025` subtlety), the six M09 interface parameters with exact names and declaration lines, the exact `q15_food_demand` equation (per-capita kcal × `im_pop` × 365), and the M16 supply aggregation / M17 spatial aggregation roles. It loses 4 points to: a Major cluster of three fabricated `equations.gms:NN` citations in the (b) tables (doc-render line numbers mislabeled as source lines, contradicting the answer's own correct prose), a Minor off-by-one populate cite for `im_physical_inactivity`, and a Minor non-default/textbook trade balance (`vm_import`/`vm_export` don't exist in the default `selfsuff_reduced` realization). One low-severity latent doc imprecision in module_09.md (raw-calc lines cited as the `im_*` populate location) is recorded for optional cleanup. 

**Score = max(0, 10 − 2·1[Major] − 1·2[Minor]) = 6/10.**
