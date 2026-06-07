# Audit Report: M55-AWMS (manure nitrogen flow trace)

**Anchored doc**: `modules/module_55.md`
**Ground truth**: `/tmp/magpie_develop_ro` (develop worktree)
**Auditor**: Opus flywheel auditor, round 50
**Date**: 2026-06-07

---

## Overall Verdict: MOSTLY ACCURATE

## Accuracy Score: 8/10

Score = max(0, 10 - 4*0 - 2*1 - 1*0) = 8.

The answer is substantively correct across the entire manure-N flow: set architecture, `vm_manure` structure, all six M55 equation citations, the awms_prp/confinement populating equations, and all four consumers (M50, M51, M53) with their equation-level read lines. The single Major bug is a citation-drift error in the M50 row of the "Complete Consumer Table": the cited line numbers (91, 92, 117) are the markdown line positions of a reproduced code block in `module_50.md`, NOT the GAMS source lines (actual: 27, 28, 77), and one (117) is out of range for the 98-line file.

---

## Realization verification (all confirmed against config/default.cfg)

| Module | Answer's realization | config default | Match |
|---|---|---|---|
| 55 awms | `ipcc2006_aug16` | `ipcc2006_aug16` | ✓ |
| 51 nitrogen | `rescaled_jan21` | `rescaled_jan21` | ✓ |
| 50 nr_soil_budget | `macceff_aug22` | `macceff_aug22` | ✓ |
| 53 methane | `ipcc2006_aug22` | `ipcc2006_aug22` | ✓ |

`ls /tmp/magpie_develop_ro/modules/55_awms/` → `ipcc2006_aug16/`, `off/` (MANDATE 8 satisfied). All four named realizations exist and are the active defaults.

---

## Verified Claims (correct)

### Set architecture (sets.gms)
- `awms` = {grazing, stubble_grazing, fuel, confinement} at `sets.gms:10-11`. ✓ (answer cites 10-11)
- `awms_prp(awms)` = {grazing, stubble_grazing} at `sets.gms:13-14`, declared as a subset of `awms`. ✓
- `awms_conf` = {lagoon, liquid_slurry, solid_storage, drylot, daily_spread, digester, other, pit_short, pit_long} (9 members) at `sets.gms:16-17`, declared STANDALONE (not `awms_conf(awms)`). ✓ The answer's framing "awms_conf is NOT a subset of awms; parallel sets" is literally correct per the declaration, and the answer also correctly explains the functional relationship (awms_conf disaggregates the single `confinement` element). No bug.

### vm_manure structure
- `vm_manure(i, kli, awms, npk)`, positive variable, "mio t X" — `declarations.gms:19`. ✓ The answer's "mio. t nutrient" matches "mio t X" (X = npk nutrient). Third index is the full `awms` set. ✓

### M55 equations (all six line ranges correct)
- `q55_bal_manure(i2,kli,awms,npk)` `equations.gms:68-71`: `vm_manure = v55_feed_intake * (1 - im_slaughter_feed_share)`. ✓ Formula and `im_slaughter_feed_share` name verified (`equations.gms:71`).
- `q55_bal_intake_grazing_pasture` `equations.gms:37-41`, with `(1-ic55_manure_fuel_shr)` factor. ✓
- `q55_bal_intake_grazing_cropland` `equations.gms:52-56`. Developing-only 25% residue grazing: factor `(1-im_development_state)*0.25` → 0.25 when developing, 0 when developed. ✓
- `q55_bal_intake_confinement` `equations.gms:26-33`: kcr+kap+ksd + residue confinement share. Residue share `(1-(1-im_development_state)*0.25)` → 100% developed, 75% developing, complementary to stubble_grazing. ✓ (arithmetic verified)
- `q55_manure_confinement` `equations.gms:75-78`: `vm_manure_confinement = vm_manure("confinement") * ic55_awms_shr`. ✓ Disaggregates into 9 awms_conf flows.
- `q55_manure_recycling` `equations.gms:83-87`. ✓
- `ic55_awms_shr` scenario-dependent + population-weighted in presolve: verified at `presolve.gms:20,23` (`f55_awms_shr(t,i,"%c55_scen_conf%",...) * p55_region_shr`, where `p55_region_shr` is `im_pop_iso`-weighted). Scenario set `scen_conf55` includes ssp1-5, GoodPractice, etc. (`sets.gms:19-20`). ✓

### M51 consumers (rescaled_jan21) — all three correct
- `q51_emissions_man_crop` (`equations.gms:22-27`) reads `vm_manure_recycling(i2,"nr")` at line **25**. ✓ NUE rescaling `/(1-s51_snupe_base)*(1-vm_nr_eff(i2))` at line 26 verified. ✓
- `q51_emissionbal_awms` (`equations.gms:65-71`) reads `vm_manure_confinement(i2,kli,awms_conf,"nr")` at line **69**, summed over (kli,awms_conf). ✓ No NUE rescaling; MACC via `im_maccs_mitigation(...,"awms","n2o_n_direct")` at line 71. ✓ "5 livestock × 9 systems": kli = {livst_rum, livst_pig, livst_chick, livst_egg, livst_milk} = 5 members (`16_demand/sector_may15/sets.gms:22`); awms_conf = 9. ✓
- `q51_emissionbal_man_past` (`equations.gms:74-80`) reads `vm_manure(i2, kli, awms_prp, "nr")` at line **78**, with pasture NUE rescaling `/(1-s51_nue_pasture_base)*(1-vm_nr_eff_pasture(i2))` at line 80. ✓

