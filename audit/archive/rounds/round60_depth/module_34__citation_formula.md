# Depth audit — `modules/module_34.md` — lens: citation_formula

**Round**: 60 (depth) · **Auditor lens**: citation_formula (entry via exact file:line citations; equation-formula fidelity)
**Ground truth**: MAgPIE `develop` read-only worktree · **Default realization**: `exo_nov21` (confirmed `config/default.cfg:1147` — `cfg$gms$urban <- "exo_nov21"`)
**Claims mechanically verified**: 63 (31 unique file:line citations × existence/range/token + 5 equation formulas verbatim + 9 default/parameter checks + 12 attribution/role-map checks + 6 count checks)

---

## 1. Citation sweep (mechanical)

All 31 unique `*.gms:NN` citations in the doc were resolved against `develop`. Files and line-ranges:

| Cited | Exists | In range | Token at line | Verdict |
|---|---|---|---|---|
| `module.gms:8-14` | ✅ (19 L) | ✅ | `@title Urban Land` … `@authors` | OK |
| `realization.gms:8` | ✅ (24 L) | ✅ | `@description Urban Land based on LUH3 (LUH2v2: Hurtt 2020, LUH3: publication not yet available) cellular (0.5 degree)` | OK |
| `exo_nov21/realization.gms:8-12` | ✅ | ✅ | description + start of `@limitations` | OK |
| `static/realization.gms:8-9`, `:8-14` | ✅ (20 L) | ✅ | `urban land remains static over time` / `1995 from the LUH2 data` | OK |
| `equations.gms:8-14` | ✅ (35 L) | ✅ | `*' @equations` block | OK |
| `equations.gms:17-18` | ✅ | ✅ | `q34_urban_cost1(j2) ..` | OK |
| `equations.gms:20-21` | ✅ | ✅ | `q34_urban_cost2(j2) ..` | OK |
| `equations.gms:25-26` | ✅ | ✅ | `q34_urban_cell(j2) ..` | OK |
| `equations.gms:30-31` | ✅ | ✅ | `q34_urban_land(i2) ..` | OK |
| `equations.gms:34-35` | ✅ | ✅ | `q34_bv_urban(j2,potnatveg) ..` | OK |
| `input.gms:8` | ✅ (20 L) | ✅ | `$setglobal c34_urban_scenario  SSP2` | OK |
| `input.gms:13` | ✅ | ✅ | `s34_urban_deviation_cost … / 1e+06 /` | OK |
| `sets.gms:9-10` | ✅ (12 L) | ✅ | `urban_scen34` / `/ SSP1, SSP2, SSP3, SSP4, SSP5 /` | OK |
| `scaling.gms:8` | ✅ (13 L) | ✅ | `vm_cost_urban.scale(j) = 1e3;` | OK |
| `scaling.gms:9-10` | ✅ | ✅ | `*v34_cost1.scale(j) = 1e-4;` / `*v34_cost2…` | OK |
| `preloop.gms:9-15`, `:10-11`, `:10-14`, `:12-13`, `:17`, `:20-21` | ✅ (21 L) | ✅ | loop / `sm_fix_SSP2` branch / else-branch / `pcm_land(j,"urban") = i34_urban_area("y1995",j);` / `vm_bv.l(...)` | OK |
| `presolve.gms:8`, `:10-11`, `:11`, `:13`, `:14`, `:11-14` | ✅ (16 L) | ✅ | `vm_carbon_stock.fx(...)=0` / `if(ord(t)=1,` / `vm_land.fx` / `vm_land.lo` / `vm_land.l` | OK |
| `presolve.gms:12-14` (doc:254) | ✅ | ⚠️ | 3rd bullet (`vm_land.up = Inf`) lives at **line 15** | **BUG-5** |
| `static/presolve.gms:9`, `:9-14` | ✅ (14 L) | ✅ | `vm_land.fx(j,"urban") = pcm_land(j,"urban");` | OK |
| `cross_module/land_balance_conservation.md` §5.6 | ✅ | ✅ | heading at line 331 | OK |

**No citation-drift-to-different-content found.** The doc's file:line layer is in unusually good shape — 30 of 31 citations resolve to exactly the claimed token.

## 2. Formula fidelity (all 5 equations)

