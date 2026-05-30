# Round 37 Adversarial Verification — module_40.md

**Verifier**: Opus 4.8 (1M ctx), adversarial / default-skeptic
**Ground truth**: `/tmp/magpie_develop_ro` (develop worktree, read-only)
**Target doc**: `magpie-agent/modules/module_40.md`
**Date**: 2026-05-30

---

## M40-B1 — Scaling: "no scaling defined; only M11 objective scaled"

**Severity (auditor)**: Major | **Class**: Behavior-misleading factual claim (scaling) / class 12
**Doc lines**: module_40.md:721, 725, 727

### Classification
`class_is_consumer_set = TRUE`.

The finding asserts WHERE an interface variable's `.scale` attribute is populated:
the doc says no scaling is defined and implies only "Module 11 objective function"
is scaled, whereas the auditor says M40's *own* interface variable `vm_cost_transp`
is explicitly scaled, and that the populator is the **cost hub (M11)** — not M40.
This is a populator/dependency-set claim about which module sets the attribute on a
shared interface variable. In scope for adversarial consumer-set re-derivation.

### Verdict: **UPHELD**

The auditor's evidence reproduces exactly and is code-true. The doc's net message
("vm_cost_transp unscaled; only M11's objective scaled, `.scale = 10e4 or similar`")
contradicts develop code. The narrow parenthetical ("no .scale in M40's own files")
is literally true, but the section as written misleads.

### Independent re-derivation (BOTH forms + positive control)

**(a) Does M40 set any `.scale` in its own files? — doc claims "No explicit scaling defined"**

```
$ rg -n '\.scale' /tmp/magpie_develop_ro/modules/40_transport/
NO .scale in M40 (rg exit 1)
```
True absence — but must prove the search dir is valid (R33 phantom-deletion guard):

**POSITIVE CONTROL** (known-present sibling token in same dir):
```
$ rg -n 'vm_cost_transp' /tmp/magpie_develop_ro/modules/40_transport/gtap_nov12/
postsolve.gms:11: ov_cost_transp(t,j,k,"marginal") = vm_cost_transp.m(j,k);
postsolve.gms:13: ov_cost_transp(t,j,k,"level")    = vm_cost_transp.l(j,k);
postsolve.gms:15: ov_cost_transp(t,j,k,"upper")    = vm_cost_transp.up(j,k);
postsolve.gms:17: ov_cost_transp(t,j,k,"lower")    = vm_cost_transp.lo(j,k);
declarations.gms:13: vm_cost_transp(j,k) Transportation costs (mio. USD17MER per yr)
equations.gms:12:  vm_cost_transp(j2,k) =e= vm_prod(j2,k)*f40_distance(j2) ...
```
Search dir valid -> the `.scale` absence in M40 is real (matches doc's literal parenthetical).

**(b) Where is vm_cost_transp scaled? — auditor: M11 default scaling.gms:10, value 1e3**

Attribute form (the `.scale` write):
```
$ rg -n 'vm_cost_transp\.scale' /tmp/magpie_develop_ro/modules/
modules/11_costs/default/scaling.gms:10:vm_cost_transp.scale(j,k) = 1e3;
```
Equation form (to be thorough, both forms grepped):
```
$ rg -n 'vm_cost_transp' /tmp/magpie_develop_ro/modules/11_costs/default/scaling.gms
10:vm_cost_transp.scale(j,k) = 1e3;
```
Full M11 scaling.gms content:
```
8:vm_cost_glo.scale = 1e7;
9:v11_cost_reg.scale(i) = 1e6;
10:vm_cost_transp.scale(j,k) = 1e3;
```

**Dedup check** (only one populator anywhere in repo):
```
$ rg -n 'vm_cost_transp\s*\.\s*scale' /tmp/magpie_develop_ro/
modules/11_costs/default/scaling.gms:10:vm_cost_transp.scale(j,k) = 1e3;   # sole match
```

**(c) Both realizations active? (so the scaling actually fires)**
```
$ rg -n 'cfg\$gms\$costs' /tmp/magpie_develop_ro/config/default.cfg
236:cfg$gms$costs <- "default"        # M11 default IS active -> scaling.gms runs
$ rg -n 'cfg\$gms\$transport' /tmp/magpie_develop_ro/config/default.cfg
1293:cfg$gms$transport <- "gtap_nov12"  # M40 gtap_nov12 IS active (doc's subject)
```

**(d) Doc parenthetical "(...declarations or presolve)" — gtap_nov12 has no presolve at all**
```
$ ls /tmp/magpie_develop_ro/modules/40_transport/gtap_nov12/presolve.gms
No such file or directory   # gtap_nov12: declarations/equations/input/postsolve/realization only
```
(only the `off` realization has presolve.gms). Minor: the doc's "or presolve" implies
gtap_nov12 has a presolve where scaling could have gone; it does not. Auditor's fix
correctly states "no presolve".

### Why UPHELD (not REFUTED/CORRECTED)
- Auditor's central factual claim (vm_cost_transp.scale = 1e3 at 11_costs/default/scaling.gms:10) is exact and reproduces.
- Doc line 727's "`.scale = 10e4 or similar`" is fabricated: M11's actual scale values are 1e7 / 1e6 / 1e3 — none equals 10e4. The fix removes a wrong number.
- Doc lines 721 + 725 + 727 jointly create the false impression that vm_cost_transp is unscaled and only an M11 "objective function" variable is scaled. Code shows vm_cost_transp itself is scaled, in the cost hub. Behavior-misleading -> Major is justified.
- No over-reach in the auditor's fix; only a tightening of exact values/line numbers is warranted (captured in corrected_set below).

### corrected_set (precise text to apply — supersedes auditor's prose with code-exact values)
Replace doc line 721 with:
"**Scaling**: Module 40 (`gtap_nov12`) sets no `.scale` in any of its own files (the
realization has only declarations/equations/input/postsolve — no presolve and no scaling
file). However, the interface variable IS explicitly scaled in the cost hub:
`vm_cost_transp.scale(j,k) = 1e3` at `modules/11_costs/default/scaling.gms:10`."

Replace doc line 727 with:
"**Comparison**: The cost hub `modules/11_costs/default/scaling.gms` scales three cost
variables — `vm_cost_glo.scale = 1e7` (line 8), `v11_cost_reg.scale(i) = 1e6` (line 9),
and `vm_cost_transp.scale(j,k) = 1e3` (line 10). (`default` is the active M11 realization.)"

Leave line 725 ("Solver handles this range...") only if rephrased to not assert
vm_cost_transp is unscaled; safer to drop or fold into the above.

---

## Summary
| Bug | Class consumer-set? | Verdict |
|-----|--------------------|---------|
| M40-B1 | TRUE (populator/where-scaled) | **UPHELD** (with tightened corrected_set: exact values 1e7/1e6/1e3, lines 8-10, no-presolve note) |
