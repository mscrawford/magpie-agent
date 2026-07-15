# R54 doc audit — `cross_module/carbon_balance_conservation.md`

**Auditor**: Opus (adversarial doc audit)
**Date**: 2026-07-14
**Ground truth**: `/tmp/magpie_develop_ro` @ `0d7ebeb90` (develop, matches working-tree HEAD)
**Config**: `/tmp/magpie_develop_ro/config/default.cfg`
**Claims checked**: 88 load-bearing, code-checkable claims
**Verdict**: **SIGNIFICANT ERRORS** — 1 Critical, 6 Major, 5 Minor, 1 Informational

---

## 0. Method notes (grep discipline)

The known `grep -r` unreliability **reproduced** in this session and is worth recording:

```
$ grep -n "cfg\$gms\$carbon" /tmp/magpie_develop_ro/config/default.cfg
(no output)
$ rg -n 'cfg\$gms\$(carbon|som|natveg|...)' /tmp/magpie_develop_ro/config/default.cfg
1574:cfg$gms$carbon <- "normal_dec17"   ...   (12 matches)
```

Plain `grep` returned **empty** on a file with 391 `cfg$gms` lines. Every absence claim below was
therefore made with `rg`, cross-checked with a second method, and backed by a **positive control**
(a known-present sibling token in the same directory). Both `NAME(` and `NAME.` forms were grepped
per MANDATE 20.

---

## 1. Verified-correct claims (the doc is right about a lot)

| Doc claim | Evidence |
|---|---|
| `c_pools` = vegc, litc, soilc; `core/sets.gms:324-325` | ✅ exact |
| `emis_oneoff` at `core/sets.gms:314-318`; 21 sources = 7 land × 3 pools | ✅ exact (counted 21) |
| `emis_land` map at `core/sets.gms:332-354`; `crop_vegc . (crop) . (vegc)` | ✅ exact |
| `q52_emis_co2_actual` at `modules/52_carbon/normal_dec17/equations.gms:16-19`, formula verbatim | ✅ exact |
| Chapman-Richards macro `core/macros.gms:18` = `S + (A-S)*(1-exp(-k*(ac*5)))**m` | ✅ exact |
| Plantation vegc growth `start.gms:17`; secdforest vegc growth `start.gms:28` | ✅ exact |
| Litter 20-yr linear IPCC convergence `start.gms:19-20,30-31` | ✅ exact |
| A (asymptote) for **plantations** = `fm_carbon_density(...,"secdforest","vegc")` | ✅ exact (subtle, doc got it right) |
| `vm_carbon_stock(j,land,c_pools,stockType)` DECLARED `56_ghg_policy/price_aug22/declarations.gms:34` | ✅ exact |
| **Populator set** = M29 (crop), M31 (past), M32 (forestry), M34 (urban, `.fx`=0), M35 (prim/secd/other), M59 (soilc) | ✅ **complete, no phantoms, no omissions** |
| M34 `vm_carbon_stock.fx(j,"urban",ag_pools,stockType)=0` at `34_urban/exo_nov21/presolve.gms:8` | ✅ exact |
| `q29_carbon` at `29_cropland/detail_apr24/equations.gms:39` (block 38-42) | ✅ |
| `q59_som_target_cropland` `59_som/cellpool_jan23/equations.gms:20-27`; **all 4 terms** correct incl. `i59_cratio_treecover` un-indexed | ✅ exact |
| `q59_som_pool` `equations.gms:46-52`; `q59_carbon_soil` `equations.gms:61-64` | ✅ exact |
| `i59_lossrate = 1-0.85**m_yeardiff(t)`, `preloop.gms:45`; table 15/56/80/96 % | ✅ arithmetic re-derived |
| `i59_subsoilc_density` derived from `fm_carbon_density(...,"other","soilc")`, `preloop.gms:12` | ✅ exact |
| Pasture/managed-forest soil-C invariance, `59_som/cellpool_jan23/realization.gms:21-24` | ✅ exact |
| Default tillage = full, default input = medium (`preloop.gms:52-55`) | ✅ exact |
| M59 receives: `vm_area`←M30, `vm_fallow`←M29, `vm_treecover`←M29, `vm_land`←M10, `vm_lu_transitions`←M10 | ✅ all declarations confirmed |
| M59 provides: `vm_nr_som`→M51 (`51_nitrogen/rescaled_jan21/equations.gms:58`), `vm_cost_scm`→M11 (`11_costs/default/equations.gms:37`) | ✅ exact |
| M53 four CH₄ sources = ent_ferm, awms, rice, resid_burn (4 equations) | ✅ exact |
| M53 receives `vm_feed_intake`←M70, `vm_area`("rice_pro")←M30, `im_maccs_mitigation`←M57 | ✅ exact |
| `vm_maccs_costs(i,factors)` declared M57, consumed M11 (`equations.gms:28`) | ✅ exact |
| MACCs do **NOT** affect M52 LUC CO₂ | ✅ (M52 has zero `im_maccs_mitigation` refs) |
| `pm_climate_class(j,clcl)` from Module 45 (`45_climate/static/input.gms:10`) | ✅ exact |
| `othertype35 / othernat, youngsecdf /` (`35_natveg/pot_forest_may24/sets.gms:23-24`) | ✅ exact |
| Urban soilc = other-land soilc (`52_carbon/normal_dec17/input.gms:35`) | ✅ exact |
| `vm_emissions_reg` unit "(Tg per yr)"; `vm_carbon_stock` unit "(mio. tC)" | ✅ exact |
| §7.5 "All populated slices flow to Module 52 **and** Module 56" | ✅ correct **parallel** phrasing (MANDATE 21 clean) |
| Default realizations: carbon=`normal_dec17`, som=`cellpool_jan23`, natveg=`pot_forest_may24`, cropland=`detail_apr24`, forestry=`dynamic_may24`, urban=`exo_nov21`, past=`endo_jun13`, ghg_policy=`price_aug22`, methane=`ipcc2006_aug22`, maccs=`on_aug22` | ✅ all match `default.cfg` |

---