All five equation formulas transcribed in the doc are **verbatim-exact** against `modules/34_urban/exo_nov21/equations.gms` (17-18, 20-21, 25-26, 30-31, 34-35). No set-expansion, no truncation, no invented terms. Equation count 5/5 matches `declarations.gms:18-24`.

The defects below are therefore **not** citation/formula defects — they are semantic over-reach *around* correct citations (the doc cites `presolve.gms:8` correctly and then mis-states what that line does), plus one wrong dependency set.

---

## 3. Bugs

### BUG-1 — Critical — `mechanism` — urban carbon stocks are **not** all zero; only the above-ground pools are

**Doc** (module_34.md:28): "**Fixes urban carbon stocks to zero** (no data available on urban land carbon density) (`presolve.gms:8`)"
Same error recurs at module_34.md:33, 198, 288-289, 304, 359-361, 366, 473-474, 545.

**Code**: `modules/34_urban/exo_nov21/presolve.gms:8` reads

```
vm_carbon_stock.fx(j,"urban",ag_pools,stockType) = 0;
```

`ag_pools` is a **strict subset** of `c_pools`: `modules/56_ghg_policy/price_aug22/sets.gms:209-210` → `ag_pools(c_pools) Above ground carbon pools / vegc, litc /`. `c_pools` = `/vegc,litc,soilc/` (`core/sets.gms:324-325`). So M34 zeroes **vegc + litc only**; `soilc` is untouched.

Urban `soilc` is endogenously computed in the **default** SOM realization (`config/default.cfg:1937` → `cfg$gms$som <- "cellpool_jan23"`):

```
q59_carbon_soil(j2,land,stockType) ..
    vm_carbon_stock(j2, land,"soilc",stockType)
    =e= v59_som_pool(j2, land) + vm_land(j2, land) * sum(ct,i59_subsoilc_density(ct,j2));
```
(`modules/59_som/cellpool_jan23/equations.gms:61-64`, no `$`-condition; `land` = `/ crop, past, forestry, primforest, secdforest, urban, other /`, `core/sets.gms:250-251`.)

Module 52 sets the urban soil-carbon **density** explicitly and non-zero: `modules/52_carbon/normal_dec17/input.gms:35` — `fm_carbon_density(t_all,j,"urban","soilc") = fm_carbon_density(t_all,j,"other","soilc")`, with the comment *"Fix urban area soilc to natural land soilc as long as preprocessed fm_carbon_density does not provide meaningful numbers for urban."*

And urban soil carbon **is** an emission source that is both accounted and priced: `core/sets.gms:313-318` puts `urban_soilc` in `emis_oneoff`; `core/sets.gms:350` maps `urban_soilc . (urban) . (soilc)` in `emis_land`; `q52_emis_co2_actual` (`modules/52_carbon/normal_dec17/equations.gms:16-19`) and `q56_emis_pricing_co2` (`modules/56_ghg_policy/price_aug22/equations.gms:19-22`) both sum over `emis_land(emis_oneoff,land,c_pools)` — i.e. over `urban_soilc`.

Corroboration from the module's own header: `modules/34_urban/module.gms:12` — "It describes urban settlement areas and **estimates their corresponding carbon content** and biodiversity values."

**Harm**: a user reading this doc would conclude urban land is carbon-inert, exclude it from an emissions/GHG-pricing analysis, and mis-attribute the CO2 signal from cropland→urban or forest→urban transitions. The doc's "Carbon Balance: ⚠️ LIMITATION — Urban land carbon set to **ZERO**" (line 304) and "All Other Laws: ❌ Does NOT participate" framing would send a modeller looking in the wrong module.

**Verify**: `rg -n 'vm_carbon_stock\.fx' modules/ --glob '*.gms'` → only two hits for urban, both `…,"urban",ag_pools,stockType) = 0` (`34_urban/exo_nov21/presolve.gms:8`, `34_urban/static/presolve.gms:10`); `rg -n -A4 'ag_pools\(c_pools\)' modules/56_ghg_policy/price_aug22/sets.gms` → `/ vegc, litc /`.

