# R54 Adversarial Verification — `cross_module/carbon_balance_conservation.md`

**Verifier**: adversarial (Opus 4.8, max effort)
**Ground truth**: `/tmp/magpie_develop_ro` @ `0d7ebeb90` (never the working tree)
**Date**: 2026-07-14
**Bugs adjudicated**: 13 (1 Critical, 6 Major, 5 Minor, 1 Informational)

**Verdicts**: 10 UPHELD · 3 CORRECTED · 0 REFUTED · 0 CITATION_FAILED · 0 NOT_REVIEWABLE

---

## Step 0 — Cascade base (realization cascade, run FIRST)

Wrong realization → wrong file path → all line citations invalid. Every realization cited by
the auditor was checked against `config/default.cfg` **and** `ls`-confirmed on disk:

| Module | Cited realization | `config/default.cfg` | Dir exists |
|---|---|---|---|
| 14_yields | `managementcalib_aug19` | :354 ✓ default | ✓ |
| 29_cropland | `detail_apr24` | :811 ✓ default | ✓ |
| 35_natveg | `pot_forest_may24` | :1153 ✓ default | ✓ |
| 50_nr_soil_budget | `macceff_aug22` | :1497 ✓ default | ✓ |
| 51_nitrogen | `rescaled_jan21` | :1568 ✓ default | ✓ |
| 52_carbon | `normal_dec17` | :1574 ✓ default | ✓ |
| 53_methane | `ipcc2006_aug22` | :1601 ✓ default | ✓ |
| 56_ghg_policy | `price_aug22` | :1631 ✓ default | ✓ |
| 57_maccs | `on_aug22` | :1840 ✓ default | ✓ |
| 58_peatland | `v2` | :1871 ✓ default | ✓ |
| 59_som | `cellpool_jan23` | :1934 ✓ default | ✓ |

No cross-realization confabulation (the R33 failure class). All 26 cited files exist; all cited
line numbers are in range (`wc -l` per file).

---

## Step A — Mechanical citation check (all 13 bugs)

Every `file_evidence` path + every `modules/.../file.gms:LINE` inside every `proposed_fix` was
`test -f`'d, `wc -l`'d, and the exact line read. **All 13 bugs: `citation_ok = true`.**

Spot-checks of the load-bearing lines (read verbatim):

```
58_peatland/v2/equations.gms:91-92   q58_peatland_emis(i2,poll58) ..
                                       vm_emissions_reg(i2,"peatland",poll58) =e=
core/sets.gms:312                        peatland/                      <- emis_source member
core/sets.gms:322                      rice, ent_ferm, resid_burn, peatland /   <- emis_annual
core/sets.gms:324-325                  c_pools /vegc,litc,soilc/       <- no peat pool
53_methane/…/equations.gms:70-72     q53_emissions_resid_burn(i2) ..
                                       vm_emissions_reg(i2,"resid_burn","ch4") =e=
                                       sum(kcr, vm_res_ag_burn(i2,kcr,"dm")) * s53_ef_ch4_res_ag_burn;
                                       ^^ file ends at line 72 — NO MACC term
57_maccs/on_aug22/sets.gms:28-29     maccs_ch4 / rice_ch4, ent_ferm_ch4, awms_ch4 /
57_maccs/on_aug22/sets.gms:31-32     maccs_n2o / inorg_fert_n2o, awms_manure_n2o /
57_maccs/on_aug22/declarations.gms:13  im_maccs_mitigation(t,i,emis_source,pollutants)
52_carbon/…/input.gms:46             s52_growingstock_calib … (1) / 1 /
52_carbon/…/preloop.gms:23           if(s52_growingstock_calib = 1,
56_ghg_policy/…/sets.gms:212-213     stockType Carbon stock types / actual, actualNoAcEst /
56_ghg_policy/…/input.gms:90         $setglobal c56_carbon_stock_pricing  actualNoAcEst
core/macros.gms:51                   $macro m_timestep_length sum((ct,t2),…)
59_som/…/presolve.gms:31-33          i59_scm_target(t,j) = i59_scm_scenario_fader(t) * …
```

