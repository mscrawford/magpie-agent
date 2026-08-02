# R60 depth audit — `cross_module/carbon_balance_conservation.md`

**Lens**: `citation_formula` (enter from file:line citations; check existence, range, token presence, formula fidelity)
**Ground truth**: MAgPIE `develop` read-only worktree, HEAD `2c02843eccd8483e0a5617864213c711c3dcd5de` ("Merge pull request #919 from alexkoberle/dyn_reg_tau"), working tree clean.
**Attribution ground truth**: `audit/integrated/depth_rolemap.json`, consulted first for every `vm_*`/`pm_*`/`im_*`/`fm_*`/`pcm_*` role claim, then confirmed by both-endpoints greps.
**Date**: 2026-08-02

> **Merge note (read before diffing against an earlier copy).** Two earlier `citation_formula` passes have occupied this path. This file supersedes both and is a **strict superset**. Every retained finding was **independently re-derived from code in this session** — role map queried afresh, greps re-run, arithmetic re-computed with `python3` — not relayed from the prior text. One finding is **new** (B13), in a section the prior passes did not probe. No prior finding was dropped, and no prior severity was silently changed.

---

## Scope and method

1. **Mechanical citation sweep** — extracted every citation in the doc, then `test -f` + `wc -l` + range check on each. **Zero missing files, zero out-of-range line numbers, zero wrong realization names.**
2. **Token-presence check** — read each cited line/range; confirmed it contains the claimed identifier or construct.
3. **Formula fidelity** — re-derived every quoted equation against source; re-computed every arithmetic result with `python3`.
4. **Attribution** — role map first, then both-endpoints greps (`NAME(` **and** `NAME.`), each grep isolated as its own command, each absence claim backed by a second method plus a positive control.
5. **Defaults** — every cited default cross-checked in *both* `input.gms` and `config/default.cfg`; every realization confirmed against `cfg$gms$<module>`.

**Claims verified: ~140.** **Bugs: 13** (1 Critical, 3 Major, 8 Minor, 1 Informational).

---

## What is CORRECT (recorded so future rounds don't re-litigate)

- **All 16 realizations named** are the current defaults: `carbon=normal_dec17` (`config/default.cfg:1577`), `som=cellpool_jan23` (1937), `methane=ipcc2006_aug22` (1604), `ghg_policy=price_aug22` (1634), `maccs=on_aug22` (1843), `peatland=v2` (1874), `nitrogen=rescaled_jan21` (1571), `nr_soil_budget=macceff_aug22` (1500), `cropland=detail_apr24` (814), `croparea=simple_apr24` (915), `natveg=pot_forest_may24` (1156), `forestry=dynamic_may24` (995), `urban=exo_nov21` (1147), `past=endo_jun13` (988), `yields=managementcalib_aug19` (357), `land=landmatrix_dec18` (232).
- **§4.1 `q52_emis_co2_actual`** is quoted verbatim-correct against `modules/52_carbon/normal_dec17/equations.gms:16-19`.
- **§3.1 `v59_som_target(j,"crop")` 4-term expansion** matches `modules/59_som/cellpool_jan23/equations.gms:20-27` term for term, including the subtlety that `i59_cratio_treecover` carries no `j` index while `i59_cratio_fallow(j)` does (`preloop.gms:73`).
- **§5.1 `q59_som_pool`** matches `equations.gms:46-52`; **§7.2 `q59_carbon_soil`** matches `equations.gms:61-64`; **§6.1 Chapman-Richards** matches `core/macros.gms:18` (`S + (A-S)*(1-exp(-k*(ac*5)))**m`) exactly.
- **`vm_carbon_stock` populator set** (§7.5): M29/M31/M32/M34/M35 + M59-soilc — exactly the role map's `populated_by: ['29','31','32','34','35','59']`; confirmed at `modules/29_cropland/detail_apr24/equations.gms:39`, `modules/31_past/endo_jun13/equations.gms:23`, `modules/32_forestry/dynamic_may24/equations.gms:108`, `modules/34_urban/exo_nov21/presolve.gms:8`, `modules/35_natveg/pot_forest_may24/equations.gms:43,50,54`, `modules/59_som/cellpool_jan23/equations.gms:62`.
- **"fill both slices" (§2.3)** holds: every populating equation carries `stockType` as a free index, and `m_carbon_stock` / `m_carbon_stock_ac` (`core/macros.gms:99-106`) emit an `"actual"` branch and an `"actualNoAcEst"` branch, the latter summing over `ac_sub` instead of `ac`. Non-obvious and correctly stated.
- **§7.3 parallel-not-serial claim** — `q56_emis_pricing` (`modules/56_ghg_policy/price_aug22/equations.gms:15-17`) is indexed over `emis_annual`, disjoint from `emis_oneoff` (`core/sets.gms:314-322`); M56 recomputes CO2 itself in `q56_emis_pricing_co2` (`:19-22`). Whole-module grep finds `vm_emissions_reg` in M56 only at `equations.gms:17` plus postsolve/declarations — so M56 genuinely does **not** consume M52's `vm_emissions_reg(...,"co2_c")`. MANDATE 21 / R51 trap correctly avoided.
- **§7.4 MACC application map** — complete and exact. Whole-tree `rg` finds `im_maccs_mitigation` only at `modules/50_nr_soil_budget/macceff_aug22/presolve.gms:56,58,61,63`, `modules/51_nitrogen/rescaled_jan21/equations.gms:71`, `modules/53_methane/ipcc2006_aug22/equations.gms:29,52,63` — matching role map `read_by: ['50','51','53','57']`. "NOT residue burning" holds (`:70-72` carries no mitigation factor); `maccs_ch4 / rice_ch4, ent_ferm_ch4, awms_ch4 /` verbatim at `modules/57_maccs/on_aug22/sets.gms:28-29`; rice N2O genuinely zero (`rice` absent from `emis_source_n51`, `modules/51_nitrogen/rescaled_jan21/sets.gms:15-16`; `preloop.gms:8-10` fixes all then selectively relaxes).
- **§10.2 item 7 (peatland)** — `q58_peatland_emis → vm_emissions_reg(i,"peatland",poll58)` at `modules/58_peatland/v2/equations.gms:91-92`; `peatland ∈ emis_annual` at `core/sets.gms:322`; `s58_fix_peatland = 2020` (`config/default.cfg:1931`); `peatland = "v2"` (`:1874`); realization description matches `modules/58_peatland/v2/realization.gms:8-17`. All exact.
- **§5.2 convergence table** (15 / 56 / 80 / 96 %) is arithmetically correct against `i59_lossrate(t)=1-0.85**m_yeardiff(t)` (`modules/59_som/cellpool_jan23/preloop.gms:45`). **Note for future editors**: the code comment at `preloop.gms:42` says "44% in 5 years", which is the **legacy remainder**, not the loss rate — §5.2 is right and the code comment is the inconsistent one. Do **not** "correct" §5.2 to match it.
- **Uncalibrated-curve consumer set** (M14 `im_growing_stock_ysf` `presolve.gms:66`, M29 tree cover `preloop.gms:46,48`, M32 aff+NDC `presolve.gms:59,61,68`, M35 youngsecdf `presolve.gms:242` + maturation test `:117`) is **complete** — every cited line contains the claimed `_uncalib` read.
- **Defaults**: `s52_growingstock_calib = 1` hard-coded at `modules/52_carbon/normal_dec17/input.gms:46` and genuinely absent from `config/default.cfg` (positive control: `s58_fix_peatland` in the same grep returns `:1931`); `s59_scm_target = 0` (`:1978`); `c59_irrigation_scenario = "on"` (`:1956` + `modules/59_som/cellpool_jan23/input.gms:61`, with the `off` neutralisation at `input.gms:70`); `i59_tillage_share("full_tillage")=1` and `i59_input_share("medium_input")=1` (`preloop.gms:53,55`).
- **§2.3 subsoil derivation** — `i59_subsoilc_density(t_all,j) = fm_carbon_density(t_all,j,"other","soilc") - f59_topsoilc_density(t_all,j)` (`modules/59_som/cellpool_jan23/preloop.gms:12`). The doc's "derived from M52 `fm_carbon_density` of **other** land" is exact; note the *other* realization (`static_jan19/preloop.gms:20`) uses `"secdforest"` instead, so the doc is right only because it correctly scopes to `cellpool_jan23`.
- **Commit `6b00f9dea`** exists, dated **2026-07-01**, author `florianh`, subject "Fix youngsecdf wood production: use uncalibrated growing stock". The doc's quoted motivation ("almost no carbon for secondary-forest-level wood volumes") is **verbatim** from the commit body. §3.6 claim exact.
- **§3.6 caveat 2 (unverified lead)** checks out as stated: `q35_prod_secdforest` (`modules/35_natveg/pot_forest_may24/equations.gms:144-147`) reads the purely calibrated `im_growing_stock(...,"secdforest")` while `q35_carbon_secdforest` (`:49-51`) reads the blend `p35_carbon_density_secdforest` (`presolve.gms:248-252`); natural-origin area bounded at `presolve.gms:177-180`. The "unverified lead, not an established defect" framing is appropriate and should stay.
- **Sets**: `land` = 7 (`core/sets.gms:250-251`), `emis_oneoff` = 21 = 7×3 (`:314-318`), `emis_land` mapping (`:332-354`), `c_pools /vegc,litc,soilc/` (`:324-325`), `stockType /actual, actualNoAcEst/` (`modules/56_ghg_policy/price_aug22/sets.gms:212-213`), `noncropland59 /past, forestry, primforest, secdforest, other, urban/` (`modules/59_som/cellpool_jan23/sets.gms:10-11`) — which is what makes the "forestry/pasture/secdforest soilc converges to natural density" claims correct.
- **`vm_carbon_stock_croparea` chain** (§7.5) — declared and populated in `modules/30_croparea/simple_apr24/declarations.gms:20` / `equations.gms:50`, read by M29 at `modules/29_cropland/detail_apr24/equations.gms:40`. Role map `populated_by: ['30'], read_by: ['29','30']`. The doc's "M30 computes it; M29 is the direct populator of the crop slice" is exactly right, including the direction.

