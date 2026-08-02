# R60 depth audit — `cross_module/carbon_balance_conservation.md`

**Lens**: `citation_formula` (enter from file:line citations; check existence, range, token presence, formula fidelity)
**Ground truth**: MAgPIE `develop` read-only worktree, HEAD `2c02843eccd8483e0a5617864213c711c3dcd5de` ("Merge pull request #919 from alexkoberle/dyn_reg_tau"), working tree clean.
**Attribution ground truth**: `audit/integrated/depth_rolemap.json`, consulted first for every `vm_*`/`pm_*`/`im_*`/`fm_*`/`pcm_*` role claim, then confirmed by both-endpoints greps.
**Date**: 2026-08-02

> **Merge note.** A first `citation_formula` pass on this doc existed at this path (8 bugs). This file supersedes it and is a **superset**: every prior finding was **independently re-derived from code in this session** (not relayed) and is retained, plus 4 findings the first pass did not have (B9-B12). One evidence detail in the first pass is corrected here: it stated that `pm_carbon_density_plantation_ac` "is not in the role map" — it **is** (`read_by: ['14','32','52']`), and the map corroborates B1 rather than being silent on it. The conclusion was unaffected.

---

## Scope and method

1. **Mechanical citation sweep** — regex-extracted every citation in the doc, then `test -f` + `wc -l` + range check on each. **Zero missing files, zero out-of-range line numbers, zero wrong realization names.**
2. **Token-presence check** — read each cited line/range; confirmed it contains the claimed identifier or construct.
3. **Formula fidelity** — re-derived every quoted equation against source; re-computed every arithmetic result with `python3`.
4. **Attribution** — role map first, then both-endpoints greps (`NAME(` **and** `NAME.`), each grep isolated, each absence claim backed by a second method plus a positive control.
5. **Defaults** — every cited default cross-checked in both `input.gms` and `config/default.cfg`; every realization confirmed against `cfg$gms$<module>`.

**Claims verified: ~130.** **Bugs: 12** (1 Critical, 2 Major, 8 Minor, 1 Informational).

---

## What is CORRECT (recorded so future rounds don't re-litigate)