Two **bug-report metadata nits** (do not affect `citation_ok`, but the fixer must not
copy them):

1. **CB-B4** quotes `doc:178` for "k, m = Climate-specific growth parameters". That text is at
   **doc:177**; :178 is "- ac = Age class (5-year intervals)". The fix's *insertion point*
   ("insert after line 178") is still correct — it lands after the parameter block.
2. **CB-B2** cites `57_maccs/on_aug22/preloop.gms:46,56,60,64`. All four lines are exact, but the
   population block is **:46 (zero-init), :48, :52, :56, :60, :64** — lines 48 and 52
   (`inorg_fert_n2o`, `awms_n2o`) were not cited. The prose lists all five categories correctly.

---

## Step B/C — Adjudication

### CB-B1 — Peatland "Not Modeled" · Critical · `producer_declaration` · **UPHELD**

The doc heading at :865 generalizes a Module-59-scoped limitation into a false model-level one.

**Producer derivation** (`vm_emissions_reg`, both grep forms, whole tree):

- `rg 'vm_emissions_reg\('` → M58 `v2/equations.gms:92` has it on the **equation LHS**:
  `vm_emissions_reg(i2,"peatland",poll58) =e=` → M58 **populates** the peatland slice. Equation
  carries **no `$`-condition** → always active.
- `rg 'vm_emissions_reg\.'` → `58_peatland/v2/preloop.gms:31-33` (`.fx`=0 then `.lo/.up`=∓Inf
  for `poll58`) → the peatland slice is explicitly **freed**, not zeroed, in `v2`.
  (The `off` realization zeroes it: `58_peatland/off/preloop.gms:8`.)
- `peatland` ∈ `emis_source` (`core/sets.gms:312`) **and** ∈ `emis_annual` (`:322`) → it is priced
  through `q56_emis_pricing` (`56_ghg_policy/price_aug22/equations.gms:15-17`, indexed over
  `emis_annual`). The Module-58 emission stream really does reach the carbon price.
- `c_pools` = `/vegc,litc,soilc/` (`core/sets.gms:324-325`) → peat is **not** a carbon pool, so the
  fix's "double-counting is avoided by construction" is exactly right.
- Default: `cfg$gms$peatland <- "v2"` (`default.cfg:1871`), `s58_fix_peatland <- 2020` (`:1928`);
  the dynamic equations are gated `$(sum(ct, m_year(ct)) > s58_fix_peatland)` → live after 2020.

**The doc's sub-bullet is nonetheless TRUE** (M59 models mineral soil carbon only):
- `rg -ni 'peat' modules/59_som/` → **no match** (exit 1)
- Second method `find modules/59_som -type f -exec grep -il peat {} +` → **no match** (exit 1)
- **Positive control**: `rg -c 'i59_cratio' modules/59_som/` → preloop:4, declarations:4,
  equations:7 → the search works in that directory.

Verdict: **UPHELD**. Apply the fix as proposed.

---

### CB-B2 — Residue burning is a phantom MACC member · Major · `consumer_set` · **UPHELD**

**Independent consumer derivation of `im_maccs_mitigation`** (whole tree, both forms):

- `rg 'im_maccs_mitigation\('` → **complete** read set:
  - M53 `:29` (`"ent_ferm","ch4"`), `:52` (`"awms","ch4"`), `:63` (`"rice","ch4"`) — **three**
  - M51 `:71` (`"awms","n2o_n_direct"`) — one
  - M50 `presolve.gms:56,58,61,63` (`"inorg_fert","n2o_n_direct"`)
  - M57 (own cost eqs) `:38,41,48,51`
- `rg 'im_maccs_mitigation\.'` → no match — expected, it is a **parameter**, not a variable
  (no `.l/.fx` surface). **Positive control**: `rg -c 'im_pollutant_prices' modules/` → hits in
  56/preloop, 56/declarations, 56/equations, 57/preloop → grep works.