---

## BUGS

### B1 — CRITICAL — `attribution_read` — calibrated-curve consumer set omits Module 32 entirely (and M14's plantation read)

**doc_line**: `carbon_balance_conservation.md:180` (identical text repeated verbatim at `:479`)

**Claim in doc**:
> "M14 and M35 read the CALIBRATED curve as well - M14 for regular secdforest growing stock (`modules/14_yields/managementcalib_aug19/presolve.gms:44`), M35 for secdforest carbon density, which it BLENDS with the uncalibrated curve by natural-origin area share (`modules/35_natveg/pot_forest_may24/presolve.gms:248-252`)."

**Reality in code**: **Module 32 (`dynamic_may24`, the default) is a major consumer of the calibrated `pm_carbon_density_plantation_ac` at three sites**, and **M14 reads it at a fourth site the doc does not mention**:

| Site | What it drives |
|---|---|
| `modules/32_forestry/dynamic_may24/presolve.gms:65` | `p32_carbon_density_ac(t,j,"plant",ac,ag_pools)` → `q32_carbon` (`equations.gms:108-109`) → **`vm_carbon_stock(j2,"forestry",ag_pools,stockType)`** — the entire timber-plantation carbon stock |
| `modules/32_forestry/dynamic_may24/preloop.gms:18` | `p32_carbon_density_ac_forestry` → marginal increment → **rotation lengths** |
| `modules/32_forestry/dynamic_may24/preloop.gms:56` | `p32_avg_increment` → rotation rule under `c32_rot_calc_type == mean_annual_increment` |
| `modules/14_yields/managementcalib_aug19/presolve.gms:26` | `im_growing_stock(t,j,ac,"forestry")` — plantation wood yield |

Role map corroborates: `pm_carbon_density_plantation_ac → read_by: ['14','32','52']` (52 = self-populate).

**Why Critical**: this is the R20 immutable anchor's exact bug class on the exact same parameter family — *"module doc cited `pm_carbon_density_ac` as having three consumers when commit added two more (M32 afforestation + NDC presolve) … → **Critical** (doc said wrong consumer set; user would have missed two modules in a refactor)"* — and the rubric's latent-doc-bug mandate restates it: *"a wrong producer/consumer set is **Critical** per the R20 anchor"*. Aggravating: the block sits directly under §3.3 "Forestry (Plantations)", the one section *about* plantation carbon, and its preceding sentence enumerates M32 only as an **un**calibrated-curve reader. A developer touching `s52_growingstock_calib`, the FRA-2025 bisection, or `i52_m_avg_plant` would conclude the M32 plantation-carbon and rotation-length machinery is unaffected. It is the primary consumer.

*Severity is the one arguable call here*: the doc's phrasing is additive ("as well") rather than explicitly exhaustive, which would argue Major under the generic tie-breaker. The latent-doc-bug mandate's explicit naming of wrong consumer sets as Critical overrides, and the parallel construction with the preceding exhaustive uncalibrated list invites an exhaustive reading.

**file_evidence**: `modules/32_forestry/dynamic_may24/presolve.gms:65`; `modules/32_forestry/dynamic_may24/preloop.gms:18`; `modules/32_forestry/dynamic_may24/preloop.gms:56`; `modules/14_yields/managementcalib_aug19/presolve.gms:26`; sink at `modules/32_forestry/dynamic_may24/equations.gms:108-109`.

