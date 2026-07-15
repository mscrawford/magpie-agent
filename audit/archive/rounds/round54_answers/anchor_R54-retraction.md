# R54-retraction — Answer

## Question
I want to run an afforestation policy scenario with `c32_aff_policy = ndcdelay`. Will that actually work, or is it silently broken? What should I watch out for?

## Answer

**It works, under the default configuration.** This is a corrected verdict — flagging that explicitly, because the documentation itself records a retracted claim in the opposite direction (see "Retraction" section below), and if you've seen that earlier claim anywhere it should be discarded.

### How `c32_aff_policy = ndcdelay` is wired

Per `modules/module_32.md` §9.2 and `modules/module_32_notes.md`:

- `c32_aff_policy` selects among `pol32 = none, npi, ndc, affexp, ndcdelay` (`sets.gms:19-20`, cited in `module_32.md`). Default is `npi`, **not** `ndcdelay` — you must set it explicitly.
- The switch is **100% data-driven** — there is no GAMS code branch for any policy. The entire selection is one table lookup documented verbatim in both files:
  ```gams
  p32_aff_pol(t,j) = round(f32_aff_pol(t,j,"%c32_aff_policy%"),6);
  ```
  (`modules/32_forestry/dynamic_may24/preloop.gms:182`)
- `ndcdelay` is described in `module_32.md` §9.2 as: "NDC afforestation with milestone target-years (≥2030) delayed by country cluster — PRISMA 'Asymmetric Roll-back': transition leaders +10y, diversifying economies +20y, fossil-dependent economies +30y (added on develop 2026-07, commit `58bde5788`)."
- Per `module_32_notes.md`: `ndcdelay` "needs no input rows at all; it is **derived in R** from the existing `ndc` rows by shifting target years ≥2030 by a country-specific PRISMA delay (`start_npi_ndc.R`)."
- The `.cs3` file this reads from (`npi_ndc_aff_pol.cs3`) is **both** a downloaded dummy (all-zero, 3 columns, per `module_32_notes.md`) **and** a run-time artifact: it is gitignored and **regenerated at run start** by `scripts/start_functions.R` under the default `cfg$recalc_npi_ndc <- "ifneeded"` (`config/default.cfg:123`, cited in `module_32_notes.md`). The regeneration guard fires whenever the on-disk file is all-zero (the shipped dummy — true for every non-`none` policy including the default `npi`) or the selected policy's column is missing. Both `affexp` and `ndcdelay` are, per the notes file, "wired into named scenario presets (`config/scenario_config.csv:51`)."
- Once established, `ndcdelay`-derived afforestation lands in the same `"ndc"` slot of the `type32` set as `npi`/`ndc`/`affexp` — there is no separate `ndcdelay` land pool. It gets the same carbon-density curve (`pm_carbon_density_secdforest_ac_uncalib`, uncalibrated natural regrowth, per `module_32.md` §4.5/§10.2), the same permanence rule, and is governed by the same two equations regardless of which policy fed the target:
  - `q32_aff_pol` (`equations.gms:74-75`): established `"ndc"`-type area + `v32_ndc_area_missing` (penalty slack) must equal the policy target each timestep.
  - `q32_ndc_aff_limit` (`equations.gms:79-80`): whenever the timestep's target flow is non-zero, natural-forest reduction in that cell must be zero.

### Retraction

`module_32_notes.md` contains a documented cautionary tale that directly matches the shape of this question, and I'm surfacing it rather than silently reusing it: *"The first version of this file asserted the opposite: that `ndcdelay` was **broken** — 'selectable but unfed', silently producing a zero policy — and recommended reporting it to the PRISMA authors."* Per the notes file, every individual premise in that earlier version was independently true (no GAMS branch exists; the on-disk `.cs3` genuinely ships with only 3 policy columns; `affexp`/`ndcdelay` genuinely appear 0 times in the shipped file's 6405 lines; neither feature commit bumped `cfg$input`) — **but the conclusion was false**, because, per the notes file, "the reasoning never left the GAMS layer: it inferred the provenance of a *gitignored, regenerated* artifact from git history alone." The regeneration guards that refute the "broken" claim (`affexp_missing`, `ndcdelay_missing` in `scripts/start_functions.R`) were added by the same commits the earlier draft was scrutinizing (`a54cd02c6`, `58bde5788`). Do not treat "silently broken" as the standing verdict for this switch — that claim was superseded in the same file that originated it.

### What to actually watch out for