## 2. LEAD A — verdict, split by decidability (as mandated)

### 2a. STRUCTURAL half → **CONFIRMED** (not refuted)

I defaulted to refuting it. It survived. Every link is mechanically verified in current develop:

| # | Link | Evidence |
|---|---|---|
| 1 | `q35_prod_secdforest` reads `im_growing_stock(ct,j2,ac_sub,"secdforest")` | `modules/35_natveg/pot_forest_may24/equations.gms:147` (block 144-147) |
| 2 | `im_growing_stock(t,j,ac,"secdforest")` is built from `pm_carbon_density_secdforest_ac` (the **post-calibration** parameter) | `modules/14_yields/managementcalib_aug19/presolve.gms:42-49` |
| 3 | `pm_carbon_density_secdforest_ac(...,"vegc")` is **overwritten** by the FRA-2025 bisection-calibrated curve | `modules/52_carbon/normal_dec17/preloop.gms:71-73`, gated by `s52_growingstock_calib` |
| 4 | `s52_growingstock_calib` default = **1**, and is **NOT overridable from `config/default.cfg`** | `modules/52_carbon/normal_dec17/input.gms:46` (`/ 1 /`); `rg 's52_growingstock_calib' /tmp/magpie_develop_ro` → only M52's own 4 files. Positive control: `s52_k_high_secdf` IS in default.cfg (1 hit) |
| 5 | `q35_carbon_secdforest` reads `p35_carbon_density_secdforest` | `modules/35_natveg/pot_forest_may24/equations.gms:51` (block 49-51) |
| 6 | `p35_carbon_density_secdforest` is a natural-origin-share-weighted **blend** of calibrated + uncalibrated, **per age class** | `modules/35_natveg/pot_forest_may24/presolve.gms:248-252` |
| 7 | Natural-origin area is bounded against harvest | `modules/35_natveg/pot_forest_may24/presolve.gms:177-180` (`v35_secdforest.lo >= pc35_secdforest_natural`) |

So: **the yield term is driven by the purely-calibrated curve; the carbon term by an age-class blend.**
Because the blend weights are per-`ac` (`pc35_secdforest_natural(j,ac) / pc35_secdforest(j,ac)`), a
marginal harvest drawn from the *non-natural* portion of a **mixed-origin** age class still books the
**blended** (age-class-average) density while yielding the **calibrated** growing stock. The `.lo` bound
protects the natural *area* from being cut; it does **not** make the *density* used in `q35_carbon_secdforest`
origin-specific. The structural asymmetry is real. The doc's caveat-2 text describing this is **accurate**.

### 2b. MATERIALITY → **NO VERDICT** (refused; requires a model run)

Whether the residual gap is material depends on two run-time quantities I cannot obtain from source:
1. the per-region magnitude of `|k_calib − k_uncalib|` **and** `|m_avg_region − m_cell|` (the FRA target
   CSVs `f52_fra_nrf_gs.cs4` and `f52_growth_par.csv` are gitignored inputs, not in the repo); and
2. the equilibrium natural-origin share **in the age classes where harvest is actually marginal**
   (`pc35_secdforest_natural / pc35_secdforest` is endogenous to the run).

**Exact experiment that would settle it:**
> Run default MAgPIE to a `fulldata.gdx`. For every `(j, ac_sub)` with `ov35_hvarea_secdforest.l > 0`,
> compute (a) `im_growing_stock(t,j,ac,"secdforest")` — the wood actually credited — and (b) the growing
> stock *implied by the carbon booked*, i.e. push `p35_carbon_density_secdforest(t,j,ac,"vegc")` through the
> **same** conversion chain used at `14_yields/managementcalib_aug19/presolve.gms:42-49`
> (`÷ sm_carbon_fraction × fm_aboveground_fraction("secdforest") ÷ BEF`). The per-cell arbitrage is
> `(a)/(b) − 1`; weight by `ov35_hvarea_secdforest.l` for the aggregate. A second run with
> `s52_growingstock_calib = 0` bounds the effect (the blend collapses to one curve, so the gap → 0).
> If the harvest-weighted mean of `(a)/(b) − 1` is within solver noise, the lead is immaterial.

### 2c. Layers I did **NOT** check (enumerated by name, as mandated)

1. **`pcm_carbon_stock` postsolve carry-forward** — I verified the *slice owners* (`56_ghg_policy/price_aug22/postsolve.gms:8` for `ag_pools`; `59_som/cellpool_jan23/postsolve.gms:13` for `soilc`) but did **not** trace whether the timestep-to-timestep carry-forward re-introduces or cancels the calibrated/uncalibrated mismatch.
2. **M56 pricing scope — `f56_emis_policy.csv` / `c56_emis_policy`** — I did not open the policy CSV. I therefore cannot state which `(emis_source × pollutant)` combos are actually priced in a default run, i.e. whether `secdforest_vegc` CO₂ is priced at all.
3. **The magpie4 reporting layer** — `reportEmissions`, `reportCarbonStocks`, `reportGrowingStock` were not read; whether the reported numbers re-derive or re-aggregate these quantities is unchecked.
4. **The R preprocessing layer** — `lpj_carbon_stocks.cs3`, `f52_growth_par.csv`, `f52_fra_nrf_gs.cs4`, `f52_fra_pla_gs.cs4` are gitignored run-time products; their numeric content is unchecked.
5. **Module 28 (`im_forest_ageclass` / GFAD)** — feeds the secdforest bisection (`52_carbon/normal_dec17/preloop.gms:53-59`); not audited.
6. **M32's `p32_carbon_density_ac` for the `"plant"` type** — I confirmed only that the `"aff"` and `"ndc"` types read the `_uncalib` curves (`32_forestry/dynamic_may24/presolve.gms:59,61,68`).

**Do not treat 2a as licence to assert materiality.** The derivation is compelling; that is precisely why it
needs the run.

### 2d. The doc's OWN new §3.6 text — verified

