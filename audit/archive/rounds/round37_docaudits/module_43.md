# Round 37 Doc Audit — module_43.md (Water Availability)

**Auditor**: Opus (adversarial doc audit)
**Date**: 2026-05-30
**Target doc**: `magpie-agent/modules/module_43.md`
**Ground truth**: `/tmp/magpie_develop_ro` (develop worktree, read-only) + `config/default.cfg`
**Realization audited**: `total_water_aug13` (the only realization; default per `config/default.cfg:1406`)

## Overall Verdict: MOSTLY ACCURATE (lower band)
## Accuracy Score: 6/10

module_43.md is a high-fidelity doc on its load-bearing spine: the core equation,
all variable names, set members, scenario switch + default, infeasibility buffer, the
real interface variable (im_wat_avail) producer/consumer, and nearly all file:line and
reference citations verify exactly against develop. Three errors lower the score:
one misattributed cross-module dependency (Major), one wrong-value scaling snippet whose
explanation repeats the error (Major-vs-Minor borderline; tie-broken DOWN to Minor per
rubric §1 since it touches only solver numerics, not results/logic), and a uniformly
off-by-one file-line-count table (Minor).

**Score derivation** (rubric §4): 0 Critical, 1 Major (B1), 2 Minor (B2 tie-broken down, B3)
→ 10 − (0 + 2 + 1 + 1) = **6**. The strict-formula alternative (B2 kept Major) gives 5,
but rubric §1 tie-breaker pulls B2 down because it is ambiguous between tiers and harms only
numerics. The §7 band for 6 is "Mostly Accurate (lower band)" — consistent here, NOT
"Significant Errors" (no confabulated variable/equation, no wrong realization/default,
correct spine). `tier_uncertainty: true` on B2.

---

## Verified Claims (correct — high confidence, code-read this session)

- **Default realization** `total_water_aug13`: only dir under `modules/43_water_availability/`;
  `config/default.cfg:1406` `cfg$gms$water_availability <- "total_water_aug13"`. ✓
- **Scenario default** `c43_watavail_scenario = cc`: `input.gms:9` `$setglobal c43_watavail_scenario cc`
  AND `config/default.cfg:1412` `<- "cc"  # def = "cc"`. ✓
- **q43_water formula** (doc lines 32-33, 633-634, 802): matches `equations.gms:10-11`
  `sum(wat_dem,vm_watdem(wat_dem,j2)) =l= sum(wat_src,v43_watavail(wat_src,j2))` (whitespace aside). ✓
- **Variable names**: `v43_watavail(wat_src,j)` (`declarations.gms:13`), `im_wat_avail(t,wat_src,j)`
  (`declarations.gms:9`), `f43_wat_avail(t_all,j)` (`input.gms:16`), `vm_watdem` (M42),
  `q43_water(j)` (`declarations.gms:17`). All correct; no confabulated names. ✓
- **wat_dem members** {agriculture, domestic, manufacturing, electricity, ecosystem} —
  `core/sets.gms:247`. Doc lists all 5 (order differs, immaterial). ✓
- **wat_src members** {surface, ground, technical, ren_ground} — `core/sets.gms:245`. ✓
- **watdem_exo** {domestic, manufacturing, electricity, ecosystem} —
  `modules/42_water_demand/all_sectors_aug13/sets.gms:9-10`. Doc's "non-agriculture exogenous"
  framing for the buffer (lines 205, 383) is correct. ✓
- **preloop.gms:8-12** — surface = f43_wat_avail; ground/ren_ground/technical = 0. Exact. ✓
- **presolve.gms:8-11** fixations + **presolve.gms:14-16** groundwater buffer — doc reproduces
  the buffer expression verbatim (lines 197-199) incl. `.up`, `*1.01`, `$(...>0)`. Exact. ✓
- **nocc / nocc_hist** code (`input.gms:24,25`), `m_fillmissingyears` (`input.gms:27`),
  `sm_fix_cc` (default 2025, `config/default.cfg:228`) — all correct. ✓
- **postsolve.gms:10-17** ov43_watavail / oq43_water level/marginal/upper/lower — exact. ✓
- **realization.gms prose citations** (12-13 runoff→rivers; 13-15 glacier/desal "not considered";
  18-20 growing-period rationale; 34-35 dam exception; 40-42 infeasibility interface) — all verify. ✓
- **Reference line citations**: Bondeau @bondeau_lpjml_2007 at realization.gms:16,20,29,38;
  Biemans @biemans_water_2011 at realization.gms:35 — exact match (doc lines 759, 762). ✓
- **~200 cells** (doc lines 41, 686): default cellular input is `c200` (`config/default.cfg:26`). ✓
- **im_wat_avail IS provided to Module 42** (doc Interface Variables table, line 845): VERIFIED.
  M42 reads it at `all_sectors_aug13/presolve.gms:58,64` (env flows) and
  `agr_sector_aug13/presolve.gms:38,44,67,73`. The table is correct AND complete (im_wat_avail
  is the sole M43-owned object consumed by another module). ✓
  [NOTE: my first `grep -rln im_wat_avail .../modules/` SILENTLY truncated to 3 files and omitted
  M42 — the documented silent-grep trap. Repo-wide grep + ripgrep + direct sed read all confirm M42.]