- **All 15 realizations named** are the current defaults: `carbon=normal_dec17` (`config/default.cfg:1577`), `som=cellpool_jan23` (1937), `methane=ipcc2006_aug22` (1604), `ghg_policy=price_aug22` (1634), `maccs=on_aug22` (1843), `peatland=v2` (1874), `nitrogen=rescaled_jan21` (1571), `nr_soil_budget=macceff_aug22` (1500), `cropland=detail_apr24` (814), `croparea=simple_apr24` (915), `natveg=pot_forest_may24` (1156), `forestry=dynamic_may24` (995), `urban=exo_nov21` (1147), `past=endo_jun13` (988), `yields=managementcalib_aug19` (357), `employment=exo_may22` (1212).
- **§4.1 `q52_emis_co2_actual`** is quoted verbatim-correct against `modules/52_carbon/normal_dec17/equations.gms:16-19`.
- **§3.1 `v59_som_target(j,"crop")` 4-term expansion** matches `modules/59_som/cellpool_jan23/equations.gms:20-27` term for term, including the subtlety that `i59_cratio_treecover` carries no `j` index (`preloop.gms:82`) while `i59_cratio_fallow(j)` does (`preloop.gms:73`).
- **§5.1 `q59_som_pool`** matches `equations.gms:46-52`; **§7.2 `q59_carbon_soil`** matches `equations.gms:61-64`; **§6.1 Chapman-Richards** matches `core/macros.gms:18` exactly.
- **`vm_carbon_stock` populator set** (§7.5): M29/M31/M32/M34/M35 + M59-soilc — exactly the role map's `populated_by: ['29','31','32','34','35','59']`; spot-confirmed at `modules/29_cropland/detail_apr24/equations.gms:39`, `modules/31_past/endo_jun13/equations.gms:23`, `modules/32_forestry/dynamic_may24/equations.gms:108`, `modules/34_urban/exo_nov21/presolve.gms:8`, `modules/35_natveg/pot_forest_may24/equations.gms:50,54`, `modules/59_som/cellpool_jan23/equations.gms:62`. All default-realization populators are indexed over the free `stockType` set, so "fill **both** slices" holds.
- **§7.3 parallel-not-serial claim** — `q56_emis_pricing` (`modules/56_ghg_policy/price_aug22/equations.gms:15-17`) is indexed over `emis_annual`, disjoint from `emis_oneoff` (`core/sets.gms:314-322`); M56 recomputes CO2 itself in `q56_emis_pricing_co2` (`:19-22`). M56 does **not** consume M52's `vm_emissions_reg(...,"co2_c")`. MANDATE 21 / R51 trap correctly avoided.
- **§7.4 MACC application map** — complete and exact. Whole-tree `rg` finds `im_maccs_mitigation` only at `modules/50_nr_soil_budget/macceff_aug22/presolve.gms:56,58,61,63`, `modules/51_nitrogen/rescaled_jan21/equations.gms:71`, `modules/53_methane/ipcc2006_aug22/equations.gms:29,52,63`. "NOT residue burning" holds (`:70-72` carries no mitigation factor); `maccs_ch4 / rice_ch4, ent_ferm_ch4, awms_ch4 /` verbatim at `modules/57_maccs/on_aug22/sets.gms:28-29`; rice N2O genuinely zero (`rice` absent from `emis_source_n51`, `modules/51_nitrogen/rescaled_jan21/sets.gms:15-16`; `preloop.gms:8-10` fixes then selectively relaxes).
- **§10.2 item 7 (peatland)** — `q58_peatland_emis → vm_emissions_reg(i,"peatland",poll58)` at `modules/58_peatland/v2/equations.gms:91-92`; `peatland ∈ emis_annual` at `core/sets.gms:322`; `s58_fix_peatland = 2020`; `peatland = "v2"`; realization description matches `modules/58_peatland/v2/realization.gms:8-17`. All exact.
- **§5.2 convergence table** (15 / 56 / 80 / 96 %) is arithmetically correct against `i59_lossrate(t)=1-0.85**m_yeardiff(t)`. **Note for future editors**: the code comment at `modules/59_som/cellpool_jan23/preloop.gms:42` says "44% in 5 years", which is the **legacy remainder**, not the loss rate — §5.2 is right and the code comment is the inconsistent one. Do **not** "correct" §5.2 to match it.
- **Uncalibrated-curve consumer set** (M14 `im_growing_stock_ysf`, M29 tree cover, M32 aff+NDC, M35 youngsecdf) is **complete**; matches `read_by: ['14','29','32','35','52']`.
- **Defaults**: `s52_growingstock_calib = 1` hard-coded and genuinely absent from `config/default.cfg` (positive control on `s58_fix_peatland` returns 1926/1931); `s59_scm_target = 0` (1978); `c59_irrigation_scenario = "on"` (1956 + `modules/59_som/cellpool_jan23/input.gms:61`, with the `off` neutralisation at `input.gms:70`); `s59_cost_scm_recur = 65` (`input.gms:15`); `i59_tillage_share("full_tillage")=1` and `i59_input_share("medium_input")=1` (`preloop.gms:53,55`).
- **Commit `6b00f9dea`** exists, dated **2026-07-01**, subject "Fix youngsecdf wood production: use uncalibrated growing stock" — §3.6 claim exact.
- **§3.6 caveat 2 (unverified lead)** checks out as stated: `q35_prod_secdforest` (`modules/35_natveg/pot_forest_may24/equations.gms:144-147`) reads the purely calibrated `im_growing_stock(...,"secdforest")` while `q35_carbon_secdforest` (`:49-51`) reads the blend `p35_carbon_density_secdforest` (`presolve.gms:248-252`); natural-origin area bounded at `presolve.gms:177-180`. The "unverified lead, not an established defect" framing is appropriate and should stay.
- **Sets**: `land` = 7 (`core/sets.gms:250-251`), `emis_oneoff` = 21 = 7x3 (`:314-318`), `emis_land` mapping (`:332-354`), `c_pools` (`:324-325`), `stockType /actual, actualNoAcEst/` (`modules/56_ghg_policy/price_aug22/sets.gms:212-213`), `noncropland59 /past, forestry, primforest, secdforest, other, urban/` (which is what makes the "forestry/pasture soilc converges to natural density" claims correct).

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
$ rg -n "pm_carbon_density_plantation_ac\b" modules/ core/ | grep -v uncalib
modules/32_forestry/dynamic_may24/preloop.gms:18:p32_carbon_density_ac_forestry(t_all,j,ac) = pm_carbon_density_plantation_ac(t_all,j,ac,"vegc");
modules/32_forestry/dynamic_may24/preloop.gms:56:  p32_avg_increment(t_all,j,ac) = pm_carbon_density_plantation_ac(t_all,j,ac,"vegc") / ((ord(ac)+1)*5);
modules/32_forestry/dynamic_may24/presolve.gms:65:p32_carbon_density_ac(t,j,"plant",ac,ag_pools) = pm_carbon_density_plantation_ac(t,j,ac,ag_pools);
modules/14_yields/managementcalib_aug19/presolve.gms:26:     pm_carbon_density_plantation_ac(t,j,ac,"vegc")
modules/14_yields/dynRegPastrTau_apr26/presolve.gms:26  (non-default realization)
modules/52_carbon/normal_dec17/{preloop.gms:114, start.gms:17,20, declarations.gms:12}  (self)

