# Adversarial verification — module_10.md (Round 55 depth)

**Target doc**: `/Users/turnip/Documents/Work/Workspace/magpie/magpie-agent/modules/module_10.md` (898 lines)
**Ground truth**: `/private/tmp/magpie_develop_ro` (develop worktree, read-only)
**Role map**: `audit/integrated/depth_rolemap.json`
**Default realization (M10)**: `landmatrix_dec18` (`config/default.cfg`) — sole realization; `ls /private/tmp/magpie_develop_ro/modules/10_land/` → `input`, `landmatrix_dec18`, `module.gms`

---

## Bug `module_10:4` — Major — set_membership

**Claim**: Doc's summary blast-radius ("15 modules") undercounts. M10 also owns `pcm_land`, read by 13_tc, 44_biodiversity, 56_ghg_policy — none of which appear in the 15-list. True distinct-dependent count = 18. Contradicts the doc's own line ~316.

**Verdict: UPHELD** · citation_ok = **true** · class = **consumer_set**

### STEP A — Mechanical citation check

| Cited file:line | `test -f` | `wc -l` | Line content | Token present? |
|---|---|---|---|---|
| `modules/13_tc/endo_jan22/presolve.gms:9` | PASS | 81 | `pc13_land(i,"pastr") = sum(cell(i,j),pcm_land(j,"past"));` | ✅ `pcm_land` |
| `modules/44_biodiversity/bii_target/preloop.gms:15` | PASS | 21 | `  sum((cell(i,j),land), pcm_land(j,land) * i44_biome_share(j,biome44));` | ✅ `pcm_land` |
| `modules/56_ghg_policy/price_aug22/preloop.gms:10` | PASS | 123 | `pcm_carbon_stock(j,land,ag_pools,stockType) = fm_carbon_density("y1995",j,land,ag_pools)*pcm_land(j,land);` | ✅ `pcm_land` |

Supporting citations in the claim:
- `10_land/declarations.gms:11` — **path as written does not exist** (`sed: No such file or directory`); the real path is `10_land/landmatrix_dec18/declarations.gms:11` → ` pcm_land(j,land)              Land area in previous time step including possible changes after optimization (mio. ha)` ✅. The doc itself (line 316) writes the same realization-less shorthand. Content claim holds; path shorthand is imprecise, not fatal.
- `10_land/landmatrix_dec18/postsolve.gms:9` → `pcm_land(j,land) = vm_land.l(j,land);` ✅ populated.