| Doc claim (line) | Verdict |
|---|---|
| youngsecdf carbon density ← `pm_carbon_density_secdforest_ac_uncalib`, `35_natveg/pot_forest_may24/presolve.gms:242` (245) | ✅ **exact** |
| youngsecdf 20 tC/ha maturation test at `presolve.gms:117` (245) | ✅ **exact** |
| youngsecdf wood yield via new `im_growing_stock_ysf`, `14_yields/managementcalib_aug19/presolve.gms:64-71` (245) | ✅ **exact** |
| Pre-fix, youngsecdf yield came from `im_growing_stock(...,"secdforest")` (247) | ✅ **exact** — `git show 6b00f9dea` diff: `- ... im_growing_stock(ct,j2,ac_sub,"secdforest")` → `+ ... im_growing_stock_ysf(ct,j2,ac_sub)` |
| Author's motivation: "booking almost no carbon for secondary-forest-level wood volumes", evading land-CO₂ caps/prices (247) | ✅ **verbatim** from the commit message |
| Commit SHA `6b00f9dea` (245) | ✅ = `6b00f9dea2971a86c42ab3cd87b595ce555d0cc9` |
| Commit **date 2026-07-14** (245) | ❌ **WRONG** → actual `2026-07-01` (author == committer date). See **B7**. |
| Caveat 1: "Both curves share an asymptote" (252) | ✅ both use `fm_carbon_density(t,j,"secdforest","vegc")` |
| Caveat 1: "…so the difference reduces to the growth-rate `k`" (252) | ❌ **WRONG** — `m` also differs. See **B4**. |
| Caveat 1: `input.gms:47` says FRA stock below LPJmL potential "in most regions" (252) | ✅ **exact** citation + content |
| Caveat 2 (the whole secdforest lead) (253) | ✅ **structurally confirmed** — see §2a |

---

## 3. Bugs found

### 🔴 B1 — CRITICAL — "Peatland Carbon Not Modeled"

- **Doc**: `carbon_balance_conservation.md:865-868`
- **Class**: 15 (latent doc error) / false-negative existence claim
- **Trigger**: §1 Critical — *"Claimed a function/variable/file does not exist when it does (false-negative honest disclaim)."*
- **Claim**: `**7. Peatland Carbon Not Modeled**: … **Implication**: Peatland drainage/restoration not accurately represented`
- **Reality**: MAgPIE has **Module 58 (peatland)**, default realization **`v2`** (`config/default.cfg:1871`), which
  models intact / degraded / rewetted peatland, drainage driven by managed-land change, **rewetting**
  (`q58_rewetting_exo`), peat extraction, and peatland GHG emissions, and writes them straight into the
  emissions interface: `vm_emissions_reg(i2,"peatland",poll58)`. `peatland` is a member of `emis_source`
  and `emis_annual` (`core/sets.gms:312,322`). `s58_fix_peatland = 2020` (default) → peatland dynamics
  are **live for every timestep after 2020** in a default run.
- **Evidence**:
  - `modules/58_peatland/v2/equations.gms:91-92` — `q58_peatland_emis(i2,poll58) .. vm_emissions_reg(i2,"peatland",poll58) =e= …`
  - `modules/58_peatland/v2/equations.gms:65` — `q58_rewetting_exo(...)`
  - `modules/58_peatland/v2/realization.gms:8-17` — Humpenöder et al. 2020 methodology, GPM 2.0 map, IPCC-2013/Wilson-2016/Tiemeyer-2020 emission factors
  - `config/default.cfg:1871` — `cfg$gms$peatland <- "v2"   # def = v2`
  - `config/default.cfg:1928` — `cfg$gms$s58_fix_peatland <- 2020`
- **Verify cmds**:
  - `ls /tmp/magpie_develop_ro/modules/58_peatland/` → `input  module.gms  off  v2`
  - `rg -n 'cfg\$gms\$peatland' config/default.cfg` → `1871:cfg$gms$peatland  <- "v2"`
  - `rg -n 'vm_emissions_reg' modules/58_peatland/v2/equations.gms` → `92: vm_emissions_reg(i2,"peatland",poll58) =e=`
  - `rg -in 'peat' modules/59_som/cellpool_jan23/` → **NOMATCH** (positive control: `soilc` = 6 hits) — so the *sub-bullet* about M59 is true
- **What IS true**: the sub-bullet "Module 59 uses mineral soil carbon dynamics" is correct — M59 has **zero** peat
  references. The error is the **heading** and the **implication**, which generalize an M59-scoped limitation
  into a false model-level one.
- **Harm**: this is the cross-module carbon hub. A reader concludes MAgPIE cannot do peatland scenarios and
  either abandons the model for that work or rebuilds Module 58 from scratch. "Build on a false foundation."
- **Fix**: replace lines 865-868 with:
  ```
  **7. Peatland Carbon Is Outside the Module-59 Soil Pool** (not outside MAgPIE):
  - Module 59 models **mineral** soil carbon only (IPCC 2019 mineral-soil stock-change factors); it contains
    no peat representation, so `vm_carbon_stock(...,"soilc",...)` does **not** carry peat carbon.
  - Peatlands ARE modelled, in **Module 58 (`peatland`, default realization `v2` —
    `config/default.cfg:1871`)**: intact / degraded / rewetted peatland areas, drainage driven by managed-land
    change, rewetting, and peat extraction, with GHG emission factors (Humpenöder et al. 2020;
    `modules/58_peatland/v2/realization.gms:8-17`). Peatland emissions enter the emissions interface directly
    via `q58_peatland_emis` → `vm_emissions_reg(i,"peatland",poll58)`
    (`modules/58_peatland/v2/equations.gms:91-92`), as an `emis_annual` source (`core/sets.gms:322`) — **not**
    through the `vm_carbon_stock` stock-change path of §4.1.
  - Default `s58_fix_peatland = 2020` (`config/default.cfg:1928`): peatland area is held at historic levels
    up to 2020 and is dynamic thereafter.
  - **Implication**: peatland carbon must be read from the Module-58 emission stream, not from the
    carbon-balance stock accounting documented here. Double-counting is avoided by construction (peat is not
    in `c_pools`).
  ```

---

