# Anchor answer — R54-youngsecdf

**Question:** How does MAgPIE make young secondary forest (`youngsecdf`) wood yield consistent with its carbon, and what changed in July 2026? Cite the interface parameter and its consumer.

**Mode:** documentation-only (no raw `.gms` code read this session). Every file:line below is copied verbatim from the cited magpie-agent doc, not independently re-verified against current code this session — treat as 🟡 *Documented*, not 🟢 *Verified*, per the AGENT.md epistemic hierarchy. Doc sync/verification dates are given so staleness can be judged.

---

## 1. Direct answer

MAgPIE keeps `youngsecdf` wood yield and carbon consistent by deriving **both from the same Module‑52 growth curve** — `pm_carbon_density_secdforest_ac_uncalib(t,j,ac,"vegc")`, the **uncalibrated** secondary-forest carbon curve (declared `modules/52_carbon/normal_dec17/declarations.gms:10`; snapshotted pre-calibration at `modules/52_carbon/normal_dec17/start.gms:43`).

- **Carbon side (Module 35):** `p35_carbon_density_other(t,j,"youngsecdf",ac,ag_pools)` is set from this uncalibrated curve at `modules/35_natveg/pot_forest_may24/presolve.gms:241-242`.
- **Wood-yield side (Module 14 → Module 35), fixed July 2026:** Module 14 now computes a dedicated interface parameter, **`im_growing_stock_ysf(t,j,ac)`**, from the *same* uncalibrated curve, and Module 35's `q35_prod_other` equation was repointed to read it for the `youngsecdf` harvest term.

Source: `cross_module/carbon_balance_conservation.md:246-251` — "**youngsecdf must stay on ONE growth curve — wood yield AND carbon**" and "**The invariant worth carrying forward:** whenever a land pool's yield and its carbon are both derived from growth curves, the harvest term and the carbon term must be driven by the same curve — otherwise harvest becomes a carbon-accounting arbitrage."

---

## 2. The interface parameter — `im_growing_stock_ysf(t,j,ac)`

Per `modules/module_14.md` §4.2 ("Young Secondary Forest on Other Land (`youngsecdf`)", doc lines 500-518) and §7.1 (doc lines 730-738):

- **Declared:** `modules/14_yields/managementcalib_aug19/declarations.gms:18`
- **Computed:** `modules/14_yields/managementcalib_aug19/presolve.gms:64-71`
- **Clamped:** `modules/14_yields/managementcalib_aug19/presolve.gms:80-81` (same two clamps as `im_growing_stock`: positivity floor at 0.0001, and zeroed below `s14_minimum_growing_stock` — restated separately because `im_growing_stock_ysf` is a distinct symbol, not reached by the `im_growing_stock(...,land_timber)` clamp)
- **Formula** (module_14.md:505-511):
  ```gams
  im_growing_stock_ysf(t,j,ac) =
      (
       pm_carbon_density_secdforest_ac_uncalib(t,j,ac,"vegc")
       / sm_carbon_fraction
       * fm_aboveground_fraction("secdforest")
       / sum(clcl, pm_climate_class(j,clcl) * fm_ipcc_bef(clcl))
      );
  ```
