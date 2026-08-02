# R60 depth audit — `cross_module/carbon_balance_conservation.md`

**Lens**: `citation_formula` (enter from file:line citations; check existence, range, token presence, formula fidelity)
**Ground truth**: MAgPIE `develop` read-only worktree, HEAD `2c02843ec`
**Auditor**: adversarial depth-first, Opus
**Date**: 2026-08-02

---

## Scope and method

1. **Mechanical citation sweep** — regex-extracted every `modules/…/*.gms:NN`, `core/*.gms:NN`, `config/default.cfg:NN` citation in the doc (66 instances), then `test -f` + `wc -l` + range check on each. **Zero missing files, zero out-of-range line numbers.** A further ~12 abbreviated citations (`normal_dec17/preloop.gms:71-73`, `:114-116`, `14_yields/…presolve.gms:66`, `29_cropland/…preloop.gms:46,48`, `32_forestry/…presolve.gms:59,61,68`, `35_natveg/…presolve.gms:117,240,242,248-252`) were resolved and checked by hand.
2. **Token-presence check** — read each cited line/range and confirmed it contains the claimed identifier or construct.
3. **Formula fidelity** — re-derived every quoted equation against source; re-computed every arithmetic result in the doc with `python3`.
4. **Attribution** — checked `audit/integrated/depth_rolemap.json` first, then confirmed direction with both-endpoints greps (`NAME(` and `NAME.`), each grep isolated, each absence claim backed by a second method plus a positive control.
5. **Defaults** — every cited default cross-checked in both `input.gms` and `config/default.cfg`; every cited realization confirmed against `cfg$gms$<module>`.

**Claims verified: ~130.** **Bugs found: 8** (1 Critical, 2 Major, 5 Minor).

---

## What is CORRECT (recorded so future rounds don't re-litigate)

This doc is unusually well-cited. The following load-bearing items were verified exact and should not be re-flagged:

- **All 14 realizations named** are the current defaults (`cropland=detail_apr24`, `past=endo_jun13`, `forestry=dynamic_may24`, `urban=exo_nov21`, `natveg=pot_forest_may24`, `carbon=normal_dec17`, `methane=ipcc2006_aug22`, `ghg_policy=price_aug22`, `maccs=on_aug22`, `peatland=v2`, `som=cellpool_jan23`, `yields=managementcalib_aug19`, `nr_soil_budget=macceff_aug22`, `nitrogen=rescaled_jan21`).
- **§4.1 `q52_emis_co2_actual`** is quoted verbatim-correct against `modules/52_carbon/normal_dec17/equations.gms:16-19`.
- **§3.1 `v59_som_target(j,"crop")` 4-term expansion** matches `modules/59_som/cellpool_jan23/equations.gms:20-27` term-for-term, including the subtlety that `i59_cratio_treecover` carries no `j` index while `i59_cratio_fallow(j)` does.
- **`vm_carbon_stock` populator set** (§7.5): M29/M31/M32/M34/M35 + M59-soilc — exactly matches the role map (`populated_by: 29,31,32,34,35,59`) and a whole-tree grep. All default-realization populating equations are indexed over the free `stockType` set, so the doc's "fill **both** slices" claim holds. (The only `stockType`-less populator is `modules/31_past/static/presolve.gms:15`, a non-default realization.)
- **§7.3 parallel-not-serial claim** — M56 recomputes CO₂ in `q56_emis_pricing_co2` and does **not** consume M52's `vm_emissions_reg(…,"co2_c")`; `q56_emis_pricing` is indexed over `emis_annual`, which excludes the `emis_oneoff` CO₂ sources. Correct, and correctly framed as parallel readers of `vm_carbon_stock` (MANDATE 21 satisfied).
- **§7.4 MACC application map** — verified in full: M53 `:29/:52/:63` carry `(1-im_maccs_mitigation)`, `q53_emissions_resid_burn` `:70-72` does not, `maccs_ch4` is exactly `/rice_ch4, ent_ferm_ch4, awms_ch4/`, M51's MACC is AWMS-only at `:71` and multiplies all `n_pollutants_direct` per the `:62-64` comment, the `inorg_fert_n2o` MACC lives in M50 `presolve.gms:54-64`, and rice N₂O is genuinely zero (`rice ∉ emis_source_n51`; `preloop.gms:8-10` fixes and selectively relaxes). `emis_source_n_cropsoils51` (which *does* contain `rice`) only dimensions the EF table — it never writes `vm_emissions_reg`.
- **§10.2 item 7 (peatland)** — `q58_peatland_emis → vm_emissions_reg(i,"peatland",poll58)` at `modules/58_peatland/v2/equations.gms:91-92`; `peatland ∈ emis_annual` at `core/sets.gms:322`; `s58_fix_peatland = 2020`; `peatland = "v2"`. All exact.
- **§5.2 convergence table** (15 / 56 / 80 / 96 %) is arithmetically correct against `i59_lossrate(t)=1-0.85**m_yeardiff(t)`. *Note for future editors*: the code comment at `modules/59_som/cellpool_jan23/preloop.gms:42` says "44% in 5 years", which is the **legacy remainder**, not the loss rate — the doc's §5.2 is right and the code comment is the inconsistent one. Do not "correct" §5.2 to match the comment.
- **The uncalibrated-curve consumer set** (M14 `im_growing_stock_ysf`, M29 tree cover, M32 afforestation + NDC, M35 youngsecdf) is **complete** for default realizations — verified by whole-tree grep of `pm_carbon_density_*_ac_uncalib`.
- **Defaults**: `s52_growingstock_calib = 1` (hard-coded, genuinely not in `config/default.cfg`), `s59_scm_target = 0`, `c59_irrigation_scenario = "on"`, `s59_cost_scm_recur = 65`, `i59_tillage_share("full_tillage")=1`, `i59_input_share("medium_input")=1`. All confirmed.
- **Commit `6b00f9dea` (2026-07-01)** exists with the stated subject ("Fix youngsecdf wood production: use uncalibrated growing stock").
- `land` = 7 members, `emis_oneoff` = 21 members (7 × 3), `othertype35` = `/othernat, youngsecdf/`, `stockType` = `/actual, actualNoAcEst/`. All exact.

---

## BUGS

### B1 — CRITICAL — Calibrated-growth-curve consumer set omits Module 32 (and M14's forestry read)

**doc_line**: `carbon_balance_conservation.md:180` (identical text repeated verbatim at `:479`)

**Claim in doc**:
> "M14 and M35 read the CALIBRATED curve as well - M14 for regular secdforest growing stock (`modules/14_yields/managementcalib_aug19/presolve.gms:44`), M35 for secdforest carbon density, which it BLENDS with the uncalibrated curve by natural-origin area share (`modules/35_natveg/pot_forest_may24/presolve.gms:248-252`)."

**Reality in code**: **Module 32 (`dynamic_may24`, the default) is a major consumer of the calibrated `pm_carbon_density_plantation_ac`, at three sites**, and **M14 reads it at a fourth site the doc does not mention**:

| Site | What it drives |
|---|---|
| `modules/32_forestry/dynamic_may24/presolve.gms:65` | `p32_carbon_density_ac(t,j,"plant",ac,ag_pools)` → `q32_carbon` (`equations.gms:108-109`) → **`vm_carbon_stock(j,"forestry",…)`** — i.e. the entire timber-plantation carbon stock |
| `modules/32_forestry/dynamic_may24/preloop.gms:18` | `p32_carbon_density_ac_forestry` → marginal increment → **rotation lengths** |
| `modules/32_forestry/dynamic_may24/preloop.gms:56` | `p32_avg_increment` → rotation rule under `c32_rot_calc_type == mean_annual_increment` |
| `modules/14_yields/managementcalib_aug19/presolve.gms:26` | `im_growing_stock(t,j,ac,"forestry")` — plantation wood yield |

