# Round 37 Doc Audit — module_40.md (Transport)

**Auditor**: Opus 4.8 (1M ctx), adversarial doc auditor
**Target**: `magpie-agent/modules/module_40.md`
**Ground truth**: `/tmp/magpie_develop_ro` (develop worktree), `config/default.cfg`
**Date**: 2026-05-30

## Overall Verdict: MOSTLY ACCURATE (upper band)
**Accuracy score**: ~8.5/10 (1 Major scaling error; remainder verified accurate)

Module 40 is a simple, single-equation module and the doc is unusually solid: the
default realization, the equation formula, the sole consumer (M11), and the entire
`vm_prod` consumer-set citation block all verify exactly against develop. The one
material code-verifiable error is in the "Scaling" subsection, which leaves the
reader believing `vm_cost_transp` is unscaled when it is explicitly scaled by 1e3 in
Module 11's `scaling.gms`.

---

## Pre-run advisory — verified

The advisory flagged: "Verify default realization. Verify transport-cost equations
(q40_*) and the vm_cost_transp consumer set (M11). Both grep forms + positive control
+ co-located-name caveat."

All three advisory concerns **REFUTED** (the doc is correct on all of them):

1. **Default realization** = `gtap_nov12`. CONFIRMED.
   `grep -n transport config/default.cfg` → line 1293 `cfg$gms$transport <- "gtap_nov12"`.
   (Note: the canonical `grep "cfg\$gms\$transport"` returned empty due to `$`-escaping in
   the shell; `grep -n transport` and `rg -n transport` both confirm. Not a doc bug — a
   grep-method artifact. Positive: `s40_pasture_transport_costs <- 0` at line 1296.)

2. **q40_* equations** = exactly 1 (`q40_cost_transport`). CONFIRMED.
   Formula at `gtap_nov12/equations.gms:11-13` is an EXACT match to the doc's quoted block
   (lines 35-37): `vm_cost_transp(j2,k) =e= vm_prod(j2,k)*f40_distance(j2) * f40_transport_costs(k)`.
   `off` has 0 equations (`rg q40_ off/` → exit 1, no match). CONFIRMED.

3. **vm_cost_transp consumer set = M11 only**. CONFIRMED (twice + positive control).
   `rg vm_cost_transp` across modules → outside M40, only `11_costs/default/equations.gms:21`
   (the `+ sum((cell(i2,j2),k), vm_cost_transp(j2,k))` cost-flow read) and
   `11_costs/default/scaling.gms:10` (`.scale`). `rg vm_cost_transp.` (attribute form, catches
   `.l/.m/.scale` presolve/postsolve reads) → same M11 scaling line, nothing else. `rg` of
   `core/` → exit 1 (none). Positive control: `rg vm_cost_landcon` correctly returns M11 + M39,
   proving the cross-module search works. The doc's "Module 11 only" claim is correct.

---

## Verified-correct claims (high-value spine, all confirmed in develop)

- **Header / realizations**: `gtap_nov12` (active/default) + `off` (disabled). `ls modules/40_transport/`
  shows exactly these two realization dirs. ✓ (MANDATE 8)
- **q40_cost_transport declaration**: `gtap_nov12/declarations.gms:9` (doc:820). ✓
- **q40_cost_transport equation**: `gtap_nov12/equations.gms:11-13` (doc:32). Exact formula match. ✓
- **vm_cost_transp declaration**: `gtap_nov12/declarations.gms:13` + `off/declarations.gms:10` (doc:166). ✓
- **off realization fix**: `off/presolve.gms:9` `vm_cost_transp.fx(j,k) = 0;` (doc:143,798). ✓
- **vm_prod source**: declared in Module 17 `flexreg_apr16/declarations.gms:9`, units `mio. tDM per yr`
  (doc says "Million tons dry matter per year"). ✓