---

## Bugs Found

### Bug module_43-B1 — "Provides to Module 11" is a misattributed dependency
- **Severity**: Major
- **Class**: 2 (hallucinated/misattributed cross-module relationship) — also engages MANDATE 2/17
- **Trigger** (§1 Major): "Right concept, wrong [attribution] ... misleads about behavior" + MANDATE 17
  (direct vs transitive/non-existent consumer). Not Critical: it is footer metadata, not a
  model-logic edit path.
- **Doc line**: module_43.md:871
- **Claim in doc**: "**Provides to**: Module 11 (costs): Shadow prices on water constraint"
- **Reality in code**: Module 43 provides NOTHING to Module 11. M11's cost equation
  (`modules/11_costs/default/equations.gms:46`) reads `vm_water_cost(i2)`, which is declared and
  populated by **Module 42** (`grep -rln vm_water_cost` → only M42 + M11). M43 owns no `vm_cost_*`
  variable. M43's marginals (`oq43_water.marginal`, `v43_watavail.m`) are diagnostic postsolve
  outputs (`postsolve.gms:10-11`) and are NOT read by any other module (cross-module grep for
  `q43_water.`/`v43_watavail.` → none outside M43). The water *cost* reaching M11 is M42's
  `vm_water_cost`, not anything from M43.
- **File evidence**: `modules/11_costs/default/equations.gms:46` (`+ vm_water_cost(i2)`);
  `modules/42_water_demand/all_sectors_aug13/declarations.gms` (vm_water_cost declared);
  `modules/43_water_availability/total_water_aug13/postsolve.gms:10-11` (marginals are outputs only).
- **verify_cmd**:
  `grep -rln 'vm_water_cost' /tmp/magpie_develop_ro/modules/` → M42 (declarations/equations/postsolve) + M11/default/equations.gms
  `grep -rln 'q43_water\.\|v43_watavail\.' /tmp/magpie_develop_ro/modules/ | grep -v 43_water_availability` → (empty: NO_CROSS_MODULE_MARGINAL_READS)
  `grep -rln 'vm_cost' /tmp/magpie_develop_ro/modules/43_water_availability/` → exit 1 (no cost var in M43)
  Positive control: `grep -c vm_watdem .../42_.../all_sectors_aug13/equations.gms` → 2 (grep works in tree).
- **confirmed**: true
- **Proposed fix**: Replace line 871 with:
  `**Provides to**: Module 42 (water_demand): \`im_wat_avail\` (read in M42 presolve to set environmental-flow and reserved-fraction water demands). Module 43 owns no cost variable and is not read by Module 11; the water cost in Module 11 (\`vm_water_cost\`, modules/11_costs/default/equations.gms:46) is produced by Module 42. The q43_water shadow price is a solver dual (diagnostic output \`oq43_water.marginal\`), not an interface variable provided to another module.`