**verify_cmd** (two methods + positive control, each isolated):
```
$ rg -n "pm_carbon_density_plantation_ac" modules/ core/ | rg -v uncalib
modules/32_forestry/dynamic_may24/preloop.gms:18:p32_carbon_density_ac_forestry(t_all,j,ac) = pm_carbon_density_plantation_ac(t_all,j,ac,"vegc");
modules/32_forestry/dynamic_may24/preloop.gms:56:  p32_avg_increment(t_all,j,ac) = pm_carbon_density_plantation_ac(t_all,j,ac,"vegc") / ((ord(ac)+1)*5);
modules/32_forestry/dynamic_may24/presolve.gms:65:p32_carbon_density_ac(t,j,"plant",ac,ag_pools) = pm_carbon_density_plantation_ac(t,j,ac,ag_pools);
modules/14_yields/managementcalib_aug19/presolve.gms:26:     pm_carbon_density_plantation_ac(t,j,ac,"vegc")
modules/14_yields/dynRegPastrTau_apr26/presolve.gms:26        (non-default realization)
modules/52_carbon/normal_dec17/{preloop.gms:114, start.gms:17,20, declarations.gms:12}  (self)

$ rg -c "pm_carbon_density_plantation_ac_uncalib" modules/32_forestry/dynamic_may24/presolve.gms   # positive control
1        (search works in this file/dir)

$ awk 'NR>=108 && NR<=109' modules/32_forestry/dynamic_may24/equations.gms                          # the sink
 q32_carbon(j2,ag_pools,stockType) .. vm_carbon_stock(j2,"forestry",ag_pools,stockType) =e=
            m_carbon_stock_ac(v32_land,p32_carbon_density_ac,"type32,ac","type32,ac_sub");
```

**confirmed**: true

**proposed_fix**: in **both** copies of the block (`:180` and `:479`), replace the final sentence with:
> "M14, M32 and M35 read the CALIBRATED curves as well — M14 for regular secdforest growing stock (`modules/14_yields/managementcalib_aug19/presolve.gms:44`) and for plantation growing stock (`:26`); **M32 for timber-plantation carbon density (`modules/32_forestry/dynamic_may24/presolve.gms:65`, feeding `q32_carbon` → `vm_carbon_stock(j2,"forestry",…)`) and for rotation lengths (`modules/32_forestry/dynamic_may24/preloop.gms:18,56`)**; M35 for secdforest carbon density, which it BLENDS with the uncalibrated curve by natural-origin area share (`modules/35_natveg/pot_forest_may24/presolve.gms:248-252`)."

Also add to §3.3's table note: plantation `vegc` comes from the **FRA-2025-calibrated** curve, unlike afforestation/NDC (`"aff"`, `"ndc"`), which use the uncalibrated one (`modules/32_forestry/dynamic_may24/presolve.gms:59,61,68`). Check `modules/module_52.md` and `modules/module_32.md` for the same omission before closing.

---

### B2 — MAJOR — `citation` — `config/default.cfg:1835` now points at a comment; the assignment is at `:1838`

**doc_line**: `carbon_balance_conservation.md:101`

**Claim in doc**:
> "⚠️ Do **not** cite `config/default.cfg:1835` for this default: that line omits the `cfg$gms$` prefix its siblings carry, so it never reaches GAMS and the switch is currently unreachable from config"

**Reality in code**: `config/default.cfg:1835` is a **comment** — `# *   actual: CO2 emissions for pricing are based on the difference of actual carbon stocks between time steps`. The assignment lives at **`:1838`**. The *substantive* claim survives intact and must be preserved: `:1838` reads `c56_carbon_stock_pricing <- "actualNoAcEst"` with no `cfg$gms$` prefix, while its sibling at `:1831` is `cfg$gms$c56_emis_policy <- …`, and `CHANGELOG.md:891` documents the intended name as `cfg$gms$c56_carbon_stock_pricing`. A whole-repo grep finds no script consuming the bare name, so the switch is indeed unreachable from config and the effective default comes from `modules/56_ghg_policy/price_aug22/input.gms:90`.

**Why Major**: rubric trigger *"file:line citation drift to adjacent but different content (would mislead a careful reader)"*. The whole point of the sentence is the **syntax of that line**; a reader who checks `:1835` finds a comment (which trivially has no `cfg$gms$` prefix and no `<-` at all) and would either dismiss the warning as bogus or conclude the config entry does not exist.

**file_evidence**: `config/default.cfg:1838` (assignment); `config/default.cfg:1835` (comment); `config/default.cfg:1831` (prefixed sibling).

**verify_cmd**:
```
$ awk 'NR>=1833 && NR<=1838 {printf "%d\t%s\n", NR, $0}' config/default.cfg
1833    # * CO2 emissions subject to carbon pricing
1834    # * options:  actual, actualNoAcEst
1835    # *   actual: CO2 emissions for pricing are based on the difference of actual carbon stocks between time steps
1836    # *   actualNoAcEst: CO2 emissions for pricing are based on actual carbon stocks but
1837    # *     without newly established forest and non-forest areas. …
1838    c56_carbon_stock_pricing <- "actualNoAcEst"   # def = actualNoAcEst

$ rg -n "c56_carbon_stock_pricing" .
./config/default.cfg:1838 | ./CHANGELOG.md:891 (documents `cfg$gms$c56_carbon_stock_pricing`)
./modules/56_ghg_policy/price_aug22/{realization.gms:14, equations.gms:12,13,22, input.gms:90}
```

**confirmed**: true

**proposed_fix**: `config/default.cfg:1835` → `config/default.cfg:1838`. Leave the substance untouched; optionally cite `CHANGELOG.md:891` as corroboration and append "(line verified against develop `2c02843ec`)" since this pointer is inherently drift-prone.

---

### B3 — MAJOR — `set_membership` — §6.3 age-class labels are ordinal indices, but the `ac` set is labelled by YEARS

**doc_line**: `carbon_balance_conservation.md:493` (table rows `:493-499`)

**Claim in doc** (§6.3 "Growth Trajectories", Age Class column): `5 → ac1`, `10 → ac2`, `20 → ac4`, `30 → ac6`, `50 → ac10`, `80 → ac16`, `100 → ac20`.

**Reality in code**: `core/sets.gms:269-275` defines `ac / ac0, ac5, ac10, ac15, ac20, …, ac300, acx /` — **62 members labelled by years in 5-year steps**. Consequences:
- `ac1`, `ac2`, `ac4`, `ac6`, `ac16` **do not exist** in the set.
- `ac10` and `ac20` **do exist**, but denote **10 and 20 years** — not the 50 and 100 the table assigns. This is the dangerous half: a reader indexing `pm_carbon_density_plantation_ac(t,j,"ac10","vegc")` for a 50-year-old stand silently gets a 10-year-old one (5× age error, no GAMS error raised).