### 🟠 B2 — MAJOR — MACCs claimed to mitigate residue-burning CH₄ (phantom)

- **Doc**: `carbon_balance_conservation.md:592`
- **Class**: 6 / 15 (fabricated member of an applicability set)
- **Trigger**: §1 Major — *"Fabricated count for a set/parameter/realization list."*
- **Claim**: `- CH₄ from enteric fermentation, AWMS, rice, residue burning (Module 53)`
- **Reality**: `q53_emissions_resid_burn` has **no** `im_maccs_mitigation` factor. The other three CH₄
  equations all end in `* (1-sum(ct, im_maccs_mitigation(ct,i2,…,"ch4")))`; residue burning does not.
  M57's CH₄ MACC category set is `maccs_ch4 / rice_ch4, ent_ferm_ch4, awms_ch4 /` — **three** categories,
  no resid_burn. `im_maccs_mitigation` is zero-initialised (`57_maccs/on_aug22/preloop.gms:46`) and then
  populated only for `inorg_fert_n2o`, `awms_n2o`, `rice_ch4`, `ent_ferm_ch4`, `awms_ch4`.
- **Evidence**:
  - `modules/53_methane/ipcc2006_aug22/equations.gms:70-72` — resid_burn, **no** MACC term
  - `modules/53_methane/ipcc2006_aug22/equations.gms:29, 52, 63` — the only three MACC applications
  - `modules/57_maccs/on_aug22/sets.gms:28-29` — `maccs_ch4 / rice_ch4, ent_ferm_ch4, awms_ch4 /`
  - `modules/57_maccs/on_aug22/preloop.gms:46,56,60,64` — population sites
- **Verify cmds** (confirmed twice + positive control):
  - `rg -n 'im_maccs_mitigation' modules/53_methane/ipcc2006_aug22/equations.gms` → lines **29, 52, 63** only
  - `rg -c 'im_maccs_mitigation' …/equations.gms` → **3** (positive control: the token IS greppable there)
  - `rg -n 'resid_burn' modules/53_methane/ipcc2006_aug22/` → equations.gms:70,71 carry no MACC
- **Fix**: see the combined replacement in **B3**.

---

### 🟠 B3 — MAJOR — N₂O MACC application attributed to the wrong module (+ phantom rice N₂O)

- **Doc**: `carbon_balance_conservation.md:593`
- **Class**: 15 + MANDATE 17 (direct vs transitive) + MANDATE 18 (module attribution)
- **Trigger**: §1 Major — *"Fabricated count for a set/parameter/realization list"* (first firing trigger).
- **Claim**: `- N₂O from fertilizer, manure, rice (Module 51)`
- **Reality**: Module 51 applies `im_maccs_mitigation` to **exactly one** source — AWMS (manure):
  `q51_emissionbal_awms` (`51_nitrogen/rescaled_jan21/equations.gms:71`). It is the **only**
  `im_maccs_mitigation` hit in all of M51.
  - **Fertilizer / soil N₂O** MACC is applied in **Module 50** (`50_nr_soil_budget/macceff_aug22/presolve.gms:56-63`),
    where it raises nitrogen-use efficiency; M51's `q51_emissions_inorg_fert`
    (`equations.gms:30-39`) has **no** MACC term and responds only through `vm_nr_eff`. That is a
    **transitive** path (M57 → M50 → `vm_nr_eff` → M51), not a direct M51 read. M50's own comment says so:
    *"The name of the MACC category 'inorg_fert_n2o' actually includes all types of soil N2O emissions …
    We therefor apply it here to Nr soil efficiency more generally"* (`presolve.gms:50-52`).
  - **Rice N₂O**: `im_maccs_mitigation(t,i,"rice","n2o_n_direct")` is *populated* (rice is a member of
    `emis_source_inorg_fert_n2o`, `57_maccs/on_aug22/sets.gms:10-11`) but is **never read by any module** —
    no rice-specific N₂O mitigation is applied anywhere.
- **Evidence**:
  - `modules/51_nitrogen/rescaled_jan21/equations.gms:71` — the sole M51 MACC read (`"awms"`)
  - `modules/51_nitrogen/rescaled_jan21/equations.gms:30-39` — `q51_emissions_inorg_fert`, no MACC
  - `modules/50_nr_soil_budget/macceff_aug22/presolve.gms:50-63` — the fertilizer/soil-N₂O MACC application
  - `modules/57_maccs/on_aug22/sets.gms:31-32` — `maccs_n2o / inorg_fert_n2o, awms_manure_n2o /` (no rice_n2o)
- **Verify cmd**: `rg -ln 'im_maccs_mitigation' modules/` → only `50_nr_soil_budget/macceff_aug22/presolve.gms`,
  `51_nitrogen/rescaled_jan21/equations.gms`, `53_methane/ipcc2006_aug22/equations.gms`, `57_maccs/on_aug22/*`
  (+ two `not_used.txt`). **Module 52 absent → the doc's "does NOT affect M52" claim is correct.**
- **Fix** (replaces doc lines 591-593, covering **B2** and **B3**):
  ```
  **Applies to** (verified against code — the mitigation factor `(1 - im_maccs_mitigation)` appears in exactly
  these equations):
  - **CH₄, Module 53** — enteric fermentation (`modules/53_methane/ipcc2006_aug22/equations.gms:29`),
    AWMS (`:52`), rice (`:63`). **NOT residue burning**: `q53_emissions_resid_burn` (`:70-72`) has no
    mitigation term, and M57's CH₄ category set is `maccs_ch4 / rice_ch4, ent_ferm_ch4, awms_ch4 /`
    (`modules/57_maccs/on_aug22/sets.gms:28-29`).
  - **N₂O, Module 51** — AWMS / manure only (`modules/51_nitrogen/rescaled_jan21/equations.gms:71`).
  - **N₂O from soils (incl. inorganic fertilizer), Module 50 — not Module 51.** The `inorg_fert_n2o` MACC is
    applied in `modules/50_nr_soil_budget/macceff_aug22/presolve.gms:56-63` as an uplift to nitrogen-use
    efficiency; M51's `q51_emissions_inorg_fert` (`equations.gms:30-39`) carries no MACC factor and responds
    only transitively via `vm_nr_eff`. There is **no** rice-specific N₂O mitigation applied anywhere.
  ```