$ grep -rn "pm_carbon_density_plantation_ac" modules/32_forestry/ | grep -v uncalib   # method 2
presolve.gms:65 / preloop.gms:18 / preloop.gms:56        (3 hits — agrees with rg)

$ grep -rn "pm_carbon_density_plantation_ac_uncalib" modules/32_forestry/             # positive control
modules/32_forestry/dynamic_may24/presolve.gms:61        (search works in this dir)

$ awk 'NR>=108 && NR<=109' modules/32_forestry/dynamic_may24/equations.gms            # the sink
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
$ awk 'NR==1835' config/default.cfg
# *   actual: CO2 emissions for pricing are based on the difference of actual carbon stocks between time steps
$ grep -n "c56_carbon_stock_pricing" config/default.cfg
1838:c56_carbon_stock_pricing <- "actualNoAcEst"   # def = actualNoAcEst
$ rg -n "c56_carbon_stock_pricing" --glob '!*.gms' .
./config/default.cfg:1838 | ./CHANGELOG.md:891 (documents `cfg$gms$c56_carbon_stock_pricing`)
```

**confirmed**: true

**proposed_fix**: `config/default.cfg:1835` → `config/default.cfg:1838`. Leave the substance untouched; optionally cite `CHANGELOG.md:891` as corroboration and append "(line verified against develop `2c02843ec`)" since this pointer is inherently drift-prone.

---

### B3 — MAJOR — `set_membership` — §6.3 age-class labels are ordinal indices, but the `ac` set is labelled by YEARS

**doc_line**: `carbon_balance_conservation.md:493` (table rows `:493-499`)

**Claim in doc** (§6.3 "Growth Trajectories", Age Class column): `5 → ac1`, `10 → ac2`, `20 → ac4`, `30 → ac6`, `50 → ac10`, `80 → ac16`, `100 → ac20`.

**Reality in code**: `core/sets.gms:269-275` defines `ac / ac0, ac5, ac10, ac15, ac20, ac25, …, ac300, acx /` — **62 members labelled by years in 5-year steps**. Consequences:
- `ac1`, `ac2`, `ac4`, `ac6`, `ac16` **do not exist** in the set.
- `ac10` and `ac20` **do exist**, but denote **10 and 20 years** — not the 50 and 100 the table assigns. This is the dangerous half: a reader indexing `pm_carbon_density_plantation_ac(t,j,"ac10","vegc")` for a 50-year-old stand silently gets a 10-year-old one (5x age error, no GAMS error raised).

The doc's own §3.5 (`:224`) gets this right — "ac0 → ac5 → ac10 → … → acx" — so the file is internally inconsistent. Root cause: `m_growth_vegc`'s last argument in `start.gms:17/28/48` is `(ord(ac)-1)`, an **ordinal**, which §6.3 mistook for the set label.

**Severity**: no Critical trigger matches literally (the fabricated names are set members, not `vm_*`/`pm_*` identifiers or equations); Major triggers *"right concept, wrong number"* and *"fabricated count for a set … list"* both fire → **Major**. (Related immutable anchor: R16 `ac140/acx` vs `ac300` → Critical for set *extent*; this is set *labelling*, one tier down.)

**file_evidence**: `core/sets.gms:269-275`; `modules/52_carbon/normal_dec17/start.gms:17`.

**verify_cmd**:
```
$ awk 'NR>=269 && NR<=275' core/sets.gms
  ac Age classes  / ac0,ac5,ac10,ac15,ac20,ac25,ac30,ac35,ac40,ac45,ac50,
                    ac55,…,ac295, ac300, acx /