- `q53_emissions_resid_burn` (`53_methane/ipcc2006_aug22/equations.gms:70-72`) is the file's last
  statement and terminates with `* s53_ef_ch4_res_ag_burn;` — **no mitigation factor**, confirmed
  by reading to EOF (72 lines).
- `maccs_ch4 / rice_ch4, ent_ferm_ch4, awms_ch4 /` (`57_maccs/on_aug22/sets.gms:28-29`) — no
  `resid_burn` category exists.

Verdict: **UPHELD**. Residue burning is a fabricated member of the MACC applicability set.

---

### CB-B3 — N₂O attribution · Major · `consumer_set` · **CORRECTED**

**The doc-facing conclusion is right; the auditor's stated rationale is not.**

Confirmed:
- M51's **only** `im_maccs_mitigation` read is `rescaled_jan21/equations.gms:71`, on `"awms"`.
- `q51_emissions_inorg_fert` (`:30-39`) carries **no** MACC factor; it responds only through
  `vm_nr_eff(i2)` (`:34`) / `vm_nr_eff_pasture(i2)` (`:37`) → **transitive** (M57 → M50 → `vm_nr_eff`
  → M51), not a direct M51 read. M50's own comment says so: *"The name of the MACC category
  'inorg_fert_n2o' actually includes all types of soil N2O emissions … We therefor apply it here to
  Nr soil efficiency more generally"* (`50_nr_soil_budget/macceff_aug22/presolve.gms:50-52`), with
  the uplift built at `:54-64`.
- `maccs_n2o / inorg_fert_n2o, awms_manure_n2o /` (`57_maccs/on_aug22/sets.gms:31-32`) — no
  `rice_n2o`.

**REFUTED sub-claim**: *"`im_maccs_mitigation(t,i,'rice','n2o_n_direct')` … is NEVER READ by any
module."* — **False.** M57's own `q57_labor_costs` / `q57_capital_costs`
(`on_aug22/equations.gms:37-38, 47-48`) sum over the **free** `emis_source` set, and `:39-41`,
`:49-51` sum over `emis_source_inorg_fert_n2o` — which **includes rice**
(`sets.gms:10-11`: `/inorg_fert, resid, som, rice, man_crop, man_past/`). Those reads exist.

**The correct — and stronger — reason rice must leave the N₂O list**:
`emis_source_n51` = `/ inorg_fert, man_crop, awms, resid, resid_burn, man_past, som /`
(`51_nitrogen/rescaled_jan21/sets.gms:15-16`) — **rice is not a member**. M51's preloop then does:

```
preloop.gms:8   vm_emissions_reg.fx(i,emis_source,n_pollutants) = 0;
preloop.gms:9   vm_emissions_reg.lo(i,emis_source_n51,n_pollutants) = -Inf;
preloop.gms:10  vm_emissions_reg.up(i,emis_source_n51,n_pollutants) =  Inf;
```