1. **The one real footgun (non-default): `cfg$recalc_npi_ndc <- FALSE`.** Per `module_32_notes.md`, this lives entirely inside `if(cfg$recalc_npi_ndc=="ifneeded")` (`scripts/start_functions.R:375`) — override it to `FALSE` and regeneration is skipped, with two distinct failure modes:
   - **Freshly-downloaded `.cs3`** (the all-zero dummy) → *every* policy reads as zero, including the default `npi` and `ndc` — "the run is silently identical to `none`, and it is invisible: all the columns are present." This is described as "the bigger trap."
   - **Stale regenerated `.cs3`** predating the PRISMA/ELEVATE columns → `ndcdelay` (and `affexp`) are absent from the header, and per the notes file, "GAMS zero-fills an absent table column with no error and no warning," so `f32_aff_pol(t,j,"ndcdelay") = 0` and `p32_aff_pol = 0` everywhere.
   - This does **not** apply under the default `cfg$recalc_npi_ndc <- "ifneeded"` — only if you've explicitly overridden it.
   - Verification recipe given in `module_32_notes.md` if you want to check your own run's `.cs3` by hand: `head -5` for a `* origin: calcOutput(...)` comment (pristine dummy, un-regenerated) vs. no comment (a prior regeneration); plus an `awk` nonzero-entry count across the policy columns.

2. **Don't confuse `ndcdelay` with `s32_npi_ndc_reversal`.** Per `module_32_notes.md`, these are unrelated switches that both "read like roll-back" and *stack* if both are touched:
   | | `c32_aff_policy = ndcdelay` | `s32_npi_ndc_reversal` |
   |---|---|---|
   | What | Shifts NDC milestone target-years (≥2030) later, by country cluster | The year NPI/NDC afforestation is reversed (land released back to free bounds) |
   | Type | A `pol32` policy name | A scalar (`dynamic_may24/input.gms:48`), default **`Inf`** (never) |
   | Effect | Delays the ramp-up | Undoes it |

   `ndcdelay` delays; it does not reverse. If you want the PRISMA scenario as intended, leave `s32_npi_ndc_reversal` at its `Inf` default — changing it too stacks a reversal on top of a delay.

3. **No annual-rate cap applies to `ndc`-type (incl. `ndcdelay`) expansion.** Per `module_32.md` §4.6, the 3%/yr `s32_annual_aff_limit` constraint (`q32_co2p_aff_limit`) applies only to the `"aff"` (carbon-price-driven) type, not `"ndc"`. Delayed targets are instead reconciled via the `q32_aff_pol` equality plus the `v32_ndc_area_missing` penalty slack (priced at `s32_free_land_cost`, described elsewhere in `module_32.md` §4.1 as a "huge cost ($1M/ha)"). This means an infeasible-in-practice `ndcdelay` target does not make the model infeasible — it shows up instead as a expensive-but-finite `v32_ndc_area_missing` residual. Check `ov32_ndc_area_missing` in your output GDX rather than assuming the delayed targets were fully met.

4. **`q32_ndc_aff_limit` ties active-policy cells to zero natural-forest reduction.** Wherever `ndcdelay` produces a non-zero timestep flow in a cell, natural-forest reduction there is constrained to zero (`equations.gms:79-80`). Worth checking if you're combining `ndcdelay` with other land-competition-heavy scenario changes.

5. **General Module 32 modification-safety context** (`module_32.md` §8.1, "Modification Safety"): Module 32 is flagged 🔴 **EXTREME RISK** — rank 4 of 46 modules by centrality, participates in 2 major circular-dependency cycles (including the "most complex cycle in the model": Forestry → Croparea → Land → NatVeg → Carbon → GHG Policy → back to Forestry). This is general context, not specific to `ndcdelay`, but relevant if you're layering this switch change alongside other modifications.

## Sources
- 🟡 Documented: `modules/module_32.md` (§9.2 Afforestation Policy, §4.1, §4.6, §4.5, §8.1 Modification Safety, §10.1)
- 🟡 Documented: `modules/module_32_notes.md` (full file — regeneration mechanism, retraction narrative, `ndcdelay` vs `s32_npi_ndc_reversal` table, footgun conditions, verification recipe)
- 🟡 Documented (cross-reference, confirms `ndcdelay`/`ndc` afforestation is a separate incentive channel from the carbon-price `vm_reward_cdr_aff` reward): `modules/module_56_notes.md`
- No raw GAMS code was read this session (per task constraint); all `.gms`/`.R` line references above are as cited verbatim in the two module-32 doc files, not independently re-verified this session.