The doc's own §3.5 (`:224`) gets this right — "ac0 → ac5 → ac10 → … → acx" — so the file is internally inconsistent. Root cause: `m_growth_vegc`'s last argument in `start.gms:17/28/48` is `(ord(ac)-1)`, an **ordinal**, which §6.3 mistook for the set label.

**Severity**: no Critical trigger matches literally (the fabricated names are set members, not `vm_*`/`pm_*` identifiers or equations); Major triggers *"right concept, wrong number"* and *"fabricated count for a set … list"* both fire → **Major**. (Related immutable anchor: R16 `ac140/acx` vs `ac300` → Critical for set *extent*; this is set *labelling*, one tier down.)

**file_evidence**: `core/sets.gms:269-275`; `modules/52_carbon/normal_dec17/start.gms:17`.

**verify_cmd**:
```
$ awk 'NR>=269 && NR<=275 {printf "%d\t%s\n", NR, $0}' core/sets.gms
269       ac Age classes  / ac0,ac5,ac10,ac15,ac20,ac25,ac30,ac35,ac40,ac45,ac50,
270-274                     ac55,…,ac295,
275                         ac300, acx /
$ awk 'NR==17' modules/52_carbon/normal_dec17/start.gms   # ordinal, not label
  …,(ord(ac)-1));
```

**confirmed**: true

**proposed_fix**: rewrite the Age Class column as `ac0, ac5, ac10, ac20, ac30, ac50, ac80, ac100, acx` (label = age in years) and add: *"Set labels are years (`ac0…ac300, acx`, `core/sets.gms:269-275`); the `ac` argument inside `m_growth_vegc` is the ordinal `ord(ac)-1`, which the macro multiplies by 5 to recover years."*

---

### B13 — MAJOR — `mechanism` — primary-forest carbon density claimed time-invariant; under the default `cc` scenario it varies with climate

**doc_line**: `carbon_balance_conservation.md:201` (repeated as a stated limitation at `:841`; table row at `:194`)

**Claim in doc** (§3.4 Primary Forest, "Key Assumption"):
> "- Carbon density does NOT change over time (climate change affects future forests, not current primary)"

and §10.1 item 1:
> "**1. Static Primary Forest Carbon**: - Primary forest carbon density does NOT change over time"

**Reality in code**: in a **default** run, primary-forest carbon density is time-varying, for all three pools:

1. `fm_carbon_density(t_all,j,land,c_pools)` is a **time-indexed** LPJmL table (`modules/52_carbon/normal_dec17/input.gms:16`). The only things that collapse it to a single year are the `nocc` / `nocc_hist` branches at `input.gms:22-23` — and the default is `cc`, set in **both** `modules/52_carbon/normal_dec17/input.gms:8` and `config/default.cfg:1590`. Under `cc` neither branch fires.
2. `q35_carbon_primforest` (`modules/35_natveg/pot_forest_may24/equations.gms:42-44`) computes the stock as `m_carbon_stock(vm_land,fm_carbon_density,"primforest")`, which expands (`core/macros.gms:99-101`) to `vm_land(j2,"primforest") * sum(ct, fm_carbon_density(ct,j2,"primforest",ag_pools))` — evaluated at the **current** timestep `ct`. So the density applied to primforest changes every timestep.
3. The soilc row is likewise not static: `primforest ∈ noncropland59` (`modules/59_som/cellpool_jan23/sets.gms:10-11`), so `q59_som_target_noncropland` drives it toward `f59_topsoilc_density(ct,j)`, which is itself `cc`-time-varying by default (`modules/59_som/cellpool_jan23/input.gms:72`; `config/default.cfg:1951`).
4. Module 52 contains **no** primforest-specific freeze: a whole-module grep for `primforest` in `modules/52_carbon/normal_dec17/` returns only two narrative comment lines (`preloop.gms:36,38`), against a positive control of 19 `secdforest` hits in the same directory.

The doc **contradicts itself**: §8.3 (`:697-700`) states "LPJmL simulates vegetation carbon density under future climate → Module 52 updates `fm_carbon_density(t,j,land,c_pools)` over time → Carbon stocks change even without land-use change", and §8.3 (`:714-716`) names `c52_carbon_scenario = "cc"` as the switch that enables exactly this. §3.4's parenthetical "(climate change affects future forests, not current primary)" is the direct negation.

**Why Major, not Critical**: the closest Critical trigger is the inverted-default family ("mechanism claimed OFF when ON by default"), and the harm is real — a user attributing observed primforest stock change would look only at area and miss the density channel, and anyone quantifying "static primary forest" as a model limitation would be quantifying a limitation the model does not have. But it does not point at a wrong file or a wrong edit, so per the tie-breaker it lands at **Major**. What *is* defensible in §3.4 and should be kept: primforest has **no age-class tracking** (`:200`) — that is true, and is probably what "Static" in the table's Dynamics column was reaching for.

**file_evidence**: `modules/52_carbon/normal_dec17/input.gms:8` (default `cc`); `config/default.cfg:1590`; `modules/52_carbon/normal_dec17/input.gms:16,22-23`; `modules/35_natveg/pot_forest_may24/equations.gms:42-44`; `core/macros.gms:99-101`; `modules/59_som/cellpool_jan23/sets.gms:10-11`; `config/default.cfg:1951`.

**verify_cmd** (each isolated; absence claim double-confirmed with positive control):
```
$ rg -n "c52_carbon_scenario" config/default.cfg modules/52_carbon/normal_dec17/input.gms
modules/52_carbon/normal_dec17/input.gms:8:$setglobal c52_carbon_scenario  cc
modules/52_carbon/normal_dec17/input.gms:22:$if "%c52_carbon_scenario%" == "nocc"      fm_carbon_density(...) = fm_carbon_density("y1995",...);
modules/52_carbon/normal_dec17/input.gms:23:$if "%c52_carbon_scenario%" == "nocc_hist" fm_carbon_density(...)$(m_year(t_all) > sm_fix_cc) = ...;
config/default.cfg:1590:cfg$gms$c52_carbon_scenario  <- "cc"   # def = "cc"
        -> default is "cc"; neither collapse branch fires

$ awk 'NR>=99 && NR<=101 {printf "%d\t%s\n", NR, $0}' core/macros.gms
99      $macro m_carbon_stock(land,carbon_density,item) \
100                 (land(j2,item) * sum(ct,carbon_density(ct,j2,item,ag_pools)))$(sameas(stockType,"actual")) + \
101                 (land(j2,item) * sum(ct,carbon_density(ct,j2,item,ag_pools)))$(sameas(stockType,"actualNoAcEst"))
        -> density read at the CURRENT timestep ct

$ rg -n "primforest" modules/52_carbon/normal_dec17/          # is there a freeze?
modules/52_carbon/normal_dec17/preloop.gms:36  * … includes primforest in the oldest age class (acx).
modules/52_carbon/normal_dec17/preloop.gms:38  * Note: We do NOT decompose into primforest and secdforest …
        -> comments only, no assignment

$ rg -c "secdforest" modules/52_carbon/normal_dec17/*.gms     # POSITIVE CONTROL
start.gms:5  declarations.gms:3  input.gms:2  preloop.gms:9   -> search works in this dir
```

