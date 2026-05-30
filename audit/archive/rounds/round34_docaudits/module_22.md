# Round 34 doc audit — module_22.md (Land Conservation)

**Auditor**: Opus 4.8 (1M)
**Date**: 2026-05-30
**Target doc**: `magpie-agent/modules/module_22.md`
**Ground truth**: `/tmp/magpie_develop_ro` develop worktree + `config/default.cfg`
**Realization audited**: `area_based_apr22` (the ONLY realization → trivially the default; verified via `ls /tmp/magpie_develop_ro/modules/22_land_conservation/` and `config/default.cfg:714 cfg$gms$land_conservation <- "area_based_apr22"`).

---

## Overall verdict: SIGNIFICANT ERRORS

The mechanism/calculation sections (Sections 2, 3, 4, parts of 6) and the `input.gms`/`preloop.gms` citations are accurate and faithfully quoted. The **consumer/dependency model (Section 5 + 5.1 + the repeated "Used by" lines) is materially wrong**: it names Module 10 (Land) as the PRIMARY CONSUMER of `pm_land_conservation`, but Module 10 never references the variable. The true direct consumers are M29, M31, M32, M35, and (conditionally) M13. Module 29 and Module 13 are omitted entirely. Separately, `vm_treecover` is attributed to Module 32 (Forestry) when it is declared and populated in Module 29 (Cropland). These are R20-anchor-class wrong-consumer-set + wrong-interface-attribution errors → Critical.

---

## Advisory cross-lead verdict (from pre-run checker)

> "vm_land_other / v35_secdforest reportedly list M22 as consumer — verify M22's actual relationship to natveg land (does M22 read/constrain vm_land_other? grep both `vm_land_other(` and `vm_land_other.`)."

**REFUTED for the stated direction**: M22 does NOT reference `vm_land_other` or `v35_secdforest` in any of its files.
- `rg -n "vm_land_other" /tmp/magpie_develop_ro/modules/22_land_conservation/` → exit 1 (no match), both `(` and `.` forms.
- `rg -n "v35_secdforest" /tmp/magpie_develop_ro/modules/22_land_conservation/` → exit 1 (no match).

The actual relationship is the reverse: **M35 (pot_forest_may24) reads M22's `pm_land_conservation`** and uses it to set `vm_land.lo(j,"other")`, `vm_land.lo(j,"secdforest")`, and `v35_secdforest.lo(...)` (presolve.gms:162,174,177,179,201,221,231). So the M35↔M22 coupling is real, but M22 is the producer and M35 the consumer; the doc does NOT claim M22 reads vm_land_other, so there is no doc bug to fix from this lead — only the (separately confirmed) M10-as-consumer error. The doc's own M35 attribution (`pm_land_conservation(t,j,land_natveg,consv_type)`) is CORRECT (M35 uses the `land_natveg` set; equations.gms:22, presolve.gms:149).

The doc's M22-depends-on-M10 direction is also CORRECT: `pcm_land` and `vm_land` are both declared in Module 10 (`modules/10_land/landmatrix_dec18/declarations.gms`), and M22 reads `pcm_land(j,land)` + `vm_land.lo(j,"crop")`.

---

## Consumer set — re-derived from code (the core finding)

`rg -n "pm_land_conservation" /tmp/magpie_develop_ro/modules/ -g '!22_land_conservation/**'` (exit 0), cross-checked, with Module 10 positive control:

| Module | Reads `pm_land_conservation`? | Evidence | Default-on? |
|---|---|---|---|
| **M10 (Land)** | **NO** | `rg` exit 1 in `10_land/`; positive control `pcm_land` found in 4 M10 files → search works | n/a |
| **M29 (Cropland)** | YES (equation) | `29_cropland/detail_apr24/equations.gms:52`, `simple_apr24/equations.gms:41` — `sum((ct,land_snv,consv_type), pm_land_conservation(ct,j2,land_snv,consv_type))` | yes (default realization `detail_apr24`) |
| **M31 (Pasture)** | YES (presolve) | `31_past/endo_jun13/presolve.gms:9` — `vm_land.lo(j,"past") = sum(consv_type, pm_land_conservation(t,j,"past",consv_type))` | yes |
| **M32 (Forestry)** | YES (presolve, reads + writes) | `32_forestry/dynamic_may24/presolve.gms:20` reads `...("other","restore")`; `:214-216` reads+writes `...("secdforest","restore")` | yes |
| **M35 (NatVeg)** | YES (equation + presolve, reads + writes) | `35_natveg/pot_forest_may24/equations.gms:22`, `presolve.gms:149,162,174,177,179,186,189,197,198,201,221,225,228,229,231` | yes |
| **M13 (TC)** | YES, CONDITIONAL | `13_tc/endo_jan22/presolve.gms:40` (and `exo/presolve.gms:16`) — `sum(consv_type, pm_land_conservation(t,j,"crop",consv_type))`; gated by `c13_croparea_consv` | **NO** — `c13_croparea_consv` default = 0 (`13_tc/endo_jan22/input.gms:12 / 0 /`) |

