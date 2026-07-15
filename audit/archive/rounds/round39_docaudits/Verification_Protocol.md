# Audit Report: reference/Verification_Protocol.md

**Round**: R39 doc-audit sweep
**Auditor**: Opus 4.8 (1M)
**Date**: 2026-05-30
**Ground truth**: `/tmp/magpie_develop_ro` (MAgPIE develop, read-only), agent repo internal files, GAMS conventions.

## Overall Verdict: SIGNIFICANT ERRORS (in the worked examples) / process body sound

### Accuracy Score: 6/10

The procedural body of the protocol (Steps 1-6, Spot/Medium/Deep checks, Red Flags, Verification Log Template, After-Verification) is process prose with generic `XX`/`qXX_` placeholders — not code-checkable and broadly sound. The defects are concentrated in the **Citation Standards** (lines 194-239) and **Common Pitfalls** (lines 243-268) sections, which present concrete `✅ Correct` / `✅ Right` exemplars styled as real, verified citations. Several of those exemplars contain a wrong module name, an out-of-range line number, a content-mismatched citation, and an internally inconsistent module-22 identity. This is acutely ironic for a doc whose stated purpose (line 5) is "Ensure 100% accuracy in module documentation" and which teaches by exemplar.

A key mitigation: three of the fabricated variable names (`f22_bii`, `f35_fire_loss`, `pm_carbon_density`) are on the doc's OWN allowlist (line 3: `<!-- check-gams-vars: allow f22_bii,f35_fire_loss,pm_carbon_density -->`), signalling the author deliberately treated them as schematic placeholders exempt from the variable checker. That framing pulls the pure-name fabrications down to Minor. It does NOT, however, exempt the wrong module PATHS, the out-of-range LINE numbers, or the content-mismatched citations — those are independent, code-verifiable errors that mislead a careful reader and teach wrong mappings.

The pre-run advisory ("verify file:line citations, variable names, realization claims; much is agent-process — flag only concrete code-claim errors, defer process prose") is CONFIRMED accurate: the concrete code-claim errors all live in the two exemplar sections; the rest is correctly deferred as process prose.

---

## Verified Claims (correct)

- **`im_growing_stock(t,j,ac,land_timber)`** (line 248): CORRECT. Declared verbatim at `modules/14_yields/managementcalib_aug19/declarations.gms:17` ("Harvestable stem biomass per ha by age class (tDM per ha)"). Signature matches exactly.
- **`pm_timber_yield` treated as deprecated/renamed** (line 248): CORRECT handling. The old name is absent from develop (positive `rg pm_timber_yield` → no match), and the doc italicizes it (`*pm_timber_yield*`) per MANDATE 14. The successor `im_growing_stock` is real.
- **`pm_land_start(j,land)`** in the q22_bii example formula (line 215): REAL parameter. Declared `modules/10_land/landmatrix_dec18/declarations.gms:9` ("Land initialization area (mio. ha)"); set/populated in `start.gms:8`. (Initially looked absent on a bare `rg vm_bii` — positive control for `pm_land_start` confirmed it is real. NOT a bug.)
- **`vm_land(j,land)` is from Module 10** (line 258): variable name + module attribution CORRECT — declared `modules/10_land/landmatrix_dec18/declarations.gms:19`. (Only the line number `:67` and the `*` glob are wrong — see VP-2.)
- **"Fire is parameterized, not dynamically modeled" in Module 35** (line 252-253): the CONCEPT is correct (module 35 has no mechanistic fire model; it applies input shares). Only the specific identifier `f35_fire_loss` and the `:45` citation are fabricated (see VP-5).
- **Module 22 default realization** is `area_based_apr22` — internally the doc gets THIS right at line 232 (`modules/22_land_conservation/area_based_apr22/...`), even while contradicting itself at lines 199/200/218. Verified: `config/default.cfg:714` `cfg$gms$land_conservation <- "area_based_apr22"`.
- **Citation-format rule** (full-path `modules/NN_name/realization/file.gms:N`, line 198) and the bare-basename prohibition (line 206) are sound guidance and match MANDATE 16.

---

## Bugs Found

### VP-1 (Major) — Wrong module name/path for the biodiversity citation exemplars
- **Severity**: Major
- **Class**: 8 (wrong/stale realization name) + 7 (broken cross-reference); R20-anchor-adjacent (wrong attribution set).
- **Trigger**: §1 Major — "File:line citation drift to adjacent but different content (would mislead a careful reader)" + wrong-realization-name flavor.
- **Doc lines**: Verification_Protocol.md:199, :200, :218
- **Claim in doc**:
  - `:199` `modules/22_biodiversity/bv_btc_mar21/equations.gms:45` (single line)
  - `:200` `modules/22_biodiversity/bv_btc_mar21/equations.gms:45-52` (range)
  - `:218` `(Source: modules/22_biodiversity/bv_btc_mar21/equations.gms:12-14)`
