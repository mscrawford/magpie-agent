# R60 depth audit — `cross_module/carbon_balance_conservation.md`

**Lens**: `declare_populate` — enter from the DECLARING / POPULATING side (`declarations.gms`, equation LHS,
`.fx`/`.l` assignments), and check whether the equation bodies match the formulas the doc attributes to them.
**Ground truth**: MAgPIE `develop` read-only worktree, HEAD `2c02843ec` (identical to local `develop`).
**Role map**: `audit/integrated/depth_rolemap.json` — consulted FIRST for every `vm_`/`pm_`/`im_`/`pcm_`/`fm_`
attribution claim, then confirmed with a both-endpoints grep (`NAME(` **and** `NAME.`).
**Date**: 2026-08-02 · **Claims verified**: 78 · **Bugs**: 12 (0 Critical · 4 Major · 7 Minor · 1 Informational)

**Provenance note**: a prior pass of this same lens on this same doc existed at this path. Five of its seven
findings are reproduced below — each **re-derived from code in this session**, not inherited; the two I could
not stand behind as filed are moved to Deferred with reasons. Six findings below are new to this pass. Each
bug is tagged `[re-derived]` or `[new]` so a reader can see which claims have two independent derivations and
which have one.

---

## Verdict

**The declare/populate spine is clean.** Every DECLARED / POPULATED / READ claim for `vm_carbon_stock`,
`pcm_carbon_stock`, `vm_emissions_reg`, `vm_carbon_stock_croparea`, `vm_nr_som`, `vm_cost_scm` and the four
`pm_carbon_density_*` parameters verifies against the role map **and** an independent whole-tree grep. The §7.5
populator set `{M29, M31, M32, M34, M35, M59}` is exactly right; the `stockType` both-slices claim is right down
to the `m_carbon_stock_ac` macro branch; the M52/M56 *parallel readers* correction is right; all 13 realization
names cited are the current config defaults; all ~30 `modules/**.gms:LINE` citations resolve to the claimed
content.

The defects are **not** in the attribution layer. They cluster in the narrative and worked-example layer:
three mechanisms whose **default state** is misstated or under-stated, one growth table that contradicts its own
printed parameters, two incomplete interface lists, and three arithmetic/citation slips.

---

## Bugs (most severe first)

### B1 — Major — `mechanism` — "Primary forest carbon density does NOT change over time" is false under the default climate scenario `[re-derived]`

**doc_line**: `carbon_balance_conservation.md:201`, repeated at `:841`

> - Carbon density does NOT change over time (climate change affects future forests, not current primary)
> **1. Static Primary Forest Carbon**: - Primary forest carbon density does NOT change over time

**Reality**: `q35_carbon_primforest` (`modules/35_natveg/pot_forest_may24/equations.gms:42-44`) expands via
`m_carbon_stock` (`core/macros.gms:99-101`) to
`vm_land(j2,"primforest") * sum(ct, fm_carbon_density(ct,j2,"primforest",ag_pools))` — it reads the **current
time step's** density. `fm_carbon_density(t_all,j,land,c_pools)` is a time-indexed LPJmL table
(`modules/52_carbon/normal_dec17/input.gms:16-20`) and is collapsed to y1995 **only** under
`c52_carbon_scenario = "nocc"` (`input.gms:22`). The default is **`cc`** (`input.gms:8`;
`config/default.cfg:1590`). So in a default run primary-forest carbon density *does* vary over time.

The doc contradicts itself: §8.3 (`:698-700`) states "Module 52 updates `fm_carbon_density(t,j,land,c_pools)`
over time; Carbon stocks change even without land-use change." Both statements cannot hold.

What *is* static about primforest: it carries no age-class structure — no Chapman-Richards curve, no `ac`
dimension — which is presumably what "Static" in the §3.4 table means. The prose overshoots that into a
false claim about time.

**verify_cmd**
```
grep -n "c52_carbon_scenario" config/default.cfg          -> 1590:cfg$gms$c52_carbon_scenario <- "cc"  # def = "cc"
sed -n '8,11p;16,24p' modules/52_carbon/normal_dec17/input.gms
   -> :8  $setglobal c52_carbon_scenario cc
   -> :16 table fm_carbon_density(t_all,j,land,c_pools)
   -> :22 $if "%c52_carbon_scenario%" == "nocc" fm_carbon_density(t_all,...) = fm_carbon_density("y1995",...)
sed -n '42,44p' modules/35_natveg/pot_forest_may24/equations.gms  -> m_carbon_stock(vm_land,fm_carbon_density,"primforest")
sed -n '99,101p' core/macros.gms                          -> sum(ct, carbon_density(ct,j2,item,ag_pools))
```
**Fix**: rescope both bullets to age-class staticness — "Primary forest carries no age-class structure: its
density is `fm_carbon_density(t,j,"primforest",c_pools)` read directly, with no Chapman-Richards growth. The
density is **not** constant in time under the default `c52_carbon_scenario = "cc"`
(`config/default.cfg:1590`) — it follows the LPJmL climate projection. It is frozen at 1995 only under `nocc`
(`modules/52_carbon/normal_dec17/input.gms:22`)."

---

### B2 — Major — `formula` — §6.3 growth-trajectory table does not follow from its own stated parameters `[re-derived]`

**doc_line**: `carbon_balance_conservation.md:485-500`

> A = 100 tC/ha · k = 0.06, m = 2.0 … then a table giving 14 / 26 / 44 / 58 / 75 / 88 / 93 tC/ha at
> 5 / 10 / 20 / 30 / 50 / 80 / 100 years.