**Why this is Critical, not Major**: this is the R20 immutable anchor's exact bug class, on the exact same parameter family — *"module doc cited `pm_carbon_density_ac` as having three consumers when commit added two more (M32 afforestation + NDC presolve) … → **Critical** (doc said wrong consumer set; user would have missed two modules in a refactor)"*. The rubric's latent-doc-bug mandate restates it: *"a wrong producer/consumer set is **Critical** per the R20 anchor"*. Aggravating context: this warning block sits **directly under §3.3 "Forestry (Plantations)"** — the one section that is *about* plantation carbon — and its surrounding sentence enumerates M32 only as an **un**calibrated-curve reader. A developer touching `s52_growingstock_calib`, the FRA-2025 bisection, or the `i52_m_avg_plant` region-averaging would conclude from this doc that the M32 timber-plantation carbon and rotation-length machinery is unaffected. It is the primary consumer.

**file_evidence**: `modules/32_forestry/dynamic_may24/presolve.gms:65`; `modules/32_forestry/dynamic_may24/preloop.gms:18`; `modules/32_forestry/dynamic_may24/preloop.gms:56`; `modules/14_yields/managementcalib_aug19/presolve.gms:26`; sink at `modules/32_forestry/dynamic_may24/equations.gms:108-109`.

**verify_cmd** (two methods + positive control, each isolated):
```
$ rg -n "pm_carbon_density_plantation_ac\b" modules/ core/ | grep -v "_uncalib"
  …/32_forestry/dynamic_may24/presolve.gms:65, …/preloop.gms:18, …/preloop.gms:56,
  …/14_yields/managementcalib_aug19/presolve.gms:26, …/52_carbon/normal_dec17/{preloop:114,start:17,20,declarations:12}

$ grep -rn "pm_carbon_density_plantation_ac" modules/32_forestry/ | grep -v uncalib      # method 2
  presolve.gms:65 / preloop.gms:18 / preloop.gms:56          (3 hits — agrees with rg)

$ grep -rn "pm_carbon_density_plantation_ac_uncalib" modules/32_forestry/                # positive control
  presolve.gms:61                                            (search works in this dir)
```
Role map (`audit/integrated/depth_rolemap.json`) is consistent: `pm_carbon_density_secdforest_ac → read_by [14,35,52]`; the plantation twin is not in the map, so the grep is the authority here — hence the double-method + control.

**confirmed**: true

**proposed_fix**: In both copies of the block (`:180` and `:479`), replace the final sentence with:
> "M14, M32 and M35 read the CALIBRATED curves as well — M14 for regular secdforest growing stock (`modules/14_yields/managementcalib_aug19/presolve.gms:44`) and for plantation growing stock (`:26`); **M32 for timber-plantation carbon density (`modules/32_forestry/dynamic_may24/presolve.gms:65`, which feeds `q32_carbon` → `vm_carbon_stock(j,"forestry",…)`) and for rotation lengths (`modules/32_forestry/dynamic_may24/preloop.gms:18,56`)**; M35 for secdforest carbon density, which it BLENDS with the uncalibrated curve by natural-origin area share (`modules/35_natveg/pot_forest_may24/presolve.gms:248-252`)."

Also add one line to §3.3's table note: plantation `vegc` comes from the **FRA-2025-calibrated** curve, unlike afforestation/NDC (`"aff"`, `"ndc"`), which use the uncalibrated one. Check `modules/module_52.md` and `modules/module_32.md` for the same omission before closing.

---

### B2 — MAJOR — Citation drift: `config/default.cfg:1835` now points at a comment; the assignment is at `:1838`

**doc_line**: `carbon_balance_conservation.md:101`

**Claim in doc**:
> "⚠️ Do **not** cite `config/default.cfg:1835` for this default: that line omits the `cfg$gms$` prefix its siblings carry, so it never reaches GAMS and the switch is currently unreachable from config"

