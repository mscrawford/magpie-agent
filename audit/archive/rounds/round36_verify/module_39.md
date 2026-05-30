# Round 36 adversarial verification — module_39

**Role**: Adversarial verifier (consumer/populator/dependency-set focus).
**Target doc**: `magpie-agent/modules/module_39.md`
**Ground truth**: `/tmp/magpie_develop_ro` @ `ee98739fd` (develop worktree, read-only).

## Summary

All three auditor findings are **NOT_CONSUMER_SET** — none asserts which modules consume / populate / depend-on an interface variable or parameter. They are, respectively, a unit-string mismatch (B1), a pseudo-code-syntax + citation-range issue (B2), and a parameterization-vs-mechanism mischaracterization (B3). Per the verification method, NOT_CONSUMER_SET findings pass to the fixer unchanged; no consumer-set re-derivation (both-forms grep, phantom/omitted-member check, direct-vs-transitive) was required.

Although out of my primary scope, I independently reproduced each underlying code claim against develop — all three reproduce cleanly. The fixer can apply all three with confidence.

---

## B1 — vm_cost_landcon unit drop at doc:578 — NOT_CONSUMER_SET (code claim confirmed)

**class_is_consumer_set = false.** This is a units-field mismatch (bug class 12), not a claim about who consumes vm_cost_landcon.

Auditor claim: doc:578 test-code comment says `(mio USD/yr)`; canonical unit is `mio. USD17MER per yr` (declarations.gms:13). Primary units field at doc:286 already correct.

Independent confirmation (not required, performed for completeness):
- `declarations.gms:13`: `vm_cost_landcon(j,land)  Costs for land expansion and reduction (mio. USD17MER per yr)` — canonical unit confirmed.
- doc:286 reads `mio USD17MER per yr` (correct); doc:578 reads `mio USD/yr` (drops `17MER`). Confirmed.

Verdict: NOT_CONSUMER_SET. Passes to fixer unchanged. Proposed fix (doc:578 → `(mio. USD17MER per yr)`) is accurate and harmless.

---

## B2 — pseudo-code syntax + citation range at doc:32-39 — NOT_CONSUMER_SET (code claim confirmed)

**class_is_consumer_set = false.** Bug class 4/10 (pseudo-code presented as code; citation range). Not a consumer/populator set claim.

Auditor claim: doc block uses `s39_... = 12300` (4 contiguous lines, `=` syntax) cited as input.gms:9-14, but input.gms uses GAMS scalar syntax `s39_... / 12300 /`; range 9-14 also contains `s39_reward_crop_reduction /7380/` (L10) and `s39_ignore_calib /0/` (L14), omitted from the block. Order: crop(9), reward(10), past(11), forestry(12), urban(13), ignore(14). Names+values correct.

Independent confirmation (input.gms read in full):
- L9 `s39_cost_establish_crop ... / 12300 /`
- L10 `s39_reward_crop_reduction ... / 7380 /`
- L11 `s39_cost_establish_past ... / 9840 /`
- L12 `s39_cost_establish_forestry ... / 1230 /`
- L13 `s39_cost_establish_urban ... / 12300 /`
- L14 `s39_ignore_calib ... / 0 /`

Syntax is `/ value /` (scalars block), not `= value`. Cited range 9-14 spans 6 lines but the doc block shows only 4 (crop/past/forestry/urban) and uses wrong syntax. All names/values in the block are correct; the establishment-cost values map to L9/L11/L12/L13 (i.e. 9, 11, 12, 13 — not contiguous 9-12). Confirmed.

Verdict: NOT_CONSUMER_SET. Passes to fixer unchanged. Either proposed fix (real GAMS `/ ... /` syntax, or relabel "Conceptually (values from input.gms:9-13)") is accurate. Minor note for fixer: if relabeling to a range, the establishment-cost values are at L9, L11, L12, L13 (L10 is the reward, L14 the switch); "9-13" is the smallest contiguous span covering the four shown values.

---

## B3 — "enforcing minimum calibration factor of 1.0 by 2050" at doc:408 — NOT_CONSUMER_SET (code claim confirmed)

**class_is_consumer_set = false.** Bug class 4 (mechanism description; parameterization-vs-mechanism). Not a consumer/populator/dependency set claim. (This is exactly the "uses data about X != models X" distinction the global instructions flag as binding.)

Auditor claim: No GAMS code in module 39 (or anywhere) enforces a 2050 minimum or any min/smax on i39_calib. The only mention of "lifted to a minimum of 1 ... by 2050" is the realization.gms:14 description comment. Convergence is a property of pre-computed input f39_calib.csv (read verbatim at preloop.gms:11), not GAMS-side enforcement.

