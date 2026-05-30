# Round 37 Adversarial Verification — module_34.md (Consumer/Populator/Dependency-set focus)

Verifier: adversarial (Opus 4.8 1M). Ground truth: /tmp/magpie_develop_ro. Default stance: skepticism.

Three auditor bugs supplied. Classification:
- **M34-B1** — consumer-set claim (omitted consumer M56 of `vm_carbon_stock`). VERIFY RIGOROUSLY.
- **M34-B2** — hardcoded variable count drift inside M34's own realizations. NOT a consumer-set claim.
- **M34-B3** — content-level citation mismatch (`i34_urban_area` presence in `static`). NOT a consumer-set claim.

Per method: B2 and B3 receive verdict NOT_CONSUMER_SET and pass to the fixer unchanged. (For the record, both auditor facts also reproduce in code — see notes below — but they are out of scope for consumer-set verification and I spend no adjudication effort beyond confirming the class.)

---

## M34-B1 — UPHELD (omitted consumer M56 is real)

### Claim
Doc lists Module 52 as the sole recipient of M34's urban `vm_carbon_stock` slice (lines 197, 288-290, 473). Auditor says M56 (GHG policy) is also a direct reader and is omitted; also that `vm_carbon_stock` is declared in M56, not M52.

### Independent re-derivation of `vm_carbon_stock` consumer/producer set

Both grep forms run as standalone commands (isolated; no chaining).

**Paren/equation form** `vm_carbon_stock(` (declarations excluded):
```
rg -n 'vm_carbon_stock\(' /tmp/magpie_develop_ro/modules/ | grep -v 'declarations.gms'
```
Results:
- 29_cropland/{detail,simple}_apr24/equations.gms — DEFINE crop slice (`=e=` LHS)
- 31_past/endo_jun13/equations.gms:23 — DEFINE past slice
- 32_forestry/dynamic_may24/equations.gms:108 — DEFINE forestry slice
- 35_natveg/pot_forest_may24/equations.gms:43,50,54 — DEFINE primforest/secdforest/other
- 59_som/{cellpool_jan23:62, static_jan19:12,18,22}/equations.gms — DEFINE soilc slices
- **52_carbon/normal_dec17/equations.gms:19** — READS `vm_carbon_stock(j2,land,c_pools,"actual")` (CO2 accounting, q52_emis_co2_actual)
- **56_ghg_policy/price_aug22/equations.gms:22** — READS `vm_carbon_stock(j2,land,c_pools,"%c56_carbon_stock_pricing%")` (emission pricing, q56_emis_pricing_co2)

**Attribute form** `vm_carbon_stock.` (.l/.lo/.up/.fx/.m/.scale) — the solution-level read a paren grep misses:
```
rg -n 'vm_carbon_stock\.' /tmp/magpie_develop_ro/modules/
```
Results:
- 34_urban/exo_nov21/presolve.gms:8 and 34_urban/static/presolve.gms:10 — `.fx(...,"urban",ag_pools,stockType)=0` (M34 = the POPULATOR of the urban slice)
- **56_ghg_policy/price_aug22**: postsolve.gms:8 (`pcm_carbon_stock = vm_carbon_stock.l`), :11/:25/:39/:53 (.m/.l/.up/.lo into ov_carbon_stock), preloop.gms:11 (`.l` init), scaling.gms:10 (`.scale`)
- 59_som/{cellpool_jan23/preloop:32,35; static_jan19/preloop:12} — `.l` init of soilc
- 31_past/static/presolve.gms:15 — `.fx(...,"past",...)`