**Reality in code**: `config/default.cfg:1835` is now a **comment**: `# *   actual: CO2 emissions for pricing are based on the difference of actual carbon stocks between time steps`. The assignment lives at **`:1838`**. The *substantive* claim survives intact — `:1838` reads `c56_carbon_stock_pricing <- "actualNoAcEst"` with no `cfg$gms$` prefix, while its sibling at `:1831` is `cfg$gms$c56_emis_policy <- …`; a whole-repo grep finds no script that consumes the bare name, so the switch is indeed unreachable from config and the effective default comes from `modules/56_ghg_policy/price_aug22/input.gms:90`.

**Why Major**: rubric trigger *"File:line citation drift to adjacent but different content (would mislead a careful reader)"*. Here the harm is specific: the whole point of the sentence is the **syntax of that line**. A reader who checks `:1835` finds a comment (which trivially has no `cfg$gms$` prefix and no `<-` at all) and would either dismiss the warning as bogus or conclude the config entry does not exist. This is the R20 citation-drift anchor pattern in miniature.

**file_evidence**: `config/default.cfg:1838` (assignment); `config/default.cfg:1835` (comment); `config/default.cfg:1831` (prefixed sibling).

**verify_cmd**:
```
$ sed -n '1835p;1838p' config/default.cfg
1835: # *   actual: CO2 emissions for pricing are based on the difference of actual carbon stocks between time steps
1838: c56_carbon_stock_pricing <- "actualNoAcEst"   # def = actualNoAcEst

$ grep -n 'c56_carbon_stock_pricing <-' config/default.cfg
1838:c56_carbon_stock_pricing <- "actualNoAcEst"   # def = actualNoAcEst

$ rg -n "c56_carbon_stock_pricing" .          # whole-repo: no script consumes the bare name
  ./config/default.cfg:1838 | ./CHANGELOG.md:891 | 4 hits inside modules/56_ghg_policy/price_aug22/
```

**confirmed**: true

**proposed_fix**: `config/default.cfg:1835` → `config/default.cfg:1838` in the §2.3 warning. Consider appending "(line number verified against develop `2c02843ec`)" since this pointer is inherently drift-prone.

---

### B3 — MAJOR — §6.3 age-class labels are ordinal indices, but the `ac` set is labelled by YEARS

**doc_line**: `carbon_balance_conservation.md:493` (table rows `:493-499`)

**Claim in doc** (§6.3 "Growth Trajectories", Age Class column):
> `| 5 | ac1 | … |`, `| 10 | ac2 | … |`, `| 20 | ac4 | … |`, `| 30 | ac6 | … |`, `| 50 | ac10 | … |`, `| 80 | ac16 | … |`, `| 100 | ac20 | … |`

**Reality in code**: `core/sets.gms:269-275` defines
`ac / ac0, ac5, ac10, ac15, ac20, ac25, …, ac300, acx /` — **62 members, labelled by years in 5-year steps**.

Consequences:
- `ac1`, `ac2`, `ac4`, `ac6`, `ac16` **do not exist** in the set.
- `ac10` and `ac20` **do exist**, but denote **10 years and 20 years** — not the 50 and 100 years the table assigns them. This is the dangerous half: a reader indexing `pm_carbon_density_plantation_ac(t,j,"ac10","vegc")` for a 50-year-old stand silently gets a 10-year-old one (5× age error, no GAMS error raised).

The doc's own §3.5 (`:224`) gets this right — *"ac0 → ac5 → ac10 → … → acx"* — so the file is internally inconsistent. The confusion is that `m_growth_vegc`'s last argument in `start.gms:17/28/48` is `(ord(ac)-1)`, an **ordinal**, which the §6.3 table has mistaken for the set label.

**Severity via decision tree**: no Critical trigger matches literally (the fabricated names are set members, not `vm_*`/`pm_*` identifiers or equations); Major triggers *"right concept, wrong number"* and *"fabricated count for a set … list"* both fire → **Major**. (Related immutable anchor: R16, `ac140/acx` vs `ac300` → Critical for set *extent*; this is set *labelling*, one tier down.)

**file_evidence**: `core/sets.gms:269-275`; `modules/52_carbon/normal_dec17/start.gms:17` (`…,(ord(ac)-1))`).