Doc-side line numbers (all confirmed by `grep -n`):
- `module_10.md:789` → `- **Provides to**: 15 modules (11, 14, 22, 29, 30, 31, 32, 34, 35, 39, 50, 58, 59, 71, 80)` ✅
- `module_10.md:791` → `- **Impact**: Changes to Module 10 affect **15 modules** - most critical module for testing` ✅
- `module_10.md:316` → the `vm_land` consumer list; the pcm_land/13/44/56 sentence sits at line 318 (auditor's "316-318" range is right) ✅
- `module_10.md:891` → `pcm_land` row of the *Provided to Other Modules* table, text: "12 direct consumers including 13_tc, 44_biodiversity, 56_ghg_policy" ✅

**citation_ok = true.**

### STEP C — Independent re-derivation (consumer_set)

Role map, restricted to `declared_in == "10_land"`, external readers only (`!= 10`):

```
pcm_land                | pop: 10,32,34,35 | read: 13,22,29,31,32,34,35,44,56,58,59,71   (12)
pm_land_hist            | pop: 10          | read: 29
pm_land_start           | pop: 10          | read: 14,32,59,71
vm_cost_land_transition | pop: 10          | read: 11
vm_land                 | pop: 10,29,31,32,34,35 | read: 22,29,30,31,32,34,35,50,58,59
vm_landdiff             | pop: 10          | read: 80
vm_landexpansion        | pop: 10          | read: 35,39,58,59
vm_landreduction        | pop: 10          | read: 39,58
vm_lu_transitions       | pop: 10          | read: 29,35,59

UNION = 11,13,14,22,29,30,31,32,34,35,39,44,50,56,58,59,71,80  → count 18
doc 15-list            = 11,14,22,29,30,31,32,34,35,39,50,58,59,71,80  → count 15
in union not in doc    = 13, 44, 56
in doc not in union    = (none)  ← the doc's 15 are all genuine; this is a pure undercount, not a mis-set
```

`pcm_land`'s 12 external readers match the doc's own "12 direct consumers" at lines 318/891 — so the doc's detail layer is right and its summary layer is stale.

**BOTH-endpoints grep (`NAME(` and `NAME.`), isolated commands:**

```
$ rg -n "pcm_land\(" /private/tmp/magpie_develop_ro/modules/13_tc/ ...44_biodiversity/ ...56_ghg_policy/
13_tc/endo_jan22/presolve.gms:9,10,40      (default realization: endo_jan22)
13_tc/exo/presolve.gms:8,9,16              (non-default, same dependence)
44_biodiversity/bii_target/preloop.gms:15  (default realization: bii_target)
56_ghg_policy/price_aug22/preloop.gms:10   (default realization: price_aug22)
```

Defaults confirmed in `config/default.cfg`: `tc <- "endo_jan22"` (:293), `biodiversity <- "bii_target"` (:1435), `ghg_policy <- "price_aug22"` (:1631) — i.e. all three dependencies are live under the default config, not a non-default-only artifact.

**Do 13/44/56 read any OTHER M10-owned var?** (would mean they should already be in the 15-list for a different reason)

```
$ rg -n "vm_land\b|pm_land_start|pm_land_hist|vm_lu_transitions|vm_landexpansion|vm_landreduction|vm_landdiff|vm_cost_land_transition" \
     .../13_tc/ .../44_biodiversity/ .../56_ghg_policy/
EXIT=1  (no matches)

POSITIVE CONTROL, same dirs, same command form:
$ rg -n "pcm_land\b" .../13_tc/ .../44_biodiversity/ .../56_ghg_policy/ | wc -l   → 9
$ rg -c "vm_carbon_stock" .../56_ghg_policy/price_aug22/equations.gms            → 2
```
Search machinery proven live in those exact directories → the zero is real. `pcm_land` is the **only** M10 interface these three consume. Union therefore = 15 + 3 = **18**, independently reproducing the auditor's count.

**Second positive control on the `.`-attribute rule** (guards against a false "M22 doesn't read vm_land"):
```
$ rg -n "vm_land\(" .../22_land_conservation/   → (empty)
$ rg -n "vm_land"   .../22_land_conservation/   → area_based_apr22/presolve_ini.gms:86,97,108: "- vm_land.lo(j,\"crop\")"
```
M22 reads `vm_land` solely via `.lo`. Confirms the both-forms discipline was necessary and that the probe above (which included `vm_land\b`) would have caught any `.`-form read in 13/44/56.

### Scope note (beyond the auditor's proposed fix)

The auditor proposes updating lines 14 and 791. `grep -n` finds the stale "15" at **ten** sites: 13, 14, 275, 295, 774, 789, 791, 834, 861, 866. A fix touching only 14/791 leaves eight contradictions.

Two of those sites are wrong on their own terms, independent of this bug (not counted as part of this finding, flagged for the maintainer):
- `:834` — "Provides interface to: 15 modules via `vm_land`, `vm_landexpansion`, `vm_landreduction`, `vm_lu_transitions`". Union of readers of just those four = {22,29,30,31,32,34,35,39,50,58,59} = **11**, not 15.
- `:866` — "15 modules depend on `vm_land`". `vm_land` alone has **10** external readers (the doc's own line 316 says 10).

Recommended fix, superseding the auditor's: set the M10 blast radius to **18 distinct dependent modules** (union over all nine M10-declared interfaces), enumerate `11, 13, 14, 22, 29, 30, 31, 32, 34, 35, 39, 44, 50, 56, 58, 59, 71, 80` at :789, and propagate to :13 (`20 total connections (2 inputs, 18 outputs)`), :14, :275, :295, :774, :791, :861. Repair :834 to "11 modules" and :866 to "10 modules depend on `vm_land`; 18 depend on Module 10 overall".

### corrected_claim

None — the auditor's substantive claim reproduces exactly. Two refinements recorded above (declaration path needs the `landmatrix_dec18/` segment; the fix must cover ten "15" sites, not two), neither of which changes the finding.
