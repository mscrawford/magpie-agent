# Round 55 — Depth Audit MEASUREMENT

**Date**: 2026-07-16
**Scope**: 3 high-centrality hub docs — `module_10.md` (land), `module_52.md` (carbon), `module_56.md` (ghg_policy)
**Ground truth**: `/private/tmp/magpie_develop_ro` (read-only develop worktree)
**Role map**: `audit/integrated/depth_rolemap.json`
**Inputs**: 15 lens files + 3 verify files in this directory; only UPHELD/CORRECTED findings survive into the matrix.
**Verdict**: **TARGETED_ONLY**

---

## 0. Provenance flags (read before using any number below)

Two premises handed to this synthesizer did not survive checking. Both are recorded here rather than relayed.

1. **"The 2026-06-29 wide-net 9.52 pass" is not locatable.** `rg "9\.52"` over `audit/` returns nothing, and no round in `audit/validation_rounds.json` carries `mean_score: 9.52` or a `2026-06-29` date. The temporally nearest wide-net pass is **R52 (2026-06-28, `mean_score: 8.5`, 6 probes over the carbon/emissions cluster, code_base `6304d830b`)`. §3 evaluates "what the prior wide-net missed" against **R52 as the actual baseline**. If the orchestrator meant a different artifact, §3's mechanism still holds but its round label needs correcting.
2. **The matrix double-counts three M52 findings.** This is not my inference — `verify__module_52.md:161` states bugs 1/5/10 are "three views of one defect" and recommends merging. §2 carries both the raw and deduped arithmetic because **the go/no-go turns on which is used**.

Everything in §1 is reproduced from the supplied matrix and cross-checks against the per-doc ledger (28 confirmed = 9+11+8; 498 claims = 135+206+157; 88 attribution claims = 20+51+17). The matrix is internally consistent; the issue is semantic, not arithmetic.

---

## 1. Residual-density matrix

### 1.1 Pooled (confirmed bugs / claims checked)

| Class | Crit | Major | Minor | Info | **Confirmed** | **Denom** | **Density /100** |
|---|---:|---:|---:|---:|---:|---:|---:|
| attribution_declare | 0 | 0 | 0 | 0 | **0** | 22 | **0.00** |
| attribution_populate | 0 | 1 | 2 | 0 | **3** | 28 | **10.71** |
| attribution_read | 1 | 3 | 5 | 0 | **9** | 38 | **23.68** |
| citation | 0 | 0 | 1 | 0 | **1** | 89 | **1.12** |
| formula | 0 | 0 | 2 | 0 | **2** | 50 | **4.00** |
| default_value | 0 | 0 | 0 | 0 | **0** | 36 | **0.00** |
| realization | 0 | 0 | 0 | 0 | **0** | 3 | **0.00** |
| mechanism | 0 | 0 | 2 | 0 | **2** | 81 | **2.47** |
| data_flow_direction | 0 | 2 | 1 | 0 | **3** | 47 | **6.38** |
| set_membership | 0 | 1 | 6 | 0 | **7** | 44 | **15.91** |
| other | 0 | 0 | 0 | 1 | **1** | 60 | **1.67** |
| **TOTAL** | **1** | **7** | **19** | **1** | **28** | **498** | **5.62** |

**Critical density: 1 / 498 = 0.20 per 100 claims.**

### 1.2 Per-doc

| Doc | Claims | Confirmed | Crit | Major | Attrib. omissions | Refuted | Corrected | Citation-failed | Density /100 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| module_10 | 135 | 9 | **0** | 1 | 4 (all Minor) | 0 | 0 | 0 | 6.67 |
| module_52 | 206 | 11 | **1** | 5 | 8 | 0 | 1 | 0 | 5.34 |
| module_56 | 157 | 8 | **0** | 1 | **0** | 0 | 1 | 0 | 5.10 |

### 1.3 The dominant signal: concentration, not corpus-wide rot

- **Class concentration**: the three `attribution_*` classes hold 12 of 28 confirmed bugs (43%) on 88 of 498 claims (18%) — a **3.4× enrichment**. `attribution_read` alone runs at 23.7 per 100.
- **Doc concentration**: **module_52 carries 100% of the Criticals and 5 of 7 Majors.** module_56 has **zero attribution bugs at any severity** across 157 claims. module_10 has zero Criticals.
- **Clean classes**: `attribution_declare` (22 claims), `default_value` (36), `realization` (3) are **spotless**. Declarations and defaults are not a residual risk surface. `citation` runs at 1.12 per 100 across 89 claims — the mechanical validator's territory is in good shape.
- **0 refuted / 0 citation-failed across all three docs** — the auditors did not confabulate. 30/30 cited artifacts reproduced mechanically. This is a quality signal about the *audit*, and it means the matrix's numerator is trustworthy.

---

## 2. Dedup: the arithmetic the matrix cannot see

The matrix counts **doc-defect sites**. The decision rule asks about **defect density**. These diverge in two places, both identified by the verification pass itself.

### 2.1 M52 bugs 1 / 5 / 10 → one defect

`verify__module_52.md:161`: *"Bugs 1/5/10 are three views of one defect (M14 missing from the uncalib consumer list at 458); recommend merging to a single Critical finding."*

All three are `attribution_read` on **the same variable** (`pm_carbon_density_secdforest_ac_uncalib`) at **the same doc line** (458). Merged: **read Critical 1, read Major 3 → 1** (only bug 9, the `im_vol_conv` false M14 attribution, is an independent defect).

### 2.2 M52 bug 4 ≅ M56 bug 7 → one code fact, two doc sites

Both are the `52 → 56 vm_emissions_reg` parallel-not-serial error, verified from opposite ends (`verify__module_52.md:95-107`, `verify__module_56.md:10-94`). Two doc-sites; **one** independent discovery.

### 2.3 Major-attribution density, three ways

| Counting basis | Numerator | Denominator | Per 100 | vs ~2 bar |
|---|---:|---:|---:|---|
| Raw, attribution classes only | 4 | 88 | **4.55** | 2.3× — clears |
| **Deduped, attribution classes only** | **2** | **88** | **2.27** | **1.14× — marginal** |
| Deduped, attribution + direction, cross-doc merged | 3 | 135 | **2.22** | 1.11× — marginal |

**The GO case rests entirely on whether the double-count stands.** It does not — the verification pass explicitly retired it.

### 2.4 The deduped numerator is 2 events

A rate built on **2 events** cannot discriminate against a `~2 per 100` bar. Poisson 95% CI on 2 observed events ≈ [0.24, 7.22] → **[0.27, 8.2] per 100**. The threshold sits well inside the interval. Criterion (b)-second-clause is **not measurable at this sample size**; reporting "2.27 > 2 → GO" would be a label on a threshold-straddling number, which is exactly the failure mode that flips under any reasonable re-count.

---

## 3. What the wide-net pass missed — and the mechanism

R52 (2026-06-28) probed **this exact cluster** and scored 8.5:

| R52 probe | Score | Touched the R55 defect? |
|---|---:|---|
| G2 — `vm_carbon_stock` M52 → GHG cost in M56 | 8 | No — found the land-set error (G2-B1), never reached the uncalib consumer list |
| P2 — default `c56_emis_policy` scope | 9 | No |
| P4 — Cprice → afforestation → M32 → M52 | 8 | No |
| P5 — carbon-pool partition M52/M59 | 10 | No |

**None of the four surfaced any of the three findings that survived R55 verification.** More pointedly: `verify__module_52.md:107` notes the parallel-not-serial pattern is the **R51 anchor** — the pattern was already a known, named MANDATE, and the doc-site instances *still* survived every subsequent wide-net pass.

### Why width structurally cannot find these

**A probe-based pass samples the doc through the answerer's retrieval.** `verify__module_56.md:71` is the smoking gun:

> Lines 90-92 state the bypass **correctly** ("CO2 pricing is calculated directly from `vm_carbon_stock`, intentionally bypassing `vm_emissions_reg`"). **Line 66 contradicts it.**

module_56.md contains **both the right answer and the wrong one**. An answerer retrieves the passage that answers the question — the correct one at 90-92 — and scores 9. The contradictory line 66 is never sampled, so it never costs a point, so it survives indefinitely. The same holds for M52: the uncalib consumer list at line 458 is only read by a probe that asks about that specific curve, and no probe did.

**This is the load-bearing conclusion of the round**, and it cuts *both* ways:

- **Width does not certify doc integrity.** A 8.5 (or a 9.52) is evidence about answers, not about lines.
- **Depth-found doc defects do not imply degraded answers.** The retrieval bias that hides line 66 from the auditor also hides it from the user. The residual is a **doc-integrity defect with low measured answer-impact** — the very passages that are wrong are the ones retrieval passes over.

The two metrics are measuring different objects. Neither substitutes for the other, and **neither may be relayed as the other** (see §6).

---

## 4. Decision-rule evaluation

> **GO if EITHER** (a) ≥1 confirmed Critical-class attribution omission **per hub** surviving the wide-net pass, **OR** (b) pooled density > ~1 Critical / 2 docs **OR** > ~2 Major-attribution bugs / 100 attribution claims.

| Criterion | Threshold | Measured | Result |
|---|---|---|---|
| **(a)** Critical attribution omission **per hub** | 3 of 3 | **1 of 3** (M52 only; M10 = 0, M56 = 0) | ❌ **FAIL** |
| **(b1)** Criticals per doc | > 0.50 /doc | **0.33 /doc** (1 / 3 docs) | ❌ **FAIL** (66% of bar) |
| **(b2)** Major-attribution per 100 | > ~2.0 | **2.27** deduped (4.55 raw) | ⚠️ **MARGINAL** — CI [0.27, 8.2] spans the bar |

**Literal reading**: (b2) clears at 2.27 → GO.
**Reading I actually hold**: the rule's own premise defeats the literal reading. Stated in the brief:

> *the hubs are highest-centrality → an UPPER-BOUND sample of corpus bug density*

**I verified that premise rather than assuming it** (`audit/integrated/depth_rolemap.json`, 125 interfaces with a declaring module across 42 modules):

```
hub reader-edges per doc  = 27.0   (10_land=47, 52_carbon=19, 56_ghg_policy=15)
rest reader-edges per doc =  7.3   (39 modules, 285 edges)
centrality ratio          = 3.69x
hub ranks in corpus       = #1, #3, #7 of 42
```

The premise **holds**. The sample sits at the top of the centrality distribution by a factor of 3.7.

**Therefore**: an upper-bound sample that fails (a), fails (b1), and clears (b2) by 11% on a 2-event numerator predicts a **corpus below threshold on every criterion**. The rule's NO_GO branch describes this case exactly — *"even the densest docs are clean at depth → run mechanical-only corpus-wide (free) and reserve semantic depth for the top-centrality quartile"* — and that branch is named **TARGETED_ONLY**.

**Verdict: TARGETED_ONLY.** Not NO_GO: the residual is real, non-zero, and concentrated in a class (`attribution_read`, 23.7/100) that mechanical checks cannot see. Not GO: 39 more docs at hub-density assumptions is a campaign priced for a yield the measurement does not support.

---

## 5. Expected corpus Criticals — extrapolation

**This is an estimate with a 2-event numerator upstream of it. It is not a guarantee, and its uncertainty is dominated by the single Critical observed.**

### Derivation

**Step 1 — attribution claims per unit of centrality** (from the hub sample):
```
88 attribution claims / 81 hub reader-edges = 1.086 claims per reader-edge
```

**Step 2 — corpus attribution claim count** (39 non-hub declaring modules, 285 reader-edges):
```
285 x 1.086 = ~310 attribution claims
```

**Step 3a — flat hub density (UPPER BOUND)**:
```
hub Critical density (deduped) = 1 / 88 = 1.14 per 100
310 x 0.0114 = 3.5 Criticals across 39 non-hub module docs
```

**Step 3b — centrality-adjusted (PREFERRED)**. An incomplete-consumer-set Critical is only *possible* on an interface with ≥3 readers — with 2 readers there is no set to get wrong. That eligible surface is much thinner outside the hubs:
```
Critical-eligible interfaces (>=3 readers):  HUB 14/21 (67%)   REST 30/104 (29%)
hub rate = 1 Critical / 14 eligible interfaces = 0.071
30 x 0.071 = 2.1 Criticals across 39 non-hub module docs
```

### Result

> **expected_corpus_criticals ≈ 2–3.5 across the 39 remaining module docs**
> (centrality-adjusted **2.1**; flat-hub-density upper bound **3.5**)
> ≈ **0.05–0.09 per doc**, i.e. **one Critical per 11–19 docs**.

Against the GO bar of **1 per 2 docs**, the corpus is **5.5–9.5× below threshold**. The gap is far larger than the estimate's own uncertainty, so the conclusion is robust to the fragility of the numerator: even at **3× the observed Critical rate**, the corpus lands at ~1 per 4–6 docs — still below the bar. The verdict does not depend on the point estimate.

### Where the exposure sits

| Tier | Docs | Crit-eligible interfaces | Expected Criticals | Per doc |
|---|---:|---:|---:|---:|
| Top-centrality quartile (untested) | 8 | 15 (50%) | **1.1** | **0.14** |
| Remaining corpus | 31 | 15 (50%) | **1.1** | **0.035** |

The top quartile yields **4× more Criticals per doc** and captures **50% of total exposure for 21% of full-campaign cost** (8 docs vs 39). The efficiency gain is real but **more modest than the 3.69× centrality ratio suggests** — eligible-interface count does not track reader-edges tightly (`32_forestry`: 18 edges but **0** eligible interfaces; `09_drivers`: 35 edges, 5 eligible). Targeting by raw centrality would misallocate; **target by eligible-interface count.**

---

## 6. Attribution-class residual — reported separately

**⚠️ This section must NEVER be relayed as an answer-quality metric, in either direction.** §3 establishes why: doc-integrity and answer-quality measure different objects, and the retrieval bias that hid line 66 from R52's auditors hides it from users too. These numbers describe **lines in docs**, not **answers to users**.

| Attribution class | Confirmed | Denom | Density /100 | Crit | Major |
|---|---:|---:|---:|---:|---:|
| attribution_declare | 0 | 22 | **0.00** | 0 | 0 |
| attribution_populate | 3 | 28 | **10.71** | 0 | 1 |
| attribution_read | 9 | 38 | **23.68** | **1** | 3 (→1 deduped) |
| **Attribution total** | **12** | **88** | **13.64** | **1** | **4 (→2)** |

- Per-doc omissions: **M52 = 8, M10 = 4 (all Minor), M56 = 0.**
- `attribution_read` at **23.68 per 100** is the single worst class in the audit — ~4× the all-class mean (5.62) and ~21× the `citation` class.
- **`attribution_declare` is clean at 0/22.** Docs know *where things are declared*; they lose track of *who reads them*. The defect is directional and consistent with the mechanism in §3: declarations are stated once and stay put, whereas consumer sets silently go stale every time a new module adds a read.
- **All 12 attribution bugs are omissions — not one is a phantom.** `verify__module_10.md:54`: *"in doc not in union = (none) ← the doc's 15 are all genuine; this is a pure undercount, not a mis-set."* The docs never invent consumers; they fail to keep up with new ones. **This is a maintenance-lag signature, not a confabulation signature** — and it is the strongest argument that the residual is tractable by a cheap recurring mechanism rather than a campaign (§7).

---

## 7. Recommendation

**TARGETED_ONLY.** Three actions, in reversibility order:

**1. Fix the 28 confirmed R55 findings (do this first — it is the entire verified yield).**
Apply the verify files' *corrected* fixes, not the auditors' originals — two would introduce new errors:
- `module_52.md`: merge bugs 1/5/10 into **one** Critical fix at line 458; restore both M14 and M35, add the switch-conditionality note (`s32_aff_plantation`, `s29_treecover_plantation`). Do **not** add M14 at line 727 (wrong subsection — `verify__module_52.md:113`).
- `module_56.md`: fix lines **66** and **716** only. **Keep 52** in the whole-variable producer lists at 591/1026 — deleting it there would strip a genuine `emis_oneoff × co2_c` producer relationship (`verify__module_56.md:86`). Fix line 591's citation, which covers only `emis_annual`.
- `module_10.md`: the "15 modules" claim is stale at **ten** sites (13, 14, 275, 295, 774, 789, 791, 834, 861, 866), not the two the auditor proposed. Correct blast radius = **18**. Lines 834 → "11 modules" and 866 → "10 modules depend on `vm_land`" are wrong on their own terms (`verify__module_10.md:93-99`).

**2. Run the mechanical validator corpus-wide** (`bash scripts/validate_consistency.sh`) — free, and the `citation` class at 1.12/100 confirms it is doing its job.

**3. Depth-audit the 8 untested top-centrality docs, ranked by Critical-eligible interfaces — not by reader-edges:**

| Priority | Doc | Edges | Crit-eligible | Note |
|---|---|---:|---:|---|
| **1** | **09_drivers** | **35** | **5** | **#2 most central module in MAgPIE; never depth-audited. Highest-value single target in the corpus.** |
| 2 | 17_production | 19 | 2 | |
| 3 | 29_cropland | 13 | 3 | |
| 4 | 70_livestock | 18 | 2 | |
| 5 | 18_residues | 12 | 2 | |
| 6 | 30_croparea | 13 | 1 | |
| — | 32_forestry | 18 | **0** | Deprioritize despite high centrality — no Critical-eligible surface |
| — | 35_natveg | 12 | **0** | Same |

Expected yield: **~1.1 Criticals for 21% of a full campaign's cost.** Scope each pass to the `attribution_read` and `attribution_populate` classes plus `set_membership` (15.91/100) — and **skip `attribution_declare`, `default_value`, `realization` entirely** (0/61 combined across three hub docs). This roughly halves per-doc cost again at no measured loss.

**4. Do not depth-audit the remaining 31 docs.** Expected yield ~1.1 Criticals over 31 docs (~1 per 28) at 79% of campaign cost.

**5. Address the actual root cause instead — this is the highest-leverage item on the list.** §6 shows every one of the 12 attribution bugs is a *stale omission*, never a phantom, and §3 shows probe-based validation is structurally blind to them. Both point at the same fix: the consumer sets are **mechanically derivable from the code** — `depth_rolemap.json` already reconstructs them, and this round used it to find every one of these bugs. A recurring **role-map-vs-doc consumer-set diff** would catch this entire class continuously, at near-zero marginal cost, and would have caught all 12 findings without a single LLM audit pass. **A depth campaign pays per-doc for a defect class a diff detects for free.** Recommend scoping this check as R56 before spending further on semantic depth.

---

## 8. Assumptions that would change the conclusion

1. **The dedup.** If `verify__module_52.md:161` is wrong and bugs 1/5/10 are genuinely independent, (b2) reads 4.55/100 and the verdict flips to **GO**. I weight this low — the three findings cite the same variable at the same doc line — but it is the single load-bearing judgment in this report, and it is a judgment, not a measurement.
2. **Attribution claims scale with reader-edges (1.086/edge).** Calibrated on 3 docs. If non-hub docs document consumers more thinly per edge, §5 overestimates the denominator and the corpus rate rises.
3. **The Critical class requires ≥3 readers.** Drawn from the one observed Critical (`pm_carbon_density_secdforest_ac_uncalib`, 4 readers). **n=1 is a weak basis for a class-eligibility rule** — a Critical of a different shape (e.g. a wrong-direction data flow on a 2-reader interface) would not be captured by the eligible-interface screen, and §5's Step 3b would undercount. Step 3a (3.5) is the guard against this; both land below the bar.
4. **The 3 hubs represent the top of the centrality distribution.** Verified (ranks #1/#3/#7 of 42), and `09_drivers` at rank #2 is *not* in the sample — a plausible source of upside surprise, which is precisely why it is the #1 recommended target.
5. **`0 refuted / 0 citation-failed` means the numerator is sound.** If the verification pass was itself insufficiently adversarial, the true numerator is lower, and the case for TARGETED_ONLY only strengthens.
6. **The "9.52 baseline" is unresolved** (§0.1). §3's mechanism is baseline-independent, but if a genuine 9.52 pass exists with different probe coverage, its miss-set should be re-checked against R55's findings.