**Fix**: replace every "urban carbon stocks fixed to zero" with the scoped statement — *"M34 fixes only the above-ground pools to zero: `vm_carbon_stock.fx(j,"urban",ag_pools,stockType) = 0` with `ag_pools = {vegc, litc}` (`modules/56_ghg_policy/price_aug22/sets.gms:209-210`). Urban **soil** carbon is endogenous, computed by Module 59 (`q59_carbon_soil`, default `cellpool_jan23`) on a density copied from `other` land (`modules/52_carbon/normal_dec17/input.gms:35`), and `urban_soilc` is a live `emis_oneoff` source in `q52_emis_co2_actual` / `q56_emis_pricing_co2`."* Rewrite Limitation §2 (line 359-368) accordingly — the real limitation is *zero above-ground urban carbon + urban soil carbon proxied by "other" land*, not zero urban carbon. Flip the "Carbon Balance ❌/⚠️" line at 304 to PARTICIPANT-with-caveat.

---

### BUG-2 — Major — `set_membership` — `vm_carbon_stock(j,"urban",*) = 0` wildcard over-expands the fixed slice

**Doc** (module_34.md:473-474): "**Module 52 (Carbon)**: Receives `vm_carbon_stock(j,"urban",*) = 0` for carbon emissions accounting" / "**Module 56 (GHG Policy)**: Receives `vm_carbon_stock(j,"urban",*) = 0` for emission pricing". Also module_34.md:545 — "`vm_carbon_stock(j,"urban",*)` to Module 52 ✓".

**Code**: the fixed slice is `(j,"urban",ag_pools,stockType)`, i.e. the third index is restricted to `{vegc, litc}`, not `*`. The `soilc` member of the same index position is populated by M59 (see BUG-1). The `*` glyph asserts the whole pool dimension is zero — the exact set-expansion error MANDATE-15 targets.

**Verify**: `sed -n '8p' modules/34_urban/exo_nov21/presolve.gms` → `vm_carbon_stock.fx(j,"urban",ag_pools,stockType) = 0;`

**Fix**: write `vm_carbon_stock(j,"urban",ag_pools,stockType) = 0` (ag_pools = vegc, litc) in all three places, and add "…the `soilc` slice is set by Module 59, not by Module 34."

---

### BUG-3 — Major — `attribution_read` — "Upstream Modules … None" is false; M34 reads interfaces from M09, M10, M44 and M56

**Doc** (module_34.md:276): "### Upstream Modules (provide data to Module 34) — **None** - Module 34 is a data provider, reads only from external input files (LUH3)". Reinforced at module_34.md:315 ("depends on 1") and contradicted by the doc's own module_34.md:181-183 and module_34.md:320.

**Code** — every non-local identifier M34 reads, with its declaring module:

| Identifier | Declared in | M34 read site |
|---|---|---|
| `sm_fix_SSP2` | `modules/09_drivers/aug17/input.gms:22` (`/ 2025 /`) | `exo_nov21/preloop.gms:10` |
| `fm_luh2_side_layers` | `modules/10_land/landmatrix_dec18/input.gms:19` | `exo_nov21/equations.gms:35`, `preloop.gms:21` |
| `potnatveg` (set) | `modules/10_land/landmatrix_dec18/sets.gms:15` | `exo_nov21/equations.gms:34-35` |
| `pcm_land` | `10_land` (role map `declared_in`) | `exo_nov21/preloop.gms:21`; `static/presolve.gms:9,12` |
| `vm_land` | `10_land` (role map) | `exo_nov21/equations.gms:18,21,31,35` |
| `fm_bii_coeff` | `modules/44_biodiversity/bii_target/input.gms:17` (default `bii_target`, `config/default.cfg:1438`) | `exo_nov21/equations.gms:35`, `preloop.gms:21` |
| `vm_bv` | `44_biodiversity` (role map) | `exo_nov21/equations.gms:34`, `preloop.gms:20` |
| `vm_carbon_stock`, `ag_pools`, `stockType` | `modules/56_ghg_policy/price_aug22/declarations.gms:34`, `sets.gms:209,212` | `exo_nov21/presolve.gms:8` |

So M34 has **four** upstream modules (09, 10, 44, 56), not zero and not one.

**Harm**: this is the R20 anchor pattern in reverse — a modeller doing impact analysis on `fm_bii_coeff` (M44) or `fm_luh2_side_layers` (M10) would be told by this doc that M34 has no upstream dependencies and skip it. The doc's "Modification Safety: 🟢 LOW RISK … Pure data provider" (line 334-341) rests partly on the same false premise.