---

### 🟠 B4 — MAJOR — FRA growing-stock calibration (default ON) omitted; `f52_growth_par` k/m presented as operative

- **Doc**: `carbon_balance_conservation.md:469` (also `:174-178`, `:211`, `:462`, `:511`, `:923-926`)
- **Class**: 4 / 13 (mechanism described as operative when a default-ON switch overrides it)
- **Trigger**: §1 Major — *"Missing default-state caveat"* (mirror case: a default-**ON** mechanism that
  overrides the described one is entirely absent from the doc).
- **Claim**: `**Effective Parameters** (Module 52, modules/52_carbon/normal_dec17/start.gms:17): k_eff = Σ(climate_class) climate_share × k(climate_class); m_eff = Σ(climate_class) climate_share × m(climate_class)`
  — and `:178` `k, m = Climate-specific growth parameters (from f52_growth_par.csv)`.
- **Reality**: `start.gms:17/28` compute exactly that — and then **`preloop.gms` overwrites the `"vegc"` slice
  of both `pm_carbon_density_secdforest_ac` and `pm_carbon_density_plantation_ac`** with curves whose
  - `k` = a **regional, bisection-calibrated** value fitted to FAO **FRA 2025** growing-stock targets
    (`i52_k_calib_secdf(i)` / `i52_k_calib_plant(i)`), and
  - `m` = the **region-average** `i52_m_avg_natveg(i)` / `i52_m_avg_plant(i)` — **not** the cell-level
    `Σ(clcl) climate_share × m(clcl)`.

  This runs whenever `s52_growingstock_calib = 1`, which is the **hard default** (`input.gms:46`, `/ 1 /`) and
  is **not exposed in `config/default.cfg`** — i.e. it is ON in every default run. The `f52_growth_par` k/m
  survive only in the `_uncalib` copies (`start.gms:43-44`), which are what M14 (`im_growing_stock_ysf`),
  M29 (treecover), M32 (afforestation + NDC) and M35 (youngsecdf) read.
- **Evidence**:
  - `modules/52_carbon/normal_dec17/preloop.gms:71-73` (secdforest overwrite), `:114-116` (plantation overwrite)
  - `modules/52_carbon/normal_dec17/preloop.gms:23` — `if(s52_growingstock_calib = 1,`
  - `modules/52_carbon/normal_dec17/input.gms:46` — `s52_growingstock_calib … (1) / 1 /`
  - `modules/52_carbon/normal_dec17/preloop.gms:29-30` — `i52_m_avg_natveg(i) = Σ(cell,clcl) … / Σ(cell) 1`
  - `modules/52_carbon/normal_dec17/realization.gms:15-21` — the model's own description of the calibration
- **Verify cmd**: `rg -n 's52_growingstock_calib' /tmp/magpie_develop_ro` → 4 hits, **all inside M52**;
  none in `config/`. Positive control: `rg -c 's52_k_high_secdf' config/default.cfg` → **1**.
- **Harm**: a user wanting to change forest growth rates edits `f52_growth_par.csv` (what the doc points at)
  and finds the main secdforest/plantation carbon curves barely move — the wrong lever. Also internally
  inconsistent: §3.6 *does* discuss calibrated-vs-uncalibrated, while §3.3/§3.5/§6 never mention calibration.
- **Fix**: after line 178 (§3.3 Parameters) and after line 475 (§6.2), insert:
  ```
  ⚠️ **The `f52_growth_par` k/m are only the STARTING curve.** With `s52_growingstock_calib = 1` — the
  hard default (`modules/52_carbon/normal_dec17/input.gms:46`; **not** exposed in `config/default.cfg`, so it
  is ON in every default run) — Module 52's preloop **overwrites the `vegc` slice** of
  `pm_carbon_density_secdforest_ac` (`normal_dec17/preloop.gms:71-73`) and
  `pm_carbon_density_plantation_ac` (`:114-116`) with curves whose `k` is calibrated **per region by
  bisection** to FAO **FRA 2025** growing-stock targets (`i52_k_calib_secdf` / `i52_k_calib_plant`) and whose
  `m` is the **region-average** (`i52_m_avg_natveg` / `i52_m_avg_plant`, `:29-30`) — not the cell-level
  climate-weighted `m`. The asymptote `A` is unchanged (`fm_carbon_density(t,j,"secdforest","vegc")`).
  The uncalibrated curves survive as `pm_carbon_density_*_ac_uncalib` (`start.gms:43-44`) and are what
  M14 (`im_growing_stock_ysf`), M29 (tree cover), M32 (afforestation + NDC) and M35 (youngsecdf) read.
  ```

---

### 🟠 B5 — MAJOR — Caveat 1: "the difference reduces to the growth-rate `k`" (it does not — `m` also differs)

- **Doc**: `carbon_balance_conservation.md:252`
- **Class**: 4 (conceptual claim contradicted by code)
- **Trigger**: §1 Major — *"The claim is wrong in a way that misleads about behavior."*
- **Claim**: `Both curves share an asymptote, so the difference reduces to the growth-rate k, and the FRA calibration raises k in some regions and lowers it in others`
- **Reality**: the shared-asymptote half is **true**. The "reduces to `k`" half is **false**: the calibrated
  curve also swaps the **shape parameter `m`** from a **cell-level** climate-weighted value to a
  **region-average** one.
  - uncalibrated (`start.gms:28`): `m = sum(clcl, pm_climate_class(j,clcl) * f52_growth_par(clcl,"m","natveg"))` — **per cell `j`**
  - calibrated (`preloop.gms:73`): `m = sum(cell(i,j), i52_m_avg_natveg(i))` where
    `i52_m_avg_natveg(i) = Σ(cell(i,j),clcl) pm_climate_class·f52_growth_par(m) / Σ(cell(i,j)) 1` (`preloop.gms:29`) — **regional mean**

  So the calibrated curve is also **spatially coarser in shape**: within a region, every cell gets the same
  `(k, m)` and only the asymptote `A` stays cell-specific. The doc's *conclusion* (sign of the pre-fix bias is
  not uniform) survives — indeed it is strengthened — but the stated mechanism is wrong, and a reader
  reconstructing one curve from the other by swapping `k` alone would get the wrong answer.