**confirmed**: true — with one scoping note: the LPJmL `.cs3` payload is a run-time artifact absent from the repo, so I verified the **code path** (unambiguous), not the numeric spread of primforest density across years in the shipped data. The doc's claim is about the model's treatment, and that treatment is what the code contradicts.

**proposed_fix**: at `:201`, replace with:
> "- No age-class tracking (assumed mature `acx`) — this, not a frozen density, is what "Static" means here
> - Carbon density **does** change over time under the default `c52_carbon_scenario = "cc"` (`modules/52_carbon/normal_dec17/input.gms:8`; `config/default.cfg:1590`): `fm_carbon_density(t,j,"primforest",c_pools)` follows the LPJmL climate trajectory and is read at the current timestep by `q35_carbon_primforest` (`modules/35_natveg/pot_forest_may24/equations.gms:42-44`). Set `c52_carbon_scenario = "nocc"` to freeze it at 1995 (`input.gms:22`)."

At `:841`, retitle item 1 to "**No age-class dynamics in primary forest**" and restate the limitation as *no regrowth/age structure* rather than *no temporal change*; the "Reality/Implication" lines below it need rewording to match. Also soften the `soilc` row at `:196` ("Static") — primforest soilc converges via `q59_som_target_noncropland` toward a `cc`-varying natural density.

---

### B4 — MINOR — `formula` — §9.3 R snippet multiplies year-labelled age classes by 5

**doc_line**: `carbon_balance_conservation.md:823`

**Claim in doc**: `ages <- as.numeric(gsub("ac", "", getNames(vegc_by_age))) * 5`

**Reality in code**: GDX labels are the GAMS set labels `ac0, ac5, ac10, …` (`core/sets.gms:269-275`), i.e. **already years**. `gsub("ac","","ac50")` → `50`; `* 5` → **250 years**. The plotted x-axis would be 5× too long for every point except `ac0`. Same root misconception as B3 but a distinct, *runnable* artifact with a distinct fix, so recorded separately.

**file_evidence**: `core/sets.gms:269-275`

**verify_cmd**: `awk 'NR>=269 && NR<=275' core/sets.gms` → labels are `ac0,ac5,ac10,…,ac300,acx` (years, 5-year steps).

**confirmed**: true

**proposed_fix**: drop the `* 5` — `ages <- as.numeric(gsub("ac", "", getNames(vegc_by_age)))  # labels are already years; drop acx first`.

---

### B5 — MINOR — `formula` — §8.4 uses the legacy fraction (44%) where the convergence fraction (56%) belongs

**doc_line**: `carbon_balance_conservation.md:734`

**Claim in doc**: "- Year 5: 44% toward new equilibrium = +4 tC/ha"

**Reality in code**: `i59_lossrate(t) = 1-0.85**m_yeardiff(t)` (`modules/59_som/cellpool_jan23/preloop.gms:45`) gives **1 − 0.85^5 = 0.5563**, i.e. **56%** toward equilibrium, 44% legacy. The doc's own §5.2 table (`:401`) and interpretation (`:412`) both say 56/44 correctly; §8.4 inverts them. The rows below are consistent (Year 10 → 80%, Year 20 → 96%), so this row is the outlier. Downstream: 9 tC/ha × 0.5563 = **+5.0 tC/ha**, not +4.

Likely inherited from the erroneous code comment at `modules/59_som/cellpool_jan23/preloop.gms:42` ("44% in 5 years"), which is itself wrong — see the CORRECT-list note.

**file_evidence**: `modules/59_som/cellpool_jan23/preloop.gms:45`

**verify_cmd**: `python3 -c "print(1-0.85**5, 9*(1-0.85**5))"` → `0.5563 5.01` (controls: 10 yr → `0.8031`, 20 yr → `0.9612`, matching §5.2).

**confirmed**: true

**proposed_fix**: `- Year 5: 56% toward new equilibrium = +5.0 tC/ha`

---

### B6 — MINOR — `formula` — §8.1 gradual soil-emission arithmetic is wrong (458 vs 550)

**doc_line**: `carbon_balance_conservation.md:656`

**Claim in doc**: "- Gradual (soilc over 20 years): 30 tC/ha × 100 Mha × (44/12) / 20 years = **458 Tg CO₂/year**"

**Reality**: 30 × 100 = 3,000 Tg C; × 44/12 = 11,000 Tg CO₂; ÷ 20 = **550 Tg CO₂/yr**. The stated 458 corresponds to dividing by 24, or equivalently to a 25 tC/ha loss — but the table immediately above (`:649`) gives the soilc loss as 30 tC/ha (80 → 50). The sibling calculation at `:655` (56,833 Tg CO₂ from 155 tC/ha) is arithmetically correct, so this is an isolated slip, not a convention difference. Labelled "made-up numbers", but the *arithmetic* is checkable and wrong on the doc's own inputs.

**file_evidence**: n/a (arithmetic on doc-internal numbers; the `mio. tC = Tg C` identity is confirmed against `modules/56_ghg_policy/price_aug22/declarations.gms:34,40`).

