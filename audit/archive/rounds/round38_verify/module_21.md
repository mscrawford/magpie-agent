# Round 38 Adversarial Verification — module_21.md

Ground truth: `/tmp/magpie_develop_ro` (develop worktree, read-only). Verifier model: Opus 4.8.

Summary: all 4 confirmed bugs UPHELD. Citations mechanically re-checked; the
one "does NOT consume" claim (B4) re-derived twice + positive control.

---

## M21-B1 — k_trade member count (header says 38, code has 33)

**Class:** other (set-member count / hardcoded count drift).
**Verdict:** UPHELD. **citation_ok:** true.

STEP A (mechanical citation check):
- `test -f modules/21_trade/selfsuff_reduced/sets.gms` -> EXISTS.
- `wc -l` -> 51 lines; cited range 17-21 in range.
- Read lines 17-21: `k_trade(kall) Production activities of tradable commodities` followed by
  the member list across lines 18-21. Token `k_trade` present on line 17. OK.

STEP C (count):
- Extracted members lines 18-21, split on commas, stripped `/` and whitespace,
  `wc -l` -> **33** members (tece ... woodfuel; full list enumerated, no duplicates).
- Cross-check: doc's OWN enumeration (module_21.md:71-74) split on commas -> **33**
  (15 crops + 10 processed + 6 livestock/fish + 2 forestry). Internally consistent.

The header "38 items" contradicts both the code (33) and the doc's own list (33).
Proposed fix 38 -> 33 is correct and the fixer can apply it cleanly (doc body already
agrees). Note: auditor's grouping prose ("6 livestock/fish + 2 forestry") matches the
doc's Livestock(6)+Forestry(2) split; total 33 unaffected.

---

## M21-B2 — realization.gms line for trade_pools.png (doc says :20, real :31)

**Class:** other (stale file:line citation).
**Verdict:** UPHELD. **citation_ok:** true.

STEP A:
- `test -f modules/21_trade/selfsuff_reduced/realization.gms` -> EXISTS; `wc -l` -> 45.
- Proposed-fix line :31 in range. Read line 31:
  `*' ![Implementation of trade.](trade_pools.png){ width=100% }` -> contains `trade_pools.png`. OK.
- `rg -n 'trade_pools.png' realization.gms` -> ONLY `31:` (single hit). Positive: pattern matches.
- Line 20 (current doc citation) reads:
  `*' in production of different superregions, though still being constrained by the upper bounds of the production band.`
  -> prose, no png reference. Confirms the stale citation.

Proposed fix 20 -> 31 is correct.

---

## M21-B3 — bilateral22 input.gms source line for bilateral trade-cost files (doc says :45-57, real :71-83)

**Class:** other (stale file:line citation / content mismatch).
**Verdict:** UPHELD. **citation_ok:** true.

STEP A:
- `test -f modules/21_trade/selfsuff_reduced_bilateral22/input.gms` -> EXISTS; `wc -l` -> 83.
- Proposed-fix range 71-83 in range. Read:
  - L71 `parameter f21_trade_margin(i_ex,i_im,kall) Bilateral freight and insurance costs ...`
  - L74 `$include ".../f21_trade_margin_bilat.cs5"`
  - L78 `parameter f21_trade_tariff(i_ex,i_im,kall) Bilateral specific duty tariff rates ...`
  - L81 `$include ".../f21_trade_tariff_bilat.cs5"`
  -> tokens `f21_trade_margin_bilat`, `f21_trade_tariff_bilat`, both parameter decls present. OK.
- `rg -n 'f21_trade_margin_bilat|f21_trade_tariff_bilat|parameter f21_trade_margin|parameter f21_trade_tariff'`
  -> 71, 74, 78, 81. Confirms.
- The doc table (module_21.md:412-413) describes exactly these two files/parameters.
- Stale range 45-57 actually covers `f21_trade_scenario_adjustments` (.cs5 block) and the
  `f21_import_supply_historical` declaration -> different parameters, as auditor stated.

Proposed fix 45-57 -> 71-83 is correct (cleanly brackets both decl+include pairs, 71..83).

---

## M21-B4 — "Land Balance: ... (reads vm_land ...)" — module 21 does NOT reference vm_land

**Class:** consumer_set (claim that module 21 reads vm_land). HIGHEST-RISK class
("does NOT consume"); required double-confirm + positive control.
**Verdict:** UPHELD (parenthetical fabricated; headline "Does NOT participate" correct).
**citation_ok:** true (doc line 612 contains the claimed token "reads `vm_land`";
proposed_fix carries NO file:line to validate; file_evidence is a directory + absence claim,
which I verified directly rather than as a line citation).

STEP C (independent re-derivation of consumer set — both `NAME(` and `NAME.` forms):
- Method 1 (rg) over modules/21_trade/:
  - `rg 'vm_land\('` -> NO MATCH
  - `rg 'vm_land\.'` -> NO MATCH (covers .l/.lo/.up/.fx/.m solution-level reads)
  - `rg 'vm_land'`  -> NO MATCH (broadest)
- Method 2 (grep, independent tool): `grep -rn 'vm_land' modules/21_trade/` -> exit 1, no output
  (consistent with rg).
- POSITIVE CONTROL 1: `grep -rln 'vm_prod' modules/21_trade/` -> 3 hits
  (selfsuff_reduced, exo, selfsuff_reduced_bilateral22 equations.gms) => grep machinery works in
  this dir; the vm_land absence is real, not a silent-empty false negative.
- POSITIVE CONTROL 2: `grep -rln 'vm_land(' modules/10_land/` -> 2 hits
  (landmatrix_dec18 equations.gms + declarations.gms) => the search pattern is valid and would
  match vm_land if present.
- Coverage: `find modules/21_trade -name '*.gms'` -> 28 files across all 3 realizations,
  all searched.

Conclusion: module 21 has ZERO vm_land references in any form. The parenthetical
"reads `vm_land`" is fabricated. The headline "❌ Does NOT participate" in Land Balance
is correct. Proposed fix (replace the parenthetical with "does not read `vm_land`;
trade operates on production/supply aggregates, not land allocation") is accurate and safe.

---

### Verdict table

| Bug | class | citation_ok | verdict |
|-----|-------|-------------|---------|
| M21-B1 | other | true | UPHELD |
| M21-B2 | other | true | UPHELD |
| M21-B3 | other | true | UPHELD |
| M21-B4 | consumer_set | true | UPHELD |