Doc's claim (Section 5, lines 509-527; repeated 11, 580, 603, 724, 1312, 1338): consumers = **M10 (PRIMARY), M35 (SECONDARY), M31 (TERTIARY)**.

- **Phantom**: M10 (no code reference at all).
- **Omitted**: M29 (direct equation consumer), M13 (conditional, default-off).
- **Mischaracterized**: M32 listed only as "Additional Dependencies (indirect)" / "land availability constraints for afforestation" (lines 504, 583) — actually a direct reader (and writer) of `pm_land_conservation`.

This matches the R20 immutable anchor (doc cited a wrong/incomplete consumer set for an interface parameter → Critical, because a user refactoring `pm_land_conservation` would edit the wrong module and miss real ones).

---

## Bugs

### BUG-1 (Critical) — Module 10 falsely claimed as consumer of `pm_land_conservation`
- **Class**: 15 (latent doc error — wrong consumer set) / Bug_Taxonomy "wrong consumer attribution".
- **Trigger**: §1 Critical — "doc said wrong consumer set; user would have missed/edited the wrong module" (R20 anchor).
- **Doc lines**: module_22.md:11, :509-516 ("Module 10 (Land) — PRIMARY CONSUMER ... Directly constrains land-use optimization"), :580, :603, :724, :1312, :1338, :1404.
- **Claim**: "PROVIDES TO (3 modules): 1. Module 10 (Land) — PRIMARY CONSUMER ... Variable provided: `pm_land_conservation` ... Directly constrains land-use optimization."
- **Reality**: Module 10 never references `pm_land_conservation`. The constraint is enforced by M35/M31 setting `vm_land.lo(...)` and by M29 in `q29_*`.
- **Evidence**: `rg -n "pm_land_conservation" /tmp/magpie_develop_ro/modules/10_land/` → exit 1, empty; positive control `rg -ln "pcm_land" /tmp/magpie_develop_ro/modules/10_land/` → 4 files (landmatrix_dec18 postsolve/declarations/equations/start) → search is valid.
- **Confirmed**: yes.

### BUG-2 (Critical) — Consumer set omits M29 (Cropland) and M13 (TC); mischaracterizes M32
- **Class**: 15 / wrong consumer set (omission side).
- **Trigger**: §1 Critical (R20 anchor — consumer-set incompleteness on an interface parameter).
- **Doc lines**: module_22.md:509-527 (the canonical "PROVIDES TO" list), :579-584 (Dependency Chains list).
- **Claim**: consumers limited to M10/M35/M31 (+M32 as indirect "land availability").
- **Reality**: direct consumers are M29 (equations.gms:52/41), M31 (presolve.gms:9), M32 (presolve.gms:20,214-216), M35 (equations.gms:22 + presolve.gms multiple), and M13 conditionally (presolve.gms:40, default-off). M29 and M13 are entirely missing; M32 is a direct reader/writer, not merely "indirect".
- **Evidence**: see consumer table above; `rg -n "pm_land_conservation" ... -g '!22_land_conservation/**'`.
- **Confirmed**: yes.