- **Evidence**: `modules/52_carbon/normal_dec17/start.gms:28` vs `modules/52_carbon/normal_dec17/preloop.gms:29-30, 71-73`
- **Verify cmd**: read both blocks; diff the 3rd and 4th `m_growth_vegc` arguments against the calibrated
  `(1-exp(-k…))**m` expression.
- **Fix**: replace the first sentence of caveat 1 (line 252) with:
  ```
  1. **The sign of the pre-fix bias is not uniform.** Both curves share the same asymptote
     (`fm_carbon_density(t,j,"secdforest","vegc")`), so the difference lives entirely in the growth
     parameters — **both of them**: the FRA calibration replaces the cell-level `k` with a region-level
     bisection-calibrated `k`, **and** the cell-level `m` with the region-average `i52_m_avg_natveg`
     (`modules/52_carbon/normal_dec17/preloop.gms:29-30, 71-73`), so the calibrated curve is also spatially
     coarser in shape. The FRA calibration raises `k` in some regions and lowers it in others
     (`modules/52_carbon/normal_dec17/input.gms:47` says FRA stock is below LPJmL potential "in most regions"
     — not all). Where `k` is lowered, the pre-fix yield was too *low*, and the fix *increases* youngsecdf
     wood supply. Do not assume the fix reduces other-land harvest globally.
  ```

---

### 🟠 B6 — MAJOR — `pm_timestep_length` does not exist (hallucinated `pm_*` name)

- **Doc**: `carbon_balance_conservation.md:762`
- **Class**: 2 (hallucinated variable name)
- **Trigger**: §1 Critical trigger *"Invented variable name presented as authoritative"* technically fires
  — but the **tie-breaker** (§1, "when between two tiers pick the lower") applies and the Critical
  *definition* (high-stakes wrong action) does not: the name appears only inside an illustrative R
  verification snippet, and the failure mode is a loud, self-correcting `readGDX` error. Scored **Major**
  (`tier_uncertainty: true`).
- **Claim**: `timestep <- readGDX(gdx, "pm_timestep_length")  # or calculate from years`
- **Reality**: **no such parameter exists anywhere in MAgPIE.** Timestep length is a compile-time GAMS
  **macro**, `m_timestep_length` (`core/macros.gms:51`), plus `m_timestep_length_forestry` (`:57`). Macros are
  text substitutions — they are not GDX objects and cannot be read with `readGDX`.
- **Evidence**: `core/macros.gms:51` — `$macro m_timestep_length sum((ct,t2),(1$(ord(t2)=1) + (m_year(t2)-m_year(t2-1))$(ord(t2)>1))$sameas(ct,t2))`
- **Verify cmds**:
  - `rg -n 'pm_timestep|im_timestep|p_timestep' core/ modules/` → **NOMATCH**
  - positive control: `rg -c 'm_timestep_length' core/macros.gms` → **2**
  - (all other GDX objects in the §9 snippets check out: `pcm_carbon_stock`, `ov_carbon_stock`,
    `ov_emissions_reg`, `ov59_som_pool`, `ov59_som_target`, `ov32_land`, `pm_carbon_density_plantation_ac`)
- **Fix**: replace line 762 with:
  ```r
  # Timestep length is a GAMS macro (m_timestep_length, core/macros.gms:51), NOT a GDX parameter.
  # Derive it from the time set instead:
  years    <- getYears(carbon_stock_curr, as.integer = TRUE)
  timestep <- c(5, diff(years))   # first timestep length is 1 in GAMS; adjust if ord(t)=1 matters
  ```

---

### 🟠 B7 — MAJOR — `stockType`: the default GHG-pricing slice is `actualNoAcEst`, not `actual`

- **Doc**: `carbon_balance_conservation.md:101`
- **Class**: 13 (wrong/omitted default) + 12 (content-level mismatch)
- **Trigger**: §1 Major — *"Missing default-state caveat"* / misleads about behavior.
- **Claim**: `equations typically use the "actual" slice of stockType`
- **Reality**: `stockType / actual, actualNoAcEst /` (`56_ghg_policy/price_aug22/sets.gms:212-213`).
  - The **populating** equations (`q29_carbon`, `q31_carbon`, `q32_carbon`, `q35_carbon_*`, `q59_carbon_soil`)
    are indexed over the **free** `stockType` set — they pin no slice, they fill **both**.
  - `q52_emis_co2_actual` reads the `"actual"` slice (`52_carbon/normal_dec17/equations.gms:19`) — this is the
    **reported/accounted** CO₂.
  - `q56_emis_pricing_co2` reads `"%c56_carbon_stock_pricing%"` (`56_ghg_policy/price_aug22/equations.gms:22`),
    whose default is **`actualNoAcEst`** (`56_ghg_policy/price_aug22/input.gms:90`;
    `config/default.cfg:1835`) — this is the **priced** CO₂.

  So in a default run the CO₂ that is **priced** is computed from a **different** carbon-stock slice than the
  CO₂ that is **reported**. The doc's "typically … actual" hides exactly the distinction a carbon-pricing user
  needs.
- **Evidence**: `modules/56_ghg_policy/price_aug22/sets.gms:212-213`, `input.gms:90`, `equations.gms:22`;
  `config/default.cfg:1835`
- **Verify cmd**: `rg -n 'c56_carbon_stock_pricing' modules/56_ghg_policy/price_aug22/input.gms config/default.cfg`
  → `input.gms:90:$setglobal c56_carbon_stock_pricing  actualNoAcEst` and
  `default.cfg:1835:c56_carbon_stock_pricing <- "actualNoAcEst"   # def = actualNoAcEst`
