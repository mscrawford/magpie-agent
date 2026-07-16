# Adversarial verification — module_56.md (Round 55 depth)

Target doc: `/Users/turnip/Documents/Work/Workspace/magpie/magpie-agent/modules/module_56.md` (1162 lines)
Ground truth: `/private/tmp/magpie_develop_ro` (read-only develop worktree)
Default realization (config/default.cfg:1631): `cfg$gms$ghg_policy <- "price_aug22"` — and it is the ONLY realization (`ls -d modules/56_ghg_policy/*/` → `input/`, `price_aug22/`). No realization ambiguity.
Relevant default (config/default.cfg:1835): `c56_carbon_stock_pricing <- "actualNoAcEst"`.

---

## Bug module_56:7 — "52 → 56 via vm_emissions_reg" data-flow direction

**Severity claimed:** Major | **Class:** `consumer_set` (per-slice producer/consumer ownership; data-flow direction)
**Verdict: CORRECTED** (core mechanism UPHELD and independently re-derived; the *scope* of the proposed fix is over-broad and would introduce a new error at two of the six cited lines)

### STEP A — MECHANICAL CITATION CHECK → citation_ok = TRUE

| Cited artifact | Command | Result |
|---|---|---|
| `modules/56_ghg_policy/price_aug22/equations.gms` | `test -f` / `wc -l` | EXISTS, 79 lines → 15-17 in range |
| ↳ line 15 | `sed -n '15p'` | ` q56_emis_pricing(i2,pollutants,emis_annual) ..` ✅ token present |
| ↳ line 17 | `sed -n '17p'` | `    vm_emissions_reg(i2,emis_annual,pollutants);` ✅ token present |
| `modules/52_carbon/normal_dec17/equations.gms` | `test -f` / `wc -l` | EXISTS, 19 lines → 16-19 in range |
| ↳ lines 16-19 | `cat -n` | `q52_emis_co2_actual(i2,emis_oneoff) .. vm_emissions_reg(i2,emis_oneoff,"co2_c") =e= sum((cell(i2,j2),emis_land(emis_oneoff,land,c_pools)), (pcm_carbon_stock(j2,land,c_pools,"actual") - vm_carbon_stock(j2,land,c_pools,"actual"))/m_timestep_length);` ✅ exact |
| `core/sets.gms` | `test -f` / `wc -l` | EXISTS, 362 lines |
| ↳ line 314 | `sed -n '314p'` | `   emis_oneoff(emis_source) oneoff emission sources` ✅ |
| ↳ line 320 | `sed -n '320p'` | `   emis_annual(emis_source) annual emission sources` ✅ |
| `56/price_aug22/equations.gms:19-22` (in fix) | `sed -n` | line 19 `q56_emis_pricing_co2(i2,emis_oneoff) ..`; line 22 `(pcm_carbon_stock(j2,land,c_pools,"actual") - vm_carbon_stock(j2,land,c_pools,"%c56_carbon_stock_pricing%"))/m_timestep_length);` ✅ |
| doc lines 66, 88-92, 591, 716, 1026, 1068, 1076 | `sed -n` | all in range, all contain the quoted text ✅ |

Every cited file exists, every line is in range, every line contains the claimed token. **citation_ok = true.**

### STEP C — INDEPENDENT RE-DERIVATION

**1. Set disjointness (core/sets.gms:314-321) — CONFIRMED.**
```
emis_oneoff = { crop_vegc/litc/soilc, past_*, forestry_*, primforest_*, secdforest_*, urban_*, other_* }
emis_annual = { inorg_fert, man_crop, awms, resid, man_past, som, rice, ent_ferm, resid_burn, peatland }
```
Zero overlap. Both are subsets of `emis_source`.

**2. Role map cross-check** (`audit/integrated/depth_rolemap.json`):
- `vm_emissions_reg`: declared_in **56_ghg_policy**, populated_by **[51, 52, 53, 58]**, read_by **[56, 57]**
- `vm_carbon_stock`: declared_in **56_ghg_policy**, populated_by [29,31,32,34,35,56,59], read_by **[52, 56, 59]**

