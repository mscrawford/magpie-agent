# Round 38 Verification — module_52.md

Ground truth: `/tmp/magpie_develop_ro` (develop worktree). Config: `/tmp/magpie_develop_ro/config/default.cfg`.

---

## Bug module_52-B1 — VERDICT: UPHELD

**Class:** consumer_set (which module consumes `fm_carbon_density`)
**Severity:** Minor
**Bug class:** 10 (off-target file:line citation / citation drift — but cross-realization, not pure line drift)

**Doc claim (module_52.md:269):** `Module 31 (Past) — modules/31_past/static/presolve.gms:16`
**Auditor reality:** M31 default = `endo_jun13` (not `static`); default consumes `fm_carbon_density` at `endo_jun13/equations.gms:24` via `m_carbon_stock(vm_land,fm_carbon_density,"past")`. Cited line is correct only for the non-default `static` realization; every sibling consumer (266-273) is cited via its DEFAULT realization, so the lone static citation is inconsistent.

### STEP A — Mechanical citation check (PASS, citation_ok=true)

file_evidence + proposed_fix targets:

```
$ test -f .../31_past/static/presolve.gms          -> EXISTS
$ wc -l .../31_past/static/presolve.gms            -> 30   (line 16 in range)
$ test -f .../31_past/endo_jun13/equations.gms     -> EXISTS
$ wc -l .../31_past/endo_jun13/equations.gms       -> 47   (line 24 in range)
```

Exact-line reads:
- `static/presolve.gms:15-16`: `vm_carbon_stock.fx(j,"past",ag_pools) = pcm_land(j,"past")*fm_carbon_density(t,j,"past",ag_pools);` — line 16 contains `fm_carbon_density`. ✓
- `endo_jun13/equations.gms:22-24`: `q31_carbon(...) .. vm_carbon_stock(...) =e= m_carbon_stock(vm_land,fm_carbon_density,"past");` — line 24 contains `fm_carbon_density`. ✓

Both cited files exist, both lines in range, both contain the claimed token. citation_ok = true.

### STEP C — Adjudication (consumer_set)

**1. Default realization (config):**
```
$ grep -F 'gms$past' config/default.cfg
cfg$gms$past <- "endo_jun13"               # def = endo_jun13
```
Confirmed via two methods (grep -F + explicit `# def =` comment). Default = endo_jun13, NOT static. ✓

**2. Realization dirs:** `ls -d modules/31_past/*/` -> only `endo_jun13/` and `static/`. Both cited paths are real realizations.

**3. fm_carbon_density references per realization (rg, isolated):**
```
endo_jun13/ : equations.gms:24:  m_carbon_stock(vm_land,fm_carbon_density,"past");   (ONLY ref)
static/     : presolve.gms:16:   ...*fm_carbon_density(t,j,"past",ag_pools);          (ONLY ref)
```
The default realization references `fm_carbon_density` at exactly ONE location = `equations.gms:24` (the proposed-fix target). So the fix line is the correct AND only default-realization citation.

**4. Macro expansion — is fm_carbon_density genuinely consumed?** (macros.gms:99-101)
```
$macro m_carbon_stock(land,carbon_density,item) \
   (land(j2,item) * sum(ct,carbon_density(ct,j2,item,ag_pools)))$(sameas(stockType,"actual")) + ...
```
`m_carbon_stock(vm_land,fm_carbon_density,"past")` substitutes `fm_carbon_density` into `sum(ct,fm_carbon_density(ct,j2,"past",ag_pools))`. This is a real consumption (equation RHS), not a passed-through name. M31 default IS a true consumer. ✓ (positive control: macro found and read; `m_carbon_stock` is defined and present in core/macros.gms.)

**5. Sibling-consistency check (the inconsistency claim).** All other consumers in lines 266-273 map to their DEFAULT realization:
| Module | Cited realization | Config default | Match |
|--------|-------------------|----------------|-------|
| 14 yields | managementcalib_aug19 | managementcalib_aug19 | ✓ |
| 29 cropland | detail_apr24 | detail_apr24 | ✓ |
| 30 croparea | simple_apr24 | simple_apr24 | ✓ |
| 32 forestry | dynamic_may24 | dynamic_may24 | ✓ |
| 35 natveg | pot_forest_may24 | pot_forest_may24 | ✓ |
| 56 ghg_policy | price_aug22 | price_aug22 | ✓ |
| 59 som | cellpool_jan23 | cellpool_jan23 | ✓ |
| **31 past** | **static** | **endo_jun13** | **✗ (off-default)** |

M31 is the sole non-default citation in the list. The auditor's inconsistency claim reproduces exactly.

### Conclusion

M31 genuinely belongs in the `fm_carbon_density` consumer list (verified consumer via macro expansion in the default realization). Only the cited realization/line is off-default. The proposed fix — replace `modules/31_past/static/presolve.gms:16` with `modules/31_past/endo_jun13/equations.gms:24` — is mechanically correct (file exists, line 24 in range, line contains `fm_carbon_density`, is the unique default-realization reference) and restores consistency with the other seven default-realization citations.

**UPHELD.** Apply the fix as proposed.