**Tier note**: assessed between Critical (wrong dependency set, R20 anchor) and Major; taken as **Major** under the rubric §1 tie-breaker because the doc's own "Inputs (from other modules/external)" block at lines 181-183 already names `fm_bii_coeff` "(from biodiversity module)", giving an attentive reader a same-page correction.

**Verify**: `rg -n 'sm_fix_SSP2' modules/09_drivers/aug17/input.gms` → `22:  sm_fix_SSP2 … / 2025 /`; `rg -n 'fm_bii_coeff' modules/44_biodiversity/*/input.gms` → `bii_target/input.gms:17`; role map `audit/integrated/depth_rolemap.json` → `fm_bii_coeff.declared_in = 44_biodiversity`, `read_by` includes `34`; `fm_luh2_side_layers.declared_in = 10_land`, `read_by` includes `34`.

**Fix**: replace "None" with the table above; change line 315 "depends on 1" to "depends on 4 (09, 10, 44, 56)"; qualify line 320's "Depends On: Module 09 (Drivers - LUH3 scenarios)" — M09 supplies the SSP2-freeze year `sm_fix_SSP2`, **not** the LUH3 data (that comes from `f34_urbanland.cs3`, `exo_nov21/input.gms:16-20`).

---

### BUG-4 — Minor — `citation` — range truncation at `presolve.gms:12-14`

**Doc** (module_34.md:254-257): "**t>1 (optimization timesteps)** (`presolve.gms:12-14`)" followed by three bullets, the third being "vm_land.up(j,"urban") = Inf (no upper bound)".

**Code**: `exo_nov21/presolve.gms` — line 12 `else`, 13 `.lo`, 14 `.l`, **15** `vm_land.up(j,"urban") = Inf;`. The cited range excludes the third bullet's line. (The doc gets this right at line 512, where it says "line 15" — internal inconsistency.)

**Verify**: `sed -n '10,16p' modules/34_urban/exo_nov21/presolve.gms`

**Fix**: `presolve.gms:12-15`.

---

### BUG-5 — Minor — `other` — line-of-code counts drifted (static undercounted 1.65×)

**Doc**: module_34.md:6 "**Lines of Code**: ~217 (exo_nov21), ~40 (static)"; module_34.md:552 "**exo_nov21 structure** (9 files, 217 lines)"; module_34.md:557 "**static structure** (4 files, ~40 lines)"; module_34.md:600 "**Lines Documented**: 217 (exo_nov21) + 40 (static)".

**Code**: `wc -l` over `modules/34_urban/exo_nov21/*.gms` → **220** total across **9** `.gms` files (37+35+20+42+21+16+24+13+12). `modules/34_urban/static/*.gms` → **66** total across **4** files (18+14+14+20). File counts are right; the static line count is off by 65%.

**Verify**: `wc -l modules/34_urban/exo_nov21/*.gms | tail -1` → `220 total`; `wc -l modules/34_urban/static/*.gms | tail -1` → `66 total`.