$ awk 'NR==17' modules/52_carbon/normal_dec17/start.gms   # ordinal, not label
  …,(ord(ac)-1));
```

**confirmed**: true

**proposed_fix**: rewrite the Age Class column as `ac0, ac5, ac10, ac20, ac30, ac50, ac80, ac100, acx` (label = age in years) and add: *"Set labels are years (`ac0…ac300, acx`, `core/sets.gms:269-275`); the `ac` argument inside `m_growth_vegc` is the ordinal `ord(ac)-1`, which the macro multiplies by 5 to recover years."*

---

### B4 — MINOR — `formula` — §9.3 R snippet multiplies year-labelled age classes by 5

**doc_line**: `carbon_balance_conservation.md:823`

**Claim in doc**: `ages <- as.numeric(gsub("ac", "", getNames(vegc_by_age))) * 5`

**Reality in code**: GDX labels are the GAMS set labels `ac0, ac5, ac10, …` (`core/sets.gms:269-275`), i.e. **already years**. `gsub("ac","","ac50")` → `50`; `* 5` → **250 years**. The plotted x-axis would be 5x too long for every point except `ac0`. Same root misconception as B3 but a distinct, *runnable* artifact with a distinct fix, so recorded separately.

**file_evidence**: `core/sets.gms:269-275`

**verify_cmd**: `awk 'NR>=269 && NR<=275' core/sets.gms` → labels are `ac0,ac5,ac10,…` (years, 5-year steps).

**confirmed**: true

**proposed_fix**: drop the `* 5` — `ages <- as.numeric(gsub("ac", "", getNames(vegc_by_age)))  # labels are already years; drop acx first`.

---

### B5 — MINOR — `formula` — §8.4 uses the legacy fraction (44%) where the convergence fraction (56%) belongs

**doc_line**: `carbon_balance_conservation.md:734`

**Claim in doc**: "- Year 5: 44% toward new equilibrium = +4 tC/ha"

**Reality in code**: `i59_lossrate(t) = 1-0.85**m_yeardiff(t)` (`modules/59_som/cellpool_jan23/preloop.gms:45`) gives **1 − 0.85^5 = 0.5563**, i.e. **56%** toward equilibrium, 44% legacy. The doc's own §5.2 table (`:401`) and interpretation (`:412`) both say 56/44 correctly; §8.4 inverts them. Rows below are consistent (Year 10 → 80%, Year 20 → 96%), so this row is the outlier. Downstream: 9 tC/ha × 0.5563 = **+5.0 tC/ha**, not +4.

Likely inherited from the erroneous code comment at `modules/59_som/cellpool_jan23/preloop.gms:42` ("44% in 5 years"), which is itself wrong — see the CORRECT-list note.

**file_evidence**: `modules/59_som/cellpool_jan23/preloop.gms:45`

**verify_cmd**: `python3 -c "print(1-0.85**5, 9*(1-0.85**5))"` → `0.5563 5.01` (controls: 10 yr → 0.8031, 20 yr → 0.9612, matching §5.2).

**confirmed**: true

**proposed_fix**: `- Year 5: 56% toward new equilibrium = +5.0 tC/ha`

---

### B6 — MINOR — `formula` — §8.1 gradual soil-emission arithmetic is wrong (458 vs 550)

**doc_line**: `carbon_balance_conservation.md:656`

**Claim in doc**: "- Gradual (soilc over 20 years): 30 tC/ha × 100 Mha × (44/12) / 20 years = **458 Tg CO₂/year**"