- **Reality in code**: There is NO `22_biodiversity` module. Module 22 is `22_land_conservation` (default realization `area_based_apr22`; about WDPA protected-area land conservation, not biodiversity). The realization `bv_btc_mar21` belongs to **Module 44 (`44_biodiversity`)**, not module 22. So `modules/22_biodiversity/bv_btc_mar21/...` is wrong on two counts (wrong module name, realization in the wrong module). The doc even contradicts itself: line 232 correctly calls module 22 `22_land_conservation`.
- **File evidence**: `ls -d /tmp/magpie_develop_ro/modules/22_*/` → `22_land_conservation/` only. `find ... -name bv_btc_mar21` → `/tmp/magpie_develop_ro/modules/44_biodiversity/bv_btc_mar21`. `config/default.cfg:714` `cfg$gms$land_conservation <- "area_based_apr22"`.
- **verify_cmd / result**: `ls -d /tmp/magpie_develop_ro/modules/22_*/*/` → `22_land_conservation/area_based_apr22/`, `22_land_conservation/input/`. `find /tmp/magpie_develop_ro/modules -type d -name 'bv_btc*'` → `/tmp/magpie_develop_ro/modules/44_biodiversity/bv_btc_mar21`.
- **Confirmed**: true.
- **Proposed fix**: Repoint the citation-format exemplars at a real, current path. Replace all three `modules/22_biodiversity/bv_btc_mar21/equations.gms:NN` references with the actual biodiversity realization, e.g. `modules/44_biodiversity/bv_btc_mar21/equations.gms:11-13` (the `q44_cost_bv_loss` equation), OR a stable land-conservation example. (See VP-3 for the full self-consistent rewrite of the equation/parameter exemplar block.)

### VP-2 (Major) — Out-of-range line number + glob path in the vm_land "✅ Right" exemplar
- **Severity**: Major
- **Class**: 10 (stale/wrong file:line citation).
- **Trigger**: §1 Major — "File:line citation drift". R34-module_21 anchor pattern (cited line is OUT OF RANGE).
- **Doc line**: Verification_Protocol.md:258
- **Claim in doc**: `✅ Right: "Receives vm_land(j,land) from Module 10 (land), declared in modules/10_land/*/declarations.gms:67"`
- **Reality in code**: `vm_land(j,land)` is declared at `modules/10_land/landmatrix_dec18/declarations.gms:19`, and that file is only **52 lines long** — so `:67` is out of range (cannot exist). Additionally the `*` glob violates the full-path rule this very doc states at line 198 (module 10 has exactly one code realization, `landmatrix_dec18`).
- **File evidence**: `modules/10_land/landmatrix_dec18/declarations.gms:19` ` vm_land(j,land)  Land area of the different land types (mio. ha)`; file length 52.
- **verify_cmd / result**: `rg -n 'vm_land\(' .../10_land/*/declarations.gms` → `19: vm_land(j,land) ...`; `wc -l .../landmatrix_dec18/declarations.gms` → `52`; `ls -d .../10_land/*/` → only `input/` and `landmatrix_dec18/`.
- **Confirmed**: true.
- **Proposed fix**: Replace `modules/10_land/*/declarations.gms:67` with `modules/10_land/landmatrix_dec18/declarations.gms:19` (real path + real line).

### VP-3 (Major) — Content-mismatched citation in the f22_bii parameter exemplar (and non-existent input file)
- **Severity**: Major
- **Class**: 12 (content-level citation mismatch) + 2 (hallucinated name, mitigated by allowlist).
- **Trigger**: §1 Major — "Citation points at content that's no longer at the cited line, AND the actual cited content says something materially different".
- **Doc line**: Verification_Protocol.md:232 (and the name in :231)
- **Claim in doc**: `✅ Correct: f22_bii(land) - BII factor by land type ... Source: input/f22_bii.csv, loaded in modules/22_land_conservation/area_based_apr22/input.gms:34`
- **Reality in code**: `area_based_apr22/input.gms:34` is in the MIDDLE of an ISO-country-code list (`...GRD,GTM,GUF,...`), not a BII-factor load. There is no `f22_bii` parameter or `f22_bii.csv` input anywhere in develop (positive control: `rg f22_bii` over all modules → no match). The real BII input is `f44_bii_coeff.cs3`, loaded at `modules/44_biodiversity/bv_btc_mar21/input.gms:17`. `f22_bii` is allowlisted (line 3), so the name-checker skips it — but the **citation to specific content at :34** is independently wrong and would mislead a careful reader.
- **File evidence**: `modules/22_land_conservation/area_based_apr22/input.gms:30-38` = ISO country codes; `modules/44_biodiversity/bv_btc_mar21/input.gms:17` `$include "./modules/44_biodiversity/bv_btc_mar21/input/f44_bii_coeff.cs3"`.
- **verify_cmd / result**: `sed -n '30,38p' .../area_based_apr22/input.gms` → ISO codes; `rg -n 'f22_bii' /tmp/magpie_develop_ro/modules/` → NO MATCH; `rg -n 'f44_bii' ...` → `bv_btc_mar21/input.gms:17`.
- **Confirmed**: true.
- **Proposed fix**: Replace the exemplar with a real parameter+source, e.g.:
  `` `f44_bii_coeff` - BII coefficient by land type/state (unitless) — Source: `modules/44_biodiversity/bv_btc_mar21/input/f44_bii_coeff.cs3`, loaded in `modules/44_biodiversity/bv_btc_mar21/input.gms:17` ``.
  (Pairs with the VP-1 rewrite to make the whole biodiversity exemplar self-consistent and real.)