Independent confirmation:
- Full enumeration of i39_calib references in module 39 (see grep below): preloop.gms:11/13/14/15 (set from f39_calib verbatim; default-to-1 ONLY when sum=0 or s39_ignore_calib=1), declarations.gms:19 (declaration), presolve.gms:8/12/13 (multiply establishment cost / reward by i39_calib). NONE enforce a per-year minimum or 2050 logic.
- preloop.gms:11 `i39_calib(t,i,type39) = f39_calib(t,i,type39);` — verbatim read of input table. The if-block at L13-16 sets cost=1/reward=0 only for the missing-file / ignore-calib fallback, not a 2050 floor.
- `smax|smin|\bmin\b|2050` search in calib/ returns only realization.gms:14 (the `*'` doc-comment): "The calibration factor for costs of cropland expansion is lifted to a minium of 1 in all regions by 2050." Comment only, no executable logic.
- Global scope: i39_calib appears ONLY in module 39 (3 files), so no other module enforces it either. Confirmed.

Verdict: NOT_CONSUMER_SET. Passes to fixer unchanged. Proposed reword (attribute convergence to the calibration input data, note no GAMS-side min/year logic, cite realization.gms:14 as comment-only) is accurate and is the correct parameterization-vs-mechanism framing.

---

## Evidence (commands run + results)

```
$ rg -n 'i39_calib' /tmp/magpie_develop_ro/modules/39_landconversion/
preloop.gms:11:i39_calib(t,i,type39) = f39_calib(t,i,type39);
preloop.gms:13:if(sum((t,i,type39),i39_calib(t,i,type39)) = 0 OR s39_ignore_calib = 1,
preloop.gms:14:  i39_calib(t,i,"cost") = 1;
preloop.gms:15:  i39_calib(t,i,"reward") = 0;
declarations.gms:19: i39_calib(t,i,type39)  Calibration factor ... (1)
presolve.gms:8:* Global cost for cropland expansion are scaled with a calibration factor (i39_calib).
presolve.gms:12:i39_cost_establish(t,i,"crop") = s39_cost_establish_crop * i39_calib(t,i,"cost");
presolve.gms:13:i39_reward_reduction(t,i,"crop") = s39_reward_crop_reduction * i39_calib(t,i,"reward");

# Attribute-form note: i39_calib is a parameter, not a variable, so there is no
# .l/.lo/.up/.fx/.m attribute form to grep. The 'i39_calib(' enumeration above is
# complete. vm_cost_landcon (B1) is a variable but B1 is a unit-string claim, not
# a consumer claim, so no NAME./NAME( consumer sweep was warranted.

$ rg -n 'smax|smin|\bmin\b|2050' /tmp/magpie_develop_ro/modules/39_landconversion/calib/
realization.gms:14:*' The calibration factor for costs of cropland expansion is lifted to a minium of 1 in all regions by 2050.
   # -> comment only; no executable min/2050 logic.

# POSITIVE CONTROL (proves search works in calib/): sibling token f39_calib present
$ rg -n 'f39_calib' /tmp/magpie_develop_ro/modules/39_landconversion/
input/files:2:f39_calib.csv
calib/preloop.gms:11:i39_calib(t,i,type39) = f39_calib(t,i,type39);
calib/input.gms:18:table f39_calib(t_all,i,type39) Calibration factor ... (1)
calib/input.gms:20:$if exist ".../f39_calib.csv" $include ".../f39_calib.csv"

# Global scope: i39_calib only in module 39
$ rg -n 'i39_calib' /tmp/magpie_develop_ro/modules/ -l
.../39_landconversion/calib/preloop.gms
.../39_landconversion/calib/declarations.gms
.../39_landconversion/calib/presolve.gms

# B1 canonical unit
$ Read declarations.gms:13 -> vm_cost_landcon(j,land)  Costs ... (mio. USD17MER per yr)

# B2 scalar syntax
$ Read input.gms:9-14 -> all use '/ value /' GAMS scalar syntax (not '= value');
  L9 crop/12300/, L10 reward/7380/, L11 past/9840/, L12 forestry/1230/,
  L13 urban/12300/, L14 ignore_calib/0/.
```

**Conclusion**: 3/3 findings are NOT_CONSUMER_SET (pass to fixer unchanged). All three underlying code claims independently reproduce against develop @ ee98739fd; the fixer may apply all three. No phantom/omitted consumer-set members were at issue.