**verify_cmd**: `python3 -c "print(30*100*44/12/20)"` → `550.0` (control `print(155*100*44/12)` → `56833.3`, matching the doc's other figure; `11000/458.33` → `24.0`, showing the wrong divisor).

**confirmed**: true

**proposed_fix**: `… / 20 years = **550 Tg CO₂/year**`

---

### B7 — MINOR — `formula` — §6.3 vegc trajectory does not follow from its own stated A, k, m

**doc_line**: `carbon_balance_conservation.md:487` (parameters `:487-488`, table values `:493-499`)

**Claim in doc**: with `A = 100 tC/ha, k = 0.06, m = 2.0`, vegc = 14 / 26 / 44 / 58 / 75 / 88 / 93 at 5 / 10 / 20 / 30 / 50 / 80 / 100 years.

**Reality**: `m_growth_vegc` (`core/macros.gms:18`) is `S + (A-S)*(1-exp(-k*(ac*5)))**m`. With S=0, A=100, k=0.06, m=2 the values are **6.7 / 20.4 / 48.8 / 69.7 / 90.3 / 98.4 / 99.5**. The tabulated series instead fits roughly `k ≈ 0.028, m = 1` (13.1 / 24.4 / 42.9 / 56.8 / 75.3 / 89.4 / 93.9). The formula quoted in §6.1 is itself correct — it is the table that does not follow from it. The 20-year (44) and 50-year (75) values are reused in §8.2 (`:676`, `:682`), so the mismatch propagates.

**file_evidence**: `core/macros.gms:18`

**verify_cmd**:
```
$ python3 -c "import math;print([(t, round(100*(1-math.exp(-0.06*t))**2,1)) for t in (5,10,20,30,50,80,100)])"
[(5, 6.7), (10, 20.4), (20, 48.8), (30, 69.7), (50, 90.3), (80, 98.4), (100, 99.5)]
$ python3 -c "import math;print([(t, round(100*(1-math.exp(-0.028*t)),1)) for t in (5,10,20,30,50,80,100)])"
[(5, 13.1), (10, 24.4), (20, 42.9), (30, 56.8), (50, 75.3), (80, 89.4), (100, 93.9)]   # what the table actually fits
```

**confirmed**: true

**proposed_fix**: recompute the table from A=100, k=0.06, m=2.0 (preferred — an m=2 sigmoid is the shape the section illustrates) and update the dependent §8.2 vegc figures; or restate the parameters as `k ≈ 0.03, m = 1.0` to match the existing series.

---

### B8 — MINOR — `citation` — References line-range no longer spans the Module-52 growth code

**doc_line**: `carbon_balance_conservation.md:987`

**Claim in doc**: "- Module 52 growth: `modules/52_carbon/normal_dec17/start.gms:8-39`"

**Reality in code**: `start.gms` is 51 lines. Growth code now occupies **8-31** (forestry + secdforest, vegc and litc) and **46-51** (other land); `:33-44` is calibration-parameter initialisation plus the uncalibrated-curve snapshot, which is not growth code. The cited `8-39` therefore (a) **omits the other-land Chapman-Richards and litter curves entirely** — which §3.6 of this same doc relies on — and (b) includes ~12 lines of calibration bookkeeping. Confirmed as drift, not a mis-write: before the forestry-overhaul commit `75d7ee167` the file was 38 lines, and `8-38` *was* exactly the growth block.

**file_evidence**: `modules/52_carbon/normal_dec17/start.gms:46-51` (other-land curves, outside the range); `:33-44` (calibration init + uncalib snapshot, inside it).

**verify_cmd**:
```
$ wc -l < modules/52_carbon/normal_dec17/start.gms
51
$ for c in $(git log --format=%h -5 -- modules/52_carbon/normal_dec17/start.gms); do echo "$c $(git show $c:modules/52_carbon/normal_dec17/start.gms | wc -l)"; done
322b9a052 51 | 896a9b728 50 | 75d7ee167 54 | 6bcb1a4bf 38 | 19d74d572 38
        -> pre-overhaul the file was 38 lines; 8-39 was the whole growth block. Drift confirmed.
$ awk 'NR==34||NR==43||NR==48 {printf "%d\t%s\n", NR, $0}' modules/52_carbon/normal_dec17/start.gms
34  i52_k_calib_secdf(i) = 0;                                          (calibration init, inside 8-39)
43  pm_carbon_density_secdforest_ac_uncalib(...) = ...;                (snapshot, inside 8-39)
48  pm_carbon_density_other_ac(t_all,j,ac,"vegc") = m_growth_vegc(...); (growth, OUTSIDE 8-39)
```

**confirmed**: true

**proposed_fix**: `Module 52 growth: modules/52_carbon/normal_dec17/start.gms:8-31 (forestry + secdforest), :46-51 (other land); FRA-2025 k/m calibration overwrite: modules/52_carbon/normal_dec17/preloop.gms:71-73, :114-116`.

---

### B9 — MINOR — `attribution_read` — `vm_maccs_costs` consumer set omits Module 36

**doc_line**: `carbon_balance_conservation.md:593`

**Claim in doc**: §7.4 "**Provides**: … `vm_maccs_costs(i,factors)`: Labor and capital costs of mitigation → to Module 11"

**Reality in code**: two direct consumers, not one. Module 36 (employment, default realization `exo_may22` per `config/default.cfg:1212`) reads it in an equation:
```
modules/36_employment/exo_may22/equations.gms:28
   =e= (vm_maccs_costs(i2,"labor")) * (1 / sum(ct,f36_weekly_hours(ct,i2)*s36_weeks_in_year*pm_hourly_costs(ct,i2,"scenario")));
```
Role map agrees: `vm_maccs_costs → read_by: ['11','36','57']`.

Rated Minor rather than Major/Critical because this bullet is an arrow-annotation in a carbon-balance narrative rather than a canonical consumer inventory, and the carbon-balance-relevant destination (M11) is correct. It still costs a reader doing modification-impact analysis on `vm_maccs_costs` one missed module. Note the same doc's §7.2 arrow-annotations (`vm_nr_som` → M51, `vm_cost_scm` → M11) **are** complete — role map `read_by: ['51','59']` and `['11','59']` respectively — so this is the lone gap.

**file_evidence**: `modules/36_employment/exo_may22/equations.gms:28` (omitted); `modules/11_costs/default/equations.gms:28` (documented, correct).

**verify_cmd**:
```
$ rg -n "vm_maccs_costs" modules/ core/
modules/11_costs/default/equations.gms:28        (documented)
modules/36_employment/exo_may22/equations.gms:28  <-- OMITTED
modules/57_maccs/on_aug22/{equations.gms:36,46 | declarations.gms:25 | scaling.gms:8 | postsolve.gms:11,14,17,20}  (self)
$ rg -n 'cfg\$gms\$employment' config/default.cfg
1212:cfg$gms$employment <- "exo_may22"        # default = "exo_may22"
```

**confirmed**: true

**proposed_fix**: `- vm_maccs_costs(i,factors): Labor and capital costs of mitigation → to Module 11 (total costs, modules/11_costs/default/equations.gms:28) and Module 36 (labor share only, modules/36_employment/exo_may22/equations.gms:28)`.

---

### B10 — MINOR — `set_membership` — the FLU factor has no category set and no default in the code

**doc_line**: `carbon_balance_conservation.md:428` (echoed at `:137`)

**Claim in doc**: §5.3 "- **FLU** (Land Use): Cropland / Set-aside / Perennial (default: annual cropland)"; §3.1 (`:137`) "- Land use: Cropland vs set-aside".

**Reality in code**: no such category set exists in `cellpool_jan23`, and there is no FLU default to select. The FLU factor is `f59_cratio_landuse(i,climate59_2019,kcr)` — indexed by **MAgPIE crop type (`kcr`)**, region and climate, resolved per crop from the input table. This matters because the two sibling bullets *do* name real GAMS sets with real hard-coded defaults, so the parallel construction implies FLU works the same way:

```
modules/59_som/cellpool_jan23/sets.gms:13-14  tillage59 /full_tillage,reduced_tillage,no_tillage/                        <- FMG bullet EXACT
modules/59_som/cellpool_jan23/sets.gms:16-17  inputs59 /low_input,medium_input,high_input_nomanure,high_input_manure/    <- FI bullet EXACT
modules/59_som/cellpool_jan23/preloop.gms:53  i59_tillage_share(i,"full_tillage")=1;   <- "default: full tillage" EXACT
modules/59_som/cellpool_jan23/preloop.gms:55  i59_input_share(i,"medium_input")=1;     <- "default: medium, no manure" EXACT
modules/59_som/cellpool_jan23/input.gms:43    table f59_cratio_landuse(i,climate59_2019,kcr)   <- FLU: no category set, no default
```

**file_evidence**: `modules/59_som/cellpool_jan23/input.gms:43`; `modules/59_som/cellpool_jan23/preloop.gms:60-67` (the `i59_cratio` product: landuse × tillage-share × tillage × input-share × input × irrigation).

**verify_cmd**:
```
$ rg -ni "setaside|set_aside|set-aside|perennial|landuse59" modules/59_som/
modules/59_som/static_jan19/realization.gms:16:*' e.g. differences for annual and perennial crops.
modules/59_som/cellpool_jan23/input.gms:24:*' … frequent use of perennial grasses in annual
   -> prose only; no set member, neither hit in cellpool_jan23's factor machinery
$ rg -c "tillage59" modules/59_som/cellpool_jan23/sets.gms    # positive control
1      # the search works in this directory
```

**confirmed**: true (Major trigger *"fabricated … list"* considered; downgraded per the rubric's "pick the lower tier" tie-breaker, since the bullet is framed as IPCC methodology and IPCC's F_LU genuinely has those categories.)

**proposed_fix**: `- **FLU** (Land Use): applied per MAgPIE crop type via f59_cratio_landuse(i,climate59_2019,kcr) (modules/59_som/cellpool_jan23/input.gms:43). IPCC's set-aside / perennial categories are collapsed into the crop-type dimension in preprocessing; there is no FLU switch in the model.` Same correction at `:137`.

---

### B11 — MINOR — `formula` — §8.2 convergence percentages are shifted one row, and mutually inconsistent

**doc_line**: `carbon_balance_conservation.md:678` (and `:684`)

**Claim in doc**: "**Year 20 (Young Plantation)**: … soilc: 70 tC/ha (80% toward natural, from Module 59)"; "**Year 50 (Mature Plantation)**: … soilc: 78 tC/ha (96% toward natural)".

**Reality in code**: the percentages are attributed explicitly to Module 59 but are shifted one row against `1 - 0.85^years` (`modules/59_som/cellpool_jan23/preloop.gms:45`): 80% corresponds to **10** years and 96% to **20** years (the doc's own §5.2 table, `:402-404`). At 20 years the model gives 96%; at 50 years, 99.97%. The two rows also imply different targets: `50 + 0.80·(N−50) = 70` → natural = 75 tC/ha, while `50 + 0.96·(N−50) = 78` → 79.2 tC/ha.

**file_evidence**: `modules/59_som/cellpool_jan23/preloop.gms:45`

**verify_cmd**: `python3 -c "print(1-0.85**10, 1-0.85**20, 1-0.85**50)"` → `0.8031 0.9612 0.9997`

**confirmed**: true

**proposed_fix**: relabel to the code-consistent schedule — Year 20 ≈ 96% toward natural; drop the Year-50 percentage or state ≈100% — and recompute both soilc values from one consistent natural density. (The block is illustrative, but the percentages are code-derived and should not contradict §5.2.)

---

### B12 — INFORMATIONAL — `citation` — several citations omit the required `modules/` prefix

**doc_line**: `carbon_balance_conservation.md:180` (identical paragraph at `:479`; also `:247`, `:254`)

**Claim in doc**: `14_yields/managementcalib_aug19/presolve.gms:66`, `29_cropland/detail_apr24/preloop.gms:46,48`, `32_forestry/dynamic_may24/presolve.gms:59,61,68`, `35_natveg/pot_forest_may24/presolve.gms:242` and `:117`, `normal_dec17/preloop.gms:71-73` / `:114-116` / `:29-30`.

**Reality**: MANDATE 16 requires the full form `modules/NN_name/realization/file.gms:LINE`. All the cited **content** is exactly right (each verified individually this session); only the path form is non-compliant, which breaks copy-paste-to-`Read` and any path-based checker.

**file_evidence**: `modules/14_yields/managementcalib_aug19/presolve.gms:66`; `modules/29_cropland/detail_apr24/preloop.gms:46,48`; `modules/32_forestry/dynamic_may24/presolve.gms:59,61,68`; `modules/35_natveg/pot_forest_may24/presolve.gms:117,242`; `modules/52_carbon/normal_dec17/preloop.gms:29-30,71-73,114-116`.

**verify_cmd**:
```
$ awk 'NR==66' modules/14_yields/managementcalib_aug19/presolve.gms
     pm_carbon_density_secdforest_ac_uncalib(t,j,ac,"vegc")
$ awk 'NR==46||NR==48' modules/29_cropland/detail_apr24/preloop.gms
 p29_carbon_density_ac(t,j,ac,ag_pools) = pm_carbon_density_secdforest_ac_uncalib(...);
 p29_carbon_density_ac(t,j,ac,ag_pools) = pm_carbon_density_plantation_ac_uncalib(...);
$ awk 'NR==59||NR==61||NR==68' modules/32_forestry/dynamic_may24/presolve.gms
 …"aff"… = …secdforest_ac_uncalib;  |  …"aff"… = …plantation_ac_uncalib;  |  …"ndc"… = …secdforest_ac_uncalib;
$ awk 'NR==117||NR==242' modules/35_natveg/pot_forest_may24/presolve.gms
 …$(pm_carbon_density_secdforest_ac_uncalib(t,j,ac,"vegc") > 20);
 p35_carbon_density_other(t,j,"youngsecdf",ac,ag_pools) = pm_carbon_density_secdforest_ac_uncalib(...);
```

**confirmed**: true

**proposed_fix**: prefix each with `modules/`. Content requires no change.

---

## Deferred (unverified / judgement calls — no edit proposed)

1. **§9.1 R consistency check** (`:756-779`): `readGDX(gdx,"pcm_carbon_stock", field="l")` applies `field="l"` to a GAMS *parameter*, `:761` passes both `select=` and `field=`, and `dimSums(stock_change, dim=c("cell","land","c_pools"))` leaves `stockType` in place and never aggregates cells to regions, so the result would not be comparable to the regional `ov_emissions_reg`. Snippet not executed — recorded as a lead, and an R-lens question rather than a GAMS-ground-truth one. (The GDX symbol names themselves all check out: `ov_carbon_stock`, `ov_emissions_reg`, `ov59_som_pool`, `ov59_som_target`, `ov32_land` all exist.)
2. **§7.2 "Receives" attributions**: `vm_land` attributed to M10 and `vm_area` to M30. Role map shows `vm_land` populated by 10, 29, 31, 32, 34, 35 and `vm_area` by 30 and 41; per-slice, the non-cropland slices are set by M31/M32/M34/M35 (`modules/31_past/…`, `modules/32_forestry/dynamic_may24/equations.gms:56`, `modules/34_urban/exo_nov21/presolve.gms:11-15`, `modules/35_natveg/pot_forest_may24/equations.gms:11,13`), not by M10. Both variables *are* declared in the attributed module and M10/M30 are the canonical owners, so the shorthand is defensible; not filed. An editor tightening §7.2 could name the per-slice populators.
3. **`vm_lu_transitions` "from Module 10"** (`:548`): role map lists `populated_by: ['10','29','35']`, but re-grepping both endpoints shows M29 (`detail_apr24/equations.gms:60`) and M35 (`pot_forest_may24/equations.gms:25-26,31`) only place it on the LHS of `=g=` *constraints*; the defining `=e=` equations are M10's `q10_transition_to`/`q10_transition_from` (`modules/10_land/landmatrix_dec18/equations.gms:19-25`). **Doc is correct; the role map is the superset here.** Recorded so a future round does not "fix" a correct line from the map alone.
4. **§2.3 "Subsoil … Static (fixed from LPJmL via M52)"**: `i59_subsoilc_density(t_all,j)` is time-indexed and derived from the time-varying `fm_carbon_density` (`modules/59_som/cellpool_jan23/preloop.gms:12`), so it is not literally static across time. The doc's operative claim — "not affected by land use" — is correct; imprecision rather than error. (Related to B13, but a weaker case, so kept separate and unfiled.)
5. **Domain-set imprecision**: the doc writes `fm_carbon_density(t,j,land,c_pools)` and `pm_carbon_density_*_ac(t,j,ac,ag_pools)` at `:107`, `:513-516`, `:699`, `:948`; the declared domain is `t_all` (`modules/52_carbon/normal_dec17/declarations.gms:9-13`, `input.gms:16`). Pervasive, and the consuming code itself indexes with `t` inside the loop — harmless to a reader (t ⊂ t_all), so recorded here rather than filed.
6. **§3.1 (`:139`) "Input level: Low, medium, high without manure"** enumerates 3 of the 4 `inputs59` members (`high_input_manure` omitted, `modules/59_som/cellpool_jan23/sets.gms:16-17`). §5.3 (`:430`) lists all four correctly. The §3.1 phrasing is parseable as a compressed 3-item list *or* as "low / medium / high-without-manure", so the omission is ambiguous rather than clearly wrong — not filed.
7. **§5.3 IPCC stock-change factor examples** (F = 0.69, F = 1.17) and **§6.2 climate-class k ranges** (0.02-0.08), and **§7.4 `im_maccs_mitigation` "(0 to ~0.3)"**: backing inputs (`f59_ch5_F_*.csv`, `f52_growth_par.csv`, MACC tables) are run-time artifacts absent from the repo. Could not verify; all explicitly labelled "typical"/"illustrative".
8. **Doc header (`:5`) "Modules Covered: 52, 53, 59 (57 for mitigation costs)"** omits Module 58, which §10.2 item 7 documents at length. Informational; not filed.
9. **§10.2 item 7 peatland double-counting claim** ("avoided by construction (peat is not in `c_pools`)"): `c_pools = /vegc,litc,soilc/` confirmed and M58 writes only `vm_emissions_reg`. Sound as far as GAMS goes, but whether preprocessing folds peat carbon into `fm_carbon_density` upstream is a preproc-agent question.
10. **§7.1 / §7.2 "Key Equation(s)" blocks** (`:522-525`, `:551-554`) are fenced ```gams but contain pseudocode (`=` not `=e=`, `Σ`, no `sum()`). More pointedly, `:552` still uses the simplified `v59_som_target(j,"crop") = Σ(crops) Area × C_ratio × Natural_density` that §3.1 (`:134`) explicitly flags as having "omitted terms 2-4". Internally inconsistent and worth an editorial pass, but the summary framing makes it a style call rather than a factual error — not filed.
11. **§11.2 summary formula** (`:935`) writes `vegc(age) = 0 + (Mature - 0) × (1 - exp(-k × age))^m`, dropping the `ac*5` conversion in `core/macros.gms:18`. Defensible if `age` is read as years (§6.1 states the conversion explicitly), so not filed.
12. **`modules/59_som/cellpool_jan23/realization.gms:9`** calls itself "The cellpool_aug23 realization" while the directory is `cellpool_jan23`. Upstream code typo, not a doc bug; the doc correctly uses `cellpool_jan23` throughout.
13. **§7.5 / §10.2 fire language** — the doc does not claim mechanistic fire modelling ("Disturbances (fire, shifting agriculture) → reset age classes"), so the parameterization-vs-mechanism rule is respected. No bug.

---

## Confidence notes

- All 13 bugs are backed by reproducible commands whose output is quoted above, re-run in **this** session against HEAD `2c02843ec`. **No finding is relayed** from an earlier pass without independent re-derivation — including the severity calls.
- **B13 is new.** It was reachable only by asking what the *default* `c52_carbon_scenario` does to a section that never cites it; the citation-entry sweep alone does not surface it, because §3.4 carries no citation at all. That absence of a citation is itself the signal.
- **B1** carries the heaviest evidence because it has the highest false-positive cost: role map + `rg` + positive control all agreeing on the same 3 hits in `modules/32_forestry/dynamic_may24/`, and the sink (`q32_carbon` → `vm_carbon_stock`) read directly.
- **B1 severity** (Critical vs Major) and **B13 severity** (Major vs Critical) are the two genuinely arguable calls; the reasoning for each is stated inline so a reviewer can overrule without re-deriving.
- **B3 and B4** share a root cause (ordinal vs year labelling of `ac`) but have different locations and different fixes; fixing one does not fix the other.
- **B5, B6, B7, B11** all sit inside blocks labelled "illustrative"/"made-up numbers". They are filed anyway because in each case the *derivation* is code-anchored (`1-0.85^n`, the 44/12 conversion, `m_growth_vegc`) and wrong on the doc's own stated inputs — a reader reconciling them would waste time hunting for a hidden factor. None is rated above Minor for that reason.
- No bug depends on an absence claim that was not double-confirmed with a second method plus a positive control. One documented grep anomaly this session: a `grep -n` on a comma-containing literal in `core/sets.gms` returned empty while `rg -n` on a substring of the same line returned the match — the known BSD-grep trap. All absence claims here use `rg` plus a positive control.
- **Deferred item 3 is a live warning for the next round**: the role map lists M29/M35 as populators of `vm_lu_transitions`, but code shows they only constrain it. The doc's line is right. Do not "correct" it from the map alone.