- **vm_prod consumer-set citations — ALL EXACT** (doc:53):
  - M18 `18_residues/flexcluster_jul23/equations.gms:18` ✓
  - M30 `30_croparea/simple_apr24/equations.gms:15` ✓
  - M31 `31_past/endo_jun13/equations.gms:17` ✓
  - M38 `38_factor_costs/sticky_feb18/equations.gms:35` ✓
  - M42 `42_water_demand/all_sectors_aug13/equations.gms:14` ✓
  - M71 `71_disagg_lvst/foragebased_jul23/equations.gms:15` ✓
  - M73 `73_timber/default/equations.gms:26` ✓
  (Enumerated actual consumer set via `rg vm_prod\b` and `rg vm_prod\(`: M17(own),18,30,31,38,40(own),
  42,71,73. The doc's 7-module "also consumed by" list = exactly the non-M17/non-M40 set. No phantoms,
  no omissions among the documented set. M20-processing does NOT consume vm_prod — correctly absent.)
- **M11 aggregation citation**: `q11_cost_reg(i2)` with `+ sum((cell(i2,j2),k), vm_cost_transp(j2,k))`
  at `11_costs/default/equations.gms:21` (doc:172). EXACT. ✓
- **M11 objective chain**: `q11_cost_glo .. vm_cost_glo =e= sum(i2, v11_cost_reg(i2))` at
  `11_costs/default/equations.gms:10` (doc:173). EXACT. ✓
- **s40_pasture_transport_costs default = 0**: `input.gms:10` `/ 0 /` + `default.cfg:1296`
  `<- 0` (doc:60,379). ✓ (MANDATE 3)
- **f40_distance**: `input.gms:15-21`, units "min" (doc:56). ✓
- **f40_transport_costs**: `input.gms:23-28`, units "USD17MER per tDM per min" (doc:57). ✓
  (Minor: declared over `kall` in code; doc writes `f40_transport_costs(k)`. k ⊆ kall; equation
  indexes by k. Not flagged — within tolerance.)
- **Units of vm_cost_transp**: `mio. USD17MER per yr` in code = doc's "Million USD17MER per year
  (2017 USD at market exchange rates)". ✓
- **realization.gms:13-16 static-infrastructure quote** (doc:398). ✓
- **postsolve**: `gtap_nov12/postsolve.gms` stores ov_cost_transp + oq40_cost_transport over
  level/marginal/upper/lower (doc:733, "postsolve.gms:10-19"). ✓
- **equations.gms prose citations**: Nelson 2008 at `equations.gms:20-28` (doc:71); GTAP at
  `equations.gms:35-68`/`36-44` (doc:100,102); calib figure at `equations.gms:66-68` (doc:259,280). ✓

---

## Bugs found

### Bug M40-B1 — Scaling section: vm_cost_transp described as unscaled; it is scaled by 1e3 in M11

- **Severity**: Major (tie-breaker uncertainty noted — see below)
- **Class**: 12 / behavior-misleading factual claim (model behavior)
- **Trigger** (§1 Major): "The claim is wrong in a way that misleads about behavior, but won't
  directly cause damaging action."
- **Doc line**: module_40.md:721,725,727
- **Claim in doc**:
  > "**No explicit scaling defined** in Module 40 gtap_nov12 realization (no `.scale` attribute
  > set in declarations or presolve)" ... "Solver handles this range without scaling issues" ...
  > "**Comparison**: Modules with much larger cost ranges (e.g., Module 11 objective function)
  > use explicit scaling (`.scale = 10e4` or similar)"