The second entry is the decisive one: **52 and 56 both READ `vm_carbon_stock`** — consistent with parallel derivation, not a hand-off.

**3. BOTH-form grep, whole-repo, isolated commands (positive control passed: `rg -cn 'q56_' .../price_aug22/equations.gms` → 7).**

`rg -n 'vm_emissions_reg\(' /private/tmp/magpie_develop_ro/modules/` → producers by slice:
| Module | Slice populated | In emis_annual? |
|---|---|---|
| 52 (`normal_dec17/equations.gms:17`) | `(i2, emis_oneoff, "co2_c")` | **NO — oneoff only** |
| 51 (`rescaled_jan21/equations.gms:23,31,43,50,56,66,75,84`) | man_crop, inorg_fert, resid, resid_burn, som, awms, man_past, emis_source_n51 × N pollutants | YES |
| 53 (`ipcc2006_aug22/equations.gms:22,49,60,71`) | ent_ferm, awms, rice, resid_burn × "ch4" | YES |
| 58 (`v2/equations.gms:92`) | "peatland" × poll58 | YES |
| 57 (`on_aug22/equations.gms:38,40,48,50`) | RHS only — reader, not producer | (reader) |

Reads of `vm_emissions_reg` inside module 56 — **both forms**:
- `vm_emissions_reg(` → `declarations.gms:40` (declaration, full `emis_source`) + `equations.gms:17` (read, **`emis_annual` only**). Nothing else.
- `vm_emissions_reg.` → `postsolve.gms:13,27,41,55` (`.m/.l/.up/.lo` → `ov_emissions_reg`, full `emis_source`, **reporting only**).

⇒ In the optimization, module 56 reads `vm_emissions_reg` **only over `emis_annual`**. Module 52 writes **only into `emis_oneoff × co2_c`**. Since the sets are disjoint, **52 contributes exactly nothing to the slice 56 prices.**

**4. The parallel (not serial) LULUCF-CO2 path — CONFIRMED.**
```
52: vm_emissions_reg(i2,emis_oneoff,"co2_c") =e= Σ (pcm_carbon_stock(...,"actual") - vm_carbon_stock(...,"actual"))/m_timestep_length
56: v56_emis_pricing(i2,emis_oneoff,"co2_c")  =e= Σ (pcm_carbon_stock(...,"actual") - vm_carbon_stock(...,"%c56_carbon_stock_pricing%"))/m_timestep_length
```
Same structural form, **different stockType slice** (52: `actual`; 56: `actualNoAcEst` by default, config/default.cfg:1835). Both read `vm_carbon_stock` directly (role map read_by = [52,56,59]). Neither reads the other's output. **Parallel, not a hand-off** — the R51/MANDATE-21 pattern exactly.

**5. Doc self-contradiction — CONFIRMED.** Lines 90-92 state the bypass correctly ("CO2 pricing is calculated **directly from `vm_carbon_stock`**, intentionally **bypassing `vm_emissions_reg`**… `q56_emis_pricing_co2` does NOT [route through vm_emissions_reg]"). Line 66 contradicts it.

### Per-line adjudication of the six cited recurrences

