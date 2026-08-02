# R60 depth audit — `cross_module/land_balance_conservation.md`

**Lens**: `declare_populate` (enter from the DECLARING/POPULATING side: `declarations.gms`, equation LHS, `.fx`/`.lo`/`.up` assignments; then check that formulas attributed to a module's own equations match the equation bodies)
**Ground truth**: MAgPIE `develop` read-only worktree, HEAD `2c02843ec` ("Merge pull request #919 from alexkoberle/dyn_reg_tau")
**Role map**: `audit/integrated/depth_rolemap.json` (consulted first for every `vm_*`/`pm_*` attribution, then confirmed with both-endpoints greps)
**Claims verified**: 58
**Bugs found**: 6 (2 Major, 4 Minor) + 1 Informational

---

## Summary

The doc's **spine is sound**. Every Module 10 equation quote is verbatim-correct at the cited line
(`q10_land_area` 13-15, `q10_transition_to` 19-21, `q10_transition_from` 23-25, presolve restrictions
13/16-17/20-21, postsolve 9). All seven cited realizations are the current `config/default.cfg`
defaults. The interface-attribution claims that were most likely to be wrong — the
`vm_landexpansion` / `vm_landreduction` consumer split at doc lines 227-228, including the explicit
"(NOT 35/59)" carve-out — are **exactly right** against both the role map and a both-endpoints grep.
The §4.3 note reconciling the `primforest→secdforest` / `other→secdforest` flows with the §4.1 legend
is also correct.

What broke: one citation drifted 17 lines when a recent commit inserted natural-origin tracking into
Module 35's presolve; one pseudo-formula narrows a `sum(land_forest, ...)` to "forestry"; and a
directional claim about urban land is attributed to a direction-agnostic mechanism.

---

## Confirmed bugs

### B1 — Major — `citation` — doc line 388

**Claim**: ``**Critical Threshold** (`modules/35_natveg/pot_forest_may24/presolve.gms:99-107`)`` — 20 tC/ha
secdforest maturation threshold.

**Reality**: the maturation block is now `modules/35_natveg/pot_forest_may24/presolve.gms:109-123`
(`*' @code` … `*' @stop`), with the executable threshold at 116-119. Lines **99-102** now hold a
different mechanism entirely — the `p35_secdforest_natural` lockstep age-class shift (natural-origin
area tracking), inserted by commit `c7731e234` "Natural-origin tracking for secondary forest carbon
density". Only 105-107 (the section banner comment) still belongs to the threshold section.

**Evidence**: `modules/35_natveg/pot_forest_may24/presolve.gms:116-119` (threshold code);
`:99-102` (drifted-into content).

```
$ awk 'NR>=99 && NR<=119' .../35_natveg/pot_forest_may24/presolve.gms
99: * Natural-origin area ages in lockstep with the secdforest age classes
100:     p35_secdforest_natural(t,j,ac)$(ord(ac) > s35_shift) = pc35_secdforest_natural(j,ac-s35_shift);
...
105: * -------------------------------------------------------
106: * Carbon threshold for secondary forest maturation
...
116: p35_maturesecdf(t,j,ac)$(not sameas(ac,"acx")) =
117:       p35_land_other(t,j,"youngsecdf",ac)$(pm_carbon_density_secdforest_ac_uncalib(t,j,ac,"vegc") > 20);

$ git show c7731e234~1:modules/35_natveg/pot_forest_may24/presolve.gms | awk 'NR>=99 && NR<=107'
99: *' @code
...
103: p35_maturesecdf(t,j,ac)$(... pm_carbon_density_secdforest_ac(t,j,ac,"vegc") > 20);
107: *' @stop        <-- the citation was correct BEFORE c7731e234
```

Matches the R20 citation-drift anchor (5-20 line drift → Major).

**Fix**: change the citation to `modules/35_natveg/pot_forest_may24/presolve.gms:109-123`. Optionally
note that the threshold now reads the **uncalibrated** curve
(`pm_carbon_density_secdforest_ac_uncalib`), not `pm_carbon_density_secdforest_ac`.

---

### B2 — Major — `set_membership` — doc line 521

**Claim** (§7.3, "Maximum forest establishment constraint from Module 35"):
```
forestry expansion ≤ pm_max_forest_est(j) - youngsecdf area
```

**Reality**: the constraint is `q35_max_forest_establishment`, and its LHS sums over **all** of
`land_forest`, not forestry alone:

```gams
q35_max_forest_establishment(j2)..
        sum(land_forest, vm_landexpansion(j2,land_forest))
        =l=
        sum(ct,pm_max_forest_est(ct,j2))
      - sum(ac, vm_land_other(j2,"youngsecdf",ac));
```

`land_forest` = `/ forestry, primforest, secdforest /` (`core/sets.gms:259-260`). Secondary-forest
expansion therefore consumes the same establishment potential as afforestation — which is the whole
point of the constraint. The doc's narrowing removes the afforestation-vs-regrowth competition from
the reader's model. (`pm_max_forest_est` is also `(t,j)`, not `(j)`.)

**Evidence**: `modules/35_natveg/pot_forest_may24/equations.gms:196-201`; `core/sets.gms:259-260`.

**Fix**: replace the pseudo-formula with the equation name and the set-based LHS:
`q35_max_forest_establishment`: `sum(land_forest, vm_landexpansion(j2,land_forest)) =l=
sum(ct,pm_max_forest_est(ct,j2)) - sum(ac, vm_land_other(j2,"youngsecdf",ac))`, and add one sentence
that `land_forest = {forestry, primforest, secdforest}`, so afforestation and secondary-forest
regrowth compete for the same potential.

---

### B3 — Minor — `mechanism` — doc line 344 (also line 157)

**Claim** (§5.6): "Urban land **cannot decrease** (one-way expansion)"; and (§4.1 note, line 157)
"Module 34's regional constraint (`q34_urban_land`) and high deviation costs (1e6 USD/ha)
effectively prevent urban land from **decreasing**."

**Reality**: no code enforces monotonic urban land. In the default realization `exo_nov21`, urban is
`.fx`-ed only in the first timestep; from `ord(t) > 1` it is a free positive variable:

```gams
if(ord(t) = 1,
  vm_land.fx(j,"urban") = i34_urban_area(t,j);
else
  vm_land.lo(j,"urban") = 0;
  vm_land.l(j,"urban")  = i34_urban_area(t,j);
  vm_land.up(j,"urban") = Inf;
);
```

`q34_urban_land` is an **equality** to `i34_urban_area` — direction-agnostic; if the input declines,
urban declines. The deviation penalty is **symmetric**: `q34_urban_cost1` charges for being *below*
input, `q34_urban_cost2` for being *above*, both at `s34_urban_deviation_cost = 1e+06`. No
`vm_lu_transitions` entry involving `"urban"` is restricted anywhere in the tree. (In the non-default
`static` realization urban is frozen at `pcm_land` — also not "one-way expansion".)

**Evidence**: `modules/34_urban/exo_nov21/presolve.gms:10-16`;
`modules/34_urban/exo_nov21/equations.gms:17-21` and `:30-31`;
`modules/34_urban/exo_nov21/input.gms:13`; `modules/34_urban/static/presolve.gms:9`.

```
$ rg -n 'vm_lu_transitions.*"urban"|"urban".*vm_lu_transitions' .../modules/
   (no match; positive control: 5 vm_lu_transitions hits in 10_land/landmatrix_dec18/presolve.gms)
```

**Fix**: line 344 → "Urban area is pinned to the exogenous `i34_urban_area` trajectory at regional
level; it rises or falls with that input. The code imposes no monotonicity (`vm_land.lo(j,"urban")=0`,
`.up=Inf` for `ord(t)>1`)." Line 157 → replace "prevent urban land from decreasing" with "pin urban
land to the input trajectory in both directions (`q34_urban_cost1`/`q34_urban_cost2` are symmetric)",
and note the matrix row reflects the usual SSP trajectory (urban rising), not a code restriction.

---

### B4 — Minor — `set_membership` — doc line 744

**Claim** (§10.1): "**Module Coordination**: 6 modules provide land types, Module 10 enforces balance"

**Reality**: **5** modules touch a `vm_land` slice — 29 (`crop`), 31 (`past`, lower bound only), 32
(`forestry`), 34 (`urban`), 35 (`primforest`/`secdforest`/`other`). Module 30 only **reads**
`vm_land(j2,"crop")` on an equation RHS (bioenergy-tree target); it never sets it. The doc states this
itself at line 275 ("**Does NOT directly set vm_land**"), so §10.1 contradicts §5.3.

**Evidence**: `modules/30_croparea/simple_apr24/equations.gms:23` (RHS read; `simple_apr24` is the
default per `config/default.cfg:915`); `modules/29_cropland/detail_apr24/equations.gms:11-12`;
`modules/31_past/endo_jun13/presolve.gms:9`; `modules/32_forestry/dynamic_may24/equations.gms:55-56`;
`modules/34_urban/exo_nov21/equations.gms:30-31`;
`modules/35_natveg/pot_forest_may24/equations.gms:11,13`.

```
$ rg -n "vm_land\(" .../modules/ | grep -v "vm_land_other\|vm_land_forestry" | cut -d/ -f1 | sort | uniq -c
  12 29_cropland   6 35_natveg   5 34_urban   3 59_som   3 31_past   3 10_land
   2 50_nr_soil_budget   2 30_croparea   1 32_forestry
$ rg -n 'vm_land\b' .../modules/30_croparea/
  detail_apr24/equations.gms:23:  vm_land(j2,"crop") * sum(ct, i30_betr_target(ct,j2)) - vm_area(...)
  simple_apr24/equations.gms:23:  vm_land(j2,"crop") * sum(ct, i30_betr_target(ct,j2)) - vm_area(...)
```

**Fix**: "5 modules populate a `vm_land` slice (29, 31, 32, 34, 35); Module 30 allocates *within*
cropland via `vm_area` and only reads `vm_land(j,"crop")`. Module 10 enforces the balance."
Optionally re-label the §10.3 table row for Module 30 (Land Type "Cropland" → "— (allocates within
`vm_land(j,"crop")`)").

---

### B5 — Minor — `data_flow_direction` — doc line 721

**Claim** (§9.3 Step 4):
```r
land_previous <- readGDX(gdx, "oq10_land_area", select=list(type="level"))
# Verify: sum(transitions from X) = previous land X
```

**Reality**: `oq10_land_area(t,j,type)` is the **equation activity** of `q10_land_area` — one value per
cell, with **no land dimension** — so it cannot supply "previous land X" per land type. Previous-timestep
land by type is the parameter `pcm_land(j,land)`, written in postsolve. (`ov_land(t,j,land,"level")` is
the *current* land by type; there is no `o*` output holding the previous one.)

**Evidence**: `modules/10_land/landmatrix_dec18/declarations.gms:11` (`pcm_land(j,land)`),
`:44` (`oq10_land_area(t,j,type)`); `modules/10_land/landmatrix_dec18/postsolve.gms:9,31`.

**Fix**: `land_previous <- readGDX(gdx, "pcm_land")` (and note that `pcm_land` in the GDX is the
*post-run* value, i.e. the last timestep's land, so a per-timestep check needs
`ov_land[,t-1,]` instead).

---

### B6 — Minor — `other` — doc lines 438-439

**Claim** (§6.2 R example):
```r
land_1995 <- total_land["y1995",,]
land_2050 <- total_land["y2050",,]
```

**Reality**: magclass objects are indexed `[spatial, temporal, data]`, so a year label must go in the
**second** slot. The doc uses the correct form everywhere else — line 621
(`total_land[,"y2050",] - total_land[,"y1995",]`) and line 710 (`total_land[,t,]`) — making this an
internal inconsistency as well as an R error. (magclass itself is outside the develop worktree; the
convention claim is general knowledge, the inconsistency is checkable in-doc.)

**Fix**: `land_1995 <- total_land[,"y1995",]` / `land_2050 <- total_land[,"y2050",]`.

---

## Informational

### I1 — `other` — doc lines 106-113 (repeated 425-429) — MANDATE 10 (set-sum non-expansion)

§3.1 "Expanded Form" and §6.2's verification block expand `sum(land, vm_land(j2,land))` into the
seven explicit members. The expansion is **factually complete and correct** (all seven members match
`core/sets.gms:251` exactly), so this is hygiene, not a content error — but it is the precise
anti-pattern MANDATE 10 was written for, and the R16 Major anchor is an agent that copied such an
expansion and truncated it. A future editor adding a land pool must remember to touch both blocks.

**Fix (optional)**: keep the expansion but annotate it — "expansion of the `land` set as of
`core/sets.gms:251`; the code uses the set-based sum, which stays correct if the set changes."

---

## Verified-correct (spot list, so a later round need not redo it)

| Doc claim | Verdict |
|---|---|
| `q10_land_area` @ `modules/10_land/landmatrix_dec18/equations.gms:13-15` | ✓ verbatim |
| `q10_transition_to` @ `:19-21`, `q10_transition_from` @ `:23-25` | ✓ verbatim (incl. the to/from ordering) |
| presolve restrictions @ `:13`, `:16-17`, `:20`, `:21`; range `:10-23` | ✓ all five lines verbatim |
| `pcm_land(j,land) = vm_land.l(j,land)` @ `postsolve.gms:9` | ✓ |
| 7 land pools @ `core/sets.gms:250-251` | ✓ `crop, past, forestry, primforest, secdforest, urban, other` |
| `vm_land` DECLARED in `10_land` (`declarations.gms:19`) | ✓ (role map + grep) |
| `vm_landexpansion` → 35, 39, 58, 59 (doc line 227) | ✓ `35_natveg/.../equations.gms:197,222`; `39_landconversion/calib/equations.gms:13`; `58_peatland/v2/equations.gms:28`; `59_som/cellpool_jan23/equations.gms:91` |
| `vm_landreduction` → 39, 58 only, **NOT** 35/59 (doc line 228) | ✓ `39_landconversion/calib/equations.gms:14`; `58_peatland/v2/equations.gms:31`; no 35/59 hit |
| §4.3 note: `primforest→secdforest`, `other→secdforest` un-fixed and live | ✓ only the `"primforest"` *column*, `primforest→forestry`, `primforest→other`, `secdforest→other` are `.fx`-ed |
| primforest can only decrease | ✓ column fixed to 0 + diagonal `.up=Inf` ⇒ `vm_land(j,"primforest") ≤ pcm_land(j,"primforest")` |
| "net land use transitions" wording | ✓ matches `landmatrix_dec18/realization.gms:11` (`@limitations ... only accounts for net land use transitions`) |
| Realizations cited (10 `landmatrix_dec18`, 29 `detail_apr24`, 31 `endo_jun13`, 32 `dynamic_may24`, 34 `exo_nov21`, 35 `pot_forest_may24`) | ✓ all are `config/default.cfg` defaults (lines 232, 814, 988, 995, 1147, 1156) |
| `q29_cropland` @ `29_cropland/detail_apr24/equations.gms:11-12` | ✓ verbatim |
| `q31_prod` @ `31_past/endo_jun13/equations.gms:16-18` | ✓ |
| `vm_land.lo(j,"past") = sum(consv_type, pm_land_conservation(...))` @ `31_past/endo_jun13/presolve.gms:9` | ✓ verbatim |
| `q32_land` @ `32_forestry/dynamic_may24/equations.gms:55-56` | ✓ verbatim; `type32 = /aff, ndc, plant/` (`sets.gms:16-17`) |
| `32_forestry/dynamic_may24/presolve.gms:213-215` "avoids conflict with secdforest restoration" | ✓ line 213 comment matches |
| `q34_urban_land` @ `34_urban/exo_nov21/equations.gms:30-31` | ✓ verbatim |
| 1e6 USD/ha urban deviation cost | ✓ `s34_urban_deviation_cost ... / 1e+06 /` @ `34_urban/exo_nov21/input.gms:13` |
| Urban data = LUH3 | ✓ `34_urban/exo_nov21/realization.gms:8` |
| `q35_land_secdforest` @ `:11`, `q35_land_other` @ `:13` | ✓ verbatim, incl. `vm_land_other(j2,othertype35,ac)` |
| `othertype35 = /othernat, youngsecdf/` | ✓ `35_natveg/pot_forest_may24/sets.gms:23-24` |
| 20 tC/ha threshold value; youngsecdf = vegc ≤ 20 | ✓ `presolve.gms:117` (only the *citation* drifted — B1) |
| `p35_min_forest` exists; forest ≥ target covers forestry+primforest+secdforest | ✓ `q35_min_forest` @ `equations.gms:78-80`, `land_forest` @ `core/sets.gms:259-260` |
| `pm_max_forest_est` declared in 35, read by 32 | ✓ `32_forestry/dynamic_may24/equations.gms:86` |
| `pm_land_conservation` declared in 22 | ✓ (role map; populated also by 32 @ `presolve.gms:214-216` and 35) |
| `kcr` = 19 members, 2 bioenergy (`begr`, `betr`) | ✓ `14_yields/managementcalib_aug19/sets.gms:23-26` (17 non-bioenergy @ `:28-31`) |
| Module 30 "does NOT directly set vm_land" (line 275) | ✓ RHS-only read |
| Module 10 inputs = `vm_landdiff_natveg` (M35) + `vm_landdiff_forestry` (M32) | ✓ `equations.gms:50-54`, both declared in their own modules |

---

## Deferred (not verified — no bug asserted)

1. **Line 230 "Centrality: 17 connections (2 inputs, 15 outputs) — Highest in MAgPIE."** The 2 inputs
   check out (`vm_landdiff_natveg`, `vm_landdiff_forestry`). "15 outputs" cannot be adjudicated: the
   doc never states the counting convention, and a union of modules reading any Module-10-declared
   interface (`vm_land`, `vm_landexpansion`, `vm_landreduction`, `vm_lu_transitions`, `vm_landdiff`,
   `vm_cost_land_transition`, `pcm_land`) gives **17** consumer modules (11, 13, 22, 29, 30, 31, 32,
   34, 35, 39, 44, 50, 56, 58, 59, 71, 80). "Highest in MAgPIE" is comparative and unverified here.
2. **magpie4 R API** (`land(gdx, level="cell")`, `dimSums(land, dim=3.1)`,
   `plot(land[,"y1995":"y2100",])` at line 730). magpie4 is not in the develop worktree; the character
   range `"y1995":"y2100"` looks suspect in base R but I did not verify magclass's dispatch.
3. **Whether `i34_urban_area` ever declines** under any SSP. `f34_urbanland.cs3` is a run-time input
   absent from the worktree (only the `input/files` marker exists), so B3 asserts only that *no
   code-level monotonicity exists*, not that urban land actually falls in a default run.
4. **Line 296 "Provides `vm_land(j,"past")` to Module 10."** Module 31 `endo_jun13` has **no** equation
   populating `vm_land(j,"past")` — `q31_prod`/`q31_carbon`/`q31_bv_manpast` all read it on the RHS,
   and the only assignment is the `.lo` bound at `presolve.gms:9`. Not filed as a bug: the adjacent
   text (lines 289-292) states the real mechanism (area is a free variable pinned by
   production ≤ area × yield), and MANDATE 18's slice-populator corollary protects this phrasing. Flagged
   for a maintainer's eye — the parallel bullets for 29/32/35 *are* backed by defining equalities, so
   the symmetry is misleading.
5. **Line 566 `presolve.gms:47-73` (abandoned-land recovery).** The block now spans 48-78; the cited
   range covers the banner and most of the code but drops the tail (74-78). Off-by-few with adjacent
   similar content — not filed.
6. **Line 263 "17 food crops".** The count 17 is right (`knbe14`), but the members include `foddr` and
   `cottn_pro`, which are not food. Wording, not a count error — not filed.
7. **Line 416 "Disturbances (fire, shifting agriculture)."** Module 35 does have
   `driver_source /... shifting_agriculture, ... wildfire .../` (`sets.gms:10-12`), applied as
   parameterized loss rates (`p35_disturbance_loss_secdf`). The doc lists it as a factor, not as a
   mechanistic process, so it does not trip the parameterization-vs-mechanism rule — but a future
   edit should keep the "applies historical rates labeled wildfire" framing.

---

_Auditor note_: the doc's most attribution-dense claims (lines 224-228, §4.3's reconciliation note)
read like the product of an earlier fix round and are now **correct against code** — the residual
defects all sit in the narrative/scenario sections (§5.7 citation, §7.3 pseudo-formula, §7/§9 R
examples), which is where the next round should look first.
