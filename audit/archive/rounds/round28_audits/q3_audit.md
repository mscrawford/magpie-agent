# Audit Report: Q3 (Urban Land Representation — Modules 34, 10, 52)

**Round**: 28
**Auditor**: Opus (adversarial)
**Verification worktree**: `/tmp/magpie-develop-r28/` @ `ee98739fd` (origin/develop)
**Answer file**: `audit/archive/rounds/round28_answers/q3_answer.md`

### Overall Verdict: MOSTLY ACCURATE
### Accuracy Score: 8/10

---

## Mechanical Checks

| # | Check | Result | Note |
|---|---|---|---|
| M1 | File:line citations present | PASS | Abundant `modules/XX/realization/file.gms:NN` citations |
| M2 | Active realization stated | PASS | States `exo_nov21` is default and matches config |
| M3 | Variable prefixes valid | PASS | `vm_*`, `i34_*`, `s34_*`, `v34_*`, `q34_*`, `q10_*`, `q52_*` all valid |
| M4 | Epistemic badges per claim | PARTIAL | Only one 🟢 badge (in closing); inline claims lack badges. Informational, not a content error |
| M5 | Confidence tier matches depth | PASS | 🟢 closing cites docs + config read this session |
| M6 | Closing source statement | PASS | "Verified against module_34.md and ... config/default.cfg" |

---

## Verified Claims (correct)