- **Anchor reference**: resembles R20 wrong-consumer-set / MANDATE 17 transitive-vs-direct
  (M11 reads M42's cost, not anything from M43); kept Major (footer, not Critical refactor path).

### Bug module_43-B2 — Scaling snippet has wrong value (10e4 vs 1e4) and the explanation repeats the error; omits q43_water.scale
- **Severity**: Minor (tie-broken down from Major; `tier_uncertainty: true`)
- **Class**: 12 (content-level citation mismatch — fenced "code" block ≠ actual code) + class 4
- **Trigger**: Major candidate — "Citation points at content that ... says something materially
  different" (`10e4` = 100000 vs actual `1e4` = 10000, a 10× difference) AND the prose
  ("scale by 10^5", line 467) repeats the wrong value, doubly misleading a careful reader.
  Tie-broken DOWN to Minor per §1: the error touches only solver scaling (numerics/convergence),
  not model logic or results, so a reader would not be misled into a damaging action. Recorded with
  `tier_uncertainty: true` so excessive downgrade is detectable.
- **Doc line**: module_43.md:463 (and the dependent prose at module_43.md:467)
- **Claim in doc**:
  ```
  v43_watavail.scale(wat_src,j) = 10e4;
  ```
  with prose "Water availability values ~ millions m³ → scale by 10^5".
- **Reality in code** (`scaling.gms:8-9`):
  ```
  v43_watavail.scale(wat_src,j) = 1e4;
  q43_water.scale(j) = 1e2;
  ```
  `1e4` = 10,000 (10^4), NOT `10e4` = 100,000 (10^5). The doc both mis-transcribes the value and
  then "explains" the wrong value as 10^5. The doc also OMITS the second scaling line
  (`q43_water.scale(j) = 1e2;`), so the scaling section is incomplete.
- **File evidence**: `modules/43_water_availability/total_water_aug13/scaling.gms:8-9`.
- **verify_cmd**: `grep -n 'scale' /tmp/magpie_develop_ro/modules/43_water_availability/total_water_aug13/scaling.gms`
  → `8:v43_watavail.scale(wat_src,j) = 1e4;` and `9:q43_water.scale(j) = 1e2;`.
- **confirmed**: true
- **Proposed fix**: Replace the code block (lines 462-464) with:
  ```
  v43_watavail.scale(wat_src,j) = 1e4;
  q43_water.scale(j) = 1e2;
  ```
  and change the Purpose prose (line 467) to: "Water availability values ~ millions m³ → variable
  scaled by 1e4 (10^4); the q43_water constraint is scaled by 1e2 (10^2)." Update the Sources line
  to `scaling.gms:8-9`.
- **Anchor reference**: content-level mismatch (class 12); 10× value error in a verbatim code block.

### Bug module_43-B3 — File-line-count table off by one on 8 of 9 files
- **Severity**: Minor
- **Class**: 6 (hardcoded counts drift) — but low-stakes (file line counts in a locations table, not
  set/equation counts a reader computes against).
- **Trigger** (§1 Minor): "Wrong detail, but a careful reader wouldn't be misled into action."
- **Doc line**: module_43.md:777-792 (Section 16, Summary of File Locations)
- **Claim in doc**: module.gms 22; realization.gms 53; declarations.gms 26; input.gms 28;
  equations.gms 21; preloop.gms 13; presolve.gms 17; postsolve.gms 20; scaling.gms 9;
  "Total code: ~190 lines".
- **Reality in code** (`wc -l`, all files end with newline so awk NR agrees): module.gms **21**;
  realization.gms **52**; declarations.gms **25**; input.gms **27**; equations.gms **20**;
  preloop.gms **12**; presolve.gms **16**; postsolve.gms **19**; scaling.gms **9** (correct);
  total **201** (not ~190). Every file except scaling is the doc's value minus 1.
- **File evidence**: `wc -l` over all 9 files (see verify_cmd).
- **verify_cmd**: `wc -l /tmp/magpie_develop_ro/modules/43_water_availability/module.gms .../total_water_aug13/*.gms`
  → 21,52,25,27,20,12,16,19,9 (total 201). Trailing-newline check via `tail -c1 | od -An -c` = `\n` on
  all sampled files, so counts are exact.
- **confirmed**: true
- **Proposed fix**: Update Section 16 counts to module.gms 21, realization.gms 52, declarations.gms 25,
  input.gms 27, equations.gms 20, preloop.gms 12, presolve.gms 16, postsolve.gms 19, scaling.gms 9;
  change "~190 lines" to "~200 lines (201 across the 9 files)".

---

## Missing Nuances (NOT scored as bugs)

- **Section 5.1 "Module 43 → Module 42" channel** (lines 265-268) describes only the shadow-price
  feedback and omits the concrete `im_wat_avail` data edge (M42 reads it for environmental-flow and
  reserved-fraction demands). The shadow-price LP feedback genuinely exists within the solve, so this
  is incompleteness, not error. The Interface Variables table (line 845) DOES list im_wat_avail, so
  the doc captures the edge elsewhere — internally slightly inconsistent but not a hard bug. If B1 is
  fixed as proposed, consider cross-referencing the im_wat_avail edge here too.
- **"Centrality Rank: Medium"** (line 868) and **"~200 cells"** rounding are not code-checkable beyond
  the c200 resolution (verified). No action.

---

## Deferred (not code-verifiable / out of scope)

- Section 14 "Typical Parameter Values" (global runoff km³/yr, per-cell magnitudes, growing-period
  day ranges) — explicitly labeled illustrative/literature, requires reading binary `lpj_watavail_grper.cs2`.
  Not verifiable; doc labels it correctly. No edit.
- Whether the off-by-one in Section 16 stems from a header year-line change vs other edits — cosmetic
  provenance, irrelevant to the fix.

---

## Advisory-checker resolution (the pre-run flag)

The pre-run advisory: "Verify default realization; vm_watavail / water-availability equations; the
M42↔M43 linkage; consumer/producer sets; both grep forms + positive control."

- Default realization `total_water_aug13`: CONFIRMED correct (config:1406; only dir). 
- "vm_watavail": there is no such name; the doc correctly uses `v43_watavail` (internal) and
  `im_wat_avail` (interface). No confabulation. q43_water equation CONFIRMED exact.
- M42↔M43 linkage: CONFIRMED two-way and correctly captured in the Interface table —
  M42→M43 via `vm_watdem` (q43_water RHS reads it), M43→M42 via `im_wat_avail` (M42 presolve reads it).
  REFUTED as a bug. The ONE dependency error is the unrelated "Provides to Module 11" footer (B1).
- Consumer/producer sets verified with BOTH grep forms + ripgrep + positive control + direct sed read
  (silent-truncation trap hit once on im_wat_avail and corrected). Net: `vm_watdem` consumers = {M42, M43};
  `im_wat_avail` producer M43 / consumer M42; `v43_watavail`,`q43_water`,`f43_wat_avail` internal-only;
  M43→M11 edge does NOT exist (B1).