- **Reality in code**: `vm_cost_transp` IS explicitly scaled by 1e3. The scale factor is set in the
  consuming cost-hub module's scaling phase, not Module 40's files:
  `modules/11_costs/default/scaling.gms:10` → `vm_cost_transp.scale(j,k) = 1e3;`
  (Same file scales `vm_cost_glo.scale = 1e7` and `v11_cost_reg.scale(i) = 1e6`.)
  The narrow parenthetical ("no .scale set in Module 40's declarations/presolve") is *literally
  true* — M40 gtap_nov12 has no presolve and its declarations.gms sets no scale. But the section's
  net message ("vm_cost_transp is unscaled; solver handles it natively; only M11's objective is
  scaled") is FALSE and contradicts code: the interface variable M40 provides carries a 1e3 scale.
- **File evidence**: `modules/11_costs/default/scaling.gms:10`
- **verify_cmd**: `rg -n 'vm_cost_transp\.' /tmp/magpie_develop_ro/modules/ | grep -v 40_transport`
  → `modules/11_costs/default/scaling.gms:10:vm_cost_transp.scale(j,k) = 1e3;` (sole hit).
  Cross-checked: `rg -n 'vm_cost_transp' modules/` lists the same scaling.gms:10 line plus the M11
  equations.gms:21 cost-flow read. Positive control `rg vm_cost_landcon` returns M11+M39 (search works).
- **confirmed**: true
- **proposed_fix**: Replace the line-721 statement with one that names the actual scaling site.
  Suggested replacement for line 721:
  "**Scaling**: Module 40's own files (gtap_nov12 declarations.gms; no presolve) set no `.scale`
  attribute, but the interface variable IS explicitly scaled: `vm_cost_transp.scale(j,k) = 1e3` is
  set in the cost hub at `modules/11_costs/default/scaling.gms:10` (alongside `vm_cost_glo.scale = 1e7`
  and `v11_cost_reg.scale(i) = 1e6`)."
  And delete or correct the line-727 "Comparison" so it no longer implies vm_cost_transp is unscaled
  (e.g. "Module 11's `scaling.gms` scales both its objective `vm_cost_glo` (1e7) and `vm_cost_transp`
  (1e3)"). Line 725's "solver handles this range" can stay but should not imply the absence of a scale
  factor.
- **Tie-breaker note**: Major vs Minor. The parenthetical is technically true within M40's scope, which
  argues Minor under the "pull down" rule. But a careful reader doing scaling/numerical-debugging work
  WOULD act on the false belief that vm_cost_transp has no scale factor (Minor's definition — "a careful
  reader wouldn't be misled into action" — fails). Net message is behavior-wrong → Major. `tier_uncertainty: true`.

---

## Deferred (not code-verifiable / not edited)

- Illustrative parameter ranges (f40_distance 5-2000+ min; f40_transport_costs ~0.001-0.05;
  vm_cost_transp 0.001-100 mio USD) — explicitly labeled illustrative; require reading binary
  `.cs2`/`.csv` input data, which I cannot parse. Not flagged.
- "~200 cells after clustering", "~59,000 cells at 0.5°" (doc:686-687) — resolution-config dependent;
  standard MAgPIE description, marked with `~`. Not precisely code-checkable.
- File-structure line counts (doc:775-801): doc uses "~"/approximate counts; actual `wc -l`:
  gtap_nov12 declarations 21 (doc "22"), input 30 (doc "31"), equations 68 (doc "69"), realization 23
  (doc "24"), postsolve 19 (doc "20"); off realization 18 (doc "19"), declarations 17 (doc "18"),
  presolve 9 (doc "10"), postsolve 15 (doc "16"). All off-by-one (trailing-newline / approximate). These
  are non-load-bearing metadata in a file-structure summary; Informational at most — NOT flagged as bugs.
- Verification-footer phrasing "s40_pasture_transport_costs ... set to 0 at line 30" (doc:833):
  input.gms:30 assigns `f40_transport_costs("pasture") = s40_pasture_transport_costs`, i.e. it sets the
  pasture *commodity factor* to the scalar's value; the scalar itself is set to 0 at line 10. Mildly
  imprecise but in a metadata footer and the mechanism is described correctly in the body (doc:60,379).
  Informational — NOT flagged.
- Calibration narrative (Stages 1-5, doc:197-287): faithful paraphrase of the equations.gms:35-68
  prose; "conceptual `vm_prod_initial`/`vm_prod_calibrated`" are correctly labeled as not-actual-GAMS
  variables. No code claim to refute.

---

## Notes on method / robustness

- All "absence" conclusions confirmed by two methods + a passing positive control (vm_cost_landcon),
  per the repo's grep-reliability rules. No bare un-cross-checked `grep -r` absence claims.
- Checked BOTH `vm_cost_transp(` and `vm_cost_transp.` forms (solution-level attribute reads) before
  concluding M11 is the sole external consumer — this is exactly how the scaling.gms `.scale` read
  (invisible to a `vm_cost_transp(` grep) surfaced.
- The vm_prod consumer-set block is a model citation block: every one of the 7 cited file:line
  references lands on the exact line in current develop. No drift.