**Reality**: the model's curve is `m_growth_vegc(S,A,k,m,ac) = S + (A-S)*(1-exp(-k*(ac*5)))**m`
(`core/macros.gms:18`), called with `(ord(ac)-1)` (`modules/52_carbon/normal_dec17/start.gms:17,28,48`). With
S=0, A=100, k=0.06, m=2:

| years | doc | `100*(1-exp(-0.06*y))**2` | (`k=0.03, m=1`) |
|---|---|---|---|
| 5 | 14 | **6.7** | 13.9 |
| 10 | 26 | **20.4** | 25.9 |
| 20 | 44 | **48.8** | 45.1 |
| 30 | 58 | **69.7** | 59.3 |
| 50 | 75 | **90.3** | 77.7 |
| 80 | 88 | **98.4** | 90.9 |
| 100 | 93 | **99.5** | 95.0 |

The doc's column tracks `k ≈ 0.03, m = 1` — i.e. the table was generated from parameters other than the ones
printed directly above it. The wrong numbers then propagate into §8.2 (`:676` "44 tC/ha (44% of mature, from
Chapman-Richards)"; `:682` "75 tC/ha (75% of mature)") and into the §8.2 sequestration totals.

**Impact**: this table is the doc's only worked demonstration of the Chapman-Richards implementation. A reader
sanity-checking `pm_carbon_density_plantation_ac` output against it would conclude the model's growth is ~2×
slower at young ages than it is, and would mis-time afforestation sequestration by decades.

**verify_cmd**
```
sed -n '18p' core/macros.gms
   -> $macro m_growth_vegc(S,A,k,m,ac) S + (A-S)*(1-exp(-k*(ac*5)))**m;
python3 -c "import math;print([round(100*(1-math.exp(-0.06*y))**2,1) for y in (5,10,20,30,50,80,100)])"
   -> [6.7, 20.4, 48.8, 69.7, 90.3, 98.4, 99.5]
python3 -c "import math;print([round(100*(1-math.exp(-0.03*y)),1)    for y in (5,10,20,30,50,80,100)])"
   -> [13.9, 25.9, 45.1, 59.3, 77.7, 90.9, 95.0]     # matches the doc's column
```
**Fix**: recompute the table with the stated k=0.06, m=2.0 (values above), and update the two §8.2 figures to
~49 tC/ha at year 20 and ~90 tC/ha at year 50; **or** restate the parameters as k=0.03, m=1.0. Keep the
"illustrative" note either way, and note that both k and m are overwritten by the FRA calibration for
secdforest/plantation (cross-reference the `:180` / `:479` warning block).

---

### B3 — Major — `default_value` — fire disturbance presented as an active carbon-loss driver, with no default-state caveat `[re-derived]`

**doc_line**: `carbon_balance_conservation.md:869-872` (echoed at `:221`, `:626`)

> **6. No Fire Emissions Separately**: - Fire disturbances (Module 35) cause carbon loss via stock change
> - Disturbances (fire, shifting agriculture) → reset age classes → carbon loss

**Reality**: under the default the channel is narrower and temporary.

- Default `s35_forest_damage = 2` (`modules/35_natveg/pot_forest_may24/input.gms:27`;
  `config/default.cfg:1184`). That branch (`.../presolve.gms:19-22`) applies **only**
  `f35_forest_lost_share(i,"shifting_agriculture")`, multiplied by `(1 - p35_damage_fader(t))`.
- `p35_damage_fader` interpolates 0→1 up to `s35_forest_damage_end = 2050` (`.../preloop.gms:88`;
  `.../input.gms:28`; `config/default.cfg:1186`) ⇒ **disturbance loss decays to zero by 2050**.
- The distinct `wildfire` member of `driver_source` (`.../sets.gms:12`) enters only via `combined_loss`
  (`.../sets.gms:14-15`) under `s35_forest_damage = 3` (`.../presolve.gms:24-26`) — an option not even offered
  in `config/default.cfg`, whose documented list is `0, 1, 2, 4` (`config/default.cfg:1180-1183`).

**Nuance that must survive the fix (do not overcorrect)**: the default channel *is* fire-related —
`f35_forest_lost_share` is titled "Share of area damaged by forest fires" (`.../input.gms:32`) and
`.../presolve.gms:9` reads "Shift ageclasses due to shifting agriculture fires". The claim is not false for
2020; it is false from 2050 onward, and the separate `wildfire` driver never fires in any config-documented
setting.

**verify_cmd**
```
grep -n "s35_forest_damage" modules/35_natveg/pot_forest_may24/input.gms
   -> :27 ... / 2 /     :28 s35_forest_damage_end ... / 2050 /
sed -n '13,33p' modules/35_natveg/pot_forest_may24/presolve.gms
   -> =1 shifting only ; =2 shifting*(1-p35_damage_fader) ; =3 sum(combined_loss) ; =4 f35_forest_shock
sed -n '10,15p' modules/35_natveg/pot_forest_may24/sets.gms  -> combined_loss / shifting_agriculture, wildfire /
sed -n '88p'    modules/35_natveg/pot_forest_may24/preloop.gms -> m_sigmoid_time_interpol(p35_damage_fader,sm_fix_SSP2,s35_forest_damage_end,0,1)
sed -n '1179,1186p' config/default.cfg  -> options documented: (0)(1)(2)(4) ; <- 2 ; end <- 2050
```
**Fix**: append to item 6 — "**Default caveat**: with `s35_forest_damage = 2` (`config/default.cfg:1184`) only
the *shifting-agriculture* loss share is applied, and it is faded to zero by `s35_forest_damage_end = 2050`
(`modules/35_natveg/pot_forest_may24/presolve.gms:19-22`, `preloop.gms:88`). The separate `wildfire` driver
(`.../sets.gms:12,15`) is used only under `s35_forest_damage = 3` (`.../presolve.gms:24-26`), an option not
listed in `config/default.cfg`. A default run therefore has **no** disturbance-driven carbon loss after 2050.
These are exogenous historical loss *shares*, not a modelled fire process." Mirror at `:626`.