- **Default realization `exo_nov21`**: `config/default.cfg:1126` → `cfg$gms$urban <- "exo_nov21"  # def = exo_nov21`; scenario `cfg$gms$c34_urban_scenario <- "SSP2"` at :1129. ✓
- **Exogenous**: confirmed by `realization.gms:12` ("Urban land is exogenous and does not interact with other model dynamics, except for reducing available non-urban land pool"). ✓
- **Regional hard constraint** `q34_urban_land(i2)`: `modules/34_urban/exo_nov21/equations.gms:30-31` — `sum(cell(i2,j2), vm_land(j2,"urban")) =e= sum((ct,cell(i2,j2)), i34_urban_area(ct,j2))`. ✓ (=e= equality, exact match)
- **Cell-level soft penalty**: `q34_urban_cost1` (eq:17-18), `q34_urban_cost2` (eq:20-21), `q34_urban_cell` → `vm_cost_urban(j2)` (eq:25-26); answer's span "17-26" correct. ✓
- **Punishment scalar** `s34_urban_deviation_cost = 1e+06` USD17MER/ha: `input.gms:13`. ✓ (answer's "1e6 USD17MER/ha" matches the source comment exactly)
- **First-timestep fix** `vm_land.fx(j,"urban") = i34_urban_area(t,j)`: `presolve.gms:11`. ✓
- **Carbon fix** `vm_carbon_stock.fx(j,"urban",ag_pools,stockType) = 0;`: `presolve.gms:8`. ✓ Verbatim.
- **`ag_pools` = above-ground only** `{vegc, litc}`: `modules/56_ghg_policy/price_aug22/sets.gms:209-210`. The answer's nuanced point — M34 fixes only ag_pools (vegc+litc), which is *why* soilc is handled separately in M52 — is CORRECT and well-reasoned. Strong claim, code-accurate.
- **`vm_carbon_stock` declared in M56** (not M52): `modules/56_ghg_policy/price_aug22/declarations.gms:34`. ✓ Matches G2 regression ground truth.
- **M10 land balance** `q10_land_area(j2)`: `modules/10_land/landmatrix_dec18/equations.gms:13-15` — `sum(land, vm_land(j2,land)) =e= sum(land, pcm_land(j2,land))`. ✓ Answer's GAMS block faithful.
- **`land` set = 7 types** in exact order `crop, past, forestry, primforest, secdforest, urban, other`: `core/sets.gms:251`. ✓ (set-based sum preserved, not enumerated — avoids the R16 Major anchor)
- **Competes with all land types / M10 does not restrict urban**: `module_10.md:406-409` ("Does NOT Restrict Urban Land ... Total land conservation still enforced"). Answer's paraphrase accurate. ✓
- **Transition matrix** `vm_lu_transitions(j,land_from,land_to)` (declared `10_land/.../declarations.gms:23`); `q10_transition_to` (eq:19-21), `q10_transition_from` (eq:23-25); answer's span "19-25" correct. ✓
- **M52 urban soilc workaround**: `fm_carbon_density(t_all,j,"urban","soilc") = fm_carbon_density(t_all,j,"other","soilc")` at `modules/52_carbon/normal_dec17/input.gms:35` (comment 33-34). Answer's "input.gms:33-35" correct; corroborated by `module_52.md:67,1000`. ✓
- **M52 emission eq** `q52_emis_co2_actual(i2,emis_oneoff)`: `equations.gms:16-19`. ✓ Answer's quoted block (LHS `vm_emissions_reg(i2,emis_oneoff,"co2_c")`, the pcm−vm difference over `m_timestep_length`) faithful.
- **LUH3-unpublished caveat**: `realization.gms:8` — "LUH3: publication not yet available"; LUH2v2 = Hurtt 2020. Answer correctly distinguishes LUH2v2 (documented) from LUH3 (pending). ✓
- **`sm_fix_SSP2` SSP2-freeze logic** (`preloop.gms:10-14`): `sm_fix_SSP2` is a real scalar (`09_drivers/aug17/input.gms:22`, = 2025). ✓
- **Input file** `f34_urbanland.cs3`: confirmed `input.gms:18`. ✓

---

## Bugs Found

### Q3-B1
- **Severity**: Minor
- **Class**: 10 (Stale/off-by-few file:line citation)
- **Trigger**: §1 Minor — "Off-by-few line citation where adjacent lines say similar things"
- **Claim in answer**: "Subsequent timesteps: `vm_land.lo(j,"urban") = 0`, `vm_land.l(j,"urban") = i34_urban_area(t,j)`, `vm_land.up(j,"urban") = Inf` ... (`presolve.gms:12-14`)."
- **Reality in code**: `presolve.gms` line 12 = `else`, line 13 = `.lo`, line 14 = `.l`, line 15 = `.up`. The three listed assignments are at lines **13-15**. The cited range 12-14 includes the `else` keyword and *excludes* `vm_land.up(j,"urban") = Inf` (line 15), which the answer explicitly lists.
- **File evidence**: `modules/34_urban/exo_nov21/presolve.gms:13-15`:
  ```
  13:  vm_land.lo(j,"urban") = 0;
  14:  vm_land.l(j,"urban") = i34_urban_area(t,j);
  15:  vm_land.up(j,"urban") = Inf;
  ```
- **Why Minor not Major**: off-by-one within the same contiguous presolve block; lines 12-15 are the same `if(ord(t)=1...else...)` structure. A reader following the citation lands in the right block. The doc (`module_34.md:511`) cites this correctly ("(lines 13-14); ... (line 15)") — the answerer drifted, the doc did not.
- **Anchor reference**: resembles R20 citation-drift anchor but far milder (1 line, same block, vs 5-20 lines across the file).

### Q3-B2
- **Severity**: Minor
- **Class**: 12 (Content-level citation mismatch)
- **Trigger**: §1 Minor — "Off-by-few line citation where adjacent lines say similar things" (tie-breaker pulls down from the Major "citation drift to adjacent but different content"; `tier_uncertainty: true`)
- **Claim in answer**: "The `emis_land` mapping includes `urban_vegc`, `urban_litc`, `urban_soilc` (docs: `core/sets.gms:314-318`)."
- **Reality in code**: `core/sets.gms:314-318` is the **`emis_oneoff(emis_source)` SET** definition (header at :314, members through :318, with `urban_vegc, urban_litc, urban_soilc` listed at :318). The **`emis_land(emis_oneoff,land,c_pools)` MAPPING** the prose names is at `core/sets.gms:332-381`, with urban entries at lines **348-350** (`urban_vegc . (urban) . (vegc)` etc.). The answer attached the emis_oneoff line range to a claim about emis_land.
- **File evidence**:
  - `core/sets.gms:314` `emis_oneoff(emis_source) oneoff emission sources`; `:318` `urban_vegc, urban_litc, urban_soilc, other_vegc, other_litc, other_soilc /`
  - `core/sets.gms:332` `emis_land(emis_oneoff,land,c_pools) Mapping between land and carbon pools`; `:348-350` urban mappings.
- **Why Minor not Major**: (a) the substantive claim — urban pools participate in emis_land — is TRUE (verified at :348-350); (b) the cited lines 314-318 DO contain the exact named tokens (`urban_vegc/litc/soilc` at :318), so a reader following the citation sees the right names; the only error is that those names live in the `emis_oneoff` set there, not the `emis_land` mapping. The misdirection is about *which construct*, not *whether the tokens exist*. Borders Major (named set ≠ cited set) → `tier_uncertainty: true`.
- **Root cause**: answerer_confabulation (citation-block merge). The DOC is correct and unambiguous: `module_52.md:329` cites `emis_oneoff` set as `core/sets.gms:314-318`; `module_52.md:338` cites `emis_land` set as `core/sets.gms:332-335`. The answerer pulled the emis_oneoff line range while writing about emis_land. NOT a doc error.

---

## Latent Doc Bugs (§1.5)

**None recorded.** The answer's load-bearing claims rest on docs that are correct vs current develop code:

- **emis_oneoff vs emis_land citations** (`module_52.md:329` / `:338`): the doc correctly separates them (314-318 vs 332-335). The Q3-B2 error is the *answerer's* merge, not a doc fault — so it is scored against the answer (Minor) and there is no `doc_error_answerer_beat_it`.
- **LUH2/LUH3 MINOR anchor**: the anchor concerns the **static** realization (`static/realization.gms:9` says "1995 from the LUH2 data") while config default (`exo_nov21`) is LUH3 (`exo_nov21/realization.gms:8`). This answer is about the DEFAULT exo_nov21 and correctly cites LUH3 (and correctly distinguishes LUH2v2 Hurtt 2020 from LUH3 pending). It never touches the static realization, so the anchor is not tripped and no doc bug is implicated. `module_34.md` represents both realizations' data sources correctly per-realization (`:47` LUH3 for exo_nov21; `:55` LUH2 for static).
- **Urban soilc workaround** (`module_52.md:67-69, 1000-1002`): matches code (`input.gms:35`). No drift.
- **vm_carbon_stock declared in M56** (G2 regression ground truth): `module_52.md:423` correctly attributes populators (29/31/32/34-fixed-to-0/35/59) and the answer matches code. No drift.

---

## Missing Nuances

- The `q34_urban_land` regional constraint is the HARD piece; the answer correctly frames cell-level allocation as soft (punishment cost), so calling urban "exogenous" is defensible — but strictly, cell-level `vm_land(j,"urban")` is an optimization variable with soft incentives, not a fixed input (except t=1, where `.fx` makes it truly exogenous). The answer handles this well (lines 21-24) — noted as a strength, not a gap.
- The answer states urban expansion is "one-way" (cannot shrink). This rests on `i34_urban_area` being monotonically increasing across SSPs plus the regional `=e=` constraint — a data-driven property, not a hard code constraint (`vm_land.lo = 0` permits shrinkage in principle). The answer attributes it to `module_34.md, Limitation 4` and frames it "in practice," which is accurate. Minor over-confidence avoided.

---

## Summary

A strong, code-faithful answer. All substantive claims verify against develop `ee98739fd`: default realization, exogenous nature, the hard regional `q34_urban_land` constraint, the soft cell-level punishment-cost trio with the 1e+06 USD17MER/ha scalar, the t=1 `.fx`, the `vm_carbon_stock` zero-fix on `ag_pools` (correctly identified as vegc+litc above-ground), the M56 declaration site, the 7-way `q10_land_area` land sum with the land set preserved as a set (not enumerated), the M52 urban-soilc→other workaround at `input.gms:35`, the `q52_emis_co2_actual` formula, and the LUH3-unpublished caveat with the LUH2v2/LUH3 distinction. The answer's recognition that ag_pools excludes soilc — and that this is precisely why M52 needs the soilc workaround — is a genuinely insightful, code-correct synthesis.

Two Minor citation defects: (B1) `presolve.gms:12-14` should be 13-15 (off-by-one, excludes the `.up=Inf` it lists); (B2) the `emis_land` mapping was cited as `core/sets.gms:314-318`, which is actually the `emis_oneoff` set (mapping is at 332-381 / urban at 348-350), though those lines do contain the named tokens and the claim is true. Both are citation-precision issues, not content errors — neither would lead a user to a wrong action.

**Score**: 10 − 1 (B1 Minor) − 1 (B2 Minor) = **8/10**.

Doc-quality note: bugs are exclusively `answerer_confabulation` (citation imprecision against correct docs). No `doc_error` / `doc_error_answerer_beat_it` → for `doc_quality_mean`, this question would be EXCLUDED (its bugs are pure answerer noise; the docs are clean).