**verify_cmd**:
```
$ awk 'NR>=269 && NR<=275' core/sets.gms
  ac Age classes  / ac0,ac5,ac10,ac15,ac20,ac25,ac30,…,ac295, ac300, acx /
```

**confirmed**: true

**proposed_fix**: Rewrite the Age Class column as `ac0, ac5, ac10, ac20, ac30, ac50, ac80, ac100, acx` (label = age in years), and add a one-line note: *"Set labels are years (`ac0…ac300, acx`, `core/sets.gms:269-275`); the `ac` argument inside `m_growth_vegc` is the ordinal `ord(ac)-1`, which the macro multiplies by 5 to recover years."*

---

### B4 — MINOR — §9.3 R snippet multiplies year-labelled age classes by 5

**doc_line**: `carbon_balance_conservation.md:823`

**Claim in doc**:
```r
ages <- as.numeric(gsub("ac", "", getNames(vegc_by_age))) * 5
```

**Reality in code**: the GDX labels are the GAMS set labels `ac0, ac5, ac10, …` (`core/sets.gms:269-275`), i.e. **already years**. `gsub("ac","", "ac50")` → `50`; `* 5` → **250 years**. The x-axis of the plotted growth curve would be 5× too long for every point except `ac0`.

Same root misconception as B3 but a distinct, *runnable* artifact with a distinct fix, so recorded separately.

**file_evidence**: `core/sets.gms:269-275`

**verify_cmd**: `awk 'NR>=269 && NR<=275' core/sets.gms` → labels are `ac0,ac5,ac10,…` (years, 5-year steps).

**confirmed**: true

**proposed_fix**: drop the `* 5`:
`ages <- as.numeric(gsub("ac", "", getNames(vegc_by_age)))  # labels are already years; drop acx first`

---

### B5 — MINOR — §8.4 uses the legacy fraction (44%) where the convergence fraction (56%) belongs

**doc_line**: `carbon_balance_conservation.md:734`

**Claim in doc**:
> "- Year 5: 44% toward new equilibrium = +4 tC/ha"

**Reality in code**: `i59_lossrate(t) = 1-0.85**m_yeardiff(t)` (`modules/59_som/cellpool_jan23/preloop.gms:45`) gives **1 − 0.85⁵ = 0.556**, i.e. **56%** toward equilibrium, 44% legacy. The doc's own §5.2 table (`:401`) and §5.2 interpretation (`:412`) both say 56/44 correctly; §8.4 inverts them. The following rows are consistent with the code (Year 10 → 80%, Year 20 → 96%), so this row is the outlier. Downstream number: 9 tC/ha × 0.556 = **+5.0 tC/ha**, not +4.

Likely inherited from the erroneous code comment at `modules/59_som/cellpool_jan23/preloop.gms:42` ("44% in 5 years") — which is itself wrong; see the CORRECT-list note above.

**file_evidence**: `modules/59_som/cellpool_jan23/preloop.gms:45`

**verify_cmd**: `python3 -c "print((1-0.85**5)*100)"` → `55.62…` (and 10 yr → 80.3, 20 yr → 96.1, matching §5.2).

**confirmed**: true

**proposed_fix**: `- Year 5: 56% toward new equilibrium = +5.0 tC/ha`

---

### B6 — MINOR — §8.1 gradual-soil-emission arithmetic is wrong (458 vs 550)

**doc_line**: `carbon_balance_conservation.md:656`

**Claim in doc**:
> "- Gradual (soilc over 20 years): 30 tC/ha × 100 Mha × (44/12) / 20 years = **458 Tg CO₂/year**"

**Reality**: 30 tC/ha × 100 Mha = 3,000 Tg C; × 44/12 = 11,000 Tg CO₂; ÷ 20 = **550 Tg CO₂/yr**. The stated 458 corresponds to 25 tC/ha, but the table immediately above (`:649`) gives the soilc loss as 30 tC/ha (80 → 50). The sibling calculation on `:655` (56,833 Tg CO₂ from 155 tC/ha) is arithmetically correct, so this is an isolated slip, not a convention difference.