---

### B4 — Major — `default_value` — §3.1's default-state note singles out term 2, implying terms 3-4 are live; all three are zero by default `[new]`

**doc_line**: `carbon_balance_conservation.md:134`

> Term 2 (SCM …) is gated by `i59_scm_target` per scenario; terms 3-4 (fallow + treecover) are land-management
> categories distinct from cropping area. … Default `s59_scm_target = 0` (`config/default.cfg:1978`), so
> **term 2 is zero in a default run**.

**Reality**: giving the default state for term 2 *only* reads as an assertion that terms 3 and 4 are live. They
are not — in a default run `q59_som_target_cropland` collapses to **term 1 alone**:

- **Term 3 (fallow)**: `s29_fallow_max = 0` (`modules/29_cropland/detail_apr24/input.gms:33`;
  `config/default.cfg:901`), and `q29_fallow_max` is
  `vm_fallow(j2) =l= vm_land(j2,"crop") * s29_fallow_max` (`.../equations.gms:70-72`) with
  `vm_fallow.lo(j) = 0` (`.../presolve.gms:120`) ⇒ `vm_fallow ≡ 0`.
- **Term 4 (treecover)**: `s29_treecover_map = 0` (`config/default.cfg:863`) ⇒ `pc29_treecover(j,ac) = 0`
  (`.../preloop.gms:37-38`), and `v29_treecover.fx(j,ac_sub) = pc29_treecover(j,ac_sub)` (`.../presolve.gms:81`)
  pins the standing stock at 0. Establishment on `ac_est` is unbounded above but costed at
  `s29_cost_treecover_est = 2460 USD17MER/ha` (`.../input.gms:18`; `config/default.cfg:887`) via
  `q29_cost_treecover_est` (`.../equations.gms:108-111`), with `s29_treecover_target = 0`
  (`config/default.cfg:868`) so `q29_treecover_min` imposes nothing ⇒ cost minimisation drives it to 0.

**Impact**: a reader planning a soil-carbon experiment concludes fallow and treecover already modulate the
cropland SOM target and that only SCM needs switching on.

**verify_cmd**
```
grep -n "s29_fallow_max\|s29_treecover_target\|s29_cost_treecover_est" modules/29_cropland/detail_apr24/input.gms
   -> :33 s29_fallow_max /0/   :24 s29_treecover_target /0/   :18 s29_cost_treecover_est /2460/
sed -n '70,72p'   modules/29_cropland/detail_apr24/equations.gms -> q29_fallow_max: vm_fallow =l= vm_land*s29_fallow_max
sed -n '120,121p' modules/29_cropland/detail_apr24/presolve.gms  -> vm_fallow.lo(j)=0 ; .up = p29_avl_cropland
sed -n '31,40p'   modules/29_cropland/detail_apr24/preloop.gms   -> s29_treecover_map=0 -> pc29_treecover(j,ac)=0
sed -n '79,81p'   modules/29_cropland/detail_apr24/presolve.gms  -> v29_treecover.fx(j,ac_sub)=pc29_treecover(j,ac_sub)
grep -nE "s29_(fallow_max|treecover_map|treecover_target) " config/default.cfg -> 901, 863, 868  (all 0)
```
**Fix**: replace the closing sentence with — "In a **default** run all three extra terms are zero:
`s59_scm_target = 0` (`config/default.cfg:1978`) kills term 2; `s29_fallow_max = 0` (`config/default.cfg:901`)
forces `vm_fallow = 0` through `q29_fallow_max` (`modules/29_cropland/detail_apr24/equations.gms:70-72`); and
`s29_treecover_map = 0` with `s29_treecover_target = 0` (`config/default.cfg:863,868`) leaves treecover pinned
at 0 (`modules/29_cropland/detail_apr24/presolve.gms:81`). The full four-term form matters only under fallow /
treecover / SCM scenarios."

---

### B5 — Minor — `citation` — `config/default.cfg` line drift on the unprefixed `c56_carbon_stock_pricing` assignment `[re-derived]`

**doc_line**: `carbon_balance_conservation.md:101`

> ⚠️ Do **not** cite `config/default.cfg:1835` for this default: that line omits the `cfg$gms$` prefix its
> siblings carry, so it never reaches GAMS…

**Reality**: the **substance is TRUE and still live** — `config/default.cfg:1838` reads
`c56_carbon_stock_pricing <- "actualNoAcEst"   # def = actualNoAcEst` with no `cfg$gms$` prefix, and it is the
**only** bare module-switch assignment in the file (384 lines carry `cfg$gms$`; the 5 other bare assignments —
`cfg`, `all_iso_countries`, `oecd90andEU`, `isoCountriesEUR`, `isoCountriesLowMiddleIncome` — are helper R
value variables). But the **line number has drifted**: `:1835` is now a comment
(`# *   actual: CO2 emissions for pricing are based on the difference of actual carbon stocks between time steps`),
so a reader following the pointer lands on a line that carries no assignment and cannot confirm the warning.

*Tier note*: the Major trigger "citation drift to adjacent but different content" and the Minor trigger
"off-by-few line citation where adjacent lines say similar things" both partly fire (1834-1837 are all comments
about the same switch). Per the rubric tie-breaker, filed as **Minor**.

