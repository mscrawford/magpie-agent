# R60 depth audit — `cross_module/carbon_balance_conservation.md`

**Lens**: `config_realization` (entry from `config/default.cfg` + `ls -d modules/NN_*/`; priority on default
values, `cfg$gms$*` switch behaviour, realization names, and default-vs-alternative framing)
**Ground truth**: MAgPIE `develop` read-only worktree, HEAD `2c02843ec`
("Merge pull request #919 from alexkoberle/dyn_reg_tau"), 2026-08-02.
**Convention**: MAgPIE paths are repo-relative to the develop worktree root; agent-repo paths are relative
to `magpie-agent/`.

> **Provenance note (read this before treating the list as one auditor's yield).** A file from an earlier
> pass of this same doc+lens already existed at this path. I completed my own pass first (finding
> bugs B3, B7, B8, B13, B14 below), then read the prior file and **independently re-derived every
> additional finding against code with my own commands** before admitting it. Each bug record below
> carries the command I ran and its output. Nothing here is relayed on the prior file's authority.
> Findings I did **not** originate are marked `[re-derived]`; the ones I originated are marked `[own]`.
> This distinction is bookkeeping for round accounting only — the evidence standard applied is identical.

---

## 1. Verdict

**15 bugs: 1 Critical, 4 Major, 9 Minor, 1 Informational. Claims verified: 78.**

The doc's **config/realization spine is clean** — the failure modes this lens exists to catch are absent:

- Every one of the **13 realizations it names is the current module default** (table §2.1).
- Every `config/default.cfg` switch value it asserts is **correct** (table §2.2), including the two
  hardest: `s52_growingstock_calib = 1` as a hard default *not* exposed in config, and
  `c56_carbon_stock_pricing = actualNoAcEst` driving a pricing slice different from the reporting slice.
- **No wrong-default-realization bug, no inverted boolean, no non-default realization described as active.**

The defects that do exist cluster in two places: (a) **consumer/reader-set enumerations** that were correct
when written and have since been outrun by code (B1 is the R20 anchor almost verbatim), and (b) **the
illustrative/summary sections (§3.7, §5.3, §7.2, §8.4, §9.1)**, which lag the carefully-maintained
"warning box" prose by one or more revisions and now contradict it.

---

## 2. What was checked and PASSED

### 2.1 Realization names — all 13 cited realizations are the current default

| Module | Doc cites | `config/default.cfg` | Alternatives that exist | OK |
|---|---|---|---|---|
| 14_yields | `managementcalib_aug19` | :357 | `dynRegPastrTau_apr26` | ✅ |
| 29_cropland | `detail_apr24` | :814 | `simple_apr24` | ✅ |
| 34_urban | `exo_nov21` | :1147 | `static` | ✅ |
| 35_natveg | `pot_forest_may24` | :1156 | (sole) | ✅ |
| 50_nr_soil_budget | `macceff_aug22` | :1500 | (sole) | ✅ |
| 51_nitrogen | `rescaled_jan21` | :1571 | `off` | ✅ |
| 52_carbon | `normal_dec17` | :1577 | (sole) | ✅ |
| 53_methane | `ipcc2006_aug22` | :1604 | `off` | ✅ |
| 56_ghg_policy | `price_aug22` | :1634 | (sole) | ✅ |
| 57_maccs | `on_aug22` | :1843 | (sole) | ✅ |
| 58_peatland | `v2` | :1874 | `off` | ✅ |
| 59_som | `cellpool_jan23` | :1937 | `static_jan19` | ✅ |
| 30_croparea / 45_climate | (named, no realization cited) | `simple_apr24` :915 / `static` :1495 | — | ✅ n/a |

Notable near-miss the doc dodges: `modules/14_yields/` has gained a **second** realization
(`dynRegPastrTau_apr26`, itself a reader of `pm_carbon_density_secdforest_ac_uncalib` at its own
`presolve.gms:66`). The doc still correctly cites `managementcalib_aug19`.

### 2.2 Default parameter values — all correct

| Doc claim | Code evidence | OK |
|---|---|---|
| `s52_growingstock_calib = 1`, hard default, **not** in `config/default.cfg` | `modules/52_carbon/normal_dec17/input.gms:46` (`/ 1 /`); repo-wide `rg` → 4 hits, all inside `modules/52_carbon/` | ✅ |
| `c56_carbon_stock_pricing` defaults to `actualNoAcEst` | `modules/56_ghg_policy/price_aug22/input.gms:90` | ✅ |
| `s59_scm_target = 0` ⇒ SCM term zero in a default run | `config/default.cfg:1978`; `i59_scm_target` = fader × (`s59_scm_target`·w + `s59_scm_target_noselect`·(1−w)), `modules/59_som/cellpool_jan23/presolve.gms:31-33`, both scalars 0 | ✅ |
| `c59_irrigation_scenario = "on"`, active by default; `"off"` ⇒ factor 1 | `config/default.cfg:1956`; `modules/59_som/cellpool_jan23/input.gms:70` | ✅ |
| `s58_fix_peatland = 2020` | `config/default.cfg:1931` | ✅ |
| `s59_cost_scm_recur = 65` USD17MER/ha | `config/default.cfg:1994` | ✅ |
| Tillage default full, input default medium | `modules/59_som/cellpool_jan23/preloop.gms:52-55` | ✅ |
| `c52_carbon_scenario` = `cc`/`nocc`/`nocc_hist`, default `cc` | `modules/52_carbon/normal_dec17/input.gms:8-11,22-23`; `config/default.cfg:1590` | ✅ |
| Module 58 default realization `v2` | `config/default.cfg:1874` | ✅ |

### 2.3 The `stockType` dual-slice mechanism (the doc's most load-bearing claim) — correct

- DECLARED in `modules/56_ghg_policy/price_aug22/declarations.gms:34`; `stockType / actual, actualNoAcEst /`
  at `sets.gms:212-213`. ✅
- "populating equations are indexed over the free set and fill **both** slices" — ✅ **confirmed
  mechanistically**: every populator is declared free over `stockType` (`q29_carbon`
  `29_cropland/detail_apr24/equations.gms:38`; `q31_carbon` `31_past/endo_jun13/equations.gms:22`;
  `q32_carbon` `32_forestry/dynamic_may24/equations.gms:108`; `q35_carbon_*`
  `35_natveg/pot_forest_may24/equations.gms:42,49,53`; `q59_carbon_soil`
  `59_som/cellpool_jan23/equations.gms:61`), and the slices differ because `m_carbon_stock_ac`
  (`core/macros.gms:104-106`) sums over full `ac` for `"actual"` and over `ac_sub` (age classes minus
  newly-established `ac_est`) for `"actualNoAcEst"`; `m_carbon_stock` (`:99-101`) writes both identically.
- M52 reads `"actual"` (`modules/52_carbon/normal_dec17/equations.gms:19`); M56 reads
  `"%c56_carbon_stock_pricing%"` (`modules/56_ghg_policy/price_aug22/equations.gms:22`). The doc's
  conclusion — priced CO₂ ≠ reported CO₂ slice in a default run — holds. ✅
- The **parallel-not-serial** claim at `:583` is right: `q56_emis_pricing_co2` recomputes CO₂ from
  `pcm_carbon_stock − vm_carbon_stock` itself (`equations.gms:19-22`) and never consumes M52's
  `vm_emissions_reg(...,"co2_c")`; `q56_emis_pricing` (`:15-17`) covers only `emis_annual`. ✅

### 2.4 Attribution spine — matches `audit/integrated/depth_rolemap.json` and both-endpoint greps

`vm_carbon_stock` populators (§7.5) are **exact**: M29 crop, M31 past, M32 forestry, M34 urban (`.fx`),
M35 primforest/secdforest/other, M59 soilc — role map `populated_by ['29','31','32','34','35','59']`,
`read_by ['52','56','59']`. `vm_carbon_stock_croparea` populated by M30 (present in **both** M30
realizations, incl. default `simple_apr24/equations.gms:50`), read by M29. `vm_nr_som` → M51,
`vm_cost_scm` → M11. `i59_subsoilc_density = fm_carbon_density(…,"other","soilc") − f59_topsoilc_density`
(`modules/59_som/cellpool_jan23/preloop.gms:12`) — note the doc correctly follows the **default**
realization here (`static_jan19/preloop.gms:20` uses `"secdforest"` instead).

### 2.5 Citations — 40+ file:line refs verified on current develop; 2 defective (B3, B10)

`core/sets.gms:251` (land, 7 members), `:314-318` (`emis_oneoff`, 21 = 7×3), `:322` (peatland ∈
`emis_annual`), `:324-325` (`c_pools`), `:332-354` (`emis_land`) · `core/macros.gms:18`, `:51` ·
`52_carbon/normal_dec17/{equations.gms:16-19; start.gms:17,19-20,28,30-31,43-44; preloop.gms:29-30,71-73,114-116; input.gms:8-23,37-43,46,47}` ·
`56_ghg_policy/price_aug22/{declarations.gms:34; sets.gms:212-213; equations.gms:15-17,19-22; input.gms:90}` ·
`59_som/cellpool_jan23/{equations.gms:20-27,46-52,61-64; preloop.gms:45; input.gms:70; realization.gms:21-24}` ·
`34_urban/exo_nov21/presolve.gms:8` (character-exact) ·
`29_cropland/detail_apr24/{equations.gms:39; preloop.gms:46,48}` ·
`32_forestry/dynamic_may24/presolve.gms:59,61,68` ·
`35_natveg/pot_forest_may24/presolve.gms:117,177-180,240,242,248-252` ·
`14_yields/managementcalib_aug19/presolve.gms:44,64-71` ·
`53_methane/ipcc2006_aug22/equations.gms:29,52,63,70-72` · `57_maccs/on_aug22/sets.gms:28-29` ·
`51_nitrogen/rescaled_jan21/{sets.gms:15-16; preloop.gms:8-10; equations.gms:30-39,62-64,71}` ·
`50_nr_soil_budget/macceff_aug22/presolve.gms:54-64` ·
`58_peatland/v2/{realization.gms:8-17; equations.gms:91-92}`.
Commit `6b00f9dea` is real, titled "Fix youngsecdf wood production: use uncalibrated growing stock",
dated 2026-07-01 as claimed. GDX symbols in the §9 snippets (`ov_carbon_stock`, `ov_emissions_reg`,
`ov59_som_pool`, `ov59_som_target`, `ov32_land`) all exist in the matching `postsolve.gms`.

---

## 3. Bugs

### B1 — 🔴 Critical — `attribution_read` — calibrated-curve reader set omits Module 32 and M14-forestry `[re-derived]`

**Doc**: `carbon_balance_conservation.md:180`, byte-identical duplicate at `:479`

> "The uncalibrated curves survive as `pm_carbon_density_*_ac_uncalib` … and are what M14's
> `im_growing_stock_ysf` …, M29's tree cover …, M32's afforestation and NDC curves … and M35's youngsecdf
> … read. **M14 and M35 read the CALIBRATED curve as well** — M14 for regular secdforest growing stock
> (`modules/14_yields/managementcalib_aug19/presolve.gms:44`), M35 for secdforest carbon density …"

**Reality**: the *calibrated* plantation curve `pm_carbon_density_plantation_ac` — overwritten at
`modules/52_carbon/normal_dec17/preloop.gms:114-116` whenever `s52_growingstock_calib = 1`, the hard
default in **every** run — has three readers in Module 32 and one more in M14, none enumerated:

- `modules/32_forestry/dynamic_may24/presolve.gms:65` —
  `p32_carbon_density_ac(t,j,"plant",ac,ag_pools) = pm_carbon_density_plantation_ac(t,j,ac,ag_pools);`
  This is the carbon density of **timber plantations**, i.e. the `vm_carbon_stock(j,"forestry",…)` slice
  produced by `q32_carbon` (`modules/32_forestry/dynamic_may24/equations.gms:108`) — the dominant forestry
  carbon pool, and squarely inside this document's subject matter.
- `modules/32_forestry/dynamic_may24/preloop.gms:18` — `p32_carbon_density_ac_forestry`.
- `modules/32_forestry/dynamic_may24/preloop.gms:56` — `p32_avg_increment`.
- `modules/14_yields/managementcalib_aug19/presolve.gms:26` — `im_growing_stock(t,j,ac,"forestry")`.

The paragraph names M32 only as a reader of the *uncalibrated* curves — true for its `aff` and `ndc`
types, false for `plant`. A reader refactoring `pm_carbon_density_plantation_ac` on this sentence would
conclude the consumers are M14-secdforest and M35 and miss Module 32 entirely. This is the immutable R20
anchor in `audit/flywheel_rubric.md` §1 (same parameter family, same omitted module, same refactor hazard)
→ **Critical** by the wrong-consumer-set trigger; also a latent doc bug under the
`doc_error_answerer_beat_it` mandate.

**Verify** (two independent methods, each standalone):
```
$ rg -n 'pm_carbon_density_secdforest_ac\b|pm_carbon_density_plantation_ac\b|pm_carbon_density_other_ac\b' modules/ core/
modules/32_forestry/dynamic_may24/preloop.gms:18:  = pm_carbon_density_plantation_ac(t_all,j,ac,"vegc");
modules/32_forestry/dynamic_may24/preloop.gms:56:  = pm_carbon_density_plantation_ac(t_all,j,ac,"vegc") / ((ord(ac)+1)*5);
modules/32_forestry/dynamic_may24/presolve.gms:65: p32_carbon_density_ac(t,j,"plant",ac,ag_pools) = pm_carbon_density_plantation_ac(t,j,ac,ag_pools);
modules/14_yields/managementcalib_aug19/presolve.gms:26:  pm_carbon_density_plantation_ac(t,j,ac,"vegc")
modules/14_yields/managementcalib_aug19/presolve.gms:44:  pm_carbon_density_secdforest_ac(t,j,ac,"vegc")
modules/35_natveg/pot_forest_may24/presolve.gms:240,248,250,251 ; modules/52_carbon/... (producer)
$ python3 -c "import json;d=json.load(open('audit/integrated/depth_rolemap.json'))"   # role map cross-check
   pm_carbon_density_plantation_ac -> read_by ['14','32','52']     # doc lists neither 32 nor M14-forestry
```
**Confirmed**: yes.

**Fix** (apply to **both** `:180` and `:479` — they are byte-identical): replace the final sentence with

> M14, M32 and M35 read the CALIBRATED curves as well — M14 for the forestry and the regular-secdforest
> growing stock (`modules/14_yields/managementcalib_aug19/presolve.gms:26,44`), M32 for the
> **timber-plantation** carbon density `p32_carbon_density_ac(…,"plant",…)`
> (`modules/32_forestry/dynamic_may24/presolve.gms:65`, plus `preloop.gms:18,56`), and M35 for secdforest
> carbon density, which it BLENDS with the uncalibrated curve by natural-origin area share
> (`modules/35_natveg/pot_forest_may24/presolve.gms:248-252`). Within M32 only the `aff` and `ndc` types
> use the uncalibrated curves; `plant` uses the calibrated one.

---

### B2 — 🟠 Major — `mechanism` — primary-forest carbon density *does* change over time in a default run `[re-derived]`

**Doc**: `carbon_balance_conservation.md:201` (and the three "Static" cells at `:194-196`)

> "- Carbon density does NOT change over time (climate change affects future forests, not current primary)"

**Reality**: under the **default** `c52_carbon_scenario = "cc"` (`config/default.cfg:1590`;
`modules/52_carbon/normal_dec17/input.gms:8`), `fm_carbon_density` keeps its full `t_all` LPJmL
trajectory. The only two statements that flatten the time dimension are `input.gms:22` (`nocc`) and `:23`
(`nocc_hist`), both `$if`-gated **off** by default. Primary-forest stock is computed by
`q35_carbon_primforest` (`modules/35_natveg/pot_forest_may24/equations.gms:42-44`) via
`m_carbon_stock(vm_land,fm_carbon_density,"primforest")`, which expands (`core/macros.gms:99-101`) to
`vm_land(j2,"primforest") * sum(ct, fm_carbon_density(ct,j2,"primforest",ag_pools))` — the **current**
timestep's density, not y1995. A repo grep finds no primforest-specific freeze anywhere in Module 52
(the only two `primforest` hits are comments in `preloop.gms:36,38`). So primary-forest carbon density —
and stock at constant area — changes over time in a default run. The doc contradicts itself at `:697-701`
("Module 52 updates `fm_carbon_density` over time; Carbon stocks change even without land-use change").

**Verify**
```
$ grep -n 'nocc' modules/52_carbon/normal_dec17/input.gms
22: $if "%c52_carbon_scenario%" == "nocc" fm_carbon_density(t_all,j,land,c_pools) = fm_carbon_density("y1995",...);
23: $if "%c52_carbon_scenario%" == "nocc_hist" ...            # both inactive under the default cc
$ awk 'NR>=99 && NR<=101' core/macros.gms
$macro m_carbon_stock(land,carbon_density,item) (land(j2,item) * sum(ct,carbon_density(ct,j2,item,ag_pools)))$(...)
$ rg -n 'primforest' modules/52_carbon/normal_dec17/    # positive control: rg -c 'fm_carbon_density' input.gms -> 7
preloop.gms:36, preloop.gms:38        # comments only; no time freeze
```
**Confirmed**: yes.

**Fix**: replace the bullet with two —
"- No age-class curve: density comes straight from `fm_carbon_density(t_all,j,"primforest",c_pools)`, not
from a Chapman-Richards curve.
- Density is **not** constant over time in a default run: with `c52_carbon_scenario = "cc"`
(`config/default.cfg:1590`) the LPJmL densities are time-varying, so primary-forest carbon changes with
climate even at constant area (see §8.3). Only `nocc` / `nocc_hist`
(`modules/52_carbon/normal_dec17/input.gms:22-23`) freeze it."
Soften the table's "**Static**" cells to "no age-class tracking (see note)".

---

### B3 — 🟠 Major — `citation` — `config/default.cfg:1835` is three lines off (actual: 1838) `[own]`

**Doc**: `carbon_balance_conservation.md:101`

> "⚠️ Do **not** cite `config/default.cfg:1835` for this default: that line omits the `cfg$gms$` prefix its
> siblings carry, so it never reaches GAMS and the switch is currently unreachable from config"

**Reality**: the prefix-less assignment is at **`config/default.cfg:1838`**. Line **1835** is a comment
(`# *   actual: CO2 emissions for pricing are based on the difference of actual carbon stocks between time steps`)
— of which "omits the `cfg$gms$` prefix" is vacuous, since comments never carry it. The doc's warning is
*specifically about the syntax of the cited line*, so a reader who opens 1835 cannot evaluate it and may
dismiss a real defect. Filed **Major** (not Minor) precisely because the drift lands on content that
cannot support the claim made about it — the rubric's "citation drift to adjacent but different content"
trigger. The substance holds at the right line: `:1838` lacks the prefix while its neighbours `:1831
cfg$gms$c56_emis_policy` and `:1843 cfg$gms$maccs` carry it.

**Verify** — including the R53 "find the producer before calling anything unreachable" check:
```
$ awk 'NR>=1833 && NR<=1839 {printf "%d: %s\n", NR, $0}' config/default.cfg
1833: # * CO2 emissions subject to carbon pricing
1834: # * options:  actual, actualNoAcEst
1835: # *   actual: CO2 emissions for pricing are based on the difference of actual carbon stocks between time steps
1836: # *   actualNoAcEst: ...
1837: # *     without newly established forest and non-forest areas. ...
1838: c56_carbon_stock_pricing <- "actualNoAcEst"   # def = actualNoAcEst
$ rg -n 'c56_carbon_stock_pricing' .          # WHOLE develop tree incl. scripts/ and .R
./config/default.cfg:1838 · ./CHANGELOG.md:891 · ./modules/56_ghg_policy/price_aug22/{realization.gms:14,
  equations.gms:12,13,22, input.gms:90}
  -> no script/.R consumer of a bare `c56_carbon_stock_pricing`; nothing regenerates or re-prefixes it.
$ git log -L 1830,1840:config/default.cfg     # the line was ~:1503 at commit 96790b8ff -> drift confirmed
```
**Confirmed**: yes.

**Fix**: `config/default.cfg:1835` → `config/default.cfg:1838` (one occurrence, doc line 101). Everything
else in the sentence is still true and should be kept verbatim.

---

### B4 — 🟠 Major — `attribution_read` — `vm_maccs_costs` consumer set omits Module 36 `[re-derived]`

**Doc**: `carbon_balance_conservation.md:593` — "`vm_maccs_costs(i,factors)`: Labor and capital costs of
mitigation → to Module 11"

**Reality**: two consumers, both active in a default run — `modules/11_costs/default/equations.gms:28`
(`+ sum(factors,vm_maccs_costs(i2,factors))`; costs default `default`, `config/default.cfg:236`) **and**
`modules/36_employment/exo_may22/equations.gms:28`, which reads the `"labor"` slice to derive agricultural
employment. Module 36 has a **single** realization, selected at `config/default.cfg:1212`, so the 57→36
edge is unconditional. Role map: `read_by ['11','36','57']`. This matters because
`cross_module/modification_safety_guide.md` treats this file as authoritative for the carbon/GHG
dependency surface. Tier: between Critical (R20 wrong-consumer-set anchor) and Minor; **tie-break to
Major** — the doc's "→ to Module 11" is a routing arrow rather than an exhaustiveness claim.

**Verify**
```
$ rg -n 'vm_maccs_costs' modules/36_employment/ modules/11_costs/
modules/11_costs/default/equations.gms:28:      + sum(factors,vm_maccs_costs(i2,factors))
modules/36_employment/exo_may22/equations.gms:28: =e= (vm_maccs_costs(i2,"labor")) * (1 / sum(ct,...))
$ ls -d modules/36_employment/*/  ; grep -n 'cfg$gms$employment' config/default.cfg
modules/36_employment/exo_may22/   ; 1212:cfg$gms$employment <- "exo_may22"   # sole realization, default
```
**Confirmed**: yes.

**Fix**: "→ to Module 11 (total costs, `modules/11_costs/default/equations.gms:28`) **and Module 36**
(the `"labor"` slice only → agricultural employment, `modules/36_employment/exo_may22/equations.gms:28`)".

---

### B5 — 🟠 Major — `attribution_read` — CH₄ `vm_emissions_reg` consumer set omits Module 57 `[re-derived]`

**Doc**: `carbon_balance_conservation.md:573` — "`vm_emissions_reg(i,emis_source,"ch4")`: Regional CH₄
emissions → to Module 56"

**Reality**: `vm_emissions_reg` has two readers (role map `read_by ['56','57']`). Besides
`q56_emis_pricing` (`modules/56_ghg_policy/price_aug22/equations.gms:15-17`), Module 57 reads it in
`q57_labor_costs` and `q57_capital_costs` at `modules/57_maccs/on_aug22/equations.gms:38,40,48,50`, summed
over the **full** `emis_source` set × `pollutants_maccs57 /ch4, n2o_n_direct/`
(`modules/57_maccs/on_aug22/sets.gms:25-26`) — i.e. the CH₄ emissions Module 53 computes feed Module 57's
MACC cost integral. The doc records the 53↔57 relationship only in the other direction
(`im_maccs_mitigation`, `:578`), so §7.3 and §7.4 together present a one-way link where the code has a
loop. Same tier reasoning as B4.

**Verify**
```
$ awk 'NR>=35 && NR<=52 {printf "%d: %s\n", NR, $0}' modules/57_maccs/on_aug22/equations.gms
35: q57_labor_costs(i2) ..
37:   (sum((ct,emis_source,pollutants_maccs57), p57_maccs_costs_integral(ct,i2,emis_source,pollutants_maccs57)
38:       * vm_emissions_reg(i2,emis_source,pollutants_maccs57) / (1 - im_maccs_mitigation(...)))
45: q57_capital_costs(i2) ..  [same structure at :47-48]
$ awk 'NR>=25 && NR<=26' modules/57_maccs/on_aug22/sets.gms
  pollutants_maccs57(pollutants) ... / ch4, n2o_n_direct /
```
**Confirmed**: yes.

**Fix**: "→ to Module 56 (pricing, `modules/56_ghg_policy/price_aug22/equations.gms:15-17`) **and Module 57**
(MACC cost integration, `modules/57_maccs/on_aug22/equations.gms:38,48` — M57 divides by
`(1 − im_maccs_mitigation)` to recover the unmitigated level)."

---

### B6 — 🟡 Minor — `attribution_populate` — urban `vegc`/`litc` zeroing credited to Module 52 `[re-derived]`

**Doc**: `carbon_balance_conservation.md:263-264` (§3.7 table) — `| vegc | Fixed to zero | None | 52 |`,
`| litc | Fixed to zero | None | 52 |`

**Reality**: Module 52 never touches urban `vegc`/`litc`. Its only urban statement is the *soilc* override
`fm_carbon_density(t_all,j,"urban","soilc") = fm_carbon_density(t_all,j,"other","soilc")`
(`modules/52_carbon/normal_dec17/input.gms:35`) — which the table's third row already attributes correctly
to "52, 59". The zeroing belongs to Module 34's default realization:
`vm_carbon_stock.fx(j,"urban",ag_pools,stockType) = 0;` (`modules/34_urban/exo_nov21/presolve.gms:8`, with
`ag_pools /vegc, litc/` at `modules/56_ghg_policy/price_aug22/sets.gms:209-210`). The doc's own §7.5
(`:622`) states this correctly, so the table is a local inconsistency — but it is the row a reader trying
to *enable* urban vegetation carbon would follow, and it sends them to the wrong module.

**Verify**
```
$ rg -n -i 'urban' modules/52_carbon/normal_dec17/           # positive control: rg -c fm_carbon_density input.gms -> 7
realization.gms:10 (prose list) · preloop.gms:41 (unrelated comment) · input.gms:33-35 (soilc only)
$ grep -n 'vm_carbon_stock' modules/34_urban/exo_nov21/presolve.gms
8:vm_carbon_stock.fx(j,"urban",ag_pools,stockType) = 0;
```
**Confirmed**: yes.

**Fix**: Module column `52` → `34` for the vegc and litc rows; Source → "fixed by `vm_carbon_stock.fx`,
`modules/34_urban/exo_nov21/presolve.gms:8`". Leave the soilc row at "52, 59".

---

### B7 — 🟡 Minor — `formula` — §8.4 uses the legacy share (44%) as the 5-year convergence share `[own]`

**Doc**: `carbon_balance_conservation.md:734` — "- Year 5: 44% toward new equilibrium = +4 tC/ha"

**Reality**: `i59_lossrate(t) = 1 - 0.85**m_yeardiff(t)`
(`modules/59_som/cellpool_jan23/preloop.gms:45`), so at 5 years the share that has converged is
`1 − 0.85⁵ = 0.556`; **44% is the legacy remainder** (`0.85⁵ = 0.444`) — exactly as this same document
states correctly at `:402` (table) and `:412` ("After 5 years: 56% toward new equilibrium, 44% legacy").
The derived value inherits the error: 0.556 × 9 tC/ha = **+5.0**, not +4. The Year-10 (80% → +7.2) and
Year-20 (96% → +8.6) rows are correct. Likely origin: the upstream code comment at
`modules/59_som/cellpool_jan23/preloop.gms:42-43` ("resulting in 44% in 5 years, 80% in 10 years and 96%
in 20 years"), which is itself internally inconsistent — 80% and 96% are convergence shares, 44% is a
remainder.

**Verify**
```
$ python3 -c "print(1-0.85**5, 1-0.85**10, 1-0.85**20)"
0.5562978515625 0.8031256469913329 0.9612434174407943
$ awk 'NR==45' modules/59_som/cellpool_jan23/preloop.gms
i59_lossrate(t)=1-0.85**m_yeardiff(t);
```
**Confirmed**: yes.

**Fix**: "Year 5: 56% toward new equilibrium = +5.0 tC/ha"; optionally note that the code comment at
`preloop.gms:42-43` quotes the 5-year *remainder*, so a later editor does not "correct" it back.

---

### B8 — 🟡 Minor — `default_value` — FLU presented as a selectable category with a default; no such set exists `[own]`

**Doc**: `carbon_balance_conservation.md:429` ("**FLU** (Land Use): Cropland / Set-aside / Perennial
(default: annual cropland)") and the parallel bullet at `:137` ("Land use: Cropland vs set-aside")

**Reality**: `cellpool_jan23` has no FLU category set and no such default. Its only management sets are
`tillage59 /full_tillage,reduced_tillage,no_tillage/` and
`inputs59 /low_input,medium_input,high_input_nomanure,high_input_manure/`
(`modules/59_som/cellpool_jan23/sets.gms:13-17`) — which is exactly why the adjacent FMG and FI bullets
*are* correct (`i59_tillage_share(i,"full_tillage")=1`, `i59_input_share(i,"medium_input")=1`,
`preloop.gms:52-55`). The land-use factor is resolved **per MAgPIE crop type**:
`f59_cratio_landuse(i,climate59_2019,kcr)` (`input.gms:43`), consumed at `preloop.gms:60-67`. Fallow gets
a separate hard-wired factor (maize × reduced tillage × low input, `preloop.gms:73-77`) and cropland tree
cover a fixed `i59_cratio_treecover = 1` (`preloop.gms:82`). The only `setaside` token in the tree is a
**crop-rotation scenario name** in the *non-default* `modules/30_croparea/detail_apr24/sets.gms:13` —
unrelated to M59's C-ratio.

**Verify**
```
$ rg -in 'set.?aside|perennial' modules/59_som/
static_jan19/realization.gms:16 (prose) · cellpool_jan23/input.gms:24 (prose)   # no set member
$ rg -c 'cratio' modules/59_som/cellpool_jan23/preloop.gms       # POSITIVE CONTROL -> 13 (grep works here)
$ rg -in 'set.?aside' .        # whole tree: only 30_croparea/detail_apr24 (non-default) + CHANGELOG
```
**Confirmed**: yes.

**Fix**: `:429` → "- **FLU** (Land Use): resolved **per crop type**, not as selectable IPCC categories —
`f59_cratio_landuse(i,climate59_2019,kcr)` (`modules/59_som/cellpool_jan23/preloop.gms:60-67`). There is
no set-aside/perennial switch; fallow has its own fixed factor `i59_cratio_fallow` (`preloop.gms:73-77`)
and cropland tree cover a fixed `i59_cratio_treecover = 1` (`preloop.gms:82`)." Amend `:137` likewise, and
note that the tillage/input shares are not exposed in `config/default.cfg` at all.

---

### B9 — 🟡 Minor — `formula` — §7.2 still carries the one-term shorthand the doc itself retracts `[re-derived]`

**Doc**: `carbon_balance_conservation.md:552` —
`v59_som_target(j,"crop") = Σ(crops) Area × C_ratio × Natural_density`

**Reality**: `q59_som_target_cropland` (`modules/59_som/cellpool_jan23/equations.gms:20-27`) has **four**
terms — cropland base, SCM uplift, `vm_fallow(j2) * i59_cratio_fallow(j2)`, and
`vm_treecover(j2) * i59_cratio_treecover`. The same document denounces exactly this shorthand at `:134`
("The simplified `Σ(crops) Area × C_ratio × Natural_density` shorthand used in earlier versions of this
doc omitted terms 2-4"). The §3.1 fix was applied; the §7.2 duplicate was left behind, so a reader landing
in §7.2 first gets the retracted version — three lines below a "Receives" list that correctly names
`vm_fallow` and `vm_treecover`.

**Verify**
```
$ awk 'NR>=20 && NR<=27 {printf "%d: %s\n", NR, $0}' modules/59_som/cellpool_jan23/equations.gms
20: q59_som_target_cropland(j2) ..
22:   =e= (sum((kcr,w), vm_area(j2,kcr,w) * i59_cratio(j2,kcr,w)) +
23:        sum((kcr,w,ct), vm_area(j2,kcr,w) * i59_scm_target(ct,j2) * i59_cratio(j2,kcr,w) * (i59_cratio_scm(j2) - 1))
25:        + vm_fallow(j2) * i59_cratio_fallow(j2)
26:        + vm_treecover(j2) * i59_cratio_treecover) * sum(ct,f59_topsoilc_density(ct,j2));
```
**Confirmed**: yes.

**Fix**: replace with "cropland base + SCM uplift + fallow + treecover, all × natural density — see §3.1
for the full four-term form (`modules/59_som/cellpool_jan23/equations.gms:20-27`)".

---

### B10 — 🟡 Minor — `citation` — four Module-52 signatures given over `t` instead of `t_all` `[re-derived]`

**Doc**: `carbon_balance_conservation.md:107` (under a "**Verified**:" badge) and `:513-516`; same
shorthand at `:699`

**Reality**: all four are declared over `t_all` —
`table fm_carbon_density(t_all,j,land,c_pools)` (`modules/52_carbon/normal_dec17/input.gms:16`) and
`pm_carbon_density_secdforest_ac(t_all,j,ac,ag_pools)` / `pm_carbon_density_other_ac(t_all,…)` /
`pm_carbon_density_plantation_ac(t_all,…)` (`modules/52_carbon/normal_dec17/declarations.gms:9,11,12`).
The distinction is load-bearing for **B2**: the point of `t_all` is that these carry the full annual
climate trajectory, and `start.gms` fills them over `t_all`, not `t`.
*(Indexing them with `t ⊂ t_all` in a formula would be legal GAMS — the defect is that the doc presents
these as declared signatures under a "Verified" badge.)*

**Verify**
```
$ awk 'NR>=9 && NR<=13 {printf "%d: %s\n", NR, $0}' modules/52_carbon/normal_dec17/declarations.gms
9:  pm_carbon_density_secdforest_ac(t_all,j,ac,ag_pools) ...
11: pm_carbon_density_other_ac(t_all,j,ac,ag_pools) ...
12: pm_carbon_density_plantation_ac(t_all,j,ac,ag_pools) ...
$ awk 'NR==16' modules/52_carbon/normal_dec17/input.gms
table fm_carbon_density(t_all,j,land,c_pools) LPJmL carbon density for land and carbon pools (tC per ha)
```
**Confirmed**: yes.

**Fix**: `t` → `t_all` at `:107`, `:513-516`, `:699`.

---

### B11 — 🟡 Minor — `default_value` — the default `c56_emis_policy` price mask is never mentioned `[re-derived]`

**Doc**: `carbon_balance_conservation.md:583` — "Both are priced in Module 56 — but by **different
paths** …"

**Reality**: the *paths* description is exactly right (verified in §2.3). What is missing is the default
*scope*. Which sources carry a non-zero price is masked by `c56_emis_policy`, default `reddnatveg_nosoil`
(`config/default.cfg:1831`; `modules/56_ghg_policy/price_aug22/input.gms:86`), applied in a loop over
`t_all` at `modules/56_ghg_policy/price_aug22/preloop.gms:85-91` — hard-coded `reddnatveg_nosoil` for
years ≤ `sm_fix_SSP2` (`:87`), `%c56_emis_policy%` thereafter (`:89`):
`im_pollutant_prices(...) = im_pollutant_prices(...) * f56_emis_policy(<scenario>,pollutants,emis_source)`.
Per the config's own description (`config/default.cfg:1811`) that scenario prices only "Above ground CO2
emis from LUC in forest and natveg; all CH4 and N2O emissions" — so in a default run cropland/pasture/
urban CO₂ and **all** `soilc` CO₂ are computed by `q56_emis_pricing_co2` but priced at zero. The switch
appears nowhere in this document, which is the one it would most naturally be looked up in.

**Scope of verification (stated because it bounds the claim)**: the switch, its default, the masking site
and the loop structure are code-verified. The per-source 0/1 values live in `f56_emis_policy.csv`, a
run-time input (`modules/56_ghg_policy/input/` holds only a `files` manifest in a clean checkout), so the
"which sources" semantics rest on the config comment at `:1811`, not on read data.

**Verify**
```
$ awk 'NR>=85 && NR<=91 {printf "%d: %s\n", NR, $0}' modules/56_ghg_policy/price_aug22/preloop.gms
85: loop(t_all,
86:  if(m_year(t_all) <= sm_fix_SSP2,
87:   im_pollutant_prices(...) = im_pollutant_prices(...) * f56_emis_policy("reddnatveg_nosoil",pollutants,emis_source);
88:  else
89:   im_pollutant_prices(...) = im_pollutant_prices(...) * f56_emis_policy("%c56_emis_policy%",pollutants,emis_source);
$ grep -n 'c56_emis_policy' config/default.cfg          # 1831: cfg$gms$c56_emis_policy <- "reddnatveg_nosoil"
$ awk 'NR==1811' config/default.cfg                     # "(Above ground CO2 emis from LUC in forest and natveg; ...)"
```
**Confirmed**: yes (for the switch/default/masking site; see scope note).

**Fix**: append to §7.3 — "Both reach the pricing equations, but what carries a non-zero price is masked by
`c56_emis_policy` (default `reddnatveg_nosoil`, `config/default.cfg:1831`), applied at
`modules/56_ghg_policy/price_aug22/preloop.gms:87,89`. Under that default only above-ground CO₂ from
forest and natveg is priced; cropland/pasture/urban CO₂ and all `soilc` CO₂ are computed but priced at
zero."

---

### B12 — 🟡 Minor — `set_membership` — §9.1's consistency check never selects the `"actual"` stock slice `[re-derived]`

**Doc**: `carbon_balance_conservation.md:760-778` (the R stock-change consistency snippet)

**Reality**: both symbols the snippet reads carry a `stockType` dimension —
`ov_carbon_stock(t,j,land,c_pools,stockType,type)`
(`modules/56_ghg_policy/price_aug22/declarations.gms:49`) and
`pcm_carbon_stock(j,land,c_pools,stockType)` (`:19`, populated for both slices,
`modules/59_som/cellpool_jan23/preloop.gms:30-35`) — while `q52_emis_co2_actual` uses **only** the
`"actual"` slice (`modules/52_carbon/normal_dec17/equations.gms:19`). The snippet's
`dimSums(stock_change, dim=c("cell","land","c_pools"))` never restricts `stockType`, and the two slices
differ by construction for every age-class land pool (`core/macros.gms:104-106`). Additionally `field="l"`
is passed on a **parameter** read (`pcm_carbon_stock`), where it is meaningless.

**Scope**: the dimensions and the slice mismatch are code-verified; I did not execute the R, so the exact
`stopifnot` failure mode is inference, not reproduction.

**Verify**
```
$ rg -n 'ov_carbon_stock|pcm_carbon_stock' modules/56_ghg_policy/price_aug22/declarations.gms
19: pcm_carbon_stock(j,land,c_pools,stockType)              Carbon stock ... (mio. tC)
49: ov_carbon_stock(t,j,land,c_pools,stockType,type)        Carbon stock ... (mio. tC)
$ awk 'NR==19' modules/52_carbon/normal_dec17/equations.gms   # uses only ...,"actual")
```
**Confirmed**: yes (dimension mismatch); the R runtime behaviour is not reproduced.

**Fix**: select `[,,"actual"]` on both `carbon_stock_prev` and `carbon_stock_curr` before differencing, and
drop `field="l"` from the `pcm_carbon_stock` read.

---

### B13 — 🟡 Minor — `mechanism` — SCM uplift is parameterised on `high_input_nomanure`, not the with-manure factor `[own]`

**Doc**: `carbon_balance_conservation.md:730` — "- SCM equilibrium: 59 tC/ha (high input factor = 1.17)",
read against `:438` where **1.17** is identified as `Cropland + No-till + High input + **manure**`.

**Reality**: the SCM uplift factor is
`i59_cratio_scm(j) = Σ_climate59 climate_share × f59_cratio_inputs(climate59,"high_input_nomanure")`
(`modules/59_som/cellpool_jan23/preloop.gms:88-90`), with the code comment at `:85-86` stating explicitly
*"For dedicated soil carbon management we use the `high_input_nomanure` values from the IPCC guidelines"*.
The arithmetic in §8.4 is flagged illustrative, but *which IPCC input column dedicated SCM maps to* is a
mechanism claim, and as written it points at the wrong one. (The numeric magnitude of the difference lives
in `f59_ch5_F_I.csv`, a run-time input — **not** checked, and the fix should not assert one.)

**Verify**
```
$ awk 'NR>=85 && NR<=90 {printf "%d: %s\n", NR, $0}' modules/59_som/cellpool_jan23/preloop.gms
85: *' For dedicated soil carbon management we use the `high_input_nomanure` values from the IPCC guidelines,
88: i59_cratio_scm(j) = sum(climate59, sum(clcl_climate59(clcl,climate59), pm_climate_class(j,clcl)) *
90:                        f59_cratio_inputs(climate59,"high_input_nomanure"));
```
**Confirmed**: yes.

**Fix**: "- SCM equilibrium: 59 tC/ha (illustrative; note the code's SCM factor `i59_cratio_scm` is built
from the IPCC **`high_input_nomanure`** column, `modules/59_som/cellpool_jan23/preloop.gms:88-90` — not
the with-manure factor quoted in §5.3)".

---

### B14 — 🟡 Minor — `set_membership` — §3.1 truncates the 4-member `inputs59` set `[own]`

**Doc**: `carbon_balance_conservation.md:139` — "- Input level: Low, medium, high without manure
(default: medium)"

**Reality**: `inputs59` is a closed 4-member set —
`/low_input, medium_input, high_input_nomanure, high_input_manure/`
(`modules/59_som/cellpool_jan23/sets.gms:16-17`). The doc's list drops `high_input_manure`. §5.3 (`:430`)
enumerates all four correctly, so this is a local truncation — but `high_input_manure` is the very
category §5.3's `F = 1.17` example rests on, which is how B13 arises.

**Verify**
```
$ awk 'NR>=16 && NR<=17 {printf "%d: %s\n", NR, $0}' modules/59_som/cellpool_jan23/sets.gms
16: inputs59 Input management categories of IPCC
17: /low_input,medium_input,high_input_nomanure,high_input_manure/
```
**Confirmed**: yes.

**Fix**: "- Input level: `low_input` / `medium_input` / `high_input_nomanure` / `high_input_manure`
(`modules/59_som/cellpool_jan23/sets.gms:16-17`; default `medium_input`, `preloop.gms:54-55`)".

---

### B15 — 🟢 Informational — `set_membership` — "appears in exactly these equations" is not exhaustive `[re-derived]`

**Doc**: `carbon_balance_conservation.md:595` — "**Applies to** (verified against code — the mitigation
factor `(1 - im_maccs_mitigation)` appears in exactly these equations)"

**Reality**: the application list that follows is correct and complete **for emission-source equations**,
but the literal `(1 - im_maccs_mitigation(...))` also appears twice inside Module 57 itself
(`modules/57_maccs/on_aug22/equations.gms:38,48`) as a **divisor** that grosses mitigated emissions back up
to the unabated baseline for the MACC cost integral. The header is also mildly inconsistent with its own
Module-50 bullet, whose code form is an NUE uplift
`im_maccs_mitigation * X / (1 + im_maccs_mitigation * (X − 1))`
(`modules/50_nr_soil_budget/macceff_aug22/presolve.gms:54-64`), not a `(1 − …)` factor.

**Verify**
```
$ rg -n 'im_maccs_mitigation' modules/ | grep -v declarations.gms
50_nr_soil_budget/macceff_aug22/presolve.gms:56,58,61,63 · 51_nitrogen/rescaled_jan21/equations.gms:71
53_methane/ipcc2006_aug22/equations.gms:29,52,63 · 57_maccs/on_aug22/equations.gms:38,41,48,51
57_maccs/on_aug22/preloop.gms (populator)
```
**Confirmed**: yes.

**Fix**: "the mitigation factor is applied to emissions in exactly these equations (Module 57's own cost
equations divide *by* `(1 − im_maccs_mitigation)` to back out unmitigated emissions —
`modules/57_maccs/on_aug22/equations.gms:38,48` — which is bookkeeping, not a second application)".

---

## 4. Deferred (no edit proposed)

1. **§6.2 k ranges** ("Tropical k ≈ 0.05-0.08", "Temperate 0.03-0.05", "Boreal 0.02-0.03") and **§5.3
   stock-change factors** (`0.69`, `1.17`): all come from run-time input tables (`f52_growth_par.csv`,
   `f59_ch5_F_*`); `modules/*/input/` holds only a `files` manifest in a clean checkout. Both labelled
   illustrative. Not checked.
2. **§7.4 "Mitigation fractions (0 to ~0.3)"** — derived from `f57_maccs_*_2022`, absent input tables.
3. **§7.2 "`vm_land(j,land)`: Non-cropland areas from Module 10"** — `vm_land` is DECLARED in `10_land`
   but the individual slices are POPULATED by M29 (`detail_apr24/equations.gms:12`), M32 (`:56`), M35
   (`:11,13`) and M31/M34 via bounds; M10 supplies the sum-to-total and transition constraints. The
   doc's list is a "Receives" list, not a populator claim — **not flagged**, but a future auditor should
   not read it as one.
4. **§7.3 M53 "Receives" list** omits `vm_manure` (M55), read by `q53_emissionbal_ch4_awms`
   (`modules/53_methane/ipcc2006_aug22/equations.gms:50`). Incompleteness in an illustrative list.
5. **Doc header "Modules Covered: 52, 53, 59 (57 for mitigation costs)"** understates real coverage
   (56, 58, 29, 30, 31, 32, 34, 35, 14, 50, 51 all appear substantively). Metadata drift.
6. **§3.1 "Crop-specific equilibrium based on residue production"** — the crop-specific FLU factors are
   exogenous inputs; whether preprocessing derived them from residue production is a preproc-agent
   question.
7. **§3.6/§10.2 "unverified lead"** on the `secdforest` yield-vs-carbon-curve mismatch (`:253-255`): the
   doc already labels it "an unverified lead, not an established defect". The code facts it rests on
   (`q35_prod_secdforest` reading calibrated `im_growing_stock`; `q35_carbon_secdforest` reading the
   blended `p35_carbon_density_secdforest`; natural-origin bound at
   `modules/35_natveg/pot_forest_may24/presolve.gms:177-180`) all check out; the *conclusion* was not
   re-derived here.
8. **§9.2 / §9.3 R snippets** beyond the B12 defect: GDX symbol names verified against `postsolve.gms`,
   but not executed.
9. **Structural, not a bug**: the `s52_growingstock_calib` warning box is byte-identical at `:180` and
   `:479`. Both are (post-B1) wrong in the same way and any fix must be applied twice — a maintenance
   hazard worth collapsing to one canonical block plus a cross-reference.
10. **Code-side observation, not a doc bug**: `modules/59_som/cellpool_jan23/realization.gms:9` describes
    itself as "The cellpool_aug23 realization" while the directory is `cellpool_jan23`. Upstream MAgPIE
    typo; the doc does not repeat it.

---

## 5. Method notes

- **Grep discipline**: every absence claim (B8's set-aside, B3's `c56_carbon_stock_pricing` consumer set,
  B6's M52-urban) was run as a standalone `rg -n` with a **positive control** in the same directory before
  concluding absence. No `find -exec grep +` chains, no bare `grep -r`.
- **Attribution**: `audit/integrated/depth_rolemap.json` was consulted FIRST for every
  `vm_`/`pm_`/`fm_`/`pcm_`/`im_` claim, then confirmed with both-endpoint greps (`NAME(` and `NAME.`).
  Role map and code agreed in every case; no discrepancy to report.
- **R53 check applied to B3**: before endorsing the doc's "never reaches GAMS" claim, the whole repo root
  (including `scripts/` and `.R`) was grepped for any producer/consumer of a bare
  `c56_carbon_stock_pricing`. None exists — the doc's claim survives; only its line number does not.
- **Read-side gate**: the prior file at this path asserted 13 defects. Each of the ones I had not
  originated was re-derived from code before admission; none was accepted on the prior file's authority.
  Two of its severity calls I revised on my own reading (its C3 → my B3, Minor → Major, because the drift
  lands on a line that cannot support the claim; its C5/C6 → my B4/B5, Minor → Major, because the R20
  anchor treats an incomplete consumer set as a refactor hazard). Its deferred item 3 I promoted to a bug
  (B13) after scoping the claim to the IPCC *category* rather than the numeric factor, which is
  code-verifiable at `preloop.gms:88-90` independent of the gitignored CSV. One finding it did not carry
  is new here (B14).
