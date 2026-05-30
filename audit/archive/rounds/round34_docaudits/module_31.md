# Round 34 Doc Audit: module_31.md (31_past, endo_jun13)

**Auditor**: Opus adversarial doc auditor
**Date**: 2026-05-30
**Target doc**: `magpie-agent/modules/module_31.md`
**Ground truth**: `/tmp/magpie_develop_ro` (develop worktree) + `config/default.cfg`

---

## Overall verdict: MOSTLY ACCURATE

The doc is substantially correct: all 5 equation formulas match code verbatim, the default realization is right, the scalar default is right, the equation header line ranges are right, and the consumer/populator relationships in the "Provides Output To" section are correct (M11 reads `vm_cost_prod_past`, M52 reads `vm_carbon_stock`, M44 reads `vm_bv`). The errors found are: one Major set-domain error on `vm_yld`, one Major carbon-stock source/attribution error (G2 class), and minor domain-label / off-by-one citation drifts.

---

## Pre-run advisory checks (confirm/refute)

1. **Default realization via config** — CONFIRMED CORRECT. `config/default.cfg:969` `cfg$gms$past <- "endo_jun13"`. Doc line 22-23 correct.
2. **M31's `vm_land('past')` populator role** — N/A as a populator: `vm_land` is DECLARED in M10 (`modules/10_land/landmatrix_dec18/declarations.gms`, `vm_land(j,land)`); M31 READS `vm_land(j2,"past")` in its equations and SETS a lower bound `vm_land.lo(j,"past")` in presolve.gms:9. Doc treats `vm_land` as an input from M10 — CORRECT.
3. **`vm_carbon_stock` contribution (G2)** — CONFIRMED: M31 IS a populator of `vm_carbon_stock` via `q31_carbon` (`modules/31_past/endo_jun13/equations.gms:22-24`). `vm_carbon_stock` is DECLARED in M56 (`modules/56_ghg_policy/price_aug22/declarations.gms:34`), READ by M52 (`modules/52_carbon/normal_dec17/equations.gms:19`). Doc's "Provides Output To Module 52" (line 497) is correct; doc's "Source: Module 52 (Carbon)" (line 310) is the G2-class attribution error — see BUG 31-2.
4. **Pasture-yield / management equations + consumer sets (`name(` and `name.` greps + positive control)** — CONFIRMED the q31_prod yield equation matches code. Found the `vm_yld` domain error (BUG 31-1) during this check. Both `vm_carbon_stock(` and `vm_carbon_stock.` (static `.fx`) checked; M52 reader confirmed via equation-level read of `q52_emis_co2_actual`.

---

## Verified-correct claims (high-value sample)