Labelled "made-up numbers for illustration", but the *arithmetic* is checkable and wrong given the doc's own inputs — a reader reconciling it would waste time hunting for a hidden factor.

**file_evidence**: n/a (pure arithmetic on doc-internal numbers; the 44/12 conversion and the mio.tC = Tg C identity are both confirmed against `modules/56_ghg_policy/price_aug22/declarations.gms:34,40`).

**verify_cmd**: `python3 -c "print(30*100*44/12/20)"` → `550.0` (control: `python3 -c "print(155*100*44/12)"` → `56833.3`, matching the doc's other figure).

**confirmed**: true

**proposed_fix**: `… / 20 years = **550 Tg CO₂/year**`

---

### B7 — MINOR — §6.3 vegc trajectory does not follow from its own stated A, k, m

**doc_line**: `carbon_balance_conservation.md:487` (parameters at `:487-488`, table values at `:493-499`)

**Claim in doc**: with `A = 100 tC/ha, k = 0.06, m = 2.0`, the table gives vegc = 14 / 26 / 44 / 58 / 75 / 88 / 93 at 5 / 10 / 20 / 30 / 50 / 80 / 100 years.

**Reality**: `m_growth_vegc` (`core/macros.gms:18`) is `S + (A-S)*(1-exp(-k*(ac*5)))**m`. With S=0, A=100, k=0.06, m=2 the values are **6.7 / 20.4 / 48.8 / 69.7 / 90.3 / 98.4 / 99.5**. The tabulated series instead fits roughly `k ≈ 0.03, m = 1`. The formula quoted in §6.1 is itself correct — it is the table that does not follow from it. The 20-year value (44) is reused in §8.2 (`:676`), so the mismatch propagates.

**file_evidence**: `core/macros.gms:18`

**verify_cmd**:
```
$ python3 -c "import math;[print(t, round(100*(1-math.exp(-0.06*t))**2,1)) for t in (5,10,20,30,50,80,100)]"
  5 6.7 | 10 20.4 | 20 48.8 | 30 69.7 | 50 90.3 | 80 98.4 | 100 99.5
```

**confirmed**: true

**proposed_fix**: either recompute the table from A=100, k=0.06, m=2.0 (and update the dependent §8.2 vegc figures), or restate the parameters as `k ≈ 0.03, m = 1.0` to match the existing series. Recomputing is preferable — an m=2 sigmoid is the shape the section is trying to illustrate.

---

### B8 — MINOR — References line-range no longer spans the Module-52 growth code

**doc_line**: `carbon_balance_conservation.md:987`

**Claim in doc**:
> "- Module 52 growth: `modules/52_carbon/normal_dec17/start.gms:8-39`"

**Reality in code**: `start.gms` is 51 lines. The growth code now spans **8-51**: the FRA-calibration commit inserted calibration-parameter initialisation at `:33-40` and the uncalibrated-curve snapshot at `:43-44`, pushing the **other-land** Chapman-Richards and litter curves down to `:46-51`. The cited `8-39` therefore (a) omits the other-land growth curves entirely and (b) now includes eight lines of calibration bookkeeping that are not growth code.

**file_evidence**: `modules/52_carbon/normal_dec17/start.gms:46-51` (other-land curves); `:33-44` (calibration init + uncalib snapshot).

**verify_cmd**:
```
$ wc -l < modules/52_carbon/normal_dec17/start.gms          → 51
$ awk 'NR>=46 && NR<=51' modules/52_carbon/normal_dec17/start.gms
  *** Other land   /  pm_carbon_density_other_ac(t_all,j,ac,"vegc") = m_growth_vegc(…)
                   /  pm_carbon_density_other_ac(t_all,j,ac,"litc") = m_growth_litc_soilc(…)
```

**confirmed**: true

**proposed_fix**: `modules/52_carbon/normal_dec17/start.gms:8-51`

---

## Deferred (unverified / judgement calls — no edit proposed)

1. **§8.2 afforestation soilc trajectory** (`:678`, `:684`): "70 tC/ha (80% toward natural)" implies natural = 75; "78 tC/ha (96% toward natural)" implies natural = 79.2 — internally inconsistent, and 96% is the *20-year* convergence figure applied at year 50 (where `1-0.85^50 ≈ 99.97%`). Explicitly illustrative with an unstated "natural" value, so not code-checkable. Flagging for an editor, not as a bug.
2. **§9.1 R consistency check** (`:756-779`): `readGDX(gdx,"pcm_carbon_stock", field="l")` applies `field="l"` to a GAMS *parameter*; and `dimSums(stock_change, dim=c("cell","land","c_pools"))` leaves the `stockType` dimension in place and never aggregates cells to regions, so the result would not be comparable to the regional `ov_emissions_reg`. I did not execute the snippet, so I record this as a lead rather than a confirmed defect.
3. **§7.2 "Receives" attributions**: `vm_land` is attributed to M10 and `vm_area` to M30. The role map shows `vm_land` populated by 10, 29, 31, 32, 34, 35 and `vm_area` by 30 and 41. Both are declared in the attributed module and M10/M30 are the primary populators, so the simplification is defensible; not filed as a bug.
4. **§2.3 "Subsoil … Static (fixed from LPJmL via M52)"**: `i59_subsoilc_density(t_all,j)` is time-indexed and derived from the time-varying `fm_carbon_density` (default `c52_carbon_scenario = "cc"`), so it is not literally static across time. The doc's operative claim — "not affected by land use" — is correct, so this is imprecision rather than error.
5. **Domain-set imprecision**: the doc writes `fm_carbon_density(t,j,land,c_pools)` and `pm_carbon_density_*_ac(t,j,ac,ag_pools)` in several places (`:107`, `:513-516`, `:699`); the declared domain is `t_all`. Harmless (t ⊂ t_all) and pervasive — Informational at most.
6. **§5.3 IPCC stock-change factor examples** (F = 0.69, F = 1.17) and **§6.2 climate-class k ranges** (0.02-0.08): the backing inputs (`f59_ch5_F_*.csv`, `f52_growth_par.csv`) are run-time artifacts absent from the repo (`modules/*/input/` contains only a `files` manifest). Could not verify; both are explicitly labelled "typical"/"illustrative".
7. **Doc header (`:5`) "Modules Covered: 52, 53, 59 (57 for mitigation costs)"** omits Module 58, which §10.2 item 7 documents at length. Informational; not filed.
8. **§10.2 item 7 peatland double-counting claim** ("avoided by construction (peat is not in `c_pools`)"): `c_pools = /vegc,litc,soilc/` confirmed, and M58 writes only `vm_emissions_reg`. The claim looks sound, but I did not audit whether any preprocessing step folds peat carbon into `fm_carbon_density` upstream — that is a preproc-agent question.

---

## Confidence notes

- All eight bugs are backed by reproducible commands whose output is quoted above.
- **B1** is the one with the highest false-positive cost, so it carries the heaviest evidence: role-map consultation, `rg` and `grep` agreeing on the same 3 hits in `modules/32_forestry/`, and a positive control proving the search works in that directory. The sink (`q32_carbon` → `vm_carbon_stock`) was read directly at `modules/32_forestry/dynamic_may24/equations.gms:108-109`.
- **B1 severity** is the one genuinely arguable call: the doc's phrasing is additive ("read the CALIBRATED curve **as well**") rather than explicitly exhaustive, which argues for Major. I land on Critical because the rubric's latent-doc-bug mandate names wrong producer/consumer sets as Critical per the immutable R20 anchor, the parameter family is literally the same one that anchor is about, and the parallel construction with the preceding (exhaustive) uncalibrated list invites an exhaustive reading in the very section about plantation carbon.
- **B3 and B4** share a root cause (ordinal vs. year labelling of `ac`) but have different locations and different fixes; fixing one does not fix the other.
- No bug in this report depends on an absence claim that was not double-confirmed with a positive control.