### BUG-3 (Critical) — `vm_treecover` attributed to Module 32 (Forestry); it is Module 29 (Cropland)
- **Class**: 2/9-adjacent (wrong-module attribution for an interface variable; cf. MANDATE 13/17).
- **Trigger**: §1 Critical — analogous to "wrong module attribution for a cost variable"; a user tracing tree-cover provenance would open the wrong module.
- **Doc lines**: module_22.md:234 ("Tree cover (from Module 32)"), :504 ("Module 32 (Forestry): `vm_treecover.l(j)` - tree cover area").
- **Reality**: `vm_treecover(j)` "Cropland tree cover" is declared in `modules/29_cropland/detail_apr24/declarations.gms:39` (and `simple_apr24/declarations.gms:23`) and populated in M29. It is NOT referenced anywhere in module 32.
- **Evidence**: `rg -n "vm_treecover" /tmp/magpie_develop_ro/modules/32_forestry/` → exit 1 (no match). `rg -n "vm_treecover" .../29_cropland/detail_apr24/declarations.gms:39: vm_treecover(j)  Cropland tree cover (mio. ha)`. All-module list of referrers: 22, 29, 59 only.
- **Confirmed**: yes.

### BUG-4 (Minor) — Section B code snippet omits actual code (the all-`land` WDPA assignment) and adds spurious `);`
- **Class**: 4 (conceptual/incomplete pseudo-code presented as real code) / 12 (content mismatch at cited lines).
- **Trigger**: §1 Minor (a careful reader could be slightly misled about the future-period assignment order; the surrounding prose at :392 is correct).
- **Doc lines**: module_22.md:96-113 (code block headed "Additional Conservation Priority Areas (`presolve_ini.gms:28-44`)").
- **Claim** (doc snippet): `else` → directly `p22_conservation_area(t,j,land_consv) = sum(...) + sum(...);` → `);`
- **Reality**: the `else` branch (presolve_ini.gms:28-45) has TWO assignments: first `p22_conservation_area(t,j,land) = sum(cell(i,j), wdpa...)` for ALL `land` (lines 31-34), THEN the `land_consv` override adding `p22_add_consv` (lines 36-44). The doc's snippet drops lines 31-34. The trailing `);` in the doc (line 112) does not correspond to the code (the close paren at code line 45 closes the `if`, not a sum).
- **Evidence**: `modules/22_land_conservation/area_based_apr22/presolve_ini.gms:28-45` (read in full).
- **Confirmed**: yes. **Fix is low-risk but optional**; surrounding prose is correct.

### BUG-5 (Minor) — `presolve_ini.gms` section-header line ranges drift by a few (comment) lines
- **Class**: 10 (stale/loose file:line citation).
- **Trigger**: §1 Minor (adjacent lines say similar things; the quoted snippets themselves are accurate).
- **Doc lines / claims vs reality**:
  - :143 "Protection Calculation (`presolve_ini.gms:47-55`)" — protection assignment is lines 54-55 (47-53 are blank/comment/section-divider). Loose but contains the target.
  - :96 "(`presolve_ini.gms:28-44`)" — else block is 28-45.
  - :186 "D.1 Grassland (`presolve_ini.gms:64-67`)" — assignment at 66-67 (64-65 comment). OK.
  - :176 "Restoration Calculation (`presolve_ini.gms:58-118`)" — restoration if-block is 62-118.
- **Evidence**: full read of presolve_ini.gms (125 lines).
- **Confirmed**: yes (loose, not wrong-content). Tier kept low per tie-breaker.

### BUG-6 (Informational/Minor) — `WDPA_I-II-III` glossed as "Ia, Ib, III"
- **Class**: 12 (content nuance).
- **Doc lines**: module_22.md:367 ("`WDPA_I-II-III`: Strict protection (IUCN Ia, Ib, III)"), :1016, :998.
- **Reality**: `config/default.cfg:737` comment: "All legally protected areas in IUCN categories I, II & III". The set member is literally `WDPA_I-II-III`. The doc reinterprets "I-II-III" as Ia/Ib/III (drops category II, splits I). The realization header (`realization.gms:16`) lists model-wide categories as "Ia, Ib, III, IV, V, VI" for the full WDPA, so the doc's Ia/Ib reading is plausible but contradicts the config's literal "I, II & III" for this specific subset.
- **Evidence**: `config/default.cfg:736-739`.
- **Confirmed**: partially (the config comment says I/II/III; whether the underlying `.cs3` maps to Ia/Ib/III is input-data-level and not GAMS-verifiable). **Defer the exact category mapping; do not assert a fix beyond aligning to the config wording.**