**verify_cmd**
```
grep -n "c56_carbon_stock_pricing" config/default.cfg      -> 1838 (not 1835)
sed -n '1833,1839p' config/default.cfg                     -> 1835 is a comment for the "actual" option
grep -cE '^cfg\$gms\$' config/default.cfg                  -> 384
grep -nE '^[a-z][A-Za-z0-9_]* *<-' config/default.cfg      -> 12,150,177,182,187,1838
```
**Fix**: `config/default.cfg:1835` → `config/default.cfg:1838`. Grep the corpus for other echoes of `:1835`
before closing.

---

### B6 — Minor — `formula` — §8.1 gradual soil-carbon emission arithmetic `[re-derived]`

**doc_line**: `carbon_balance_conservation.md:656`

> Gradual (soilc over 20 years): 30 tC/ha × 100 Mha × (44/12) / 20 years = **458 Tg CO₂/year**

**Reality**: 30 tC/ha × 100 Mha = 3 000 Tg C; × 44/12 = 11 000 Tg CO₂; / 20 = **550 Tg CO₂/year**. The sibling
line `:655` (155 tC/ha → 56 833 Tg CO₂) applies the identical method correctly, which makes the 458 look
authoritative by association. (458 is what you get dividing by 24, or from a 25 tC/ha loss — neither matches
the table at `:649`, which gives −30.)

**verify_cmd**
```
python3 -c "print(30*100*(44/12)/20, round(155*100*(44/12),1))"   -> 550.0 56833.3
```
**Fix**: `458 Tg CO₂/year` → `550 Tg CO₂/year`.

---

### B7 — Minor — `formula` — §8.4 Year-5 convergence uses the legacy share (44 %) instead of the loss rate (56 %) `[new]`

**doc_line**: `carbon_balance_conservation.md:734`

> **Convergence Timeline** (Module 59): - Year 5: **44%** toward new equilibrium = **+4 tC/ha**

**Reality**: 44 % is `0.85^5` — the **legacy** share, not the converged share. The code sets
`i59_lossrate(t) = 1 - 0.85**m_yeardiff(t)` (`modules/59_som/cellpool_jan23/preloop.gms:45`) ⇒ the 5-year
lossrate is **0.556**. Correct row: **56 % toward the new equilibrium = +5 tC/ha** (0.556 × 9).

This contradicts the doc's own §5.2 (`:401` table row "5 years | 56% | 44%" and `:412` "After 5 years: 56%
toward new equilibrium, 44% legacy"). The Year-10 (80 % → +7.2) and Year-20 (96 % → +8.6) rows in §8.4 are
correct, confirming a single-row slip rather than a method error.

**Likely upstream**: the GAMS comment at `modules/59_som/cellpool_jan23/preloop.gms:42` itself says "resulting
in 44% in 5 years, 80% in 10 years and 96% in 20 years" — internally inconsistent code prose (44 % is the
remainder; 80/96 % are the loss rates). **The doc's §5.2 is right and the code comment is the loose one** — a
future auditor must not "fix" §5.2 toward the comment. Only §8.4 needs changing.

**verify_cmd**
```
sed -n '41,45p' modules/59_som/cellpool_jan23/preloop.gms
   -> :42 comment "44% in 5 years"   :45 i59_lossrate(t)=1-0.85**m_yeardiff(t)
python3 -c "print(round(1-0.85**5,4), round((1-0.85**5)*9,2), round(1-0.85**10,4), round(1-0.85**20,4))"
   -> 0.5563 5.01 0.8031 0.9612
```
**Fix**: `Year 5: 44% toward new equilibrium = +4 tC/ha` → `Year 5: 56% toward new equilibrium = +5 tC/ha`.
Optionally add: "(the code comment at `modules/59_som/cellpool_jan23/preloop.gms:42` quotes 44 % here, which is
the *legacy* share; the formula on `:45` gives 56 %.)"

---

### B8 — Minor — `attribution_read` — `vm_maccs_costs` consumer arrow omits Module 36 `[re-derived]`

**doc_line**: `carbon_balance_conservation.md:593`

> `vm_maccs_costs(i,factors)`: Labor and capital costs of mitigation → to Module 11

**Reality**: declared at `modules/57_maccs/on_aug22/declarations.gms:25`, populated at
`modules/57_maccs/on_aug22/equations.gms:36` (`"labor"`) and `:46` (`"capital"`); read by **two** modules —
M11 (`modules/11_costs/default/equations.gms:28`, `sum(factors, vm_maccs_costs(i2,factors))`) **and** M36
(`modules/36_employment/exo_may22/equations.gms:28`, `vm_maccs_costs(i2,"labor")`). M36's default realization
is `exo_may22` (`config/default.cfg:1212`), so the consumer is live in a default run. Role map agrees:
`read_by: ["11","36","57"]`.

The neighbouring arrows in the same block (`vm_nr_som` → M51, `vm_cost_scm` → M11) *are* exhaustive against
the role map, so the asymmetry reads as a complete list to a careful reader. *Tier note*: the R20 anchor
(wrong consumer set → Critical) is in tension here; filed **Minor** per the tie-breaker because this doc is not
the canonical Module-57 interface inventory and the arrow does not claim exhaustiveness.

**verify_cmd**
```
rg -n "vm_maccs_costs" modules/ --glob "!*not_used.txt"
   -> 57 declarations:25, equations:36,46, scaling:8, postsolve:11,14,17,20
   -> 11_costs/default/equations.gms:28 ; 36_employment/exo_may22/equations.gms:28
grep -nE 'cfg\$gms\$employment' config/default.cfg          -> 1212: exo_may22
```
**Fix**: "→ to Module 11 (total costs) and Module 36 (`"labor"` slice only, agricultural employment)".

