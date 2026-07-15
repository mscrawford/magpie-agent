# R54 Doc Audit — `modules/module_35.md` (Natural Vegetation)

**Auditor**: Opus adversarial doc-auditor
**Date**: 2026-07-14
**Target doc**: `<magpie-agent>/modules/module_35.md` (1,199 lines)
**Ground truth**: `/tmp/magpie_develop_ro` @ `0d7ebeb90` (develop HEAD; matches the doc's "Last Verified" sync tag)
**Realization checked**: `pot_forest_may24` — the ONLY realization (`ls /tmp/magpie_develop_ro/modules/35_natveg/` → `input/`, `module.gms`, `pot_forest_may24/`) and the default (`config/default.cfg:1153` → `cfg$gms$natveg <- "pot_forest_may24"`).

**Verdict**: **MOSTLY ACCURATE (upper band)**. This is a high-quality doc. All 32 equation names and all 32 equation file:line citations are exact; the whole natural-origin (§5.1) machinery is cited line-perfect; every scalar default is correct; the Quick-Reference consumer set (doc:25) is *exactly* right against code. Nine bugs found: **1 Critical** (an inverted data-flow claim in §10.1), 2 Major, 6 Minor.

**Claims verified**: ~105 load-bearing, code-checkable claims.
**Bugs**: 9 (1 Critical, 2 Major, 6 Minor). **Deferred**: 5.

---

## 1. Advisory pre-run leads — DISPOSITION

The pre-run advisory carried two UNVERIFIED leads and instructed: default to REFUTING them.

### (A) secdforest yield-curve vs carbon-curve mismatch — STRUCTURAL HALF SETTLED; MATERIALITY NOT ADJUDICATED; **NO DOC BUG**

**Structural half (decidable by reading, and I read it):** CONFIRMED.

| Equation | Curve it reads | Provenance |
|---|---|---|
| `q35_prod_secdforest` (`modules/35_natveg/pot_forest_may24/equations.gms:144-147`) | `im_growing_stock(ct,j2,ac_sub,"secdforest")` | built in `modules/14_yields/managementcalib_aug19/presolve.gms:42-49` from **`pm_carbon_density_secdforest_ac`** = the FRA-calibrated curve |
| `q35_carbon_secdforest` (`modules/35_natveg/pot_forest_may24/equations.gms:49-51`) | `p35_carbon_density_secdforest` | built in `modules/35_natveg/pot_forest_may24/presolve.gms:248-252` = **natural-origin-share-weighted BLEND** of calibrated + uncalibrated |

So for secdforest *proper*, wood yield is priced off the purely calibrated curve while carbon is booked off an age-class-average blend. Wherever `pc35_secdforest_natural(j,ac) > 0`, the two differ. That is a fact about the code, established with citations.

**Mitigation, also read:** the natural-origin area is protected by a lower bound — `v35_secdforest.lo(j,ac_sub) = max(..., pc35_secdforest_natural(j,ac_sub))` (`presolve.gms:177` historical branch, `:179` else branch) — and `q35_hvarea_secdforest` (`equations.gms:176-179`) caps harvest at `v35_secdforest_reduction = pc35_secdforest - v35_secdforest` (`equations.gms:112-114`). Harvestable area in an age class is therefore at most the *existing/managed* portion, i.e. exactly the portion the calibrated curve describes. What the bound does **not** do is make the *carbon* booked per harvested hectare equal to the calibrated density: `q35_carbon_secdforest` multiplies total `v35_secdforest` by the **blended** (age-class-average) density, so a hectare of managed forest removed from a mixed-origin age class books the average, not its own, density.

**Materiality — NOT ADJUDICATED, by design.** Whether the residual gap matters requires the magnitude of `|calib − uncalib|` and realized natural-origin shares — neither is derivable by reading. **Layers I did NOT check** (named, per the advisory): (1) the `pcm_carbon_stock` postsolve carry-forward; (2) the M56 pricing scope (`f56_emis_policy.csv` — which pools/land types are actually priced under the default `c56_emis_policy = "reddnatveg_nosoil"`); (3) the magpie4 reporting layer. **Experiment that would settle it**: run default MAgPIE, and from `fulldata.gdx` compute per (t,j,ac) the quantity `pc35_secdforest_natural / pc35_secdforest` alongside `pm_carbon_density_secdforest_ac − pm_carbon_density_secdforest_ac_uncalib` (vegc); the product, integrated over harvested area (`ov35_hvarea_secdforest`), is the mis-booked carbon. If that is ~0 (because natural-origin share is ~0 in harvested age classes), the gap is immaterial.

**Why this produces no doc bug**: the doc asserts nothing false here. §6.6's "yield and carbon now come from the same curve" is explicitly scoped to **youngsecdf** — and for youngsecdf it is TRUE (carbon at `presolve.gms:242` and yield via `im_growing_stock_ysf` at `modules/14_yields/managementcalib_aug19/presolve.gms:64-71` both read `pm_carbon_density_secdforest_ac_uncalib`). No edit proposed. A "confirmed defect" verdict here would require mechanical evidence I do not have.

### (B) doc:305 rationale allegedly INVERTED — **UNRESOLVED; DEFERRED; NO EDIT**

The advisory reported a prior auditor's claim that replicating the M52 bisection shows the calibration RAISES `k` in 10 of 12 regions. This is a **numerical** claim. I attempted to settle it numerically and **could not**, because the required inputs are not in the repository:

```
$ ls -la /tmp/magpie_develop_ro/modules/52_carbon/input/
total 8 … only: files          <-- a manifest, no data
$ cat /tmp/magpie_develop_ro/modules/52_carbon/input/files
lpj_carbon_stocks.cs3 / f52_growth_par.csv / f52_fra_nrf_gs.cs4 / f52_fra_pla_gs.cs4 / …
$ find /tmp/magpie_develop_ro -name 'f52_fra_nrf_gs*'      -> (nothing)
$ ls -d /tmp/magpie_develop_ro/input                        -> No such file or directory
$ grep -n input /tmp/magpie_develop_ro/.gitignore           -> 11:/input/
```

The bisection at `modules/52_carbon/normal_dec17/preloop.gms:49-68` needs `f52_fra_nrf_gs(i)` (FRA target), `fm_carbon_density` (LPJmL asymptote, from `lpj_carbon_stocks.cs3`), `im_forest_ageclass` (GFAD, M28 input), `f52_growth_par` (the *uncalibrated* `k`), `fm_ipcc_bef`, `f52_volumetric_conversion`. **Every one of these is a gitignored run-time product of the R layer and is absent.** No numerical replication is possible in this environment; therefore the prior auditor's "10 of 12 regions" figure is **not reproducible here and I will not act on it** — and neither will I assert the doc is right. Marked UNRESOLVED.

What IS verifiable, and is *consistent with* (not proof of) the doc's rationale: the M52 code comment at `modules/52_carbon/normal_dec17/input.gms:47` reads verbatim *"Upper bound for secdforest k bisection - kept low because FRA NRF growing stock is below LPJmL potential in most regions"*. Note carefully: this says the FRA **target** is below the LPJmL **potential** — it does not by itself establish that `k_calib < k_uncalib`, which is the quantity in dispute. Adjudicating from that comment would be exactly the prose-adjudication the advisory forbids. **Line 305 is left untouched.** (The doc, to its credit, already carries the correct hedge at doc:516, which quotes this same comment and warns that the calibration moves `k` in both directions regionally.)

---

## 2. BUGS

### B1 — 🔴 **CRITICAL** — `vm_landexpansion` listed as an M35 **output to Module 10** (inverted data flow / wrong populator)

* **Class**: 15 (latent doc error) — wrong producer attribution; MANDATE 21 (data-flow direction)
* **Trigger**: Critical — *"the user would … edit the wrong file, build on a false foundation"*; rubric §1.5 + R20 anchor (*a wrong producer/consumer set is Critical by future-reader harm*)
* **Doc line**: `module_35.md:881`, in §10.1 **Provides To (Outputs)**
* **Claim**: `**To Module 10 (Land)**:` … `- `vm_landexpansion(j,land_natveg)` - Natural land expansion`
* **Reality in code**: `vm_landexpansion` is DECLARED in **Module 10** (`modules/10_land/landmatrix_dec18/declarations.gms:20` — `vm_landexpansion(j,land)  Land expansion (mio. ha)`) and DEFINED by Module 10's `q10_landexpansion` (`modules/10_land/landmatrix_dec18/equations.gms:30-33`):
  ```gams
   q10_landexpansion(j2,land_to) ..
          vm_landexpansion(j2,land_to) =e=
          sum(land_from$(not sameas(land_from,land_to)),
          vm_lu_transitions(j2,land_from,land_to));
  ```
  Module 35 **only READS** it — `equations.gms:197` (`q35_max_forest_establishment`, where it sits on the LHS of a `=l=` *constraint*, not a defining `=e=`) and `equations.gms:222` (`q35_other_regeneration`, an RHS input term). M35 **does not declare it** and has **no equation with it on the LHS of an `=e=`**. Direction is M10 → M35, not M35 → M10.
* **Verify cmd (with results)**:
  ```
  $ rg -n 'vm_landexpansion' /tmp/magpie_develop_ro/modules/*/*/declarations.gms
    modules/10_land/landmatrix_dec18/declarations.gms:20: vm_landexpansion(j,land)  Land expansion (mio. ha)
    modules/32_forestry/dynamic_may24/declarations.gms:74: vm_landexpansion_forestry(j,type32)   [different variable]
  $ rg -n 'vm_landexpansion' /tmp/magpie_develop_ro/modules/35_natveg/pot_forest_may24/declarations.gms
    -> NO MATCH  (M35 does not declare it)
  $ rg -n 'vm_landexpansion' /tmp/magpie_develop_ro/modules/35_natveg/
    equations.gms:197:  sum(land_forest, vm_landexpansion(j2,land_forest))     [read, =l= constraint]
    equations.gms:222:  + vm_landexpansion(j2,"other")                          [read, RHS term]
  ```
  Positive control: the same `rg` invocation *did* return M10's declaration and M39/M59 consumers, so the tool works in this tree.
* **Corroboration — the doc contradicts itself**: `module_35.md:578` (§6.7) already states the truth: *"`vm_landexpansion(j,"other")` (land expansion from **Module 10**)"*. §10.1 is the section a refactorer consults, and it is the one that is wrong. The doc also **omits** `vm_landexpansion` from §10.2 "Receives From → From Module 10" (which lists only `vm_lu_transitions`) — the same root error, twice.
* **Harm**: a user wanting to change how natural land expansion is computed would open `35_natveg` and find no definition — or worse, would "fix" `q35_other_regeneration`, which merely reads it.
* **Proposed fix** — two edits:
  1. **DELETE** line 881: `- \`vm_landexpansion(j,land_natveg)\` - Natural land expansion`
  2. **ADD** under §10.2 `**From Module 10 (Land)**:` (after line 901): `- \`vm_landexpansion(j,land)\` - Land expansion, declared and computed in Module 10 (\`modules/10_land/landmatrix_dec18/declarations.gms:20\`, \`q10_landexpansion\` at \`modules/10_land/landmatrix_dec18/equations.gms:30-33\`). M35 **reads** it in \`q35_max_forest_establishment\` (\`equations.gms:197\`) and \`q35_other_regeneration\` (\`equations.gms:222\`); M35 does not produce it.`

---

### B2 — 🟠 **MAJOR** — "4 disturbance modes" list omits mode 2 — the **default**

* **Class**: 6 (hardcoded count drift) / fabricated set count
* **Trigger**: Major — *"Fabricated count for a set/parameter/realization list"*
* **Doc line**: `module_35.md:18`
* **Claim**: `- **4 disturbance modes**: No disturbance, shifting agriculture, combined shocks, generic scenarios`
* **Reality in code**: `s35_forest_damage` spans **five** values 0–4. `modules/35_natveg/pot_forest_may24/input.gms:27` declares it with default `/ 2 /`; `presolve.gms` branches at lines **13** (`=1`), **19** (`=2`), **24** (`=3`), **30** (`=4`); `=0` fires no branch. The Quick-Reference enumeration lists four items *including* "No disturbance" and therefore **drops mode 2 — "shifting agriculture faded out" — which is the DEFAULT** (and which the doc's own §4.3 correctly labels `(DEFAULT)`).
* **Verify cmd**:
  ```
  $ rg -n 's35_forest_damage=' modules/35_natveg/pot_forest_may24/presolve.gms
    13:if(s35_forest_damage=1,   19:if(s35_forest_damage=2,   24:if(s35_forest_damage=3,   30:if(s35_forest_damage=4,
  $ awk 'NR==27' modules/35_natveg/pot_forest_may24/input.gms
    s35_forest_damage Damage simulation in forests (0=none 1=shifting agriculture 2= Damage from shifting
    agriculture is faded out by c35_forest_damage_end 4= f35_forest_shock scenario) / 2 /
  ```
* **Note**: line 62 ("Implements 4 disturbance modes") is *defensible* under the reading "4 modes in which disturbance occurs (1–4)" and is **left alone**. Only line 18, whose enumeration includes "No disturbance" and thus must total five, is wrong.
* **Proposed fix**: replace line 18 with:
  `- **5 disturbance modes** (\`s35_forest_damage\` = 0-4): 0 none, 1 shifting agriculture, 2 shifting agriculture faded out (**DEFAULT**), 3 combined (shifting agriculture + wildfire), 4 generic shock scenarios`

---

### B3 — 🟠 **MAJOR** — "age-classes 1-15" contradicts the 62-member `ac` set

* **Class**: 6 (hardcoded count drift) / fabricated set count
* **Trigger**: Major — *"Fabricated count for a set"*. (`tier_uncertainty`: the R16 immutable anchor rates this same error class **Critical** when it appears in an answer — "agent claimed age classes go to `ac140, acx`; actual set extends to `ac300` (62 elements) → Critical". I take the lower tier per the §1 tie-breaker because the correct count is stated prominently and correctly in §3 of this same doc.)
* **Doc line**: `module_35.md:925` (§10.1 "Participates In → Land Balance")
* **Claim**: `Three land types: primary forest, secondary forest (age-classes 1-15), other land (grassland, shrubland, etc.)`
* **Reality in code**: `ac` has **62** members — `ac0, ac5, …, ac295, ac300, acx` — `core/sets.gms:269-275`.
* **Verify cmd**:
  ```
  $ python3 -c "…regex-extract the 'ac Age classes' set literal from core/sets.gms; count members…"
    ac member count: 62      first: ['ac0','ac5','ac10']   last: ['ac295','ac300','acx']
  $ awk 'NR>=269 && NR<=275' /tmp/magpie_develop_ro/core/sets.gms   -> the ac set literal, exactly
  ```
* **Corroboration**: `module_35.md:134` already says "(62 age classes; `acx` is the mature/absorbing class, >300 years). Defined in `core/sets.gms:269-275`." — verified exact. Line 925 contradicts it.
* **Proposed fix**: replace `secondary forest (age-classes 1-15)` with `secondary forest (62 age classes: ac0, ac5, …, ac300, acx — see §3)`

---

### B4 — 🟡 **MINOR** — non-default M29 realization cited for the `vm_lu_transitions` consumer

* **Class**: 8 / stale-realization citation
* **Trigger**: Minor — *"Stale package/realization citation that's recoverable (correct concept, findable in a different location)"*. (`tier_uncertainty`: Minor/Major. Every literal element of the claim is TRUE — M29 *is* a consumer and `simple_apr24/equations.gms:49` *does* contain the reference — so no Major trigger fires cleanly on the top-down walk. But AGENT.md Step 1c requires leading with the default realization.)
* **Doc line**: `module_35.md:411`
* **Claim**: `` `vm_lu_transitions` (land use transitions from Module 10; also consumed by Module 29 `modules/29_cropland/simple_apr24/equations.gms:49`, Module 59 `modules/59_som/cellpool_jan23/equations.gms:51`) ``
* **Reality in code**: the **default** cropland realization is `detail_apr24` (`config/default.cfg:811` → `cfg$gms$cropland <- "detail_apr24"`), which consumes `vm_lu_transitions` at `modules/29_cropland/detail_apr24/equations.gms:60`. `simple_apr24` is the non-default alternative — not compiled in a default run. (The M59 citation is fine: `cellpool_jan23` **is** the default, `config/default.cfg:1934`; it also uses the variable a second time at `cellpool_jan23/equations.gms:73`.)
* **Verify cmd**:
  ```
  $ rg -n 'vm_lu_transitions\(' /tmp/magpie_develop_ro/modules/
    29_cropland/detail_apr24/equations.gms:60      <-- DEFAULT realization
    29_cropland/simple_apr24/equations.gms:49      <-- the one the doc cites (non-default)
    59_som/cellpool_jan23/equations.gms:51 and :73
    10_land/landmatrix_dec18/declarations.gms:23   <-- declaration (M10) ✓ doc correct
  $ grep -n 'cfg$gms$cropland' /tmp/magpie_develop_ro/config/default.cfg
    811:cfg$gms$cropland    <- "detail_apr24"               # def = detail_apr24
  ```
* **Proposed fix**: replace `Module 29 \`modules/29_cropland/simple_apr24/equations.gms:49\`` with `Module 29 (default realization: \`modules/29_cropland/detail_apr24/equations.gms:60\`; also \`simple_apr24/equations.gms:49\`)` and `Module 59 \`modules/59_som/cellpool_jan23/equations.gms:51\`` with `Module 59 \`modules/59_som/cellpool_jan23/equations.gms:51\` and \`:73\``.

---

### B5 — 🟡 **MINOR** — `pm_carbon_density_secdforest_ac` consumer list omits Module 35 itself

* **Class**: 15 (latent doc error — incomplete consumer set)
* **Trigger**: Minor (an incomplete consumer set, but the omitted consumer is the module the doc is *about*, and its use is documented in full detail at §5.1/§6.3)
* **Doc line**: `module_35.md:126`
* **Claim**: `` - `pm_carbon_density_secdforest_ac` is consumed by Module 14 (`modules/14_yields/managementcalib_aug19/presolve.gms:44`) ``
* **Reality in code**: the complete consumer set is **Module 14** (`modules/14_yields/managementcalib_aug19/presolve.gms:44`) **and Module 35 itself** (`modules/35_natveg/pot_forest_may24/presolve.gms:248`, `:250`, `:251` — the FRA-calibrated leg of the blend). Declared/populated in M52 (`modules/52_carbon/normal_dec17/declarations.gms:9`; `start.gms:28,31`; overwritten by the calibration at `preloop.gms:71`). The sibling bullet at doc:127 (for the `_uncalib` twin) *does* say "and Module 35 itself" — the asymmetry is the defect.
* **Verify cmd**:
  ```
  $ rg -n 'pm_carbon_density_secdforest_ac[^_]' /tmp/magpie_develop_ro/modules/ /tmp/magpie_develop_ro/core/
    14_yields/managementcalib_aug19/presolve.gms:44
    35_natveg/pot_forest_may24/presolve.gms:248, :250, :251
    52_carbon/normal_dec17/start.gms:28, :31, :43 ; preloop.gms:71 ; declarations.gms:9
  ```
* **Proposed fix**: append to line 126: `, and by Module 35 itself (\`presolve.gms:248-251\` — the FRA-calibrated leg of the blended \`p35_carbon_density_secdforest\`)`

---

### B6 — 🟡 **MINOR** — `+=` is not GAMS (pseudo-code inside a ```gams fence)

* **Class**: 4 (conceptual pseudo-code presented as code)
* **Trigger**: Minor
* **Doc line**: `module_35.md:289` (§5 Step 4)
* **Claim**:
  ```gams
  pc35_land_other(j,"youngsecdf",ac_est) += p35_forest_recovery_area(t,j,ac_est);
  ```
* **Reality in code**: GAMS has **no compound-assignment operator**. `modules/35_natveg/pot_forest_may24/presolve.gms:77-78` reads (othernat *first*, then youngsecdf):
  ```gams
  pc35_land_other(j,"othernat",ac_est) = pc35_land_other(j,"othernat",ac_est) - p35_forest_recovery_area(t,j,ac_est);
  pc35_land_other(j,"youngsecdf",ac_est) = pc35_land_other(j,"youngsecdf",ac_est) + p35_forest_recovery_area(t,j,ac_est);
  ```
* **Verify cmd**: `awk 'NR>=77 && NR<=78' modules/35_natveg/pot_forest_may24/presolve.gms` → exactly the two lines above.
* **Proposed fix**: replace the Step-4 block body with the verbatim two lines from `presolve.gms:77-78` (keeping the explanatory comments as `*`-comments), i.e. `pc35_land_other(j,"youngsecdf",ac_est) = pc35_land_other(j,"youngsecdf",ac_est) + p35_forest_recovery_area(t,j,ac_est);`

---

### B7 — 🟡 **MINOR** — §14 says "8 files"; the realization has **9** `.gms` files

* **Class**: 6 (hardcoded count drift)
* **Trigger**: Minor
* **Doc line**: `module_35.md:1147`
* **Claim**: `**Complexity**: VERY HIGH (1,165 lines, 32 equations, 8 files)`
* **Reality in code**: **9** `.gms` files — declarations, equations, input, postsolve, preloop, presolve, realization, scaling, sets — totalling 1,165 lines. The doc's own header (line 5) correctly says "1,165 lines across 9 files".
* **Verify cmd**:
  ```
  $ ls -1 /tmp/magpie_develop_ro/modules/35_natveg/pot_forest_may24/*.gms | wc -l   -> 9
  $ wc -l  …/*.gms   -> 143+233+66+210+107+294+47+35+30 = 1165 total  (all 9 sizes match the doc header exactly)
  ```
* **Proposed fix**: `**Complexity**: VERY HIGH (1,165 lines, 32 equations, 9 files)`

---

### B8 — 🟡 **MINOR** — §12.6 presents the satellite/GFAD age-class initialization as unavailable, but it **is the default**

* **Class**: 5 / stale-source citation (the doc faithfully repeats a **stale upstream code comment**)
* **Trigger**: Minor — *"Stale … citation that's recoverable"*. (`tier_uncertainty`: Minor/Major. No Major trigger fires cleanly on the top-down walk: the doc's citation is accurate — `realization.gms:30-34` really does say this — and the doc's second bullet and §9.3 both name the correct default. But bullet 1, listed under "**VERIFIED** Limitations", is false against the default config.)
* **Doc line**: `module_35.md:1092` (§12 item 6)
* **Claim**: `6. **Age-class initialization** (\`realization.gms:30-34\`): ❌ MODIS data available but causes negative LUC emissions / ❌ Current default: Poulter distribution or equal/acx only`
* **Reality in code**: `s35_secdf_distribution` **defaults to 2** (`modules/35_natveg/pot_forest_may24/input.gms:26`, `… 2=Poulter distribution from MODIS satellite data) (1) / 2 /`), and mode 2 initializes secdforest age classes **from the satellite-derived GFAD distribution** — `preloop.gms:18-34`, with the comment at `:19`: *"For the initialization of age-classes in secondary forest, forest area in 5-year age-classes based on GFAD is used"*, feeding `p35_secdf_ageclass(j,ac) = im_forest_ageclass(j,ac);` (`preloop.gms:20`). The `realization.gms:30-34` `@limitations` block the doc paraphrases — *"Inclusion of this data in MAgPIE remains work in progess and is not available for release yet"* — is **stale MAgPIE-side text**, contradicted by `input.gms:26` + `preloop.gms:18-34`. A reader of §12.6 bullet 1 would conclude MAgPIE does not use the satellite age-class data; it does, by default.
* **Verify cmd**:
  ```
  $ awk 'NR==26' modules/35_natveg/pot_forest_may24/input.gms
    s35_secdf_distribution Flag for secdf initialization (0=… 1=… 2=Poulter distribution from MODIS satellite data) (1) / 2 /
  $ awk 'NR>=18 && NR<=34' modules/35_natveg/pot_forest_may24/preloop.gms
    18: elseif s35_secdf_distribution = 2,
    19: *For the initialization of age-classes in secondary forest, forest area in 5-year age-classes based on GFAD is used
    20:  p35_secdf_ageclass(j,ac) = im_forest_ageclass(j,ac);
  ```
* **Proposed fix**: replace item 6 with:
  `6. **Age-class initialization** (\`input.gms:26\`, \`preloop.gms:18-34\`): the default \`s35_secdf_distribution = 2\` initializes secdforest age classes from the satellite-derived **GFAD** distribution (\`im_forest_ageclass\`, \`preloop.gms:19-20\`). Alternatives: 0 = all area in \`acx\`; 1 = equal across all age classes. ⚠️ The \`@limitations\` block at \`realization.gms:30-34\` still says this satellite data "is not available for release yet" — **that MAgPIE comment is stale**; the code path is the default. Reality: actual age distribution is more complex than any of the three options.`

---

### B9 — 🟡 **MINOR** — the "Interface Variables → Provided to Other Modules" table omits `vm_landdiff_natveg`

* **Class**: 15 (incomplete interface/producer set)
* **Trigger**: Minor
* **Doc line**: `module_35.md:1187` (table spans 1185-1193; footer at 1193 claims "**Source**: `declarations.gms` (verified against GAMS code)")
* **Claim**: the table lists exactly `vm_land_other`, `vm_prod_natveg`, `vm_cost_hvarea_natveg`, `vm_natforest_reduction`, `pm_max_forest_est`.
* **Reality in code**: `vm_landdiff_natveg` is also declared in M35 (`modules/35_natveg/pot_forest_may24/declarations.gms:79`) and **is** consumed outside M35 — by Module 10's `q10_landdiff` (`modules/10_land/landmatrix_dec18/equations.gms:53`). It belongs in a table whose stated source is `declarations.gms`. (The Quick Reference at doc:25 and §10.1 at doc:880 both list it correctly — only this table drops it.)
* **Verify cmd**:
  ```
  $ rg -n 'vm_landdiff_natveg' /tmp/magpie_develop_ro/modules/ | grep -v 35_natveg
    10_land/landmatrix_dec18/equations.gms:53:   + vm_landdiff_natveg
  $ awk 'NR==79' modules/35_natveg/pot_forest_may24/declarations.gms
    vm_landdiff_natveg   Aggregated difference in natveg land compared to previous timestep (mio. ha)
  ```
* **Proposed fix**: add a table row: `| \`vm_landdiff_natveg\` | (scalar) | Aggregated difference in natveg land compared to previous timestep | mio. ha |`

---

## 3. VERIFIED-CORRECT (highlights — the doc is strong here)

**Consumer/producer sets — the highest-risk surface — are EXACTLY right:**

* **doc:25** *"Provides to: Modules 10, 11, 32, 59 (SOM — only in the non-default `static_jan19` realization, via `vm_land_other`; the default `cellpool_jan23` consumes no M35 interface variable), 73 … Modules 22, 28, 52, 56 do NOT directly consume any M35 interface variable"* — **CONFIRMED, exactly**, by per-variable greps in BOTH `NAME(` and `NAME.` forms, each run standalone, with a positive control:
  | M35-declared interface | Consumer(s) outside M35 |
  |---|---|
  | `vm_land_other` (decl:78) | **M59 `static_jan19`/equations.gms:23-24 ONLY** (non-default; default `som` = `cellpool_jan23`, `config/default.cfg:1934`) |
  | `vm_landdiff_natveg` (decl:79) | M10 `landmatrix_dec18`/equations.gms:53 |
  | `vm_prod_natveg` (decl:88) | M73 `default`/equations.gms:27,48,57,79 |
  | `vm_cost_hvarea_natveg` (decl:89) | M11 `default`/equations.gms:35 |
  | `vm_natforest_reduction` (decl:90) | M32 `dynamic_may24`/equations.gms:80 |
  | `pm_max_forest_est` (decl:27) | M32 `dynamic_may24`/equations.gms:86, presolve.gms:22-23 |
  | `v35_*` | **none** — module-internal (grep outside M35: zero hits; positive control: 34 hits inside M35's equations.gms) |
  Union = {10, 11, 32, 59(non-default), 73}. No phantoms, no omissions. M22/M28/M52/M56 confirmed absent.

* **doc:127** — the `pm_carbon_density_secdforest_ac_uncalib` consumer list is **exact and complete**: M14 `presolve.gms:66`; M29 `detail_apr24/preloop.gms:46` (**the default realization** ✓); M32 `dynamic_may24/presolve.gms:59` and `:68`; M35 `presolve.gms:117`, `:242`; declared M52 `declarations.gms:10`, snapshotted `start.gms:43`. Every line number hits. (`29_cropland/simple_apr24/not_used.txt:6` explicitly declares it "not needed" — consistent.)

* **doc:914** — *"`im_growing_stock_ysf` … Read **only** by the `youngsecdf` term of `q35_prod_other` (`equations.gms:166`). M35 is its sole consumer in the model."* — **CONFIRMED, exactly**. Repo-wide grep: declared `modules/14_yields/managementcalib_aug19/declarations.gms:18`; populated `presolve.gms:64`; clamped `:80` (positivity) and `:81` (`s14_minimum_growing_stock`); **single** read site = `modules/35_natveg/pot_forest_may24/equations.gms:166`.

* **doc:663** — `vm_natforest_reduction` → M32 `q32_ndc_aff_limit` at `modules/32_forestry/dynamic_may24/equations.gms:80` — **exact**, equation header at `:79`, body `sum(ct, p32_aff_pol_timestep(ct,j2)) * vm_natforest_reduction(j2) =e= 0;`.

**Equations**: all **32** equation names in `declarations.gms:42-73` match `equations.gms`; the doc's count of 32 is right; **all 32 file:line citations verified exact in current develop** (q35_land_secdforest:11, q35_land_other:13, q35_natveg_conservation:19-22, q35_secdforest_restoration:24-28, q35_other_restoration:30-33, q35_carbon_primforest:42-44, q35_carbon_secdforest:49-51, q35_carbon_other:53-55, q35_bv_primforest:59-61, q35_bv_secdforest:63-66, q35_bv_other:68-71, q35_min_forest:78-80, q35_min_other:82, q35_natforest_reduction:84-85, q35_landdiff:92-98, q35_other_expansion:100-102, q35_other_reduction:104-106, q35_secdforest_expansion:108-110, q35_secdforest_reduction:112-114, q35_primforest_reduction:116-118, q35_cost_hvarea:132-138, q35_prod_secdforest:144-147, q35_prod_primforest:153-156, q35_prod_other:162-168, q35_hvarea_secdforest:176-179, q35_hvarea_primforest:181-184, q35_hvarea_other:186-189, q35_max_forest_establishment:196-201, q35_secdforest_regeneration:208-214, q35_other_regeneration:218-223, q35_secdforest_est:228-229, q35_other_est:231-232). Equation *bodies* quoted in the doc are verbatim.

**Defaults — all correct** (`input.gms` + `config/default.cfg`): `s35_forest_damage=2` (:27), `s35_forest_damage_end=2050` (:28), `s35_hvarea=2` (:18), `s35_natveg_harvest_shr=1` (:25), `s35_secdf_distribution=2` (:26), `s35_npi_ndc_reversal=Inf` (:29), `c35_ad_policy="npi"` (:8; also `config/default.cfg:1159`), `c35_pot_forest_scenario="cc"` (:12, with `nocc`→y1995 at :64 and `nocc_hist`→`sm_fix_cc` at :65 — both semantics correct). Harvest costs `2460 / 3075 / 3690 USD17MER/ha` (input.gms:22-24) — exact, and the primforest > other > secdforest ordering in the doc is right. `s52_growingstock_calib = 1` by default (`modules/52_carbon/normal_dec17/input.gms:46`) — correct.

**§5.1 natural-origin machinery — line-perfect**: `declarations.gms:16,17,29`; `preloop.gms:49-50`; `presolve.gms:42-45` (disturbance), `:99-102` (age shift), `:116-122` (maturation), `:127-128` (clamp), `:175-180` (protection bound, both `t_past` and else branches), `:241-242` (youngsecdf density), `:248-252` (blend); `postsolve.gms:11-16`, `:14-16`. The blend formula is quoted verbatim. The parenthetical *"the `1e-12` threshold in commit `c7731e234` was raised to `1e-6` by refactor `2fa7b8bea`"* — **git-verified**: `c7731e234` introduced `> 1e-12`; `2fa7b8bea` changed it to `> 1e-6`.

**Commits**: `6b00f9dea` (2026-07-01, "Fix youngsecdf wood production: use uncalibrated growing stock"), `c7731e234` (2026-04-20, "Natural-origin tracking for secondary forest carbon density"), `2fa7b8bea` (2026-04-28, "refactor based on review comments") — all exist; the commit-message quote at doc:514 is **verbatim**; the "Ungated; result-changing …" characterization matches the commit body.

**§6.6 hedge (doc:516) is exemplary** and I want it preserved: it correctly warns that the FRA calibration moves `k` **both** directions regionally, quotes `modules/52_carbon/normal_dec17/input.gms:47` accurately ("in most regions", not all), correctly cites the bisection at `modules/52_carbon/normal_dec17/preloop.gms:23-73`, and correctly names the `s14_minimum_growing_stock` zero-clamp — which does exist and **does** apply to `im_growing_stock_ysf` (`modules/14_yields/managementcalib_aug19/presolve.gms:81`; scalar `= 5` tDM/ha at `input.gms:19`). It explicitly declines to predict regional direction without a GDX. That is the right epistemic posture and it is code-accurate.

**Sets**: `othertype35 / othernat, youngsecdf /` (sets.gms:23-24) ✓; `combined_loss / shifting_agriculture, wildfire /` (sets.gms:14-15) ✓; `shock_scen / none, 002lin2030, 004lin2030, 008lin2030, 016lin2030 /` (sets.gms:26-28) ✓ — all five members exact; `pol35 / none, npi, ndc /` ✓; `ac` = 62 members (core/sets.gms:269-275) ✓; `youngsecdf` correctly noted as **not** a member of `land_timber` (core/sets.gms:255-256: `/ forestry, primforest, secdforest, other /`) ✓.

**Other exact citations**: `module.gms:10-15` (core purpose) ✓; `realization.gms:35-36` (one-way primforest→secdforest; harvested secdforest stays secdforest) ✓; `realization.gms:17-23` (NPI/NDC ramp to 2030) ✓; `preloop.gms:70-71` — **both** `p35_min_forest` and `p35_min_other` really do use `%c35_ad_policy%` (I specifically hypothesized `%c35_aolc_policy%` for the latter and the code **refuted** me) ✓; `presolve.gms:13-16 / 18-22 / 24-27 / 29-33 / 35-39 / 84-97 / 87-90 / 155-160 / 258-260 / 262-266 / 268-272 / 274-282` ✓; `preloop.gms:88` (sigmoid fader, `sm_fix_SSP2` → `s35_forest_damage_end`) ✓; `modules/14_yields/managementcalib_aug19/presolve.gms:51-58` and `:64-71` (the two distinct M14 parameters) ✓.

**Below the noise floor, NOT filed as bugs** (recorded for completeness): (a) doc:813 cites `presolve.gms:172-180` but the quoted comment "`* Secondary forest conservation`" is at line **171** — a one-line range-start drift on a comment; the substantive code (`:173`, `:176-180`) is inside the cited range. (b) doc:914/:127 date `im_growing_stock_ysf` as "added 2026-07-14" (the doc-sync date) whereas commit `6b00f9dea` is dated 2026-07-01 — the doc gives the unambiguous SHA, and this is the doc's changelog-date convention throughout. (c) §10.1 writes `vm_bv(j,land_natveg,potnatveg)` / `vm_carbon_stock(j,land_natveg,…)` where the declared domains are `landcover44` / `land` — this is the doc's consistent *slice* shorthand for "the natveg members M35 populates", which is accurate in substance.

---

## 4. DEFERRED (not verifiable here → **no edits proposed**)

1. **Advisory (B) — M52 bisection direction (doc:305 rationale)**: UNRESOLVED. The calibration inputs (`f52_fra_nrf_gs.cs4`, `f52_growth_par.csv`, `lpj_carbon_stocks.cs3`, `im_forest_ageclass`) are gitignored R-layer products, absent from the worktree (`modules/52_carbon/input/` holds only a `files` manifest; no root `input/`). No numerical replication is possible; the prior auditor's "10 of 12 regions" figure is **not reproducible here** and I did not act on it in either direction. Doc line 305 left untouched.
2. **Advisory (A) — materiality of the secdforest yield-vs-carbon curve gap**: structural half settled above with citations; materiality NOT decidable by reading. Unread layers named: `pcm_carbon_stock` postsolve carry-forward; M56 pricing scope (`f56_emis_policy.csv` under default `c56_emis_policy="reddnatveg_nosoil"`); magpie4 reporting. Settling experiment stated in §1(A). No doc bug — the doc asserts nothing false.
3. **Centrality/graph metrics** (doc:941-947: "Rank 10 of 46", "Total Connections: 12 (provides to 5, depends on 7)", "3+ circular cycles"; doc:1153 "Dependencies: VERY HIGH (8 modules)"): derived from `Module_Dependencies.md`, not from code; the metric's definition is not pinned. Noted only: doc:945 lists **seven** provides-to targets while doc:942 says "provides to 5" — an internal inconsistency I cannot adjudicate without the metric definition.
4. **`c35_aolc_policy`** (`input.gms:9`, `config/default.cfg:1165`, default `"npi"`): has **no GAMS consumer** — `preloop.gms:70-71` uses `%c35_ad_policy%` for *both* `p35_min_forest` and `p35_min_other`. Applying the R53 discipline (search beyond `modules/*.gms` before calling anything dead), I found it **is** live in the R layer at `scripts/start_functions.R:387` (an input-data validation guard). So it is a real, live config switch that the doc's §9 "Configuration Options" does not list. Since the doc never *claims* anything false about it and never claims its switch list is exhaustive, this is a **gap, not an error** — reported, not filed, and not edited.
5. **Doc:929-933 conservation-law participation blurbs** ("Water: INDIRECT", "Nitrogen: INDIRECT", "Carbon: LARGEST carbon stocks") — qualitative/quantitative assertions not settleable from the GAMS source alone (the "largest pool" claim needs a GDX). Not edited.

---

## 5. Score

`raw_severity_weighted = 4·1 + 2·2 + 1·6 = 14` → `score_0_10 = max(0, 10 − 14) = 0` under the strict per-question formula — but that formula is calibrated for a single Q&A answer, not a 1,199-line document. As a **document**, weighting by claim density (9 bugs / ~105 load-bearing claims ≈ 91.4% confirmed, with the one Critical confined to a single bullet in an interface summary that the doc itself contradicts correctly elsewhere), the verdict is **MOSTLY ACCURATE (upper band)**. The equation layer, the citation layer, the defaults layer, and — most importantly — the consumer/producer-set layer are in excellent shape. The Critical is a single inverted arrow, and it is mechanically fixable.