### VP-4 (Minor) — Broken internal cross-reference: archive/MODULE_59_ERRORS_FOUND.md
- **Severity**: Minor
- **Class**: 7 (broken cross-reference).
- **Trigger**: §1 Minor — "Stale package/realization citation that's recoverable (correct concept, findable in a different location)".
- **Doc line**: Verification_Protocol.md:190
- **Claim in doc**: ``**See**: `archive/MODULE_59_ERRORS_FOUND.md` for example``
- **Reality in code/repo**: No file named `*MODULE_59_ERRORS*` exists anywhere in the magpie-agent repo. The recoverable equivalents are `modules/module_59_notes.md` and `audit/archive/rounds/round34_docaudits/module_59.md`.
- **File evidence**: `find ~/.../magpie-agent -iname '*MODULE_59*'` → returns only `modules/module_59.md`, `modules/module_59_notes.md`, `audit/archive/rounds/round34_answers/module_59.md`, `audit/archive/rounds/round34_docaudits/module_59.md` — none is `MODULE_59_ERRORS_FOUND.md`.
- **verify_cmd / result**: `ls .../archive/MODULE_59_ERRORS_FOUND.md` → "No such file or directory"; `find ... -iname '*MODULE_59_ERRORS*'` → none.
- **Confirmed**: true.
- **Proposed fix**: Replace with a pointer that exists, e.g. ``**See**: `modules/module_59_notes.md` (lessons/errors recorded for module 59)`` or drop the line.