---

### B9 — Minor — `attribution_declare` — §7.1 "Module 52 Provides" omits three parameters M52 declares and populates `[re-derived]`

**doc_line**: `carbon_balance_conservation.md:512-516`

§7.1 is headed "Module 52 (Carbon) — Central Data Provider / **Provides**:" and lists four parameters
(`fm_carbon_density`, `pm_carbon_density_{plantation,secdforest,other}_ac`).

**Reality**: M52 also declares and populates three more interface parameters with live consumers:

| Parameter | Declared | Populated | Read by (role map + grep) |
|---|---|---|---|
| `pm_carbon_density_secdforest_ac_uncalib` | `modules/52_carbon/normal_dec17/declarations.gms:10` | `start.gms:43` | M14, M29, M32, M35 |
| `pm_carbon_density_plantation_ac_uncalib` | `declarations.gms:13` | `start.gms:44` | M29, M32 |
| `im_vol_conv(i)` | `declarations.gms:23` | `preloop.gms:21` (fallback `start.gms:40`) | M73 (`modules/73_timber/default/preloop.gms:49,51,90,91`) |

The two `*_uncalib` parameters are the subject of two long ⚠️ blocks **elsewhere in this same file**
(`:180`, `:247`, `:479`), so §7.1 is internally inconsistent with the rest of the doc, and a reader using §7.1
as the M52 interface inventory would miss exactly the parameters most likely to be touched in a growth-curve
refactor — the R20 anchor's failure mode. M73's default realization is `default` (`config/default.cfg:2226`),
so the `im_vol_conv` consumer is live.

**verify_cmd**
```
sed -n '8,26p' modules/52_carbon/normal_dec17/declarations.gms   -> the 3 params at :10, :13, :23
rg -n "pm_carbon_density_secdforest_ac_uncalib|pm_carbon_density_plantation_ac_uncalib" modules/
rg -n "im_vol_conv" modules/ --glob "!*not_used.txt"             -> 73_timber/default/preloop.gms:49,51,90,91
python3 -c "import json;m=json.load(open('audit/integrated/depth_rolemap.json'));print(m['im_vol_conv'])"
   -> {'declared_in':'52_carbon','populated_by':['52'],'read_by':['52','73']}
grep -nE 'cfg\$gms\$timber' config/default.cfg                   -> 2226: default
```
**Fix**: add the three to the §7.1 Provides list, with a one-line note that the `*_uncalib` pair is the
pre-FRA-calibration snapshot and carries a *different* consumer set from the calibrated pair (cross-link the
`:180` block), and that `im_vol_conv` is M52's wood-density output consumed by M73.

---

### B10 — Minor — `mechanism` — "equilibrium based on residue production" describes a channel that does not exist in Module 59 `[new]`

**doc_line**: `carbon_balance_conservation.md:122` (and `:434`)

> Crop-specific equilibrium based on residue production
> … **Crop-specific**: Different crops produce different residue amounts

**Reality**: Module 59 contains **no residue variable of any kind** — no `vm_res_ag_recycling`,
`vm_res_recycling`, `vm_res_ag_burn`, nothing from Module 18. The crop-specificity of the equilibrium comes
entirely from the exogenous IPCC stock-change table `f59_cratio_landuse(i,climate59,kcr)` folded into
`i59_cratio` (`modules/59_som/cellpool_jan23/preloop.gms:60-67`). This is **parameterization, not a modelled
residue→SOC channel**: changing residue removal in Module 18 does not move the cropland SOM target.

The only "residue" strings in the module are comment prose (`input.gms:22-23`, `preloop.gms:86`), both
describing what the IPCC *high-input* factor is meant to represent.

**verify_cmd**
```
rg -n "vm_res|residue|resid" modules/59_som/cellpool_jan23/
   -> preloop.gms:86, input.gms:22, input.gms:23  — all comment prose; ZERO variable references
rg -c "vm_area" modules/59_som/cellpool_jan23/equations.gms   -> 3    # positive control: search works here
sed -n '60,67p' modules/59_som/cellpool_jan23/preloop.gms
   -> i59_cratio = FLU(f59_cratio_landuse, per kcr) * FMG(tillage) * FI(inputs) * F_irr
```
**Fix**: `:122` → "Crop-specific equilibrium via the IPCC land-use stock-change factor
`f59_cratio_landuse(i,climate59,kcr)` — an exogenous table indexed by crop, **not** a function of modelled
residue production (Module 18 residue flows do not enter Module 59)." Same at `:434`.

---

### B11 — Minor — `attribution_populate` — `vm_land` "Non-cropland areas from Module 10" is wrong on both attribution and scope `[new]`

**doc_line**: `carbon_balance_conservation.md:547`

> **Receives**: … `vm_land(j,land)`: Non-cropland areas from Module 10

**Reality**, two distinct problems:

1. **Scope** (the firm half): M59 reads `vm_land` over **all** land types, not just non-cropland —
   `q59_carbon_soil` uses `vm_land(j2, land)` for the subsoil term
   (`modules/59_som/cellpool_jan23/equations.gms:63`). Only `q59_som_target_noncropland` (`:33`) restricts to
   `noncropland59` (`/past, forestry, primforest, secdforest, other, urban/`, `.../sets.gms:10-11`).