- **Not a `land_timber` slice.** `land_timber` = `/ forestry, primforest, secdforest, other /` (`core/sets.gms:256-257`, as cited by module_14.md:516) and does not contain `youngsecdf`; `youngsecdf` lives in the Module-35-local set `othertype35` (`/ othernat, youngsecdf /`). So the new growing stock had to be a **standalone parameter** `(t,j,ac)`, dimensionally distinct from `im_growing_stock(t,j,ac,land_timber)`, not a fifth slice of it.
- **Renamed context:** `im_growing_stock` itself (the `land_timber`-keyed parameter) was renamed from *pm_timber_yield* on 2026-04-20 (PR #869, `75d7ee167`) — flux → stock. `im_growing_stock_ysf` is a **new, second** parameter added later, not part of that rename.

---

## 3. The consumer — `q35_prod_other` (Module 35), sole consumer model-wide

Per `modules/module_35.md` §6.6 (doc lines 511-552) and §9/glossary (doc line 914):

- **Equation:** `q35_prod_other`, declared `modules/35_natveg/pot_forest_may24/equations.gms:162-168`; the `youngsecdf` term specifically is at `equations.gms:166`.
  ```gams
  sum(kforestry, vm_prod_natveg(j2,"other",kforestry))
  =e=
  (sum(ac_sub, v35_hvarea_other(j2,"othernat",ac_sub) * sum(ct, im_growing_stock(ct,j2,ac_sub,"other")))
  + sum(ac_sub, v35_hvarea_other(j2,"youngsecdf",ac_sub) * sum(ct, im_growing_stock_ysf(ct,j2,ac_sub))))
  / m_timestep_length_forestry;
  ```
- The two `othertype35` subtypes read **two different Module-14 parameters**: `othernat` reads the `"other"` slice of `im_growing_stock`; `youngsecdf` reads the separate `im_growing_stock_ysf`.
- **Explicitly stated as the sole consumer**, both directions:
  - module_14.md:732 — "Provided to: Module 35 (Natural Vegetation): the `youngsecdf` term of `q35_prod_other` **only** (`equations.gms:166`) — this is its **sole consumer** in the model."
  - module_35.md:914 — "Read **only** by the `youngsecdf` term of `q35_prod_other` (`equations.gms:166`). M35 is its sole consumer in the model."
- Confirmed by omission: `modules/module_32.md` and `modules/module_32_notes.md` contain **zero** matches for `youngsecdf` or `im_growing_stock_ysf` (checked this session) — Module 32 is not a consumer of this parameter, even though it *is* a separate consumer of the underlying `pm_carbon_density_secdforest_ac_uncalib` curve for afforestation/NDC carbon (module_14.md:773).

**Producer→consumer chain:** M52 (`pm_carbon_density_secdforest_ac_uncalib`) → M14 (`im_growing_stock_ysf`, `presolve.gms:64-71`) → M35 (`q35_prod_other`, `equations.gms:166`).

---

## 4. What changed in July 2026

**MAgPIE commit `6b00f9dea`**, "Fix youngsecdf wood production: use uncalibrated growing stock."

- **Before:** the `youngsecdf` term of `q35_prod_other` read `im_growing_stock(ct,j2,ac_sub,"secdforest")` — the **FRA-2025-calibrated** curve (via `s52_growingstock_calib = 1`, the hard-coded default). youngsecdf's *carbon*, meanwhile, already read the **uncalibrated** curve. Wood yield and carbon were driven by two different growth curves.
- **After:** the term reads the new `im_growing_stock_ysf`, sourced from the same uncalibrated curve as carbon. Yield and carbon now move together.
- **Stated motivation** (commit message, quoted at module_35.md:514): the mismatch "let the optimiser evade land-CO2 caps/prices by relocating wood harvest onto youngsecdf, booking almost no carbon for secondary-forest-level wood volumes." I.e. a carbon-accounting arbitrage channel, material under land-CO2 pricing or AFOLU caps; the change is **ungated** (no switch controls it).

### 4.1 A dating nuance worth flagging

Two different July-2026-adjacent dates appear in the docs and should not be conflated:
- `cross_module/carbon_balance_conservation.md:247` gives the **commit** date explicitly: "since MAgPIE commit `6b00f9dea` (**2026-07-01**)."
- `modules/module_14.md:730` and `modules/module_35.md:914` instead label the parameter "added **2026-07-14**" — this is the **magpie-agent documentation sync** date (sync commit `0d7ebeb90`, per `audit/BACKLOG.md`'s "2026-07-14 — develop sync (`6304d830b..0d7ebeb90`)" entry and both modules' "Last Verified: 2026-07-14" footers), reused as shorthand in the glossary entries. The underlying model fix landed in develop on 2026-07-01; the agent's documentation caught up to it two weeks later, on 2026-07-14.

### 4.2 The mismatch had a two-step history — only the yield side moved in July

Reading `modules/module_35.md` §5.1 (doc lines 125, 344-356) against its own change-log footer (doc line 1180, "2026-05-16 sync to commit `c7731e234`") shows the "why it exists" framing in module_14.md:404 ("youngsecdf carbon **has always been** read from the uncalibrated curve") is only true *since* an earlier, separate commit:

- **2026-04-20, commit `c7731e234`** ("secondary forest split by origin"): this is what first set `p35_carbon_density_other(...,"youngsecdf",...)` from the uncalibrated curve (module_35.md:356 — "is **now also** set from `pm_carbon_density_secdforest_ac_uncalib` (**previously the calibrated curve**)"), and switched the 20 tC/ha maturation test the same way (module_35.md:125). This is what *created* the latent mismatch, since wood yield was not touched at the same time.
- **2026-07-01, commit `6b00f9dea`**: closed the mismatch by moving wood yield onto the same (already-uncalibrated-since-April) curve via `im_growing_stock_ysf`.

So "what changed in July 2026" is precisely: **the wood-yield side caught up to a carbon-side change that had already been in place since April 2026.**

### 4.3 The documentation itself had also been wrong

Per `audit/BACKLOG.md` (line 12): before this sync, `module_35.md` had been documenting an equation that no longer existed, and stated the *bug* as if it were the design rationale ("youngsecdf uses secdforest growing stock since it has timber characteristics closer to secondary forest"). That framing was corrected in the same 2026-07-14 doc sync alongside the code-behavior update.

---

## 5. Mandatory caveat — do not assert a universal direction for the pre-fix bias

`modules/module_35.md:516` (⚠️, verbatim, condensed):

> "Do not assume the pre-fix bias pointed the same way everywhere. Both curves share an asymptote, so calibrated-vs-uncalibrated reduces to the growth-rate parameter `k`, and the FRA calibration (`modules/52_carbon/normal_dec17/preloop.gms:23-73`) adjusts `k` **upward in some regions and downward in others** — the M52 code comment at `input.gms:47` says FRA growing stock is below LPJmL potential 'in most regions', not all. Where calibration *raises* `k`, pre-fix youngsecdf yield was too high (the carbon-cheap-wood channel). Where it *lowers* `k`, the pre-fix yield was too **low** — possibly clamped to zero by `s14_minimum_growing_stock` — and the fix *increases* youngsecdf wood supply there. So 'the fix reduces other-land harvest' is **not** a safe global prediction."

`cross_module/carbon_balance_conservation.md:254` states the same caveat as item 1 of "Two caveats, so this is not over-applied," adding that the calibration also replaces the cell-level `m` with a region-average `m` (`i52_m_avg_natveg`), so the calibrated curve is spatially coarser in shape, not just differently scaled.

**A correct answer must name `im_growing_stock_ysf` and must NOT claim the pre-fix bias always went one way** (e.g. must not assert wood yield was *always* overstated relative to carbon) — this is stated as an explicit grading criterion in `audit/archive/rounds/round54_design.md` Stage 3 ("The youngsecdf coupling — must name `im_growing_stock_ysf`, must NOT claim a universal direction for the pre-fix bias").

---

## 6. Adjacent open leads (unverified — do not assert as fact)

Both recorded in `audit/BACKLOG.md` and `cross_module/carbon_balance_conservation.md:253-255` as leads from a 2026-07-14 adversarial audit, **not confirmed by a run**:

- **Lead A:** whether an analogous yield/carbon curve mismatch is *still* live for `secdforest` proper — `q35_prod_secdforest` reads the purely calibrated `im_growing_stock(...,"secdforest")`, while `q35_carbon_secdforest` reads `p35_carbon_density_secdforest`, a **blend** of calibrated and uncalibrated weighted by natural-origin area share (`presolve.gms:248-252`). Natural-origin area is bound against harvest (`presolve.gms:177-180`), which mitigates but may not close the gap, since the blend is an age-class average. Explicitly flagged as algebraically derived, not run-confirmed.
- **Lead B:** whether `module_35.md`'s rationale for the natural-origin feature (that FRA calibration produces a *suppressed* growth rate) has the calibration direction backwards for most regions — a numerical claim, explicitly marked unresolved and not to be adjudicated by reading prose.

Neither lead is asserted as an established defect anywhere in the corpus; both are out of scope for a direct answer to this question beyond flagging their existence.

---

## 7. Sources (all 🟡 Documented, read this session)

| Doc | What it supplied |
|---|---|
| `modules/module_14.md` (doc lines 398-544, 700-780, 1230-1250, 1430-1450, 1570) | `im_growing_stock_ysf` declaration/formula/clamps/glossary; producer chain from M52; "why it exists" note |
| `modules/module_35.md` (doc lines 9, 125-127, 340-356, 495-552, 905-916, 1177-1180) | `q35_prod_other` equation + youngsecdf term; carbon-density presolve citation; the region-direction caveat; §5.1 change history (dates the April 2026 carbon-side switch) |
| `cross_module/carbon_balance_conservation.md` (lines 160-260, 470-495) | The "one growth curve" invariant; both numbered caveats; commit date `2026-07-01` for `6b00f9dea` |
| `audit/BACKLOG.md` (lines 1-19) | Doc-sync provenance (`6304d830b..0d7ebeb90`, 2026-07-14); the pre-fix documentation-bug note; both open leads |
| `audit/archive/rounds/round54_design.md` (lines 71-75, 88-98) | The grading criteria this anchor answers to (Lead A/B framing; Stage-3 QA requirement on `im_growing_stock_ysf` + non-universal bias direction) |

**Not consulted for this answer** (out of scope / not needed): `modules/module_32.md`, `modules/module_32_notes.md` (checked only to confirm they do *not* mention `youngsecdf`), raw `.gms` source (excluded by task instructions).