- **Fix**: replace line 101 with:
  ```
  - Interface: `vm_carbon_stock(j,land,c_pools,stockType)` includes both — 4D, declared at
    `modules/56_ghg_policy/price_aug22/declarations.gms:34`. `stockType` has two members,
    `actual` and `actualNoAcEst` (`modules/56_ghg_policy/price_aug22/sets.gms:212-213`); the populating
    equations are indexed over the free set and fill **both** slices. The two readers then pick
    different slices: Module 52 accounts CO₂ from the **`"actual"`** slice
    (`modules/52_carbon/normal_dec17/equations.gms:19`), while Module 56 **prices** CO₂ from
    `%c56_carbon_stock_pricing%`, which defaults to **`actualNoAcEst`**
    (`modules/56_ghg_policy/price_aug22/equations.gms:22`; `config/default.cfg:1835`). In a default run the
    **priced** CO₂ is therefore not computed from the same stock slice as the **reported** CO₂.
  ```

---

### 🟡 B8 — MINOR — wrong date for commit `6b00f9dea`

- **Doc**: `carbon_balance_conservation.md:245`
- **Class**: 10 (stale/incorrect citation metadata)
- **Claim**: ``since MAgPIE commit `6b00f9dea` (2026-07-14)``
- **Reality**: author date == committer date == **2026-07-01**. No MAgPIE commits landed 2026-07-13..15.
  (The SHA itself is correct: `6b00f9dea2971a86c42ab3cd87b595ce555d0cc9`.) The doc was *written* 2026-07-14;
  that date was mistakenly attached to the commit.
- **Verify cmd**: `git log -1 --format='author:%ad  committer:%cd' --date=short 6b00f9dea`
  → `author:2026-07-01  committer:2026-07-01`
- **Fix**: `(2026-07-14)` → `(2026-07-01)`

---

### 🟡 B9 — MINOR — "Both sent to Module 56" implies a serial M52 → M56 CO₂ hand-off (MANDATE 21)

- **Doc**: `carbon_balance_conservation.md:579`
- **Class**: MANDATE 21 (cross-module data-flow direction; parallel-not-serial)
- **Claim**: `- Both sent to Module 56 (GHG Policy) for carbon pricing` — in a bullet list whose preceding
  sibling uses the arrow notation `` `vm_emissions_reg(i,emis_source,"ch4")` … → to Module 56``.
- **Reality**: for **CH₄** the hand-off is genuine — `q56_emis_pricing` reads
  `vm_emissions_reg(i2,emis_annual,pollutants)` (`56_ghg_policy/price_aug22/equations.gms:15-17`), and the four
  CH₄ sources are all in `emis_annual` (`core/sets.gms:320-322`). For **CO₂ it is not**: M56 does **not** read
  M52's `vm_emissions_reg(...,"co2_c")`. `q56_emis_pricing_co2` recomputes the emission itself from
  `pcm_carbon_stock − vm_carbon_stock` (`equations.gms:19-22`), differing from M52's `q52_emis_co2_actual` only
  in the `stockType` slice. M52 and M56 are **parallel readers** of `vm_carbon_stock`, not a producer→consumer
  pair. (§7.5 line 626 gets this right — "All populated slices flow to Module 52 **and** Module 56" — so the
  doc is internally inconsistent.)
- **Evidence**: `modules/56_ghg_policy/price_aug22/equations.gms:15-17` (CH₄, serial) vs `:19-22` (CO₂, parallel);
  `modules/52_carbon/normal_dec17/equations.gms:16-19`
- **Fix**: replace line 579 with:
  ```
  - Both are priced in Module 56 — but by **different paths**: CH₄ flows through `vm_emissions_reg` into
    `q56_emis_pricing` (`modules/56_ghg_policy/price_aug22/equations.gms:15-17`, the `emis_annual` subset),
    whereas CO₂ is **recomputed inside M56** from `pcm_carbon_stock − vm_carbon_stock` in
    `q56_emis_pricing_co2` (`:19-22`). M56 does **not** consume M52's `vm_emissions_reg(...,"co2_c")`:
    M52 and M56 are **parallel readers** of `vm_carbon_stock`, not a serial producer→consumer chain.
  ```

---

### 🟡 B10 — MINOR — `c59_irrigation_scenario` called "optional" without stating that the default is `"on"`

- **Doc**: `carbon_balance_conservation.md:140` and `:431`
- **Class**: 13 / MANDATE 4 (capability vs default)
- **Claim**: `Irrigation: Increases carbon (optional, controlled by c59_irrigation_scenario)` (140);
  `**Irrigation effect**: Optional increase in equilibrium (controlled by c59_irrigation_scenario)` (431)
- **Reality**: the default is **`"on"`** (`config/default.cfg:1953`; `59_som/cellpool_jan23/input.gms:61`).
  `f59_cratio_irrigation` is an unconditional factor inside `i59_cratio`
  (`59_som/cellpool_jan23/preloop.gms:67`); the switch only *neutralises* it (`input.gms:70`:
  `$if "%c59_irrigation_scenario%" == "off" f59_cratio_irrigation(...) = 1;`). "Optional" reads as
  off-by-default, which is the wrong direction. MANDATE 4 requires the default state to be stated.
- **Verify cmd**: `rg -n 'c59_irrigation_scenario' config/default.cfg modules/59_som/cellpool_jan23/input.gms`
  → `default.cfg:1953:cfg$gms$c59_irrigation_scenario <- "on"   # def = "on"`
- **Fix**: both lines → `Irrigation: adjusts the equilibrium via `f59_cratio_irrigation`, **active by default** (`c59_irrigation_scenario = "on"`, `config/default.cfg:1953`); set to `"off"` to neutralise it (factor forced to 1, `modules/59_som/cellpool_jan23/input.gms:70`).`

---

### 🟡 B11 — MINOR — `im_maccs_mitigation` index set is `pollutants`, not `pollutant`