2. **Attribution**: `vm_land` is DECLARED in `10_land`, but the non-cropland slices are POPULATED elsewhere —
   `secdforest`/`other` by M35 (`modules/35_natveg/pot_forest_may24/equations.gms:11,13`), `forestry` by M32,
   `past` by M31, `urban` by M34, `crop` by M29 (`modules/29_cropland/detail_apr24/equations.gms:12`). Module
   10's own equations (`modules/10_land/landmatrix_dec18/equations.gms:13-25`, `q10_land_area`,
   `q10_transition_to/from`) are **balance constraints**, not slice populators. Role map:
   `populated_by: [10,29,31,32,34,35]`. This contradicts the doc's own careful §7.5 populator list.

*Tier note*: the attribution half alone is arguable ("from Module 10" could be read as "via the module-10 land
interface"); the scope half is not. Filed **Minor** on the strength of the scope error.

**verify_cmd**
```
rg -n "vm_land\(|vm_land\." modules/59_som/cellpool_jan23/
   -> equations.gms:33 (noncropland59)   equations.gms:63 (ALL land)   postsolve.gms:9 (vm_land.l)
sed -n '10,11p' modules/59_som/cellpool_jan23/sets.gms   -> noncropland59 / past, forestry, primforest, secdforest, other, urban /
sed -n '13,25p' modules/10_land/landmatrix_dec18/equations.gms -> q10_land_area / q10_transition_to / q10_transition_from
sed -n '11,13p' modules/35_natveg/pot_forest_may24/equations.gms -> q35_land_secdforest / q35_land_other
python3 -c "import json;print(json.load(open('audit/integrated/depth_rolemap.json'))['vm_land'])"
   -> populated_by ['10','29','31','32','34','35']
```
**Fix**: "`vm_land(j,land)`: land areas — **declared** in Module 10; populated per slice by M29 (crop),
M31 (past), M32 (forestry), M34 (urban), M35 (primforest/secdforest/other), with M10 supplying the area balance
and transition matrix. M59 reads **all** slices in `q59_carbon_soil`
(`modules/59_som/cellpool_jan23/equations.gms:63`) and the non-cropland subset in `q59_som_target_noncropland`
(`:33`)."

---

### B12 — Informational — `other` (declaration signature) — `t` written where the declaration says `t_all` `[new]`

**doc_line**: `carbon_balance_conservation.md:107`, `:513-516`, `:699`

> `fm_carbon_density(t,j,land,c_pools)` … `pm_carbon_density_plantation_ac(t,j,ac,ag_pools)` …

**Reality**: all five carbon-density parameters are declared over **`t_all`**:
`table fm_carbon_density(t_all,j,land,c_pools)` (`modules/52_carbon/normal_dec17/input.gms:16`);
`pm_carbon_density_{secdforest,other,plantation}_ac(t_all,j,ac,ag_pools)` and the two `*_uncalib` variants
(`modules/52_carbon/normal_dec17/declarations.gms:9-13`). Since `t ⊂ t_all`, indexing with `t` inside an
equation is legal and nothing breaks — but the doc is quoting a declaration signature, and the signature is
`t_all`.

**verify_cmd**
```
sed -n '8,14p' modules/52_carbon/normal_dec17/declarations.gms   -> all (t_all,j,ac,ag_pools)
sed -n '16p'   modules/52_carbon/normal_dec17/input.gms          -> table fm_carbon_density(t_all,j,land,c_pools)
```
**Fix**: write `(t_all,j,…)` in the §3 header and the §7.1 Provides list.

---

## Cleared — load-bearing claims verified against code this session

**Attribution spine (role map consulted first, then both-endpoints grep — all confirmed)**

| Claim (doc line) | Verdict |
|---|---|
| `vm_carbon_stock` DECLARED at `modules/56_ghg_policy/price_aug22/declarations.gms:34`, 4-D `(j,land,c_pools,stockType)` (`:101`) | ✅ exact |
| `stockType / actual, actualNoAcEst /` at `modules/56_ghg_policy/price_aug22/sets.gms:212-213` (`:101`) | ✅ exact |
| "populating equations are indexed over the free set and fill **both** slices" (`:101`) | ✅ `q29_carbon`, `q31_carbon`, `q32_carbon`, `q35_carbon_{primforest,secdforest,other}`, `q59_carbon_soil` all carry `stockType` free; M34 uses `.fx(…,stockType)`. The macros `m_carbon_stock` / `m_carbon_stock_ac` (`core/macros.gms:99-106`) each emit an `actual` **and** an `actualNoAcEst` term — and `m_carbon_stock_ac` is what makes them differ (sums `ac` vs `ac_sub`) |
| Slice split: M52 reads `"actual"` (`modules/52_carbon/normal_dec17/equations.gms:19`); M56 prices `%c56_carbon_stock_pricing%` = `actualNoAcEst` (`modules/56_ghg_policy/price_aug22/equations.gms:22`, default `input.gms:90`) (`:101`) | ✅ exact |
| Direct populators `{M29 crop, M31 past, M32 forestry, M34 urban, M35 prim/secd/other, M59 soilc}` (`:629-632`) | ✅ matches role map `populated_by [29,31,32,34,35,59]` and a whole-tree `rg "vm_carbon_stock"`; no phantom, no omission. (M56's `preloop.gms:11` `vm_carbon_stock.l = pcm_carbon_stock` is an *initialisation*, correctly excluded) |
| Readers `{M52, M56}` (+M59) (`:632`) | ✅ role map `read_by [52,56,59]` |
| M56 does **not** consume M52's `vm_emissions_reg(…,"co2_c")` — parallel readers, not a serial chain (`:583`) | ✅ `q56_emis_pricing` is domained on `emis_annual` only (`equations.gms:15-17`); `co2_c` lives on `emis_oneoff` (`core/sets.gms:314-322`). A whole-module grep of `56_ghg_policy` finds no other `vm_emissions_reg` read |
| M30 computes `vm_carbon_stock_croparea`; M29 populates the crop slice (`:610-611`) | ✅ both M30 realizations populate it; `q29_carbon` at `modules/29_cropland/detail_apr24/equations.gms:38-42` |
| M34: `vm_carbon_stock.fx(j,"urban",ag_pools,stockType) = 0` at `modules/34_urban/exo_nov21/presolve.gms:8` (`:622`) | ✅ character-exact |
| `vm_nr_som` → M51, `vm_cost_scm` → M11 (`:540-541`) | ✅ exhaustive against role map; declarations `modules/59_som/cellpool_jan23/declarations.gms:41,45` |

**Equation bodies vs the doc's rendered formulas**

- `q52_emis_co2_actual` quoted verbatim at `modules/52_carbon/normal_dec17/equations.gms:16-19` — ✅ exact, including the `emis_land` domain and `m_timestep_length`.
- `q59_som_target_cropland` 4-term expansion (`:126-131`) vs `modules/59_som/cellpool_jan23/equations.gms:20-27` — ✅ all four terms and the `× f59_topsoilc_density` factor.
- `q59_som_pool` (`:373-375`) vs `.../equations.gms:46-52` — ✅; `p59_carbon_density` is genuinely the legacy density (`= pc59_som_pool/pcm_land`, `.../presolve.gms:28`).
- `q59_carbon_soil` = topsoil + subsoil (`:557`) vs `.../equations.gms:61-64` — ✅.
- `i59_lossrate = 1 - 0.85**m_yeardiff` (`.../preloop.gms:45`) and the 56/80/96 % table at `:399-404` — ✅ recomputed.
- `i59_subsoilc_density = fm_carbon_density(…,"other","soilc") − f59_topsoilc_density` (`:94`) vs `.../preloop.gms:12` — ✅.
- `m_growth_vegc` at `core/macros.gms:18` (`:448`) and `m_timestep_length` at `core/macros.gms:51` (`:768`) — ✅ character-exact.
- `i59_cratio = FLU × FMG × FI × F_irr`, defaults `full_tillage` / `medium_input` (`:136-140`, `:420-433`) vs `.../preloop.gms:52-55, 60-67` — ✅.

**FRA-2025 calibration block (`:180` / `:479`, identical text)** — every citation exact:
`s52_growingstock_calib = 1` (`modules/52_carbon/normal_dec17/input.gms:46`; absent from `config/default.cfg` ✅
positive-controlled); overwrites `preloop.gms:71-73` (secdforest) and `:114-116` (plantation); region-average
`m` `:29-30`; "below LPJmL potential in most regions" `input.gms:47`; uncalib snapshots `start.gms:43-44`.
Uncalibrated readers: M14 `presolve.gms:66`, M29 `preloop.gms:46,48`, M32 `presolve.gms:59,61,68`, M35
`presolve.gms:242` + `:117`. Calibrated readers: M14 `presolve.gms:44`, M35 blend `presolve.gms:248-252`,
harvest bound `:177-180`. `q35_prod_secdforest` reads calibrated `im_growing_stock`
(`modules/35_natveg/pot_forest_may24/equations.gms:147`) while `q35_carbon_secdforest` reads the blend (`:51`) —
the §3.6 caveat-2 "unverified lead" is accurately flagged as such.

**Sets** — `c_pools` `core/sets.gms:324-325`; `emis_oneoff` `:314-318` (21 = 7×3 ✅); `emis_land` `:332-354`
(exact range ✅); `peatland` in `emis_annual` `:322`.

**MACC applicability (§7.4)** — all five claims verified: M53 mitigation at
`modules/53_methane/ipcc2006_aug22/equations.gms:29,52,63`; `q53_emissions_resid_burn` `:70-72` carries none;
`maccs_ch4 / rice_ch4, ent_ferm_ch4, awms_ch4 /` at `modules/57_maccs/on_aug22/sets.gms:28-29`; M51 AWMS-only
MACC at `modules/51_nitrogen/rescaled_jan21/equations.gms:71` with the `n_pollutants_direct` comment at
`:62-64`; `q51_emissions_inorg_fert` `:30-39` MACC-free; M50 NUE uplift at
`modules/50_nr_soil_budget/macceff_aug22/presolve.gms:54-64`; `emis_source_n51`
(`modules/51_nitrogen/rescaled_jan21/sets.gms:15-16`, no `rice`) with `.fx`/`.lo`/`.up` at `preloop.gms:8-10`.
**This section is the strongest part of the doc.**

**Peatland (§10.2 item 7)** — `q58_peatland_emis` at `modules/58_peatland/v2/equations.gms:91-92` populating
`vm_emissions_reg(i,"peatland",poll58)`; realization prose `realization.gms:8-17`; defaults
`config/default.cfg:1874` (`v2`) and `:1931` (`s58_fix_peatland = 2020`); peat absent from `c_pools`. ✅

**Realization names** — `52_carbon/normal_dec17`, `59_som/cellpool_jan23`, `56_ghg_policy/price_aug22`,
`34_urban/exo_nov21`, `35_natveg/pot_forest_may24`, `32_forestry/dynamic_may24`, `29_cropland/detail_apr24`,
`14_yields/managementcalib_aug19`, `31_past/endo_jun13`, `53_methane/ipcc2006_aug22`, `57_maccs/on_aug22`,
`51_nitrogen/rescaled_jan21`, `50_nr_soil_budget/macceff_aug22`, `58_peatland/v2` — ✅ all exist **and are the
config defaults**. **Heads-up for future rounds**: `modules/14_yields/` gained a second realization
`dynRegPastrTau_apr26` at `2c02843ec`; `managementcalib_aug19` remains the default (`config/default.cfg:357`),
so the doc's citations stay correct — but Module 14 is now a multi-realization module and any new claim about
it must state which realization.

**Illustrative arithmetic that is correct** — §8.1 immediate-emission line (56 833 Tg CO₂); §8.2 sequestration
(3 200 / 5 400 Tg C); §8.4 cost block (48 750 M USD17, 144 USD17/tC); `s59_cost_scm_recur = 65 USD17MER/ha`
(`modules/59_som/cellpool_jan23/input.gms:15`, `config/default.cfg:1994`).

---

## Deferred (no bug filed, no edit proposed)

1. `:552` §7.2 "Key Equations" repeats the one-term shorthand
   `v59_som_target(j,"crop") = Σ(crops) Area × C_ratio × Natural_density` that §3.1 (`:134`) explicitly labels
   as an earlier-version omission. Numerically it is **correct for a default run** (see B4 — terms 2-4 are all
   zero by default), so no formula bug is filed; but it is an internal inconsistency worth a cross-reference to
   §3.1 when B4 is fixed.
2. `:466-469` k ranges by Köppen class (tropical 0.05-0.08 etc.) — `modules/52_carbon/input/f52_growth_par.csv`
   is not in the tree (the module `input/` dir holds only `files`; the `.csv`/`.cs3` inputs are run-time
   products). Cannot check. Weak corroboration only: `s52_k_high_secdf = 0.1` / `s52_k_high_plant = 0.15`
   (`modules/52_carbon/normal_dec17/input.gms:47-48`) bracket the doc's ranges.
3. `:428-430` FLU/FMG/FI category names and `:437-438` the 0.69 / 1.17 example factors — values live in
   `f59_ch5_F_*.csv` / `.cs3`, untracked. The doc labels them "typical values from IPCC", so no code-provenance
   claim is made.
4. `:730` uses factor 1.17 (labelled "high input **+ manure**" at `:438`) for the SCM example, while the code's
   SCM factor is `f59_cratio_inputs(climate59,"high_input_nomanure")`
   (`modules/59_som/cellpool_jan23/preloop.gms:88-90`). Both figures are explicitly illustrative and the CSV is
   unreadable here, so I cannot say whether 1.17 is the nomanure or the manure value.
5. `:592` `im_maccs_mitigation` "(0 to ~0.3)" — depends on untracked MACC input data.
6. `:544-548` §7.2 "Receives" omits `vm_landexpansion(j,"crop")`
   (`modules/59_som/cellpool_jan23/equations.gms:91`); §7.3 "Receives" omits `vm_manure` (M55) and
   `vm_res_ag_burn` (M18). These lists do not claim exhaustiveness and have several omissions of the same kind,
   so they sit below the B8 threshold (where the sibling arrows *were* exhaustive).
7. `:760-761` R snippet passes both `select=` and `field="l"` to `readGDX`, and `field="l"` on the *parameter*
   `pcm_carbon_stock`. `readGDX` is `gdx`/`gdx2` API, outside this repo — not assessed. The GDX symbols it
   names do exist: `ov_carbon_stock` / `ov_emissions_reg`
   (`modules/56_ghg_policy/price_aug22/declarations.gms:49,51`), `ov59_som_pool` / `ov59_som_target`
   (`modules/59_som/cellpool_jan23/declarations.gms:51-52`), `ov32_land`
   (`modules/32_forestry/dynamic_may24/declarations.gms:125`).
8. `:874-878` "Module 59 models **mineral** soil carbon only" — the IPCC-2019 stock-change framing is in
   `modules/59_som/cellpool_jan23/realization.gms:9-12` and peat is absent from `c_pools`, but the word
   "mineral" appears in no `.gms` file. A very likely correct inference from the methodology, not a code claim.
9. `:987` references block cites `modules/52_carbon/normal_dec17/start.gms:8-39` for "Module 52 growth"; the
   file runs to 51 lines and the *other-land* curves sit at `:46-51`, outside the cited range. Range-truncation
   nit; the plantation and secdforest curves are inside the range. Noted in case a range-completeness checker
   wants it.
10. Two findings from the prior pass of this lens are **not** reproduced here: its deferred note claiming "the
    code comment `modules/59_som/cellpool_jan23/realization.gms:42` says 44%" — that comment is at
    **`preloop.gms:42`**, not `realization.gms:42` (which does not exist; the file is 40 lines) — and its
    conclusion "the doc is right" about the 44 %, which holds for §5.2 but **not** for §8.4 (see B7).

---

## Method notes

- Every absence claim was run as its **own standalone command** with a positive control in the same directory
  (e.g. the "no residue variable in M59" finding is paired with
  `rg -c "vm_area" modules/59_som/cellpool_jan23/equations.gms` → 3).
- `rg -n` throughout — never `rg -r` (which is `--replace` and silently mangles matches).
- Attribution claims were checked **role map first**, then confirmed by grepping both `NAME(` and `NAME.` forms
  across `modules/`. That is how `modules/56_ghg_policy/price_aug22/preloop.gms:11`
  (`vm_carbon_stock.l = pcm_carbon_stock`, invisible to a `vm_carbon_stock(` grep) was found and correctly
  classified as an initialisation rather than a populator.
- Data-flow direction was re-derived at **both** endpoints for the M52↔M56 claim rather than inherited.
- Every finding carried over from the prior pass at this path was re-derived from source in this session before
  being filed; the two that did not survive re-derivation are listed in Deferred item 10.
