# R60 depth audit — `cross_module/carbon_balance_conservation.md`

**Lens**: `declare_populate` (enter from the declaring/populating side: `declarations.gms`, equation LHS, `.fx`/`.l` assignments; and whether the formulas the doc attributes to a module's equations match the equation bodies)
**Ground truth**: MAgPIE `develop` read-only worktree (referred to below as `<develop>`; HEAD `2c02843ec`)
**Role map**: `audit/integrated/depth_rolemap.json` (checked first for every `vm_`/`pm_`/`im_`/`pcm_`/`fm_` attribution claim, then confirmed with both-endpoints greps)
**Date**: 2026-08-02

---

## 1. Scope and what was verified

The doc is unusually citation-dense (≈70 `file:line` references). Every citation and every
declare/populate/read attribution was checked. **The core attribution spine is correct and
survived every probe** — including the parts that are historically the highest-risk:

| Claim class | Result |
|---|---|
| `vm_carbon_stock` DECLARED in `modules/56_ghg_policy/price_aug22/declarations.gms:34`, 4D over `stockType` | ✅ exact |
| `stockType / actual, actualNoAcEst /` at `modules/56_ghg_policy/price_aug22/sets.gms:212-213` | ✅ exact |
| Populator set = M29 (crop), M31 (past), M32 (forestry), M34 (urban, `.fx`=0), M35 (primforest/secdforest/other), M59 (soilc, all land) | ✅ matches role map `populated_by: [29,31,32,34,35,59]` **and** whole-tree grep; no phantom, no omission |
| "populating equations are indexed over the free `stockType` set and fill **both** slices" | ✅ `m_carbon_stock` / `m_carbon_stock_ac` (`core/macros.gms:99-106`) each emit an `actual` term **and** an `actualNoAcEst` term; every populating equation carries `stockType` free |
| M52 reads the `"actual"` slice (`modules/52_carbon/normal_dec17/equations.gms:19`); M56 reads `%c56_carbon_stock_pricing%` (`modules/56_ghg_policy/price_aug22/equations.gms:22`), default `actualNoAcEst` (`modules/56_ghg_policy/price_aug22/input.gms:90`) | ✅ exact |
| M52/M56 are **parallel** readers of `vm_carbon_stock`; M56 does *not* consume M52's `vm_emissions_reg(...,"co2_c")` | ✅ `q56_emis_pricing` is restricted to `emis_annual` (`modules/56_ghg_policy/price_aug22/equations.gms:15-17`); `co2_c` oneoff sources are not in `emis_annual` (`core/sets.gms:320-322`) |
| The FRA-2025 growing-stock calibration block: `s52_growingstock_calib` default `1` (`modules/52_carbon/normal_dec17/input.gms:46`, not exposed in `config/default.cfg`), overwrite of `pm_carbon_density_secdforest_ac` at `preloop.gms:71-73` and `pm_carbon_density_plantation_ac` at `preloop.gms:114-116`, region-average `m` at `preloop.gms:29-30`, uncalibrated copies at `start.gms:43-44` | ✅ every line number exact |
| Uncalibrated-curve consumer set (M14 `presolve.gms:66`, M29 `preloop.gms:46,48`, M32 `presolve.gms:59,61,68`, M35 `presolve.gms:242` and `:117`) and calibrated-curve readers (M14 `presolve.gms:44`, M35 blend `presolve.gms:248-252`, harvest bound `presolve.gms:177-180`) | ✅ every line number exact; matches role map `read_by` for both `*_uncalib` params |
| `q59_carbon_soil` at `modules/59_som/cellpool_jan23/equations.gms:61-64`; `q59_som_target_cropland` 4-term formula at `:20-27`; `q59_som_pool` at `:46-52`; `i59_lossrate=1-0.85**m_yeardiff(t)` at `preloop.gms:45`; `i59_subsoilc_density` derived from `fm_carbon_density(...,"other","soilc")` at `preloop.gms:12` | ✅ exact, incl. the 4-term equilibrium expansion |
| MACC application set: M53 `equations.gms:29,52,63`, **not** `q53_emissions_resid_burn` (`:70-72`); `maccs_ch4 / rice_ch4, ent_ferm_ch4, awms_ch4 /` (`modules/57_maccs/on_aug22/sets.gms:28-29`); M51 `equations.gms:71` only; M50 `presolve.gms:54-64`; `emis_source_n51` at `modules/51_nitrogen/rescaled_jan21/sets.gms:15-16`; `.fx`/`.lo`/`.up` at `preloop.gms:8-10` | ✅ whole-tree grep for `im_maccs_mitigation` returns **exactly** those sites — the doc's "appears in exactly these equations" is literally true |
| Peatland: `q58_peatland_emis → vm_emissions_reg(i,"peatland",poll58)` at `modules/58_peatland/v2/equations.gms:91-92`; `peatland` in `emis_annual` at `core/sets.gms:322`; default realization `v2` (`config/default.cfg:1874`); `s58_fix_peatland=2020` (`config/default.cfg:1931`) | ✅ exact |
| Set citations: `c_pools` `core/sets.gms:324-325`; `emis_oneoff` `:314-318` (21 = 7×3 ✓); `emis_land` `:332-354`; `m_growth_vegc` `core/macros.gms:18`; `m_timestep_length` `core/macros.gms:51` | ✅ exact |
| Defaults: `s59_scm_target=0` (`config/default.cfg:1978`), `c59_irrigation_scenario="on"` (`:1956`), `s59_cost_scm_recur=65` (`modules/59_som/cellpool_jan23/input.gms:15`), `f59_cratio_irrigation` neutralised at `input.gms:70` | ✅ exact |
| Commit `6b00f9dea` (2026-07-01) "Fix youngsecdf wood production: use uncalibrated growing stock" | ✅ exists, date and subject match |

**Claims verified: 71.** Seven defects found — none in the interface-attribution spine; the
failures cluster in (a) default-state framing of two mechanisms, (b) the illustrative
arithmetic, (c) one drifted `config` line, (d) two incomplete "provides/consumes" lists.

---

## 2. Bugs

### B1 — Major — `default_value` — fire disturbance presented as an active carbon-loss driver

**Doc** (`carbon_balance_conservation.md:626`, echoed at `:221` and `:870`):
> "Disturbances (fire, shifting agriculture) → reset age classes → carbon loss"
> "**6. No Fire Emissions Separately**: Fire disturbances (Module 35) cause carbon loss via stock change"

**Code**: the default is `s35_forest_damage = 2` (`config/default.cfg:1184`; scalar default also
`2` at `modules/35_natveg/pot_forest_may24/input.gms:27`). That branch
(`modules/35_natveg/pot_forest_may24/presolve.gms:19-22`) uses **only**
`f35_forest_lost_share(i,"shifting_agriculture")`, multiplied by `(1 - p35_damage_fader(t))`,
and the fader is a sigmoid from `sm_fix_SSP2` to `s35_forest_damage_end = 2050`
(`preloop.gms:88`; `input.gms:28`) — so the loss **fades to zero by 2050**. The distinct
`wildfire` member of `driver_source` (`sets.gms:12`) enters only via `combined_loss`
(`sets.gms:14-15`) under `s35_forest_damage = 3` (`presolve.gms:24-27`), which is **not** the
default.

Nuance that must survive the fix (do not overcorrect): the code comment at `presolve.gms:9`
calls the default channel "shifting agriculture **fires**", so a fire-related loss *is* active
by default — but it is the shifting-agriculture share, not the separate `wildfire` driver, and
it is phased out.

**Impact**: a reader analysing a default run's LUC emissions would attribute a wildfire
component that the run does not contain, and would not know the disturbance term goes to zero
after 2050.

**Fix**: replace with — "Disturbance losses are applied to secondary and primary forest via
`p35_disturbance_loss_secdf`/`_primf`. Under the default `s35_forest_damage = 2`
(`config/default.cfg:1184`) only the `shifting_agriculture` loss share is applied, and it is
faded to zero by `s35_forest_damage_end = 2050` (`modules/35_natveg/pot_forest_may24/presolve.gms:19-22`,
`preloop.gms:88`). The separate `wildfire` driver is included only under `s35_forest_damage = 3`
(`presolve.gms:24-27`). These are exogenous historical loss *shares*, not a modelled fire process."

---

### B2 — Major — `mechanism` — "Primary forest carbon density does NOT change over time" is false under the default climate scenario

**Doc** (`carbon_balance_conservation.md:201`, repeated at `:841`):
> "Carbon density does NOT change over time (climate change affects future forests, not current primary)"
> "**1. Static Primary Forest Carbon**: Primary forest carbon density does NOT change over time"

**Code**: `q35_carbon_primforest` (`modules/35_natveg/pot_forest_may24/equations.gms:42-44`)
expands to `vm_land(j2,"primforest") * sum(ct, fm_carbon_density(ct,j2,"primforest",ag_pools))`
(`core/macros.gms:99-101`) — i.e. it reads the **current time step's** density.
`fm_carbon_density(t_all,j,land,c_pools)` is a time-indexed LPJmL table
(`modules/52_carbon/normal_dec17/input.gms:16-20`) and is collapsed to 1995 **only** under
`c52_carbon_scenario = "nocc"` (`input.gms:22`). The default is `cc`
(`input.gms:8`; `config/default.cfg:1590`), so primary-forest carbon density **does** vary over
time in a default run.

The doc contradicts itself: §8.3 (`:698-700`) states "Module 52 updates `fm_carbon_density(t,j,land,c_pools)`
over time; Carbon stocks change even without land-use change."

**Fix**: rewrite the two bullets to scope "static" to age-class dynamics —
"Primary forest carries no age-class structure: its density is `fm_carbon_density(t,j,"primforest",c_pools)`
directly, with no Chapman-Richards growth. The density is **not** constant in time under the
default `c52_carbon_scenario = "cc"` (`config/default.cfg:1590`) — it follows the LPJmL climate
projection; it is frozen at 1995 only under `nocc` (`modules/52_carbon/normal_dec17/input.gms:22`)."

---

### B3 — Major — `formula` — §6.3 growth-trajectory table does not follow from its own stated parameters

**Doc** (`carbon_balance_conservation.md:485-500`): "A = 100 tC/ha, k = 0.06, m = 2.0" then a
table giving 14 / 26 / 44 / 58 / 75 / 88 / 93 tC/ha at 5 / 10 / 20 / 30 / 50 / 80 / 100 years.

**Code**: the model's curve is `m_growth_vegc(S,A,k,m,ac) = S + (A-S)*(1-exp(-k*(ac*5)))**m`
(`core/macros.gms:18`), called with `(ord(ac)-1)` (`modules/52_carbon/normal_dec17/start.gms:17,28,48`),
so with S=0, A=100, k=0.06, m=2 the values are:

| years | doc | `100*(1-exp(-0.06*y))**2` |
|---|---|---|
| 5 | 14 | **6.7** |
| 10 | 26 | **20.4** |
| 20 | 44 | **48.8** |
| 30 | 58 | **69.7** |
| 50 | 75 | **90.3** |
| 80 | 88 | **98.4** |
| 100 | 93 | **99.5** |

The doc's column instead matches `k ≈ 0.03, m = 1` (13.9 / 25.9 / 45.1 / 59.3 / 77.7 / 90.9 / 95.0),
i.e. the table was generated from different parameters than the ones printed above it. The bad
numbers propagate into §8.2 (`:676` "44 tC/ha (44% of mature, from Chapman-Richards)"; `:682`
"75 tC/ha (75% of mature)").

**Impact**: the table is the doc's only worked demonstration of the Chapman-Richards
implementation; a reader sanity-checking `pm_carbon_density_*_ac` output against it would
conclude the model's growth is ~2× slower at young ages than it is, and would mis-time
afforestation sequestration by decades.

**Fix**: recompute the table with the stated k=0.06, m=2 (values above) and update the two
§8.2 figures to 49 tC/ha at year 20 and 90 tC/ha at year 50; or restate the parameters as
k=0.03, m=1.0. Keep the "illustrative" note either way.

---

### B4 — Minor — `formula` — §8.1 gradual soil-carbon emission arithmetic

**Doc** (`carbon_balance_conservation.md:656`):
> "Gradual (soilc over 20 years): 30 tC/ha × 100 Mha × (44/12) / 20 years = **458 Tg CO₂/year**"

**Reality**: 30 tC/ha × 100 Mha = 3,000 Tg C; × 44/12 = 11,000 Tg CO₂; / 20 = **550 Tg CO₂/year**.
(The sibling line `:655` — 56,833 Tg CO₂ — is arithmetically correct, which makes the 458
look authoritative by association.)

**Fix**: `458` → `550`.

---

### B5 — Minor — `citation` — `config/default.cfg` line drift on the unprefixed `c56_carbon_stock_pricing` assignment

**Doc** (`carbon_balance_conservation.md:101`):
> "⚠️ Do **not** cite `config/default.cfg:1835` for this default: that line omits the `cfg$gms$` prefix its siblings carry…"

**Reality**: the substantive claim is **TRUE and still live** — `config/default.cfg:1838` reads
`c56_carbon_stock_pricing <- "actualNoAcEst"   # def = actualNoAcEst`, with no `cfg$gms$`
prefix, while its siblings at `:1831` (`cfg$gms$c56_emis_policy`), `:1843`, `:1847` all carry it.
But the **line number has drifted**: `:1835` is now a comment line
(`# *   actual: CO2 emissions for pricing are based on the difference of actual carbon stocks between time steps`).
A reader following the pointer lands on a comment and cannot confirm the defect.

**Fix**: `config/default.cfg:1835` → `config/default.cfg:1838`.

---

### B6 — Minor — `attribution_read` — `vm_maccs_costs` consumer arrow omits Module 36

**Doc** (`carbon_balance_conservation.md:593`):
> "`vm_maccs_costs(i,factors)`: Labor and capital costs of mitigation → to Module 11"

**Reality**: declared/populated in `modules/57_maccs/on_aug22/declarations.gms:25` and
`equations.gms:36,46`; read by **two** modules — M11 (`modules/11_costs/default/equations.gms:28`)
**and** M36 (`modules/36_employment/exo_may22/equations.gms:28`, `vm_maccs_costs(i2,"labor")`).
M36's default realization is `exo_may22` (`config/default.cfg:1212`), so this consumer is live.
Role map agrees: `read_by: ["11","36","57"]`.

This is the only incomplete arrow in the doc — the neighbouring arrows (`vm_nr_som` → M51,
`vm_cost_scm` → M11) are exhaustive against the role map, so the asymmetry reads as a
complete list to a careful reader.

**Fix**: "→ to Module 11 (total costs) and Module 36 (`"labor"` slice only, agricultural employment)".

---

### B7 — Minor — `attribution_declare` — §7.1 "Module 52 Provides" list omits three parameters the doc itself relies on

**Doc** (`carbon_balance_conservation.md:512-516`): §7.1 "Module 52 (Carbon) — Central Data
Provider / **Provides**:" lists `fm_carbon_density`, `pm_carbon_density_plantation_ac`,
`pm_carbon_density_secdforest_ac`, `pm_carbon_density_other_ac`.

**Reality**: M52 also declares and populates:
- `pm_carbon_density_secdforest_ac_uncalib` (`modules/52_carbon/normal_dec17/declarations.gms:10`, populated `start.gms:43`) — read by M14, M29, M32, M35
- `pm_carbon_density_plantation_ac_uncalib` (`declarations.gms:13`, populated `start.gms:44`) — read by M29, M32
- `im_vol_conv(i)` (`declarations.gms:23`, populated `preloop.gms:21`, fallback `start.gms:40`) — read by M73 (`modules/73_timber/default/preloop.gms:49,51,90,91`)

The two `*_uncalib` parameters are the subject of two long ⚠️ blocks elsewhere in this same doc
(`:180`, `:247`, `:479`), so §7.1 is internally inconsistent with the rest of the file, and a
reader using §7.1 as the M52 interface inventory would miss the parameters most likely to be
touched in a growth-curve refactor (the R20 anchor failure mode).

**Fix**: add the three parameters to the §7.1 Provides list, with a one-line note that the
`*_uncalib` pair is the pre-FRA-calibration snapshot and carries a different consumer set.

---

## 3. Deferred (not bugs — unverifiable or judgment calls)

- §6.2 k ranges ("Tropical k ≈ 0.05-0.08", "Temperate 0.03-0.05", "Boreal 0.02-0.03"): `modules/52_carbon/input/f52_growth_par.csv` is not tracked (the module `input/` dir holds only `files`), so the numeric ranges cannot be checked offline.
- §5.3 example IPCC stock-change factors (0.69, 1.17): same — `f59_ch5_*.csv` inputs are untracked.
- §7.4 `im_maccs_mitigation` "(0 to ~0.3)": depends on untracked MACC input data.
- §7.2 "`vm_land(j,land)`: Non-cropland areas from Module 10" — declare-vs-populate looseness. M10 declares `vm_land` and its `q10_land_area`/`q10_transition_to` do constrain it, but the non-cropland slices are actually set by M31/M32/M34/M35 equations and bounds. Not clearly false; flagged for a maintainer's judgment, not proposed as an edit.
- §7.2 "Receives" omits `vm_landexpansion(j,"crop")` (`modules/59_som/cellpool_jan23/equations.gms:91`); §7.3 "Receives" omits `vm_manure` (M55) and `vm_res_ag_burn` (M18). Incompleteness in lists the doc does not claim to be exhaustive — below the B6 threshold because those lists have other omissions of the same kind.
- References block `:987` "Module 52 growth: `modules/52_carbon/normal_dec17/start.gms:8-39`" — the range no longer reaches the other-land growth block (now `start.gms:46-51`). Borderline; the plantation and secdforest curves are inside the cited range.
- §9.1-§9.3 R verification snippets were not executed (no GDX available in this environment); `ov_carbon_stock`, `ov_emissions_reg`, `pm_carbon_density_plantation_ac` all exist as GDX-visible symbols, and the `m_timestep_length`-is-a-macro caveat at `:768` is correct (`core/macros.gms:51`).
- The code comment `modules/59_som/cellpool_jan23/realization.gms:42` says "44% in 5 years" where the formula gives 56% loss / 44% legacy. The **doc is right** and the code comment is the loose one; noted only so a future auditor does not "fix" the doc toward the comment.

---

## 4. Verification commands (all run against `<develop>` = the read-only develop worktree)

```
awk 'NR>=310 && NR<=360' <develop>/core/sets.gms                      # emis_oneoff/emis_annual/c_pools/emis_land
grep -n "vm_carbon_stock\|pcm_carbon_stock" <develop>/modules/56_ghg_policy/price_aug22/declarations.gms
grep -n "stockType\|actualNoAcEst" <develop>/modules/56_ghg_policy/price_aug22/sets.gms
grep -n "m_carbon_stock" <develop>/core/macros.gms                    # -> 99, 104 ; both slices emitted
rg -n "vm_carbon_stock" <develop>/modules/ <develop>/core/            # full populator/reader census
rg -n "pm_carbon_density_secdforest_ac_uncalib|pm_carbon_density_plantation_ac_uncalib" <develop>/modules/
rg -n "pm_carbon_density_secdforest_ac\b|pm_carbon_density_plantation_ac\b|pm_carbon_density_other_ac\b" <develop>/modules/
rg -n "im_maccs_mitigation" <develop>/modules/ | grep -v 57_maccs     # exactly M50/M51/M53 sites
rg -n "vm_maccs_costs" <develop>/modules/                             # M11 + M36
grep -n "c56_carbon_stock_pricing" <develop>/config/default.cfg       # -> 1838 (doc says 1835)
grep -n "s35_forest_damage" <develop>/config/default.cfg              # -> 1184: def = 2
awk 'NR>=6 && NR<=35' <develop>/modules/35_natveg/pot_forest_may24/presolve.gms
grep -n "c52_carbon_scenario" <develop>/config/default.cfg            # -> 1590: def = "cc"
python3 -c 'import math; print([round(100*(1-math.exp(-0.06*y))**2,1) for y in (5,10,20,30,50,80,100)])'
python3 -c 'print(30*100/20*44/12)'                                   # -> 550.0
git -C <develop> log --format="%h %ad %s" --date=short -1 6b00f9dea
```

---

## 5. Bottom line

The declare/populate spine of this document — the part most likely to cause a cascading
failure if wrong — is **clean**: the `vm_carbon_stock` declaration site, the six-module
populator set, the both-slices `stockType` claim, the M52/M56 parallel-reader correction, the
FRA-calibration overwrite sites, and the uncalibrated-vs-calibrated consumer split all verify
line-for-line against current `develop`. The seven defects are concentrated in the *narrative*
layer: two mechanisms whose default state is misstated (fire disturbance, primary-forest
density), the illustrative arithmetic (a growth table that contradicts its own parameters, and
one wrong emission figure), one drifted `config` line, and two lists that stop one consumer
short.