- **Doc**: `carbon_balance_conservation.md:588`
- **Class**: 3 / 12 (imprecise identifier)
- **Claim**: `` `im_maccs_mitigation(t,i,emis_source,pollutant)` ``
- **Reality**: `im_maccs_mitigation(t,i,emis_source,pollutants)` — `modules/57_maccs/on_aug22/declarations.gms:13`
  (`vm_emissions_reg(i,emis_source,pollutants)` at `56_ghg_policy/price_aug22/declarations.gms:40` uses the same set).
- **Verify cmd**: `rg -n 'im_maccs_mitigation' modules/57_maccs/on_aug22/declarations.gms`
- **Fix**: `pollutant` → `pollutants`

---

### 🟡 B12 — MINOR — `othernat` vegc also follows an age-class growth curve

- **Doc**: `carbon_balance_conservation.md:232` (table) and `:237`
- **Class**: 4 (mechanism claim contradicted by code)
- **Claim**: table row `| vegc | Chapman-Richards growth | **Grows if young secondary forest** | 52 |` and
  `` - `othernat`: Natural grassland, savanna, shrubland (**stable**) ``
- **Reality**: **both** other-land subtypes carry an age-class Chapman-Richards curve; only the **asymptote**
  differs.
  - `p35_carbon_density_other(t,j,"othernat",ac,ag_pools) = pm_carbon_density_other_ac(t,j,ac,ag_pools)`
    (`35_natveg/pot_forest_may24/presolve.gms:240`), and `pm_carbon_density_other_ac(...,"vegc")` is
    `m_growth_vegc(0, fm_carbon_density(t,j,"other","vegc"), k_natveg, m_natveg, ord(ac)-1)`
    (`52_carbon/normal_dec17/start.gms:48`) — **age-varying**.
  - `p35_carbon_density_other(t,j,"youngsecdf",...) = pm_carbon_density_secdforest_ac_uncalib` (`presolve.gms:242`)
    — same functional form, **secdforest** asymptote (hence the higher growth and the 20 tC/ha graduation).
  `q35_carbon_other` (`equations.gms:53-55`) integrates both over `ac` via `m_carbon_stock_ac`.
- **Fix**: table `Dynamics` cell → `Grows with age class (both subtypes); youngsecdf uses the secdforest asymptote, othernat the lower other-land asymptote`; and line 237 →
  `` - `othernat`: Natural grassland, savanna, shrubland — grows along the **other-land** Chapman-Richards curve (`pm_carbon_density_other_ac`, `modules/35_natveg/pot_forest_may24/presolve.gms:240`), whose low asymptote makes the pool near-static in practice ``

---

### 🟢 B13 — INFORMATIONAL — `s59_scm_target` default (0) never stated

- **Doc**: `carbon_balance_conservation.md:134` (and §8.4 `:719`)
- **Reality**: `s59_scm_target = 0` and `s59_scm_target_noselect = 0` by default
  (`59_som/cellpool_jan23/input.gms:11-12`; `config/default.cfg:1975-1976`). Term 2 of the cropland
  equilibrium equation (the SCM uplift) is therefore **identically zero in a default run**.
  The doc does frame SCM as scenario-gated ("gated by `i59_scm_target` per scenario", and §8.4 explicitly
  sets 0.5 as an *intervention*), so no false impression is created — but MANDATE 4 wants the default stated.
- **Fix** (line 134, append): ``Default `s59_scm_target = 0` (`config/default.cfg:1975`), so term 2 is zero in a default run.``

---

## 4. Deferred (not code-verifiable → **no edit proposed**)

1. §6.2 climate-specific `k` ranges (Tropical ≈ 0.05-0.08, Temperate ≈ 0.03-0.05, Boreal ≈ 0.02-0.03) —
   `f52_growth_par.csv` is a gitignored run-time input (`modules/52_carbon/input/` holds only a `files` manifest).
2. §5.3 example IPCC stock-change factors (F = 0.69, F = 1.17) — from `f59_cratio_*.csv` inputs, not in repo.
3. §7.4 `im_maccs_mitigation` range "(0 to ~0.3)" — from `f57_maccs_ch4/n2o` CSV inputs, not in repo.
4. §6.2 "Climate Classes (Köppen-Geiger): Tropical / Temperate / Boreal" — these are **not** `clcl` set members
   (the real `clcl` labels are Af, Am, Aw, BSh, Cfa, Dfb, …). The doc reads as an illustrative grouping rather
   than a set enumeration, so I do not call it a MANDATE-22 violation — flagged for a human call.
5. §5.3 "FLU / FMG / FI" naming — the code composes four factors (`f59_cratio_landuse` × `f59_cratio_tillage`
   × `f59_cratio_inputs` × `f59_cratio_irrigation`, `preloop.gms:60-67`); the doc's 3-factor IPCC framing plus a
   separate irrigation bullet is a defensible rendering. Not called a bug.
6. All §8 scenario arithmetic — explicitly labelled "Made-up numbers for illustration". Correctly labelled.
7. §3.6 caveat-2 **materiality** — structurally confirmed (§2a), materiality deliberately **not** adjudicated (§2b).
8. §9 R snippets' `magpie4` call signatures (`readGDX(..., select=list(type="level"), field="l")`) — the
   reporting layer was not read (see §2c item 3).

---

## 5. Score

```
raw_severity_weighted = 4·1 (Critical) + 2·6 (Major) + 1·5 (Minor) + 0·1 = 4 + 12 + 5 = 21
score_0_10            = max(0, 10 − 21) = 0
```

Per §4 of the rubric the arithmetic floors at 0. That is an artefact of a **long hub doc** (997 lines) being
scored with a per-question formula: 88 claims checked, ~86 % verified correct. The honest read is
**"Mostly Accurate (lower band) with one Critical"**: the spine (pools, sets, populator set, the M52
emission equation, the M59 SOM machinery, the new §3.6 youngsecdf story) is **right**, and the failures
cluster in three places — (a) the peatland limitation (B1, Critical), (b) the MACC applicability block
(B2/B3), and (c) the FRA-calibration layer that the doc's own §3.6 knows about but §3.3/§3.5/§6 never mention
(B4/B5).

**The single most important fix is B1.** It is the only bug in the "user builds on a false foundation" class.