**Reality**: 30 × 100 = 3,000 Tg C; × 44/12 = 11,000 Tg CO₂; ÷ 20 = **550 Tg CO₂/yr**. The stated 458 corresponds to 25 tC/ha, but the table immediately above (`:649`) gives the soilc loss as 30 tC/ha (80 → 50). The sibling calculation at `:655` (56,833 Tg CO₂ from 155 tC/ha) is arithmetically correct, so this is an isolated slip, not a convention difference. Labelled "made-up numbers", but the *arithmetic* is checkable and wrong given the doc's own inputs.

**file_evidence**: n/a (arithmetic on doc-internal numbers; the 44/12 conversion and the `mio. tC = Tg C` identity are confirmed against `modules/56_ghg_policy/price_aug22/declarations.gms:34,40`).

**verify_cmd**: `python3 -c "print(30*100*44/12/20)"` → `550.0` (control `print(155*100*44/12)` → `56833.3`, matching the doc's other figure; `25*100*44/12/20` → `458.3`, showing where 458 came from).

**confirmed**: true

**proposed_fix**: `… / 20 years = **550 Tg CO₂/year**`

---

### B7 — MINOR — `formula` — §6.3 vegc trajectory does not follow from its own stated A, k, m

**doc_line**: `carbon_balance_conservation.md:487` (parameters `:487-488`, table values `:493-499`)

**Claim in doc**: with `A = 100 tC/ha, k = 0.06, m = 2.0`, vegc = 14 / 26 / 44 / 58 / 75 / 88 / 93 at 5 / 10 / 20 / 30 / 50 / 80 / 100 years.

**Reality**: `m_growth_vegc` (`core/macros.gms:18`) is `S + (A-S)*(1-exp(-k*(ac*5)))**m`. With S=0, A=100, k=0.06, m=2 the values are **6.7 / 20.4 / 48.8 / 69.7 / 90.3 / 98.4 / 99.5**. The tabulated series instead fits roughly `k ≈ 0.03, m = 1`. The formula quoted in §6.1 is itself correct — it is the table that does not follow from it. The 20-year value (44) is reused in §8.2 (`:676`), so the mismatch propagates.

**file_evidence**: `core/macros.gms:18`

**verify_cmd**:
```
$ python3 -c "import math;print([(t, round(100*(1-math.exp(-0.06*t))**2,1)) for t in (5,10,20,30,50,80,100)])"
[(5, 6.7), (10, 20.4), (20, 48.8), (30, 69.7), (50, 90.3), (80, 98.4), (100, 99.5)]
```

**confirmed**: true

**proposed_fix**: recompute the table from A=100, k=0.06, m=2.0 (preferred — an m=2 sigmoid is the shape the section illustrates) and update the dependent §8.2 vegc figures; or restate the parameters as `k ≈ 0.03, m = 1.0` to match the existing series.

---

### B8 — MINOR — `citation` — References line-range no longer spans the Module-52 growth code

**doc_line**: `carbon_balance_conservation.md:987`

**Claim in doc**: "- Module 52 growth: `modules/52_carbon/normal_dec17/start.gms:8-39`"

**Reality in code**: `start.gms` is 51 lines. Growth code now occupies **8-31** (forestry + secdforest) and **46-51** (other land); `:33-44` is calibration-parameter initialisation plus the uncalibrated-curve snapshot, which is not growth code. The cited `8-39` therefore (a) **omits the other-land Chapman-Richards and litter curves entirely** — which §3.6 of this same doc relies on — and (b) includes ~12 lines of calibration bookkeeping. Confirmed as drift, not a mis-write: before the forestry-overhaul commit the file was 38 lines and `8-38` *was* exactly the growth block.

**file_evidence**: `modules/52_carbon/normal_dec17/start.gms:46-51` (other-land curves, outside the range); `:33-44` (calibration init + uncalib snapshot, inside it).

**verify_cmd**:
```
$ wc -l < modules/52_carbon/normal_dec17/start.gms
51
$ git show 75d7ee167~1:modules/52_carbon/normal_dec17/start.gms | wc -l
38        # pre-overhaul: 8-38 WAS exactly the growth block -> confirms drift
$ awk 'NR==34||NR==43||NR==48' modules/52_carbon/normal_dec17/start.gms
i52_k_calib_secdf(i) = 0;
pm_carbon_density_secdforest_ac_uncalib(t_all,j,ac,ag_pools) = pm_carbon_density_secdforest_ac(...);
pm_carbon_density_other_ac(t_all,j,ac,"vegc") = m_growth_vegc(...);
```

**confirmed**: true

**proposed_fix**: `Module 52 growth: modules/52_carbon/normal_dec17/start.gms:8-31 (forestry + secdforest), :46-51 (other land); FRA-2025 k/m calibration overwrite: modules/52_carbon/normal_dec17/preloop.gms:71-73, :114-116`.

---

### B9 — MINOR — `attribution_read` — `vm_maccs_costs` consumer set omits Module 36

**doc_line**: `carbon_balance_conservation.md:593`

**Claim in doc**: §7.4 "**Provides**: … `vm_maccs_costs(i,factors)`: Labor and capital costs of mitigation → to Module 11"

**Reality in code**: two direct consumers, not one. Module 36 (employment, default realization `exo_may22`) reads it in an equation:
```
modules/36_employment/exo_may22/equations.gms:27-28
 q36_employment_maccs(i2) .. v36_employment_maccs(i2)
   =e= (vm_maccs_costs(i2,"labor")) * (1 / sum(ct,f36_weekly_hours(ct,i2)*s36_weeks_in_year*pm_hourly_costs(ct,i2,"scenario")));
```
Role map agrees: `vm_maccs_costs → read_by: ['11','36','57']`.

Rated Minor rather than Major/Critical because this bullet is an arrow-annotation in a carbon-balance narrative rather than a canonical consumer inventory, and the carbon-balance-relevant destination (M11) is correct. It still costs a reader doing modification-impact analysis on `vm_maccs_costs` one missed module. Note the same doc's §7.2 arrow-annotations (`vm_nr_som` → M51, `vm_cost_scm` → M11) **are** complete — verified by whole-tree grep — so this is the lone gap.

**file_evidence**: `modules/36_employment/exo_may22/equations.gms:28` (omitted); `modules/11_costs/default/equations.gms:28` (documented, correct).

**verify_cmd**:
```
$ rg -n "vm_maccs_costs" modules/ core/
modules/57_maccs/on_aug22/{postsolve.gms:11,14,17,20 | declarations.gms:25 | scaling.gms:8 | equations.gms:36,46}  (self)
modules/36_employment/exo_may22/equations.gms:28      <-- OMITTED
modules/11_costs/default/equations.gms:28             (documented)
$ grep -nE 'cfg\$gms\$employment' config/default.cfg
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
$ rg -ni "setaside|set_aside|perennial" modules/59_som/
modules/59_som/static_jan19/realization.gms:16:*' e.g. differences for annual and perennial crops.
modules/59_som/cellpool_jan23/input.gms:24:*' … frequent use of perennial grasses in annual
   -> prose only; no set member, neither hit in cellpool_jan23's factor machinery
$ rg -c "kcr" modules/59_som/cellpool_jan23/preloop.gms
6      # positive control: the search works in this directory
```

**confirmed**: true (Major trigger *"fabricated … list"* considered; downgraded per the rubric's "pick the lower tier" tie-breaker, since the bullet is framed as IPCC methodology and IPCC's F_LU genuinely has those categories.)

**proposed_fix**: `- **FLU** (Land Use): applied per MAgPIE crop type via f59_cratio_landuse(i,climate59_2019,kcr) (modules/59_som/cellpool_jan23/input.gms:43). IPCC's set-aside / perennial categories are collapsed into the crop-type dimension in preprocessing; there is no FLU switch in the model.` Same correction at `:137`.

---

### B11 — MINOR — `formula` — §8.2 convergence percentages are shifted one row, and mutually inconsistent

**doc_line**: `carbon_balance_conservation.md:678` (and `:684`)

**Claim in doc**: "**Year 20 (Young Plantation)**: … soilc: 70 tC/ha (80% toward natural, from Module 59)"; "**Year 50 (Mature Plantation)**: … soilc: 78 tC/ha (96% toward natural)".

**Reality in code**: the percentages are attributed explicitly to Module 59 but are shifted one row against `1 - 0.85^years`: 80% corresponds to **10** years and 96% to **20** years (the doc's own §5.2 table, `:402-404`). At 20 years the model gives 96%; at 50 years, 99.97%. The two rows also imply different targets: `50 + 0.80·(N−50) = 70` → natural = 75 tC/ha, while `50 + 0.96·(N−50) = 78` → 79.2 tC/ha.

**file_evidence**: `modules/59_som/cellpool_jan23/preloop.gms:45`

**verify_cmd**: `python3 -c "print(1-0.85**10, 1-0.85**20, 1-0.85**50)"` → `0.8031 0.9612 0.9997`

**confirmed**: true

**proposed_fix**: relabel to the code-consistent schedule — Year 20 ≈ 96% toward natural; drop the Year-50 percentage or state ≈100% — and recompute both soilc values from one consistent natural density. (The block is illustrative, but the percentages are code-derived and should not contradict §5.2.)

---

### B12 — INFORMATIONAL — `citation` — five citations omit the required `modules/` prefix

**doc_line**: `carbon_balance_conservation.md:180` (identical paragraph at `:479`; also `:247`, `:254`)

**Claim in doc**: `14_yields/managementcalib_aug19/presolve.gms:66`, `29_cropland/detail_apr24/preloop.gms:46,48`, `32_forestry/dynamic_may24/presolve.gms:59,61,68`, `35_natveg/pot_forest_may24/presolve.gms:242`, `normal_dec17/preloop.gms:71-73` / `:114-116` / `:29-30`.

**Reality**: MANDATE 16 requires the full form `modules/NN_name/realization/file.gms:LINE`. All the cited **content** is exactly right (verified individually); only the path form is non-compliant, which breaks copy-paste-to-`Read` and any path-based checker.

**file_evidence**: `modules/14_yields/managementcalib_aug19/presolve.gms:66`; `modules/29_cropland/detail_apr24/preloop.gms:46,48`; `modules/32_forestry/dynamic_may24/presolve.gms:59,61,68`; `modules/35_natveg/pot_forest_may24/presolve.gms:242`; `modules/52_carbon/normal_dec17/preloop.gms:29-30,71-73,114-116`.

**verify_cmd**:
```
$ awk 'NR==66' modules/14_yields/managementcalib_aug19/presolve.gms
     pm_carbon_density_secdforest_ac_uncalib(t,j,ac,"vegc")
$ awk 'NR==46||NR==48' modules/29_cropland/detail_apr24/preloop.gms
 p29_carbon_density_ac(t,j,ac,ag_pools) = pm_carbon_density_secdforest_ac_uncalib(...);
 p29_carbon_density_ac(t,j,ac,ag_pools) = pm_carbon_density_plantation_ac_uncalib(...);
$ awk 'NR==59||NR==61||NR==68' modules/32_forestry/dynamic_may24/presolve.gms
 …"aff"… = pm_carbon_density_secdforest_ac_uncalib(...);  |  …"aff"… = pm_carbon_density_plantation_ac_uncalib(...);  |  …"ndc"… = pm_carbon_density_secdforest_ac_uncalib(...);
$ awk 'NR==242' modules/35_natveg/pot_forest_may24/presolve.gms
p35_carbon_density_other(t,j,"youngsecdf",ac,ag_pools) = pm_carbon_density_secdforest_ac_uncalib(...);
```

**confirmed**: true

**proposed_fix**: prefix each with `modules/`. Content requires no change.

---

## Deferred (unverified / judgement calls — no edit proposed)

1. **§9.1 R consistency check** (`:756-779`): `readGDX(gdx,"pcm_carbon_stock", field="l")` applies `field="l"` to a GAMS *parameter* (`modules/56_ghg_policy/price_aug22/declarations.gms:19`), `:761` passes both `select=` and `field=`, and `dimSums(stock_change, dim=c("cell","land","c_pools"))` leaves `stockType` in place and never aggregates cells to regions, so the result would not be comparable to the regional `ov_emissions_reg`. Snippet not executed — recorded as a lead, and an R-lens question rather than a GAMS-ground-truth one.
2. **§7.2 "Receives" attributions**: `vm_land` attributed to M10 and `vm_area` to M30. Role map shows `vm_land` populated by 10, 29, 31, 32, 34, 35 and `vm_area` by 30 and 41. Both are *declared* in the attributed module and M10/M30 are the primary populators, so the simplification is defensible; not filed.
3. **§2.3 "Subsoil … Static (fixed from LPJmL via M52)"**: `i59_subsoilc_density(t_all,j)` is time-indexed and derived from the time-varying `fm_carbon_density` (default `c52_carbon_scenario = "cc"`, `modules/59_som/cellpool_jan23/preloop.gms:12`), so it is not literally static across time. The doc's operative claim — "not affected by land use" — is correct; imprecision rather than error.
4. **Domain-set imprecision**: the doc writes `fm_carbon_density(t,j,land,c_pools)` and `pm_carbon_density_*_ac(t,j,ac,ag_pools)` at `:107`, `:513-516`, `:699`, `:948`; the declared domain is `t_all` (`modules/52_carbon/declarations.gms:9-13`, `modules/52_carbon/normal_dec17/input.gms:16`), and the sibling `modules/module_52.md` uses `t_all` throughout (`:50`, `:738`). Pervasive and harmless to a reader (t ⊂ t_all) — Informational at most, so recorded here rather than filed.
5. **§5.3 IPCC stock-change factor examples** (F = 0.69, F = 1.17) and **§6.2 climate-class k ranges** (0.02-0.08): backing inputs (`f59_ch5_F_*.csv`, `f52_growth_par.csv`) are run-time artifacts absent from the repo (`modules/*/input/` contains only a `files` manifest). Could not verify; both explicitly labelled "typical"/"illustrative".
6. **Doc header (`:5`) "Modules Covered: 52, 53, 59 (57 for mitigation costs)"** omits Module 58, which §10.2 item 7 documents at length. Informational; not filed.
7. **§10.2 item 7 peatland double-counting claim** ("avoided by construction (peat is not in `c_pools`)"): `c_pools = /vegc,litc,soilc/` confirmed and M58 writes only `vm_emissions_reg`. Sound as far as GAMS goes, but whether preprocessing folds peat carbon into `fm_carbon_density` upstream is a preproc-agent question.
8. **§11.2 summary formula** (`:935`) writes `vegc(age) = 0 + (Mature - 0) × (1 - exp(-k × age))^m`, dropping the `ac*5` conversion in `core/macros.gms:18`. Defensible if `age` is read as years (§6.1 states the conversion explicitly), so not filed — but an editor touching §11.2 could disambiguate.
9. **`modules/59_som/cellpool_jan23/realization.gms:9`** calls itself "The cellpool_aug23 realization" while the directory is `cellpool_jan23`. Upstream code typo, not a doc bug; the doc correctly uses `cellpool_jan23` throughout.
10. **§7.5 / §10.2 fire language** — checked against `modules/35_natveg/pot_forest_may24/sets.gms:11-15` and `presolve.gms:14-26`, which apply historical `f35_forest_lost_share(i,{shifting_agriculture,wildfire})` rates. The doc does not claim mechanistic fire modelling, so the parameterization-vs-mechanism rule is respected. No bug.

---

## Confidence notes

- All 12 bugs are backed by reproducible commands whose output is quoted above, re-run in **this** session against HEAD `2c02843ec`. No finding is relayed from the earlier pass without independent re-derivation.
- **B1** carries the heaviest evidence because it has the highest false-positive cost: role map + `rg` + `grep` all agreeing on the same 3 hits in `modules/32_forestry/`, a positive control proving the search works in that directory, and the sink (`q32_carbon` → `vm_carbon_stock`) read directly.
- **B1 severity** is the one genuinely arguable call (Critical vs Major); the reasoning is stated inline so a reviewer can overrule it without re-deriving.
- **B3 and B4** share a root cause (ordinal vs year labelling of `ac`) but have different locations and different fixes; fixing one does not fix the other.
- **B5, B6, B7, B11** are all inside blocks labelled "illustrative"/"made-up numbers". They are filed anyway because in each case the *derivation* is code-anchored (the `1-0.85^n` lossrate, the 44/12 conversion, `m_growth_vegc`) and wrong on the doc's own stated inputs — a reader reconciling them would waste time hunting for a hidden factor. None is rated above Minor for that reason.
- No bug depends on an absence claim that was not double-confirmed with a second method plus a positive control.