- Default realization `endo_jun13` — `config/default.cfg:969`. ✓
- `s31_fac_req_past` default = 1 — `input.gms:10` (`/ 1 /`) AND `config/default.cfg:972` (`cfg$gms$s31_fac_req_past <- 1`). ✓
- Zeroed in postsolve — `postsolve.gms:10` `s31_fac_req_past = 0;`. ✓ (doc line 376 correctly cites postsolve.gms:10, not equations.gms — good DECLARED-vs-RESET discipline)
- q31_prod formula `vm_prod(j2,"pasture") =l= vm_land(j2,"past") * vm_yld(j2,"pasture","rainfed")` — `equations.gms:16-18`. ✓ (=l= inequality correct)
- q31_carbon formula + `m_carbon_stock` macro — `equations.gms:22-24`; macro exists `core/macros.gms:99`. ✓
- q31_cost_prod_past formula — `equations.gms:31-32`. ✓
- q31_bv_manpast / q31_bv_rangeland formulas — `equations.gms:38-40` / `42-44`, verbatim match incl. `fm_luh2_side_layers`, `fm_bii_coeff`. ✓
- `ag_pools / vegc, litc /` (above ground only) — `modules/56_ghg_policy/price_aug22/sets.gms:209-210`. ✓ (doc carbon-pool list correct)
- `vm_cost_prod_past(i)` declared `declarations.gms:18`, positive var. ✓ Consumed by M11 `modules/11_costs/default/equations.gms:17`. ✓
- `vm_carbon_stock` read by M52 `modules/52_carbon/normal_dec17/equations.gms:19`. ✓
- `vm_bv` read by M44 (`bii_target/equations.gms:16`, `bv_btc_mar21/equations.gms:23`). ✓
- Conservation lower bound `vm_land.lo(j,"past") = sum(consv_type, pm_land_conservation(t,j,"past",consv_type))` — `presolve.gms:9`. ✓ formula verbatim.
- preloop `vm_bv.l` init for manpast (9-10) and rangeland (12-13). ✓
- static realization fixes `vm_land.fx`, carbon, bv, cost — `static/presolve.gms:11,15,20,23,28`; only realization.gms + presolve.gms (+ not_used.txt). ✓
- `vm_prod` declared in M17 `modules/17_production/.../declarations.gms:9` (`vm_prod(j,k)`). Source attribution to M17 correct.
- `fm_carbon_density(t_all,j,land,c_pools)` from M52 `modules/52_carbon/normal_dec17/input.gms:16`. ✓ source M52 correct.
- `fm_luh2_side_layers(j,luh2_side_layers10)` from M10 `modules/10_land/landmatrix_dec18/input.gms:19`. (doc says "External data" — loosely true, it is an `fm_` input table; declared in M10's input.gms. Not flagged — both framings are defensible.)
- `fm_bii_coeff(bii_class44,potnatveg)` from M44 `modules/44_biodiversity/bv_btc_mar21/input.gms:15`. ✓ source M44 correct.

---

## BUGS FOUND

### BUG 31-1 (Major) — Wrong set domain for `vm_yld`

- **Class**: 3 (suffix/domain truncation) / wrong set member
- **Trigger** (§1 Major): "Wrong variable prefix/scope — semantic scope wrong" (domain set wrong).
- **Doc line**: module_31.md:290
- **Claim**: "`vm_yld(j,kcr,w)` - cells × crops × water source"
- **Reality**: declared `vm_yld(j,kve,w)` — `modules/14_yields/managementcalib_aug19/declarations.gms:26`. The first index set is `kve` (Land-use activities, INCLUDES `pasture`), NOT `kcr`. `kcr(kve)` is "Cropping activities" and **excludes `pasture`** (`modules/14_yields/managementcalib_aug19/sets.gms:18-26`). Because `pasture ∉ kcr`, the documented domain makes the very expression the doc documents — `vm_yld(j2,"pasture","rainfed")` in q31_prod (`equations.gms:18`) — appear out-of-domain. The doc's own equation block (line 92, 102) correctly uses `"pasture"`, so the prose domain `(j,kcr,w)` self-contradicts.
- **verify_cmd**: `grep -n 'vm_yld' .../14_yields/managementcalib_aug19/declarations.gms` → `26: vm_yld(j,kve,w) ...`; `sed`/Read of `.../sets.gms` → `kve(k)` line 18 includes `pasture`, `kcr(kve)` line 23 excludes `pasture`.
- **Confirmed**: true.
- **Proposed fix**: replace doc line 290 `**Dimensions**: `(j,kcr,w)` - cells × crops × water source, here specifically ("pasture","rainfed")` with `**Dimensions**: `(j,kve,w)` - cells × land-use activities (kve includes pasture) × water source, here specifically ("pasture","rainfed")`.

### BUG 31-2 (Major) — `vm_carbon_stock` "Source: Module 52" misattributes declarer/producer

- **Class**: 15 (latent doc error — producer/consumer attribution) — also MANDATE 17 (direct vs transitive) + G2 anchor.
- **Trigger** (§1): R20/G2 anchor — wrong producer/consumer/declaration set. Assessed Major (not Critical) under the tie-breaker because the same doc's "Provides Output To: Module 52" line (497) is correct, so a careful reader is not cleanly pointed at the wrong module; the harm is the inverted "input/source" framing.
- **Doc line**: module_31.md:309-310
- **Claim**: "`vm_carbon_stock(j,"past",ag_pools,stockType)` ... **Source**: Module 52 (Carbon) - but calculated here"
- **Reality**: `vm_carbon_stock` is DECLARED in Module 56 (`modules/56_ghg_policy/price_aug22/declarations.gms:34`), POPULATED by M31 itself (and M29/M32/M34/M35/M59) via `q31_carbon` (`equations.gms:22-24`), and READ by M52 (`modules/52_carbon/normal_dec17/equations.gms:19`). M52 is a *consumer*, not the source/declarer. Listing it under "Input Variables (From Other Modules) — Source: Module 52" inverts the relationship (M31 → M52, not M52 → M31). This is the exact G2 anchor pattern.
- **verify_cmd**: `grep -n 'vm_carbon_stock' .../56_ghg_policy/price_aug22/declarations.gms` → `34: vm_carbon_stock(j,land,c_pools,stockType) ...`; `rg -ln 'vm_carbon_stock\(' .../modules/` → includes 31_past, 29, 32, 35, 59 (populators) + 52 reads it at equations.gms:19.
- **Confirmed**: true.
- **Proposed fix**: change doc line 310 from "**Source**: Module 52 (Carbon) - but calculated here" to "**Declared in**: Module 56 (GHG policy, `price_aug22/declarations.gms:34`). **Populated here** by `q31_carbon` (M31 is one of the populators alongside M29/M32/M34/M35/M59). **Read by**: Module 52 (`normal_dec17/equations.gms:19`). This variable is a Module-31 OUTPUT, not an input." (And move it out of the "Input Variables" subsection or relabel that subsection.)

### BUG 31-3 (Minor) — Off-by-one within-equation line citations for `vm_land`, `fm_luh2_side_layers`, `fm_bii_coeff`

- **Class**: 10 (stale file:line citation) — adjacent, same-equation content.
- **Trigger** (§1 Minor): "Off-by-few line citation where adjacent lines say similar things."
- **Doc lines**: module_31.md:276 (`vm_land` usage `equations.gms:17,23,39,43`), :347 (`fm_luh2_side_layers` `equations.gms:40,40,43,43`), :359 (`fm_bii_coeff` `equations.gms:40,43`).
- **Reality**: `vm_land` appears at `equations.gms:17, 24, 40, 44` (not 17,23,39,43). `fm_luh2_side_layers` and `fm_bii_coeff` appear at lines `40 and 44` (not 40/43). The cited 23/39/43 are each the equation's `=e=`/header line one above the actual formula line (24/40/44). The equation *header* ranges elsewhere in the doc (22-24, 38-40, 42-44) are correct, so the doc is internally inconsistent on the back half of equations.gms (likely a single inserted line drift). `vm_bv` usage (line 320: `equations.gms:38,42`) is CORRECT; `vm_prod` (17,32) and `fm_carbon_density` (24) are CORRECT.
- **verify_cmd**: `grep -n 'vm_land' .../31_past/endo_jun13/equations.gms` → `17, 24, 40, 44`; `grep -n 'fm_luh2_side_layers\|fm_bii_coeff' .../equations.gms` → `40, 44`.
- **Confirmed**: true.
- **Proposed fix**: line 276 → `equations.gms:17,24,40,44`; line 347 → `equations.gms:40,40,44,44`; line 359 → `equations.gms:40,44`.

### BUG 31-4 (Minor) — Imprecise domain-set labels `kall` (vm_prod), `landcover` (vm_bv)

- **Class**: 3 (domain imprecision).
- **Trigger** (§1 Minor): "Wrong detail, careful reader not misled into action" (the literal indices in the formulas are correct; only the prose generic domain is loose).
- **Doc lines**: module_31.md:302 (`vm_prod(j,kall)`), :318 & :321 (`vm_bv(j,landcover,potnatveg)`).
- **Reality**: `vm_prod` is declared `vm_prod(j,k)` (`modules/17_production/.../declarations.gms:9`) — domain `k` (Primary products), not `kall` (`k ⊂ kall`). `vm_bv` is declared `vm_bv(j,landcover44,potnatveg)` (`modules/44_biodiversity/bv_btc_mar21/declarations.gms:19`) — the set is `landcover44`, not `landcover`. `pasture`/`manpast`/`rangeland` are members of the correct sets so the documented usages are valid; only the generic domain label is imprecise.
- **verify_cmd**: `grep -n 'vm_prod' .../17_production/*/declarations.gms` → `vm_prod(j,k)`; `grep -rn 'vm_bv\b' .../44_biodiversity/*/declarations.gms` → `vm_bv(j,landcover44,potnatveg)`.
- **Confirmed**: true.
- **Proposed fix**: line 302 `(j,kall)` → `(j,k)`; lines 318/321 `(j,landcover,potnatveg)` → `(j,landcover44,potnatveg)`. (Low priority — informational-to-minor.)

---

## Deferred (not code-verifiable / interpretive — DO NOT EDIT)

- "Centrality: ~20 of 46 modules, 6 connections (provides to 5-7, depends on 3)" (line 524) and "Provides To … Module 17" (line 527): centrality metrics are derived from an external dependency analysis, not directly checkable from a single grep. M31 constrains `vm_prod` (M17's variable) rather than providing a new variable to M17 — arguably "provides a constraint to," defensible. Not flagged.
- Mechanism chain "M70 → M16 → M21 (Trade) → M31 → M10" (lines 388-393): components exist (M16 references pasture; M21 `selfsuff_reduced/sets.gms:12,15` lists pasture as non-traded/self-sufficient). The narrative is a reasonable cross-module description; not a clean code error.
- static "Appears to be deprecated (not_used.txt present)" (line 578): `not_used.txt` is a standard MAgPIE input-bookkeeping file, not a deprecation marker; but the realization IS selectable and the doc hedges ("Appears to", "Inactive"). Interpretive, not a code bug.
- stockType gloss "Actual stocks vs. reference stocks" (line 140-141): actual members are `actual, actualNoAcEst` (`56_ghg_policy/price_aug22/sets.gms:212-213`). The doc does not assert member names, only an interpretive gloss; borderline informational, left as a note.
- Newbold et al. (2015) BII citation (line 663): literature, not code.

---

## Mechanical checks
- M1 file:line citations present: PASS (50+).
- Equation formulas: 5/5 verbatim match. PASS.
- Realization names: `endo_jun13`, `static` both exist (`ls modules/31_past/`). PASS.
- Default value: `s31_fac_req_past = 1` verified in input.gms AND default.cfg. PASS.

## Severity-weighted score (this doc, treated as one answer)
2 Major + 2 Minor → 10 − 2·2 − 1·2 = **4/10** on the raw severity formula. Verdict band "Mostly Accurate (lower band)" given the structural correctness of equations/defaults; the two Majors are localized (one domain set, one source-attribution line) and both have precise one-line fixes.