**Declaration site** (auditor's secondary claim):
```
rg -n 'vm_carbon_stock' /tmp/magpie_develop_ro/modules/*/*/declarations.gms
```
Only hit for the exact token `vm_carbon_stock(`: **56_ghg_policy/price_aug22/declarations.gms:34**. (M30's `vm_carbon_stock_croparea` is a different variable.) Confirmed: declared in M56, NOT M52.

**Positive controls** (prove the search works in each candidate dir before any absence call):
```
rg -n 'pcm_carbon_stock' /tmp/magpie_develop_ro/modules/56_ghg_policy/price_aug22/   -> 5 hits (works)
rg -n 'pcm_carbon_stock' /tmp/magpie_develop_ro/modules/52_carbon/normal_dec17/      -> 1 hit  (works)
```

**Does the urban slice actually reach M56/M52?** `urban` is a member of set `land`:
```
rg -n 'urban' /tmp/magpie_develop_ro/core/sets.gms
-> 251:  / crop, past, forestry, primforest, secdforest, urban, other /   (set 'land')
```
So M52's and M56's `sum((cell(i2,j2),...),land,...)` both span the urban slice. The slice is fixed to 0 (M34 presolve), so no numeric propagation, but the structural consumer link to M56 is real — exactly the "value is 0 so look-alike phantom?" trap, resolved in favor of a real listing.

**Defaults active** (so this is not a non-default realization artifact):
```
rg -n 'cfg\$gms\$(carbon|ghg_policy)\b|c56_carbon_stock_pricing' /tmp/magpie_develop_ro/config/default.cfg
-> carbon <- "normal_dec17"; ghg_policy <- "price_aug22"; c56_carbon_stock_pricing <- "actualNoAcEst"
```
Both M52 normal_dec17 and M56 price_aug22 (the readers found) are the defaults.

**Equation names in the proposed-fix prose** (verified exact, so the fix introduces no new fabrication):
```
rg -n 'q52_emis' .../52_carbon/normal_dec17/equations.gms -> q52_emis_co2_actual (line 16)
rg -n 'q56_emis_pricing' .../56_ghg_policy/price_aug22/equations.gms -> q56_emis_pricing_co2 (line 19)
```

### Verdict: UPHELD
M56 is a genuine, direct (one-hop) consumer of `vm_carbon_stock` including the urban slice M34 populates, and it is absent from the doc's downstream/output lists (197, 288-290, 473). The declaration-in-M56-not-M52 sub-claim also holds. Auditor's proposed fix is accurate verbatim (equation names and the `ag_pools`/`stockType` indexing match code). No correction needed.

DIRECT vs TRANSITIVE (MANDATE 17): M56 reads `vm_carbon_stock(...)` literally in q56_emis_pricing_co2 — DIRECT, not via an intermediary. Correctly described as a direct recipient.

---

## M34-B2 — NOT_CONSUMER_SET (passes through unchanged)

Claim is about how many *variables* the `static` realization eliminates vs `exo_nov21` (3 vs 2). This concerns M34's own internal declarations, not the producer/consumer set of any interface variable. Class = false -> NOT_CONSUMER_SET.

(Confirmed incidentally and consistent with auditor: static/declarations.gms declares only `vm_cost_urban(j)` (line 10); exo_nov21/declarations.gms declares `vm_cost_urban`, `v34_cost1`, `v34_cost2` (lines 13-15). static thus drops 2 variables — v34_cost1, v34_cost2 — and keeps vm_cost_urban (fixed to 0 in static/presolve.gms:14). Not adjudicated further — out of scope.)

---

## M34-B3 — NOT_CONSUMER_SET (passes through unchanged)

Claim is a content-level citation mismatch: whether `i34_urban_area` participates in the `static` presolve equality at module_34.md:514. No producer/consumer-set assertion about an interface variable. Class = false -> NOT_CONSUMER_SET.

(Confirmed incidentally and consistent with auditor: static/realization.gms:16-20 includes only declarations/presolve/postsolve — no input.gms, no preloop. static/presolve.gms:9 is `vm_land.fx(j,"urban") = pcm_land(j,"urban");` with no `= i34_urban_area` term. `i34_urban_area` is declared/defined only in exo_nov21 (declarations.gms:9, preloop.gms:11-17). Not adjudicated further — out of scope.)

---

## Summary
- M34-B1: **UPHELD** — omitted direct consumer M56 confirmed via both grep forms + positive control + set-membership + default check; equation names in fix verified. The highest-risk class (omitted consumer) reproduces cleanly.
- M34-B2: **NOT_CONSUMER_SET**
- M34-B3: **NOT_CONSUMER_SET**