**Fix**: 220 / 66 in all four places (or drop the figures — per AGENT.md's "no figure without an artifact", a re-runnable `wc -l` command in the footer is preferable to a frozen number).

---

### BUG-6 — Informational — `other` — unbacked citation count "60+"

**Doc**: module_34.md:548 and module_34.md:601 — "**File Citations**: 60+ file:line citations throughout documentation ✓".

**Measured**: 55 backticked `…:NN` citations (31 unique); 58 backticked file references in total.

**Verify**: `grep -oE '\`[^\`]*:[0-9]+(-[0-9]+)?\`' modules/module_34.md | wc -l` → `55`.

**Fix**: state "55 file:line citations (31 unique)" or delete the figure.

---

## 4. Checked and CORRECT (recorded so a later round does not re-litigate)

- Default realization `exo_nov21` — `config/default.cfg:1147`. Doc leads with it (line 10-11). ✅
- `c34_urban_scenario` default `SSP2` — `exo_nov21/input.gms:8`; options SSP1-5 at line 9; matches `config/default.cfg:1150`. ✅
- `s34_urban_deviation_cost = 1e+06` USD17MER/ha — `exo_nov21/input.gms:13`. ✅
- All 5 formulas verbatim-exact (§2). Equation count 5 (exo) / 0 (static). ✅
- `vm_cost_urban` declared in `34_urban`, populated by 34, read by 11 — role map + `modules/11_costs/default/equations.gms:45` (`+ sum(cell(i2,j2), vm_cost_urban(j2))`). Doc's Module-11 interface claim ✅.
- `vm_bv` → M44: `urban` **is** a member of `landcover44` (`modules/44_biodiversity/bii_target/sets.gms:11`) and of `bii_class44` (line 14), and M44 reads `vm_bv(j2,landcover44,potnatveg)` at `bii_target/equations.gms:16`. The doc's hedge "(likely Module 44)" at line 165 is unnecessary but not wrong. ✅
- `q52_emis_co2_actual` and `q56_emis_pricing_co2` both exist and both read `vm_carbon_stock` directly (parallel, not serial) — the doc's line-288 framing ("Both read … M56 prices them … `vm_carbon_stock` is declared in Module 56, not Module 52") is **correct** and matches the role map (`declared_in: 56_ghg_policy`; `read_by: [52,56,59]`). Good MANDATE-21 hygiene. ✅
- Static realization: `vm_land.fx = pcm_land`, `vm_cost_urban.fx = 0`, no `i34_urban_area` — doc lines 514-515 correct. ✅
- Cross-reference `cross_module/land_balance_conservation.md` §5.6 exists (line 331). ✅
- Scaling: `vm_cost_urban.scale(j) = 1e3` active; `v34_cost1/2` scale statements commented out. ✅

---

## 5. Deferred (not verifiable / not flagged)

1. **"i34_urban_area monotonically increasing in all SSPs"** (module_34.md:386) — rests on `exo_nov21/input/f34_urbanland.cs3`, which is gitignored (only `input/files` is tracked). The "One-Way Urban Transition" limitation is a data property, not a code property: `q34_urban_land` is an equality, so urban land *would* shrink if the input trajectory shrank. Not flagged; cannot read the data.
2. **static realization LUH2 vs LUH3** — `static/realization.gms:9` says "LUH2 data set [@hurtt2018luh2]"; `config/default.cfg:1145` says "static urban land fixed on 1995 patterns from LUH3". The doc (line 55) follows `realization.gms`. Source itself is inconsistent; already the immutable Minor anchor in `audit/flywheel_rubric.md` §1 (R16, 2026-03-08). Not re-flagged.
3. **Module 39 land-conversion cost on urban** — `modules/39_landconversion/calib/presolve.gms:16` sets `i39_cost_establish(t,i,"urban") = s39_cost_establish_urban` (`config/default.cfg:1303`, 12300 USD17MER/ha), charged on `vm_landexpansion(j2,land)` at `calib/equations.gms:13`. This is a real economic cost on urban expansion that the doc's "Downstream Modules" list omits — but M39 consumes `vm_landexpansion` (an M10 product), so it is a **one-hop-transitive**, not a direct, consumer of an M34 output. Not flagged under MANDATE 17; worth a sentence in the doc's Cost Structure section if a maintainer agrees.
4. **`pcm_land(j,"urban")` readers** — M22 (`area_based_apr22/presolve_ini.gms:83,93,104`), M35 (`pot_forest_may24/presolve.gms:64,66`), M71 (`foragebased_jul23/preloop.gms:9`, via `pm_land_start`) all read the urban slice that M34 populates at `exo_nov21/preloop.gms:17`. The doc's "Provides To" list (line 318) hedges M22 as "potentially" (it is definite) and omits M35/M71. Under-specified rather than wrong; the boundary between "M34 provides pcm_land(urban)" and "core initialization provides it" is genuinely ambiguous in the code. Not flagged.
5. **Citation format** — the doc uses bare `equations.gms:17-18` rather than MANDATE-16's full `modules/34_urban/exo_nov21/equations.gms:17-18`. Consistent throughout and unambiguous given the doc's title; an editorial call for the maintainer, not a defect I will assert.
6. **"Centrality: ~30 of 46 modules"** (module_34.md:314) — no artifact behind the ranking; not independently reproducible this session.
