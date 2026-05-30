# Round 36 Adversarial Verification — module_44.md

Verifier role: adversarial, default-skeptical. Ground truth: `/tmp/magpie_develop_ro` (develop worktree, read-only). Focus class: CONSUMER / POPULATOR / DEPENDENCY-SET findings.

## Classification summary

None of the four auditor findings are consumer-set findings (none asserts which modules consume/populate/depend-on an interface variable or parameter). Per method, all four pass to the fixer unchanged with verdict NOT_CONSUMER_SET. As a courtesy to the fixer, I nonetheless reproduced each auditor claim against develop code; all four reproduce. No corrections needed; no phantom/omitted-member risk applies.

| bug | claims-which-modules-consume/populate? | verdict | underlying claim reproduces? |
|-----|----------------------------------------|---------|------------------------------|
| 44-B1 | No — it is about which *realizations* exist (Pattern 8 realization-name), not an interface var's consumer set | NOT_CONSUMER_SET | YES |
| 44-B2 | No — config example vs. doc-internal validation rule (Pattern 12) | NOT_CONSUMER_SET | YES |
| 44-B3 | No — hardcoded file-count drift (Pattern 6) | NOT_CONSUMER_SET | YES |
| 44-B4 | No — stale file:line citation off-by-3 (Pattern 10) | NOT_CONSUMER_SET | YES |

---

## 44-B1 — Stale realization name `bii_target_apr24`

**class_is_consumer_set = false.** This is a realization-existence claim, not an interface-variable consumer/producer set.

Reproduction (independent):
- `cat .../44_biodiversity/module.gms` → `$Ifi` block lists ONLY `bii_target` and `bv_btc_mar21`. No `bii_target_apr24`.
- `ls .../44_biodiversity/` → only `bii_target/`, `bv_btc_mar21/`, `module.gms`.
- `config/default.cfg:1414-1417` → `cfg$gms$biodiversity <- "bii_target"  # def = bii_target`; the only two glossed realizations are `bii_target` and `bv_btc_mar21`.
- `CHANGELOG.md:204` → "realisation `bii_target_apr24` removed because it is identical to `bii_target`. `bii_target` set as new default." (Also :178 default change apr24→bii_target; :369/:380 are the older entries when apr24 was added — historical, now superseded.)

Absence check (isolated + positive control):
```
rg -n "bii_target_apr24" /tmp/magpie_develop_ro/modules/ ; echo EXIT=$?   -> EXIT=1 (absent)
rg -ln "bii_target"      /tmp/magpie_develop_ro/modules/                  -> 8 hits (positive control: rg works in dir)
```
The "(updated BII formulation)" gloss in the doc is also wrong per CHANGELOG (apr24 was identical to bii_target, which is why it was deleted).

Note on auditor's proposed fix: the replacement text describes `bv_btc_mar21` as "Global optimization of range-rarity weighted biodiversity stock losses/gains via a price", matching `config/default.cfg:1416` verbatim. Fix is sound and drops the removed realization correctly.

**Verdict: NOT_CONSUMER_SET (auditor's correction independently confirmed; passes to fixer unchanged).**

---

## 44-B2 — Scenario 3 config violates the module's own abort rule

**class_is_consumer_set = false.** Config-example vs. doc-internal validation-rule contradiction; no module-set assertion.

Reproduction (independent):
- `.../44_biodiversity/bii_target/preloop.gms:19-21`:
  ```
  if (s44_start_year <= sm_fix_SSP2,
    abort "Start year for BII target interpolation has to be greater than sm_fix_SSP2"
  );
  ```
- `sm_fix_SSP2` value: `grep -rn "sm_fix_SSP2" .../09_drivers/*/input.gms` → `09_drivers/aug17/input.gms:22:  sm_fix_SSP2  ...  / 2025 /`.
- Active drivers realization: `config/default.cfg:209-210` → `cfg$gms$drivers <- "aug17"`. So `sm_fix_SSP2 = 2025` under default.
- Doc Scenario 3 (`module_44.md:509-512`) sets `s44_start_year = 2025`. With 2025 <= 2025 TRUE → abort.
- Doc states the SAME rule at `module_44.md:273-280` ("Validation (preloop.gms:19-21) ... Start year ... has to be greater than sm_fix_SSP2"), so the doc internally contradicts itself. Failure mode is a loud safe abort (not silent corruption), consistent with auditor's borderline Major/Minor.

Auditor's proposed fix (change to `s44_start_year = 2030`, strictly > 2025) is correct.

**Verdict: NOT_CONSUMER_SET (auditor's correction independently confirmed; passes to fixer unchanged).**

---

## 44-B3 — "Code files: 7" vs. 8 files

**class_is_consumer_set = false.** Hardcoded count drift.

Reproduction (independent):
- `ls .../44_biodiversity/bii_target/` → 8 `.gms` files: declarations, equations, input, postsolve, preloop, presolve, realization, sets.
- Doc `module_44.md:621` parenthetical lists 8 file types (realization, sets, declarations, input, equations, preloop, presolve, postsolve) but states count "7" — internally inconsistent. Auditor's fix (7→8) is correct.

**Verdict: NOT_CONSUMER_SET (auditor's correction independently confirmed; passes to fixer unchanged).**

---

## 44-B4 — Stale citation `equations.gms:56` for q35_bv_primforest

**class_is_consumer_set = false.** Off-by-3 file:line citation drift; formula text itself is correct.

Reproduction (independent), `.../35_natveg/pot_forest_may24/equations.gms`:
- Line 54-55: tail of `vm_carbon_stock(j2,"other",...)` =e= `m_carbon_stock_ac(vm_land_other,...)`.
- Line 56: BLANK (confirms auditor).
- Line 57: comment introducing the BV computation.
- Lines 59-61: `q35_bv_primforest(j2,potnatveg) .. vm_bv(j2,"primforest",potnatveg) =e= vm_land(j2,"primforest") * fm_bii_coeff("primary",potnatveg) * fm_luh2_side_layers(j2,potnatveg);`

The doc's prose formula (`module_44.md:222`) matches lines 59-61 exactly; only the cited line 56 is stale. Auditor's fix (56 → 59-61) is correct.

**Verdict: NOT_CONSUMER_SET (auditor's correction independently confirmed; passes to fixer unchanged).**

---

## Overall

All 4 findings are NOT_CONSUMER_SET (none asserts a module consumer/producer/dependency set). No consumer-set re-derivation protocol triggered; no phantom-member or omitted-member risk. Every auditor claim independently reproduces against develop; no REFUTE/CORRECT. Fixer may apply all four proposed fixes as-is.
