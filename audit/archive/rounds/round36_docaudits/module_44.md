# Round 36 Doc Audit — module_44.md (Biodiversity, `bii_target`)

**Auditor**: Opus 4.8 (adversarial doc auditor)
**Date**: 2026-05-30
**Target doc**: `magpie-agent/modules/module_44.md`
**Ground truth**: develop worktree `/tmp/magpie_develop_ro` @ HEAD `ee98739fd` (Merge PR #887)
**Default realization**: `bii_target` (confirmed `config/default.cfg:1417` → `cfg$gms$biodiversity <- "bii_target"`)

---

## Overall Verdict: MOSTLY ACCURATE
## Accuracy Score: 6/10

This doc is unusually well-verified on its core spine: every equation, every interface
variable name, every per-module `vm_bv` producer attribution, every scalar default, and
~95% of file:line citations are correct against current develop. The bugs are concentrated
in (1) a stale realization list (a realization removed upstream is still presented as an
alternative), (2) one example scenario whose config would abort the model, and two minor
count/citation drifts.

Score derivation (rubric §4): 2 Major (-4) + 2 Minor (-2) = 6/10.

---

## Verified Claims (correct against code)

### Equations (all 3 correct, citations exact)
- `q44_bii` — `equations.gms:13-17` ✓. Formula `v44_bii =e= sum((cell,landcover44,potnatveg), vm_bv*i44_biome_share)/i44_biome_area_reg`, guarded `$(i44_biome_area_reg(i2,biome44) > 0)`. Doc cite `:13-17` exact.
- `q44_bii_target` — `equations.gms:22-23` ✓. (See deferred note on the `sum(ct,...)` simplification.)
- `q44_cost` — `equations.gms:28-29` ✓. `sum(cell, vm_cost_bv_loss) =e= sum(biome44, v44_bii_missing)*s44_cost_bii_missing`. Doc cite exact.

### Interface variables (declarations.gms — all citations exact)
- `vm_cost_bv_loss(j)` → `declarations.gms:10` ✓
- `vm_bv(j,landcover44,potnatveg)` → `declarations.gms:11` ✓
- `v44_bii(i,biome44)` → `declarations.gms:12` ✓
- `v44_bii_missing(i,biome44)` → `declarations.gms:13` ✓
- `p44_bii_target(t,i,biome44)` → `declarations.gms:17` ✓
- `p44_start_value(i,biome44)` → `declarations.gms:18` ✓
- `i44_biome_share(j,biome44)` → `declarations.gms:19` ✓
- `i44_biome_area_reg(i,biome44)` → `declarations.gms:20` ✓ (the word "range-rarity weighted" is on this line — doc:546 cite correct)

### Producer set for `vm_bv` (received) — CORRECT and COMPLETE
Doc claims `vm_bv` populated by 29, 30, 31, 32, 34, 35. Verified by two independent greps + positive control. Per-class attribution table (doc:371-378) is fully correct:
- M29 `detail_apr24/equations.gms`: `crop_fallow` (:77), `crop_tree` (:102) ✓
- M30 `detail_apr24/equations.gms`: `crop_ann` (q30_bv_ann :95), `crop_per` (q30_bv_per :99) ✓
- M31 `endo_jun13/equations.gms`: `manpast` (q31_bv_manpast :38), `rangeland` (q31_bv_rangeland :42) ✓
- M32 `dynamic_may24/equations.gms`: `aff_co2p` (q32_bv_aff :128), `aff_ndc` (q32_bv_ndc :133), `plant` (q32_bv_plant :138) ✓
- M34 `exo_nov21/equations.gms`: `urban` (:35) ✓
- M35 `pot_forest_may24/equations.gms`: `primforest` (q35_bv_primforest :59), `secdforest` (q35_bv_secdforest :63), `other` (q35_bv_other :68) ✓
- No other module references `vm_bv` (grep excluding the 7 known modules → empty; `core/` empty with `vm_land` positive control passing).

### Consumer of `vm_cost_bv_loss` (provided) — CORRECT and COMPLETE
Doc claims fed to Module 11 (Costs). Verified: only consumer outside M44 is `11_costs/default/equations.gms:44` (`+ sum(cell(i2,j2), vm_cost_bv_loss(j2))` inside `q11_cost_reg` → `v11_cost_reg` → `vm_cost_glo` via `q11_cost_glo:10`). Both `vm_cost_bv_loss(` and `vm_cost_bv_loss.` greps confirm no other reader. ✓

### `fm_bii_coeff` (advisory item) — CORRECT
Read by M29/M30/M31/M32/M34/M35 (both `fm_bii_coeff(` and word-boundary greps agree + `fm_luh2_side_layers` positive control). Doc treats it correctly as M44's input file `f44_bii_coeff.cs3` loaded as `fm_bii_coeff` (`input.gms:17`). M30 and M35 both read it — advisory confirmed, no wrong consumer claim in doc.

### Scalar defaults (all verified against config/default.cfg)
- `s44_bii_target = 0` (input.gms:9; cfg:1439 `#def = 0`) ✓
- `c44_bii_decrease = 1` (input.gms:10; cfg:1452 `#def = 1`) ✓ — semantics gloss "Allow BII to decrease (1=yes,0=no)" matches config comment "1 (decrease allowed)". NOT an inverted boolean.
- `s44_target_year = 2100` (input.gms:11; cfg:1423) ✓
- `s44_start_year = 2030` (input.gms:12; cfg:1420) ✓
- `s44_cost_bii_missing = 1e+06` (input.gms:13; cfg:1455 `1000000`) ✓

### Sets
- `landcover44` 13 classes (sets.gms:10-11) ✓
- `bii_class44` 9 classes (sets.gms:13-14) ✓
- `biome44` 71 members, 8 realms AA/AN/AT/IM/NA/NT/OC/PA (sets.gms:33-37) ✓ (counted)
- Age mapping: secd_young = ac0..ac30, secd_mature = ac35..ac300,acx (sets.gms:19-31) ✓

### Other citations verified
- Purpose/Core Concept `realization.gms:8-13` ✓
- "regional layer ... high resolution parallel optimization output script" quote → `equations.gms:11` ✓
- References `@olson_biome_2001`/`@purvis_chapter_2018`/`@leclere_biodiv_2018`/`@leclere_bending_2020` → `realization.gms:9-12` ✓ (all 4 keys present)
- preloop.gms:9-11 (biome share), 14-15 (regional area), 19-21 (sm_fix_SSP2 abort) ✓
- presolve.gms:8-20 (BII level update), 22-42 (target interpolation incl. ratchet 39-41) ✓
- postsolve.gms:9-36 ✓
- `bv_btc_mar21/equations.gms:16-18` (v44_bv_loss formula) ✓; `f44_rr_layer` usage ✓

---

## Bugs Found

### Bug 44-B1 — Phantom realization `bii_target_apr24` (removed upstream)
- **Severity**: Major
- **Class**: 8 (stale realization name) / 6 (count drift) — fabricated realization-list entry
- **Trigger** (§1 Major): "Fabricated count for a set/parameter/realization list."
- **doc_line**: module_44.md:10
- **Claim in doc**: "Alternatives: `bii_target_apr24` (updated BII formulation), `bv_btc_mar21` (biodiversity value with BTC approach)."
- **Reality in code**: Only TWO realizations exist: `bii_target` and `bv_btc_mar21`. `bii_target_apr24` was REMOVED. CHANGELOG.md:204: "**44_biodiversity** realisation `bii_target_apr24` removed because it is identical to `bii_target`. `bii_target` set as new default." CHANGELOG.md:178: default changed from `bii_target_apr24` to `bii_target`. The doc's parenthetical "(updated BII formulation)" is also wrong — the changelog says it was *identical* to `bii_target`, which is why it was deleted. The module.gms `$Ifi` block lists only `bii_target` and `bv_btc_mar21`. Note the doc is NOT claiming it as default (default `bii_target` is correct), so this is not Critical.
- **File evidence**: `ls /tmp/magpie_develop_ro/modules/44_biodiversity/` → only `bii_target/`, `bv_btc_mar21/`, `module.gms`; `/tmp/magpie_develop_ro/CHANGELOG.md:204`; `config/default.cfg:1414-1417`
- **verify_cmd**: `ls /tmp/magpie_develop_ro/modules/44_biodiversity/` → `bii_target  bv_btc_mar21  module.gms`; `grep -rn "bii_target_apr24" /tmp/magpie_develop_ro/` → only CHANGELOG.md hits (lines 178/204 = removal; 369/380 = original addition).
- **confirmed**: true
- **proposed_fix**: Replace line 10 with: `> Confirmed in `config/default.cfg`: `cfg$gms$biodiversity <- "bii_target"`. Only alternative: `bv_btc_mar21` (global optimization of range-rarity weighted biodiversity stock losses/gains via a price). (Note: `bii_target_apr24` was removed upstream — it was identical to `bii_target`; see CHANGELOG.)`

### Bug 44-B2 — Scenario 3 example config aborts the model (`s44_start_year = 2025`)
- **Severity**: Major (tier_uncertainty: borderline Major/Minor — the failure is a loud, safe abort, not a silent corruption)
- **Class**: 12 (content-level mismatch — example config contradicts the module's own stated validation rule)
- **Trigger** (§1 Major): "The claim is wrong in a way that misleads about behavior" — presents a runnable-looking config that cannot run.
- **doc_line**: module_44.md:511 (Scenario 3 "Configuration" block, lines 507-513)
- **Claim in doc**: Scenario 3 config sets `s44_start_year = 2025` (with `s44_target_year = 2100`, `c44_bii_decrease = 0`) and is presented as a usable "Ratchet Mechanism" run.
- **Reality in code**: `preloop.gms:19-21` aborts the run if `s44_start_year <= sm_fix_SSP2`. `sm_fix_SSP2 = 2025` (`modules/09_drivers/aug17/input.gms:22`). With `s44_start_year = 2025`, `2025 <= 2025` is TRUE → abort "Start year for BII target interpolation has to be greater than sm_fix_SSP2". The doc itself states this rule at lines 273-280 but then violates it in the Scenario 3 example. (The config-file comment block at cfg:1441 uses 2025 only in an *indicative-outcomes* note, not as a prescribed runnable start year.)
- **File evidence**: `/tmp/magpie_develop_ro/modules/44_biodiversity/bii_target/preloop.gms:19-21`; `/tmp/magpie_develop_ro/modules/09_drivers/aug17/input.gms:22`
- **verify_cmd**: `grep -n "sm_fix_SSP2" .../09_drivers/aug17/input.gms` → `22:  sm_fix_SSP2 ... / 2025 /`; preloop.gms:19-20 → `if (s44_start_year <= sm_fix_SSP2, abort "Start year ... has to be greater than sm_fix_SSP2")`.
- **confirmed**: true
- **proposed_fix**: In Scenario 3 change `s44_start_year = 2025` to `s44_start_year = 2030` (must be strictly greater than `sm_fix_SSP2 = 2025`). Optionally add a one-line note under the example: "Note: `s44_start_year` must be > `sm_fix_SSP2` (2025) or the model aborts in preloop."

### Bug 44-B3 — "Code files: 7" should be 8
- **Severity**: Minor
- **Class**: 6 (hardcoded counts drift)
- **Trigger** (§1 Minor): "Wrong detail, but a careful reader wouldn't be misled into action."
- **doc_line**: module_44.md:621
- **Claim in doc**: "**Code files**: 7 (realization, sets, declarations, input, equations, preloop, presolve, postsolve)"
- **Reality in code**: The parenthetical itself lists 8 file types, and there are 8 `.gms` files in the realization dir: declarations, equations, input, postsolve, preloop, presolve, realization, sets. Count "7" is internally inconsistent and wrong.
- **File evidence**: `/tmp/magpie_develop_ro/modules/44_biodiversity/bii_target/*.gms` (8 files)
- **verify_cmd**: `ls .../bii_target/*.gms | wc -l` → `8`
- **confirmed**: true
- **proposed_fix**: Change "**Code files**: 7" to "**Code files**: 8".

### Bug 44-B4 — Citation drift: primforest BV formula cited at `equations.gms:56` (actual 59-61)
- **Severity**: Minor
- **Class**: 10 (stale file:line citation, off-by-few)
- **Trigger** (§1 Minor): "Off-by-few line citation where adjacent lines say similar things."
- **doc_line**: module_44.md:224
- **Claim in doc**: `modules/35_natveg/pot_forest_may24/equations.gms:56` for `vm_bv(j,"primforest",...) = vm_land(j,"primforest") × fm_bii_coeff("primary",potnatveg) × fm_luh2_side_layers(...)`
- **Reality in code**: Line 56 is blank; line 57 is the comment introducing the BV calc; the `q35_bv_primforest` equation populating `vm_bv(j2,"primforest",...)` is at lines 59-61. The formula itself is stated correctly; only the line number drifts by 3 (points at the comment/blank just above).
- **File evidence**: `/tmp/magpie_develop_ro/modules/35_natveg/pot_forest_may24/equations.gms:59-61`
- **verify_cmd**: `grep -n "vm_bv(" .../35_natveg/pot_forest_may24/equations.gms` → `59: q35_bv_primforest ... vm_bv(j2,"primforest",potnatveg)` (and read of lines 54-67 confirms 56 blank, 57 comment).
- **confirmed**: true
- **proposed_fix**: Change citation on line 224 from `equations.gms:56` to `equations.gms:59-61`.

---

## Deferred (not flagged as bugs — uncertain or not code-verifiable harm)

1. **module_44.md:68** — `q44_bii_target` formula drops the `sum(ct, ...)` wrapper: doc writes `p44_bii_target(ct,i2,biome44)` where code (equations.gms:23) has `sum(ct, p44_bii_target(ct,i2,biome44))`. `ct` is the singleton current-timestep set; the sum extracts the current value, so the doc's `(ct,...)` notation is a faithful simplification of a singleton-set sum and does not mislead about element count (MANDATE 10 is about expanding sums into wrong member lists; here no member list is invented). Borderline Informational; left unflagged.

2. **module_44.md:356-358** — `vm_cost_glo = ... + Σ(j2) vm_cost_bv_loss(j2) + ...` telescopes two equations. Actual path: `vm_cost_bv_loss → q11_cost_reg → v11_cost_reg → q11_cost_glo → vm_cost_glo` (it enters the *regional* cost eq, line 44, not `vm_cost_glo` directly). The surrounding prose says "aggregates into total regional costs," which is accurate; the formula is explicitly illustrative ("..."). Not a clean code-checkable error.

3. **module_44.md:210** — M30 `crop_ann` formula gloss writes `vm_land(j,"crop") × [crop shares]` whereas code (equations.gms:96) uses `sum((crop_ann30,w), vm_area(j2,crop_ann30,w))`. The doc explicitly frames this as an informal "example" with a bracketed placeholder `[crop shares]`, and the citation line (:95) is exact. Borderline; the paraphrase is loose but labeled. Left unflagged (would need an editorial, not code-correctness, call).

4. **module_44.md:236** — `v44_bii` listed under "Interface Variables (Provided)" though it is a module-internal `v44_` variable used for reporting only (the doc qualifies it "Reporting only"). Loose use of "interface," not a code error.

---

## Mechanical checks (M1-M6)
- M1 (file:line citations present): PASS (60+ citations).
- M2 (active realization stated + matches default): PASS — `bii_target` stated and is the verified default. (The *alternatives list* is stale → B1, but the default claim is correct.)
- M3 (variable prefixes valid): PASS.
- M4-M6: doc-style metadata; doc is a reference page, not a Q&A answer — N/A for scoring.

## Summary
module_44.md is highly accurate on its load-bearing spine (equations, all interface variable
names, the complete `vm_bv` producer set with exact per-class attribution, the `vm_cost_bv_loss`
→ M11 consumer, all 5 scalar defaults, set counts). Two Major bugs: (B1) it lists a removed
realization `bii_target_apr24` as a live alternative; (B2) Scenario-3 example sets
`s44_start_year = 2025`, which the model aborts on (`sm_fix_SSP2 = 2025`, must be strictly greater).
Two Minor: (B3) "Code files: 7" vs actual 8; (B4) primforest-formula citation `:56` vs actual `:59-61`.
The advisory's Critical-prone areas (default realization, vm_bv/vm_cost_bv_loss producer/consumer
sets, fm_bii_coeff readers, inverted boolean default) are all CLEAN.