### VP-5 (Minor) — Non-existent variable names presented as ✅ exemplars (grouped; allowlist-mitigated)
- **Severity**: Minor (down-tiered from class-2 Critical-tendency by the doc's explicit allowlist + schematic framing; §1 tie-breaker pulls down)
- **Class**: 2 (hallucinated variable name) / 4 (conceptual pseudo-code presented as real).
- **Trigger**: would be §1 Critical "Invented variable name presented as authoritative" — but mitigated: `f22_bii`, `f35_fire_loss`, `pm_carbon_density` are on the doc's own allowlist (line 3), i.e. deliberately marked schematic. `q22_bii`/`vm_bii` are not allowlisted but appear inside a fenced ```gams example block. Net: Minor, grouped.
- **Doc lines**: :212, :215 (`q22_bii`, `vm_bii`), :248 (`pm_carbon_density(t,j,"forestry",c_pools)`), :253 (`f35_fire_loss(t,j)`).
- **Claim in doc**: presents `q22_bii(j) .. vm_bii(j) =e= sum(land, pm_land_start(j,land)*f22_bii(land)) / sum(...)`; `pm_carbon_density(t,j,"forestry",c_pools)`; `f35_fire_loss(t,j)` as the gold-standard ✅ examples.
- **Reality in code**:
  - `vm_bii`, `q22_bii`, `f22_bii`: NONE exist (positive control: `q44_bii` and `f44_bii_coeff` DO appear in module 44, proving the search works). The real biodiversity equation is `q44_bv_weighted(j2) .. v44_bv_weighted(j2) =e= f44_rr_layer(j2) * sum((potnatveg,landcover44), vm_bv(j2,landcover44,potnatveg))` (`modules/44_biodiversity/bv_btc_mar21/equations.gms:21-23`). A `q44_bii`/`vm_bii`-style BII *index* equation exists ONLY in the non-default `bii_target` realization (`equations.gms:13`, over `i2,biome44`) and even there the variable is `q44_bii`, not `vm_bii`.
  - bare `pm_carbon_density(t,j,"forestry",c_pools)`: does NOT exist. The forestry carbon-density parameter is `p32_carbon_density_ac_forestry(t_all,j,ac)` (module-internal `p32_`), and the `pm_`-prefixed family is `pm_carbon_density_secdforest_ac` / `_plantation_ac` / `_other_ac` (module 52). No bare `pm_carbon_density` token exists.
  - `f35_fire_loss(t,j)`: does NOT exist. The real fire-loss input in module 35 is `f35_forest_lost_share(i,driver_source)` ("Share of area damaged by forest fires", `pot_forest_may24/input.gms:32`). Note `pot_forest_may24/input.gms:45` (cited in the doc) is inside the `f35_forest_shock` table block — unrelated to fire loss. This is self-undermining: the lesson at line 252 is "don't claim features that don't exist," yet its ✅ answer names a non-existent variable.
- **File evidence**: `modules/44_biodiversity/bv_btc_mar21/equations.gms:21-23` (real BII-stock eq); `modules/52_carbon/normal_dec17/declarations.gms:9-13` (`pm_carbon_density_*_ac`); `modules/32_forestry/dynamic_may24/declarations.gms:20` (`p32_carbon_density_ac_forestry`); `modules/35_natveg/pot_forest_may24/input.gms:32` (`f35_forest_lost_share`).
- **verify_cmd / result**: `rg -n 'vm_bii|q22_bii' /tmp/.../modules/` → no match; `rg -n 'q44_bii' .../44_biodiversity/` → bii_target only (positive control passes); `rg -n 'pm_carbon_density\b' .../declarations.gms` → NONE bare; `rg -n 'f35_fire_loss' .../35_natveg/` → no match; `rg -n 'fire' .../pot_forest_may24/input.gms` → `:32 f35_forest_lost_share`.
- **Confirmed**: true.
- **Proposed fix**: Either (a) replace the placeholders with real identifiers so the gold-standard examples are themselves verifiable — `q44_bv_weighted`/`vm_bv`/`f44_rr_layer` (biodiversity), `pm_carbon_density_secdforest_ac` or `p32_carbon_density_ac_forestry` (forestry carbon), `f35_forest_lost_share` (fire) — OR (b) if intentionally schematic, annotate each inline per MANDATE 7: "(conceptual placeholder, not an actual GAMS variable)". Option (a) is strongly preferred for a verification-protocol doc. If kept schematic, add `q22_bii`,`vm_bii` to the allowlist marker for consistency (currently only `f22_bii`,`f35_fire_loss`,`pm_carbon_density` are exempted).

---

## Deferred (not code-verifiable / out of scope — NO edit proposed)

- **"PR #869 rename on 2026-04-20"** (line 248): the rename `pm_timber_yield → im_growing_stock` is corroborated by code (old name absent, new name present), but the PR number and date are git-history metadata not verifiable from the read-only tree. Defer.
- **"(R6 2026-05-25: CURRENT_STATE.json was retired as SSOT...)"** (line 322): agent-process note; not a code claim.
- **Template grep commands using `modules/XX_*/...` without `../`** (lines 49, 71, 134, 140, 156): in the agent's working layout GAMS code is at `../modules/`, so a literal copy-paste from the agent dir would miss; but these are `XX`-placeholder templates and several other agent docs use the `modules/` (parent-relative) convention loosely. Path-prefix style is a process/convention matter, not a concrete code-claim error. Defer (no edit).
- **All Step 1-6 / Spot-Medium-Deep / Red-Flags / Log-Template / After-Verification prose**: process guidance with generic placeholders; not code-checkable. Confirmed consistent with current repo structure (e.g., `audit/validation_rounds.json`, `modules/module_XX_notes.md`, `project/sync_log.json` all exist). Defer.

---

## Summary

The protocol's *process* is sound; its *worked examples* are not. The Citation-Standards and Common-Pitfalls exemplars — the sections that are supposed to model 100% accuracy — contain a wrong module name (`22_biodiversity`; module 22 is `22_land_conservation`, and `bv_btc_mar21` is module 44's realization), an out-of-range line citation (`10_land/.../declarations.gms:67` in a 52-line file; real line 19), a content-mismatched citation (`f22_bii` at `area_based_apr22/input.gms:34`, which is an ISO-country list; the real input is `f44_bii_coeff` in module 44), a broken internal cross-reference (`archive/MODULE_59_ERRORS_FOUND.md` does not exist), and several non-existent variable names presented as gold-standard ✅ answers (mitigated by the doc's own allowlist for three of them). 3 Major + 2 Minor confirmed. The pre-run advisory is confirmed accurate. Recommended remedy: rewrite the exemplar block to use REAL, currently-verified identifiers and citations (the doc that teaches verification should pass its own verifier).