| Line | Text | Verdict |
|---|---|---|
| **66** | `**vm_emissions_reg(i,emis_annual,pollutants)**: … from the emission modules (51 N2O, **52 LULUCF CO2**, 53 CH4, 58 peatland)` | **WRONG — fix required.** The index is explicitly narrowed to `emis_annual`, then 52 is attributed to it. 52 populates zero members of `emis_annual`. Per-slice ownership violation. |
| **716** | `**DOES price** emissions calculated by the emission modules (51, **52**, 53, 58)` | **WRONG — fix required.** 56 does not price 52's computed emissions; it recomputes the priced LULUCF CO2 itself (`q56_emis_pricing_co2`, different stockType). |
| **591** | §4.2 Inputs: `From the emission modules (51, 52, 53, 58): vm_emissions_reg(i,emis_source,pollutants)` … `**Citation:** Used in equations.gms:17` | **PARTIALLY wrong — narrow fix.** At the whole-variable (`emis_source`) level, 52 IS a genuine producer (role map + `52/equations.gms:17`). Removing 52 here would be a NEW error. The defect is the citation: `equations.gms:17` reads only `emis_annual`, which excludes 52's slice. Fix the citation/scope, keep 52 in the producer list. |
| **1026** | §12.2: `Emission modules (51, 52, 53, 58): Regional emissions by source and gas (vm_emissions_reg)` | **PARTIALLY wrong — narrow fix.** True at whole-variable level (52's oneoff slice reaches 56's `postsolve.gms:27` reporting). Misleading only if read as "priced". Add a slice qualifier; do NOT delete 52. |
| **1068** | `What It Doesn't Do: Calculate emissions (done by … 51, **52**, 53, 58)` | **Wrong for a different reason than claimed.** The parenthetical attribution to 52 is fine (52 does calculate LULUCF CO2 for reporting). The *false* part is the header claim "Module 56 doesn't calculate emissions" — `q56_emis_pricing_co2` computes a carbon-stock-difference CO2 flow itself. Same for line 714 (`Does NOT calculate emissions`). |
| **1076** | `Upstream: Emission modules (51, 52, 53, 58), … Carbon stocks (29,31,32,34,35,59 …)` | **Defensible as written.** 52 populates a 56-declared variable that 56 reports. Not upstream of *pricing*, but the line does not say "pricing". Lowest-value edit; leave or add a qualifier. |

### Why CORRECTED rather than UPHELD

Every clause of the auditor's `reality_in_code` reproduced exactly and independently — the mechanism finding is real and Major at lines 66 and 716. But the `proposed_fix` instructs the same edit at all six lines, and applying it verbatim at **591** and **1026** would strip 52 from the producer set of `vm_emissions_reg`, which the role map and `52/equations.gms:17` both prove is a **true** producer relationship (`emis_oneoff × co2_c`). That would trade one error for another. The fix must be slice-scoped, not module-scoped.

### Corrected claim to apply

> Module 52 populates `vm_emissions_reg` **only** for `emis_oneoff × co2_c` (`52_carbon/normal_dec17/equations.gms:16-19`); `q56_emis_pricing` reads `vm_emissions_reg` **only** over `emis_annual` (`56_ghg_policy/price_aug22/equations.gms:15-17`). `emis_oneoff` and `emis_annual` are disjoint (`core/sets.gms:314,320`), so 52 contributes nothing to the priced-annual slice — the annual-pricing producers are **51 (N), 53 (CH4), 58 (peatland)** only.
> Fix **line 66** (drop "52 LULUCF CO2" from the `emis_annual` attribution) and **line 716** (56 does not price 52's emissions).
> **Keep 52** in the whole-variable producer lists at **591** and **1026** — it is a real producer of the `emis_oneoff` slice, which reaches 56 only via `postsolve.gms:13,27,41,55` reporting; add a slice qualifier and fix line 591's `equations.gms:17` citation, which covers only `emis_annual`.
> Module 56 prices LULUCF CO2 via its **own** `q56_emis_pricing_co2` (`equations.gms:19-22`) reading `vm_carbon_stock` at stockType `%c56_carbon_stock_pricing%` (default `actualNoAcEst`, config/default.cfg:1835), **in parallel** with 52's `q52_emis_co2_actual` at stockType `actual` — neither hands off to the other (both are in `vm_carbon_stock`'s `read_by` set).
> Separately (beyond the auditor's finding): lines **714/1068** ("Does NOT calculate emissions") are false as stated — `q56_emis_pricing_co2` computes a carbon-stock-difference CO2 flow.