### BUG-7 (Informational) — internal inconsistency: "PROVIDES TO" count and "Depends On" module
- **Class**: 6 (count drift) — informational because internal-only.
- **Doc lines**: Section 5 says "3 critical outputs" / "PROVIDES TO (3 modules)" (:491, :509); Section 5.1 "Dependency Chains" says "Provides To (5-7 modules)" and lists M10/M31/M35/M32 + "2-3 other" (:579-584); "Depends On (1 module): Module 09 (Drivers)" (:586-587) contradicts Section 5's "DEPENDS ON (1 module): Module 10 (Land)" (:493-495). Both 09 and 10 are real inputs (`fm_land_iso` from M09; `pcm_land`/`vm_land.lo` from M10), so "depends on 1 module" is itself wrong (≥2).
- **Reality**: M22 depends on at least M10 (`pcm_land`, `vm_land.lo`), M09 (`fm_land_iso`), and reads `vm_treecover` (M29). Provides to M29/M31/M32/M35/M13.
- **Confirmed**: yes (internal inconsistency + undercount). Low stakes (narrative), but should be reconciled when fixing BUG-1/2.

---

## Verified-correct claims (sampled)

- No `equations.gms` in the realization → "NO EQUATIONS" claim correct (`ls` shows declarations/input/preloop/presolve_ini/realization/sets only).
- Runs in `preloop` + `presolve_ini` only — `realization.gms:37-38`. Correct.
- `pm_land_conservation(t,j,land,consv_type)` declared `declarations.gms:15`. Correct.
- `land_consv` = primforest, secdforest, other; defined `input.gms:51-52`. Correct (doc :118, :390-392).
- `consv_type` = protect, restore (`sets.gms:26-27`). Correct.
- `base22` = none, WDPA, WDPA_I-II-III, WDPA_IV-V-VI (`sets.gms:10-11`). Correct.
- `consv_prio22` priority list (`sets.gms:21-24`) — doc's 20+ scenario list incl. `IrrC_75pc_30by30` etc. matches. Correct.
- Defaults: `c22_base_protect=WDPA`, `c22_protect_scenario=none`, `s22_restore_land=1`, `s22_conservation_start=2025`, `s22_conservation_target=2050`, `s22_base_protect_reversal=Inf` — all match `input.gms:8-17` + `config/default.cfg:723-782`. Correct.
- `policy_countries22` = 249 ISO codes (Python count). Doc's "249 countries" correct.
- `input.gms` Common-Modification citations (:8, :10, :14, :15-16, :17, :23-48) all accurate.
- `preloop.gms` citations (:20 `i22_land_iso`, :20-21 country weights, :36 sigmoid fader) all accurate.
- `i22_land_iso(iso) = sum(land, fm_land_iso("y1995",iso,land))` from M09 — correct (`preloop.gms:20`).
- IFL primforest special case `presolve_ini.gms:16-17` — correct.
- Restoration-potential equations E.1/E.2/E.3 (`presolve_ini.gms:82-89/92-100/103-111`) — citations and snippets correct.
- No-restoration `:113-118`, reversal `:120-122` — correct.
- M22 does NOT reference `vm_land_other`/`v35_secdforest` (advisory refuted).

---

## Deferred (not code-verifiable / out of scope — DO NOT EDIT)

- "30by30 scenario restores 3,094 Mha globally by 2030" (:556, :660) and other Mha-by-scenario figures (:827, :1010, :1041, :1434) — depend on input `.cs3` data + a model run; not GAMS-verifiable.
- Per-land-type WDPA coverage breakdown (:414-419) labeled "approximate" — input-data level.
- `WDPA_I-II-III` → exact IUCN category mapping (Ia/Ib/III vs I/II/III) — input `.cs3` semantics; config comment says "I, II & III" but the underlying mapping is not in GAMS. Flag wording only.
- `sm_fix_SSP2` exact numeric cutoff vs the doc's "1995-2020 / post-2020" framing — `sm_fix_SSP2` traces to M09 `n` (def 2025), but the realization header itself (authoritative, quoted at doc :47) says "After 2020 ... held constant at 2020 values", so the doc matches its source; the 2020-vs-2025 question is a model-design detail, not a doc-vs-code bug.