### M50 consumers (macceff_aug22) — concept correct, prose citations correct, table citations WRONG (see bug)
- `q50_nr_inputs` (prose cite `equations.gms:22-32` — CORRECT) reads `vm_manure_recycling(i2,"nr")` at GAMS line **27** and `sum(kli, vm_manure(i2,kli,"stubble_grazing","nr"))` at GAMS line **28**. ✓ concept
- `q50_nr_inputs_pasture` (prose cite `equations.gms:74-80` — CORRECT) reads `sum(kli,vm_manure(i2,kli,"grazing","nr"))` at GAMS line **77**. ✓ concept
- "M50 reads the awms_prp elements of vm_manure directly. It does NOT read vm_manure_confinement." ✓ verified by grep.

### M53 consumer (ipcc2006_aug22) — correct
- `q53_emissionbal_ch4_awms` (`equations.gms:48-52`) reads `sum(kli, vm_manure(i2,kli,"confinement","nr"))` at line **50** — the AGGREGATE confinement element of `vm_manure`, NOT `vm_manure_confinement`. ✓ This is a subtle and correct distinction.
- Enteric-fermentation CH4 uses `vm_feed_intake`, `q53_emissionbal_ch4_ent_ferm` (`equations.gms:21-29`). ✓

### Consumer-set completeness (MANDATE 13 + 17 + 20)
- `rg "vm_manure\("` across all modules: equation-level reads ONLY in M50 (28, 77), M53 (50), M51 (78). Plus M55 own producer lines. ✓ The answer's consumer set {M50, M51, M53} is COMPLETE.
- `rg "vm_manure\."` (solution-level): only M55's own postsolve (output recording) and `off` realization preloop `.fx=0`. No hidden `.l/.lo` consumer in another module. ✓ MANDATE 20 satisfied — no phantom omission.
- All listed consumers are DIRECT equation-level reads (MANDATE 17 satisfied — no transitive mislabeling).
- `vm_manure_recycling` consumers: M50 (`equations.gms:27`), M51 (`equations.gms:25`). ✓ matches answer.
- `vm_manure_confinement` consumers: M51 only (`equations.gms:69`), plus M55 internal use in q55_manure_recycling (`equations.gms:86`). ✓ matches answer.

---

## Bugs Found

### Bug M55-B1 — M50 consumer-table line citations are doc-markdown lines, not GAMS source lines
- **Bug ID**: M55-B1
- **Severity**: Major
- **Class**: 10 (Stale/wrong file:line citation)
- **Trigger** (§1 Major): "File:line citation drift to *adjacent* but different content (would mislead a careful reader)" + the line-117 instance is out-of-range (file has 98 lines).
- **Claim in answer** (Complete Consumer Table):
  - `vm_manure(i,kli,"stubble_grazing","nr")` → `q50_nr_inputs` → M50 → `equations.gms:92`
  - `vm_manure(i,kli,"grazing","nr")` → `q50_nr_inputs_pasture` → M50 → `equations.gms:117`
  - `vm_manure_recycling(i,"nr")` → `q50_nr_inputs` → M50 → `equations.gms:91`
  - Answer's own note: "M50 line numbers are from `module_50.md §3.1-3.2`".
- **Reality in code** (`modules/50_nr_soil_budget/macceff_aug22/equations.gms`):
  - `vm_manure_recycling(i2,"nr")` is at line **27** (not 91)
  - `sum(kli, vm_manure(i2,kli,"stubble_grazing","nr"))` is at line **28** (not 92)
  - `sum(kli,vm_manure(i2,kli,"grazing","nr"))` is at line **77** (not 117)
  - The file is **98 lines long**, so `equations.gms:117` is OUT OF RANGE; `equations.gms:91-92` fall inside the `q50_nr_cost_fert` / atmospheric-deposition region, i.e. unrelated content.
- **Root cause**: `answerer_confabulation`. The numbers 91/92/117 are the MARKDOWN line positions of a reproduced GAMS code block inside `module_50.md` (the block at doc-lines 85-96 and 113-120; `vm_manure_recycling` lands on doc-line 91, stubble on doc-line 92, grazing on doc-line 117). The answerer copied the markdown line positions and presented them as `equations.gms:` source citations. The `module_50.md` doc itself is CORRECT — its section headers (`module_50.md:83`, `:111`) explicitly cite `equations.gms:22-32` and `equations.gms:74-80`, the right GAMS ranges. The answerer ignored the correct header range and used the inner code-block line positions. This is NOT a doc error.
- **Internal contradiction**: the answer's PROSE section (M50 Consumers) cites the correct ranges `equations.gms:22-32` and `equations.gms:74-80`; only the summary TABLE drifted. A careful reader gets conflicting line numbers from the same answer.
- **Anchor reference**: R20 (citation drift, 13 line-number drifts bundled as one Major) + MANDATE 16 (post-merge line numbers; out-of-range/wrong-content citation). Bundled here as ONE Major (single class, single root cause, three instances), consistent with the R20 anchor's treatment of 13 drifts as one Major.