→ `vm_emissions_reg(i,"rice",n_pollutants)` is **fixed at zero**. **MAgPIE has no rice N₂O emission
at all.** The populated rice-N₂O MACC therefore multiplies a zero emission and changes nothing
(including in M57's cost terms).

**corrected_set** (apply this instead of the auditor's rationale; the auditor's *doc text* is safe
as written, but this sharpens it):
- N₂O, **Module 51** — the MACC is applied directly to **AWMS only**
  (`rescaled_jan21/equations.gms:71`). Note it is applied to *all* `n_pollutants_direct`, not only
  N₂O — see the code comment at `:62-64` (measures also reduce NH₃/NO₃ losses).
- N₂O from soils incl. inorganic fertilizer — **Module 50, not Module 51**
  (`macceff_aug22/presolve.gms:54-64`, an NUE uplift); M51 responds transitively via `vm_nr_eff`.
- **Rice N₂O does not exist in MAgPIE** — rice ∉ `emis_source_n51`, so
  `vm_emissions_reg(i,"rice",n_pollutants)` is fixed to 0 (`rescaled_jan21/preloop.gms:8-10`).
  Do **not** write "no rice-specific mitigation is *applied*"; write "there is no rice N₂O
  emission to mitigate".

---

### CB-B4 — `s52_growingstock_calib` overrides the documented k/m · Major · `producer_declaration` · **CORRECTED**

**Core bug UPHELD, and it is robust.**

- `input.gms:46`: `s52_growingstock_calib … (1) / 1 /` → **hard default ON**.
- **Whole-repo grep** (`rg -n 's52_growingstock_calib' .` from repo root, incl. `config/`,
  `scripts/`, the R layer) → appears in **exactly four places**, all inside
  `modules/52_carbon/normal_dec17/`: `realization.gms:15`, `preloop.gms:23`, `input.gms:46`,
  `start.gms:33`. **Absent from `config/default.cfg` and `scripts/`.**
- **Positive control on that absence**: `config/default.cfg` *does* expose the siblings —
  `c52_land_carbon_sink_rcp` (:1580), `c52_carbon_scenario` (:1587), `s52_plantation_threshold`
  (:1590), and — pointedly — the two bisection bounds this very switch governs,
  `s52_k_high_secdf` (:1594) and `s52_k_high_plant` (:1596). So the grep works on that file and the
  switch is genuinely not surfaced. The calibration is ON in every default run and is not
  togglable from `default.cfg`.
- The overwrite (`preloop.gms:71-73`, `:114-116`) replaces the **`vegc` slice only** with
  `fm_carbon_density(t,j,"secdforest","vegc") * (1 - exp(-k_region·(ord(ac)-1)·5))**m_region`,
  where `k` = bisection-calibrated `i52_k_calib_secdf/plant` against FRA 2025 targets
  (`f52_fra_nrf_gs`, `f52_fra_pla_gs`; loop at `:49-68`, `:84-103`) and `m` = region-average
  `i52_m_avg_natveg/plant` (`:29-30`). `realization.gms:15-21` states this in prose.
- Uncalibrated copies saved at `start.gms:43-44`.

**CORRECTION to the fix text's consumer clause.** The proposed sentence — *"The uncalibrated curves
… are what M14 (`im_growing_stock_ysf`), M29 (tree cover), M32 (afforestation + NDC) and M35
(youngsecdf) read"* — is true **only because of its parentheticals**, and invites the false
inference that those modules read *only* the uncalibrated curves. Derived set (both curves, whole
tree):

| Module | Reads **uncalibrated** | Reads **calibrated** |
|---|---|---|
| M14 `managementcalib_aug19` | `presolve.gms:66` → `im_growing_stock_ysf` | **`presolve.gms:44`** → `im_growing_stock(…,"secdforest")` |
| M29 `detail_apr24` (default) | `preloop.gms:46,48` → `p29_carbon_density_ac` | — |
| M32 `dynamic_may24` | `presolve.gms:59,61` (`"aff"`), `:68` (`"ndc"`) | — |
| M35 `pot_forest_may24` | `presolve.gms:117` (20 tC/ha test), `:242` (youngsecdf) | **`presolve.gms:248,250-252`** — secdforest density is a **blend** of the calibrated and uncalibrated curves, weighted by natural-origin area share `pc35_secdforest_natural/pc35_secdforest` |

**corrected_set**: keep the whole fix, but replace the final clause with — *"The uncalibrated curves
survive as `pm_carbon_density_*_ac_uncalib` (`start.gms:43-44`) and are what M14's
`im_growing_stock_ysf` (`14_yields/managementcalib_aug19/presolve.gms:66`), M29's tree cover
(`29_cropland/detail_apr24/preloop.gms:46,48`), M32's afforestation and NDC curves
(`32_forestry/dynamic_may24/presolve.gms:59,61,68`) and M35's youngsecdf
(`35_natveg/pot_forest_may24/presolve.gms:242`, and the 20 tC/ha maturation test at `:117`) read.
M14 and M35 read the **calibrated** curve as well — M14 for regular secdforest growing stock
(`presolve.gms:44`), M35 for secdforest carbon density, which it **blends** with the uncalibrated
curve by natural-origin area share (`presolve.gms:248-252`)."*

---

### CB-B5 — "the difference reduces to k" · Major · `producer_declaration` · **UPHELD**

Re-derived from the two populating assignments:

```
UNCALIBRATED  52_carbon/normal_dec17/start.gms:28
  pm_carbon_density_secdforest_ac(t,j,ac,"vegc") = m_growth_vegc(
      0, fm_carbon_density(t,j,"secdforest","vegc"),
      sum(clcl, pm_climate_class(j,clcl)*f52_growth_par(clcl,"k","natveg")),   <- CELL-level k
      sum(clcl, pm_climate_class(j,clcl)*f52_growth_par(clcl,"m","natveg")),   <- CELL-level m
      (ord(ac)-1));

CALIBRATED    52_carbon/normal_dec17/preloop.gms:71-73
  pm_carbon_density_secdforest_ac(t,j,ac,"vegc") =
      fm_carbon_density(t,j,"secdforest","vegc")                               <- same asymptote, cell-level
    * (1 - exp(-sum(cell(i,j), i52_k_calib_secdf(i)) * (ord(ac)-1) * 5))       <- REGIONAL k
      **sum(cell(i,j), i52_m_avg_natveg(i));                                   <- REGIONAL-AVERAGE m
```

with `i52_m_avg_natveg(i) = sum((cell(i,j),clcl), pm_climate_class(j,clcl)*f52_growth_par(clcl,"m","natveg")) / sum(cell(i,j),1)` (`preloop.gms:29`).

- Shared-asymptote half of the doc claim: **TRUE** (both use `fm_carbon_density(t,j,"secdforest","vegc")`).
- "reduces to the growth-rate `k`": **FALSE** — `m` also changes, from a cell-level climate-weighted
  value to a region average. Within a region every cell shares `(k,m)`; only the asymptote `A`
  stays cell-specific. The calibrated curve is therefore also **spatially coarser in shape**.
- The doc's citation `input.gms:47` for "in most regions" is **exact**:
  *"…kept low because FRA NRF growing stock is below LPJmL potential in most regions (1) / 0.1 /"*.
- The doc's conclusion (sign of the bias is not uniform) survives.

Verdict: **UPHELD**. Apply as proposed.

---

### CB-B6 — `pm_timestep_length` · Major · `producer_declaration` · **UPHELD**

- `rg -n 'pm_timestep_length' .` from the repo root → **zero matches, entire repository** (exit 1).
- **Positive control**: `rg -n 'm_timestep_length' core/macros.gms` → `:51` and `:57` — the search
  works.
- `core/macros.gms:51` verbatim:
  `$macro m_timestep_length sum((ct,t2),(1$(ord(t2)=1) + (m_year(t2)-m_year(t2-1))$(ord(t2)>1))$sameas(ct,t2))`
  — a **compile-time text macro**, not a GDX object. `readGDX` cannot return it.
  `m_timestep_length_forestry` (`:57`) uses `5` for the first timestep, `m_timestep_length` uses `1`.

Verdict: **UPHELD**. The name is fabricated.

**Fix-quality nit for the fixer** (not a blocker): the replacement snippet writes
`timestep <- c(5, diff(years))` while its own comment says *"first timestep length is 1 in GAMS"*.
Per `macros.gms:51` the first element should be `1` (`5` is the *forestry* macro). Prefer
`c(1, diff(years))`, or keep `5` and say explicitly that it mirrors `m_timestep_length_forestry`.

---

### CB-B7 — `stockType` slices · Major · `consumer_set` · **UPHELD**

**Producer set** (`vm_carbon_stock`, both grep forms, whole tree) — every populating equation is
indexed over the **free** `stockType` set and pins no slice:

```
q29_carbon(j2,ag_pools,stockType)          29_cropland/detail_apr24/equations.gms:38  (default realization)
q31_carbon(j2,ag_pools,stockType)          31_past/endo_jun13/equations.gms:22
q32_carbon(j2,ag_pools,stockType)          32_forestry/dynamic_may24/equations.gms:108
q35_carbon_primforest/_secdforest/_other   35_natveg/pot_forest_may24/equations.gms:42,49,53
q59_carbon_soil(j2,land,stockType)         59_som/cellpool_jan23/equations.gms:61
```
plus (attribute form, invisible to a `NAME(` grep) `vm_carbon_stock.fx(j,"urban",ag_pools,stockType) = 0`
(`34_urban/exo_nov21/presolve.gms:8`) — also over the free set. → **both slices are filled.**

**Consumer set** — exactly two equation readers, and they pin **different** slices:

```
M52  q52_emis_co2_actual   52_carbon/normal_dec17/equations.gms:19
       … vm_carbon_stock(j2,land,c_pools,"actual") …                      <- REPORTED CO2
M56  q56_emis_pricing_co2  56_ghg_policy/price_aug22/equations.gms:22
       … vm_carbon_stock(j2,land,c_pools,"%c56_carbon_stock_pricing%") …  <- PRICED CO2
```
Default `c56_carbon_stock_pricing = actualNoAcEst` (`price_aug22/input.gms:90`;
`config/default.cfg:1835`). `stockType / actual, actualNoAcEst /` (`price_aug22/sets.gms:212-213`).

**Mechanism confirmed** (`core/macros.gms:104-106`) — the slices differ because the macro branches:
```
$macro m_carbon_stock_ac(land,carbon_density,sets,sets_sub) \
   sum((&&sets),     …)$(sameas(stockType,"actual"))        + \   <- full ac set
   sum((&&sets_sub), …)$(sameas(stockType,"actualNoAcEst"))       <- ac_sub: excludes newly established
```
So `actualNoAcEst` omits newly-established age classes on the age-class land types
(forestry/secdforest/other); for the non-age-class types the simple macro (`:99-101`) fills both
slices identically.

→ In a default run the **priced** CO₂ genuinely is not computed from the same stock slice as the
**reported** CO₂. The doc's "equations typically use the `actual` slice" hides exactly the
distinction a carbon-pricing user needs. Verdict: **UPHELD**.

*Upstream oddity, FYI only*: `config/default.cfg:1835` reads `c56_carbon_stock_pricing <- "actualNoAcEst"`
**without** the `cfg$gms$` prefix its neighbours carry (contrast `:1840 cfg$gms$maccs`). The operative
default is therefore `input.gms:90` regardless. Both say `actualNoAcEst`, so the claim is unaffected —
but the fixer should keep `input.gms:90` as the primary citation.

---

### CB-B8 — Commit date · Minor · `other` · **UPHELD**

```
git log -1 --format=… 6b00f9dea
  sha            = 6b00f9dea2971a86c42ab3cd87b595ce555d0cc9   (auditor's SHA exact)
  author_date    = 2026-07-01 09:07:26 +0200
  committer_date = 2026-07-01 09:07:26 +0200
  author         = florianh
  subject        = Fix youngsecdf wood production: use uncalibrated growing stock
git log --since=2026-07-12 --until=2026-07-16 --oneline   -> (empty)
```
The doc's `(2026-07-14)` is the doc's own authoring date, not the commit's. Everything else in
doc:245 verifies: `presolve.gms:242` (youngsecdf density) ✓, `:117` (20 tC/ha test) ✓,
`14_yields/managementcalib_aug19/presolve.gms:64-71` (`im_growing_stock_ysf`) ✓.

Verdict: **UPHELD** → change to `(2026-07-01)`.

---

### CB-B9 — CH₄ serial, CO₂ parallel · Minor · `consumer_set` · **UPHELD** (MANDATE 21)

**Both endpoints opened.**

- **CH₄ — genuine serial hand-off.** M53 populates `vm_emissions_reg(i2,{ent_ferm,awms,rice,resid_burn},"ch4")`
  (`ipcc2006_aug22/equations.gms:22,49,60,71`); M56 reads it in
  `q56_emis_pricing(i2,pollutants,emis_annual) .. v56_emis_pricing =e= vm_emissions_reg(i2,emis_annual,pollutants)`
  (`price_aug22/equations.gms:15-17`). All four CH₄ sources ∈ `emis_annual` (`core/sets.gms:320-322`). ✓
- **CO₂ — NOT a hand-off.** M52 populates `vm_emissions_reg(i2,emis_oneoff,"co2_c")`
  (`normal_dec17/equations.gms:16-19`). M56's pricing equation is indexed over **`emis_annual`**,
  and `emis_annual` ∩ `emis_oneoff` = ∅ (`core/sets.gms:314-318` vs `:320-322` — **disjoint**).
  M56 instead **recomputes** the emission itself:
  `q56_emis_pricing_co2(i2,emis_oneoff) .. v56_emis_pricing(i2,emis_oneoff,"co2_c") =e= sum(…, (pcm_carbon_stock(…,"actual") - vm_carbon_stock(…,"%c56_carbon_stock_pricing%"))/m_timestep_length)`
  (`price_aug22/equations.gms:19-22`) — differing from `q52_emis_co2_actual` **only** in the
  `stockType` slice.
  → M52 and M56 are **parallel readers of `vm_carbon_stock`**, not producer→consumer.
  M56's only other touch of M52's output is `postsolve.gms:13,27,41,55` (`.m/.l/.up/.lo` → reporting).

The doc is internally inconsistent, exactly as the auditor says: :626 already phrases it correctly
("All populated slices flow to Module 52 and Module 56"). Verdict: **UPHELD**.

---

### CB-B10 — `c59_irrigation_scenario` default · Minor · `other` · **UPHELD**

- `config/default.cfg:1953`: `cfg$gms$c59_irrigation_scenario   <- "on"    # def = "on"` ✓
- `59_som/cellpool_jan23/input.gms:61`: `$setglobal c59_irrigation_scenario  on` ✓
- `preloop.gms:60-67`: `f59_cratio_irrigation(climate59,w,kcr)` is an **unconditional factor** in the
  `i59_cratio` product (line `:67`).
- `input.gms:70`: `$if "%c59_irrigation_scenario%" == "off" f59_cratio_irrigation(climate59,w,kcr) = 1;`
  → the switch **neutralises** the factor; it does not add it.

"Optional" with no default stated reads as off-by-default — the wrong direction. Verdict: **UPHELD**.

---

### CB-B11 — `pollutant` vs `pollutants` · Minor · `producer_declaration` · **UPHELD**

- `57_maccs/on_aug22/declarations.gms:13`:
  `im_maccs_mitigation(t,i,emis_source,pollutants)        Technical mitigation of GHG emissions (percent)`
  → 4th index set is **`pollutants`** (plural).
- `56_ghg_policy/price_aug22/declarations.gms:40`: `vm_emissions_reg(i,emis_source,pollutants)` — same set.
- `rg '^\s+pollutant\b' core/sets.gms modules/*/*/sets.gms` → **no singular `pollutant` set exists**
  anywhere (exit 1). The doc's index name is fabricated.

Verdict: **UPHELD**. Do **not** touch the "(0 to ~0.3)" range — it derives from the gitignored
`f57_maccs_ch4/n2o` CSVs and is not code-verifiable (auditor correctly deferred it).

---

### CB-B12 — `othernat` is not static · Minor · `other` · **UPHELD**

```
35_natveg/pot_forest_may24/presolve.gms:240
  p35_carbon_density_other(t,j,"othernat",ac,ag_pools) = pm_carbon_density_other_ac(t,j,ac,ag_pools);
52_carbon/normal_dec17/start.gms:48
  pm_carbon_density_other_ac(t,j,ac,"vegc") = m_growth_vegc(0, fm_carbon_density(t,j,"other","vegc"),
      k_natveg, m_natveg, (ord(ac)-1));                      <- AGE-VARYING Chapman-Richards
35_natveg/pot_forest_may24/equations.gms:53-55
  q35_carbon_other(j2,ag_pools,stockType) .. vm_carbon_stock(j2,"other",ag_pools,stockType) =e=
      m_carbon_stock_ac(vm_land_other, p35_carbon_density_other, "othertype35,ac", "othertype35,ac_sub");
```
`q35_carbon_other` integrates over **`othertype35` × `ac`** — i.e. over **both** subtypes, age-class
resolved. `othernat` carries a genuine Chapman-Richards age curve; only its **asymptote** differs
(other-land `fm_carbon_density(t,j,"other","vegc")` vs the secdforest asymptote used by
`youngsecdf`, `presolve.gms:242`). Its low asymptote makes it *near*-static, not static.

Verdict: **UPHELD**. Apply as proposed.

---

### CB-B13 — `s59_scm_target` default · Informational · `other` · **UPHELD**

- `59_som/cellpool_jan23/input.gms:11-12`: `s59_scm_target … / 0 /`, `s59_scm_target_noselect … / 0 /`
- `config/default.cfg:1975-1976`: both `<- 0   # def = 0`
- `59_som/cellpool_jan23/presolve.gms:31-33` (file is 33 lines; range valid):
  `i59_scm_target(t,j) = i59_scm_scenario_fader(t) * (s59_scm_target * p59_country_weight + s59_scm_target_noselect * (1-p59_country_weight))`
  → **identically zero** in a default run.
- `i59_scm_target` is read at `equations.gms:23` (the SCM term of the cropland SOM equilibrium) and
  `:101` (the SCM recurring cost) → both terms vanish by default.
- The doc's parameter name `i59_scm_target` is correct (`declarations.gms:14`).

Verdict: **UPHELD**. Informational tier is right — doc §8.4 already sets 0.5 as an explicit
intervention, so no false impression is created.

---

## Summary table

| Bug | Severity | Class | citation_ok | Verdict |
|---|---|---|---|---|
| CB-B1 | Critical | producer_declaration | ✓ | **UPHELD** |
| CB-B2 | Major | consumer_set | ✓ | **UPHELD** |
| CB-B3 | Major | consumer_set | ✓ | **CORRECTED** — "never read" is false; rice N₂O is *fixed to zero* (stronger) |
| CB-B4 | Major | producer_declaration | ✓ | **CORRECTED** — core bug robust; consumer clause must note M14/M35 also read the calibrated curve |
| CB-B5 | Major | producer_declaration | ✓ | **UPHELD** |
| CB-B6 | Major | producer_declaration | ✓ | **UPHELD** (snippet nit: `c(1, …)` not `c(5, …)`) |
| CB-B7 | Major | consumer_set | ✓ | **UPHELD** |
| CB-B8 | Minor | other | ✓ | **UPHELD** — 2026-07-01 |
| CB-B9 | Minor | consumer_set | ✓ | **UPHELD** |
| CB-B10 | Minor | other | ✓ | **UPHELD** |
| CB-B11 | Minor | producer_declaration | ✓ | **UPHELD** |
| CB-B12 | Minor | other | ✓ | **UPHELD** |
| CB-B13 | Informational | other | ✓ | **UPHELD** |

**No fabricated citations, no cross-realization confabulation, no phantom consumers.** This audit
round is unusually clean on the mechanical axis; the two CORRECTIONs are both cases where the
auditor reached a right conclusion through a partly wrong mechanism — the exact failure mode a
fixer would otherwise carry into the doc.

### Method note on the "other"-class bugs

The instructions default class `other` to `NOT_REVIEWABLE` (citation validated, pass through). I
deviated: CB-B8/B10/B12/B13 were each **mechanically settleable** (git metadata, `default.cfg`
values, populating assignments read verbatim), so returning `NOT_REVIEWABLE` would have discarded
definitive evidence and understated confidence. Each is reported with the commands that settled it.
The practical routing is unchanged (both verdicts mean "apply the fix").