---

## Latent doc bugs (recorded independent of answer score)

### Latent M55-L1 — module_55.md "Outputs → To Module 51" cites M55 producer lines, not M51 consumer lines
- **Severity**: Major (by future-reader harm) — `tier_uncertainty: true`
- **Class**: 15 (latent doc error, answer beat it)
- **Doc location**: `modules/module_55.md:264-265`
  - Line 264: ``- `vm_manure_confinement(i,kli,awms_conf,npk)`: ... (`equations.gms:76`)`` under heading "**To Module 51 (Nitrogen)**"
  - Line 265: ``- `vm_manure(i,kli,awms_prp,npk)`: ... (`equations.gms:69`)`` under the same heading
- **Code reality**: lines 76 and 69 (path-less, so they resolve to the anchor module M55) are the M55 PRODUCER lines (`q55_manure_confinement` LHS at `55_awms/.../equations.gms:76`; `q55_bal_manure` at `:69`). M51's actual CONSUMER reads are at `51_nitrogen/rescaled_jan21/equations.gms:69` (confinement, q51_emissionbal_awms) and `:78` (awms_prp, q51_emissionbal_man_past). Placing producer-line numbers under a "To Module 51" (consumer) heading is misleading; a reader following `equations.gms:69` for the awms_prp read would, in the M51 file, land on the confinement equation (line 69) rather than the man_past equation (line 78) — a confusing coincidence that the doc's structure invites.
- **Why latent**: the answer was CORRECT here — it cited M51 consumer lines 69 (confinement) and 78 (awms_prp) accurately, beating the doc's ambiguous producer-line refs. Root cause `doc_error_answerer_beat_it`.
- **Mitigating context**: `module_55.md` ELSEWHERE has the correct consumer set and lines — the consumer table at `module_55.md:511-517` lists M50/M51/M53 correctly, and `module_51.md:238-239` cites `equations.gms:69` and `:78` for the M51 reads. So the bad refs are recoverable, which is why I flag `tier_uncertainty` (Major vs Minor). Fix per validate-semantic Step 5 regardless: relabel `module_55.md:264-265` as producer locations (e.g., "produced at q55_manure_confinement, `55_awms/.../equations.gms:76`; consumed by M51 at `51_nitrogen/.../equations.gms:69`") with full paths to disambiguate.

---

## Missing Nuances (not bugs)

- The answer states M55 line numbers are "documented" (🟡) but the M55 equation citations actually match current develop code exactly, so they are stronger than docs-only — they are code-accurate. Minor under-claim, not scored.
- The answer's epistemic footer is honestly 🟡 (docs-only, no code read this session) and recommends verifying against `../modules/55_awms/.../equations.gms`. That caveat is warranted but points only at the M55 file, so it would NOT have caught the M50 table drift. Informational, not separately scored.

---

## Mechanical checks

| # | Check | Result |
|---|---|---|
| M1 | File:line citations present | PASS (many) |
| M2 | Active realization stated | PASS (all 4, all match default) |
| M3 | Variable prefixes valid | PASS (vm_, v55_, ic55_, im_, f51_, f53_ all correct) |
| M4 | Epistemic badges | PASS (🟡 closing badge) |
| M5 | Confidence tier matches depth | PASS (🟡 documented, no code read claimed; honest) |
| M6 | Closing source statement | PASS ("Based on ... module_55.md, module_51.md, module_50.md") |

---

## Summary

A strong, near-complete answer. Every conceptual claim about the manure-N flow is correct: the awms/awms_prp/awms_conf set architecture and members, the `vm_manure(i,kli,awms,npk)` structure, the mass-balance formula, the four populating equations with correct developing/developed splits, and all four consumers (M50 soil budget, M51 emissions, M53 methane) — including the subtle and correct point that M53 reads the AGGREGATE `vm_manure("confinement")` rather than the 9-way `vm_manure_confinement`, and that M51 alone consumes `vm_manure_confinement`. Consumer-set completeness verified by both `vm_manure(` and `vm_manure.` greps with positive control: no phantom omissions, no transitive mislabeling.

The one Major bug: the M50 row of the summary consumer table cites markdown line positions (91, 92, 117) from a reproduced code block in `module_50.md` as if they were GAMS `equations.gms:` source lines. The real GAMS lines are 27, 28, 77; line 117 is out of range (file is 98 lines). The answer's own prose section cited the correct M50 ranges, making this an internal contradiction. Root cause: answerer misread doc-internal code-block line numbers as citations — the doc itself is correct.

One latent doc bug recorded: `module_55.md:264-265` places M55 producer-line numbers (69, 76) under a "To Module 51" consumer heading; the answer correctly cited M51's own consumer lines (69, 78), beating the doc. Fix the doc regardless (add full paths; separate produced-at from consumed-at).

**Score: 8/10** (1 Major).
