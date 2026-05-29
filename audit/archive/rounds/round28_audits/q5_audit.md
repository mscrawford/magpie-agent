# Audit Report: Q5 (Phosphorus tracking — Module 54 default-off + cross-module connections when enabled)

**Round**: R28
**Auditor**: Opus adversarial auditor
**Verification worktree**: `/tmp/magpie-develop-r28/` @ ee98739fd (clean origin/develop)
**Answer file**: `magpie-agent/audit/archive/rounds/round28_answers/q5_answer.md`

### Overall Verdict: MOSTLY ACCURATE
### Accuracy Score: 9/10

---

## Summary judgment

This is a strong, code-faithful answer. The load-bearing thesis — **MAgPIE does NOT track phosphorus by default; M54's only realization is `off`, which declares a single variable `vm_p_fert_costs(i)`, fixes it to zero, and defines zero equations** — is fully verified. The Critical trigger for this round ("Active mechanism claimed when OFF by default") does NOT fire: the answer correctly states `off`, labels all 11 P-flows as intended/not-implemented, and frames every cross-module linkage as hypothetical ("when/if enabled", "would be"). Every file:line citation I checked (M54, M18, M50, M59) is exact. One genuine factual error: the answer claims P content of **belowground** residues is "already computed" by M18, but the BG production equation ranges only over `dm_nr = {dm,nr,c}`, which excludes phosphorus. Scored Minor (small blast radius, AG half correct, off-realization context).

---

## Verified Claims (correct)

**M54 core (the spine):**
- "Module 54's only realization is `off`" — CONFIRMED. `ls modules/54_phosphorus/` shows only `off/` (+ `module.gms`). `config/default.cfg`: `cfg$gms$phosphorus <- "off"  # def = off`.
- "0 equations are active" — CONFIRMED. No `equations.gms` exists in `off/`; phases are declarations/preloop/postsolve only (`off/realization.gms:13-17`).
- "1 variable exists: `vm_p_fert_costs(i)` ... declared in `off/declarations.gms:10`" — CONFIRMED exactly (`off/declarations.gms:9-10`).
- "fixed to zero in `off/preloop.gms:10`: `vm_p_fert_costs.fx(i)=0;`" — CONFIRMED verbatim (`off/preloop.gms:10`).
- `realization.gms:8-9` deactivation quote — CONFIRMED verbatim.
- `realization.gms:11` "still under development" — CONFIRMED verbatim.
- `module.gms:27-28` future-development quote — CONFIRMED verbatim.
- 11 intended P-flows cited at `module.gms:14-24` (answer block-cites 12-24) — CONFIRMED; the bullet list spans lines 14-24, line 12-13 is the framing sentence. Answer correctly labels all as "intended structure, not implemented code."
- "P does not volatilize during burning, unlike N" (module.gms:17) — CONFIRMED against `module.gms:17` ("no combustion losses assumed").

**M18 (residues, `flexreg_apr16` — default CONFIRMED):**
- `q18_res_recycling_pk(i2,pk18)` at `flexreg_apr16/equations.gms:104-110` — CONFIRMED exactly, body matches (sum of `v18_res_ag_recycling` + `vm_res_ag_burn`, no combustion-eff term, no BG term).
- Set `pk18 = {p, k}` at `flexreg_apr16/sets.gms:14-15` — CONFIRMED exactly (`pk18(npk) ... /p, k/`).
- Contrast with `q18_res_recycling_nr` at `equations.gms:90-96` — CONFIRMED; the N equation DOES carry `*(1-f18_res_combust_eff(kcr))` (line 94) and `vm_res_biomass_bg(i2,kcr,"nr")` (line 95), both absent from the P/K equation. Answer's contrast is precisely right.
- `vm_res_recycling(i,npk)` produced by M18 → so `vm_res_recycling(i,"p")` is valid; "part of the `npk` attribute set" — CONFIRMED (`declarations.gms:16`; `npk = {nr,p,k}` core/sets.gms:294-295).
- `q18_prod_res_ag_reg` at `equations.gms:14-19` applying `f18_attributes_residue_ag(attributes,kcr)` — CONFIRMED exactly (line 19); `attributes = {dm,ge,nr,p,k,wm,c}` includes p (core/sets.gms:284-285), so AG-P IS computed.

**M50 (N soil budget, `macceff_aug22` — default CONFIRMED):**
- `q50_nr_bal_crp(i2)` at `macceff_aug22/equations.gms:14-16`, body `vm_nr_eff(i2) * v50_nr_inputs(i2) =g= sum(kcr,v50_nr_withdrawals(i2,kcr))` — CONFIRMED verbatim.
- `vm_res_recycling(i2,"nr")` consumed at `equations.gms:24` — CONFIRMED exactly.
- `vm_nr_som_fertilizer(j2)` consumed at `equations.gms:30` (`sum(cell(i2,j2),vm_nr_som_fertilizer(j2))`) — CONFIRMED exactly.
- `vm_nr_inorg_fert_costs(i)` flows M50 → M11 — CONFIRMED (declared in M50 declarations.gms; consumed in `11_costs/default/equations.gms`).
- `vm_manure_recycling(i,"nr")` analogy — variable CONFIRMED (`55_awms/ipcc2006_aug16/declarations.gms:21`, dim `(i,npk)`).

**M59 (SOM, `cellpool_jan23` — default CONFIRMED, 2 realizations exist: cellpool_jan23 + static_jan19):**
- `q59_nr_som(j2)` at `equations.gms:69-75`, produces `vm_nr_som(j)` — CONFIRMED exactly.
- C:N = 15:1 at `equations.gms:76` ("carbon to nitrogen ratio of soils assumed to be 15:1"; `*1/15` at line 71) — CONFIRMED exactly.
- `q59_nr_som_fertilizer(j2)` at `equations.gms:81-84`, `vm_nr_som_fertilizer(j2) =l= vm_nr_som(j2)` — CONFIRMED verbatim.
- `q59_nr_som_fertilizer2(j2)` at `equations.gms:88-91`, `vm_nr_som_fertilizer(j2) =l= vm_landexpansion(j2,"crop") * s59_nitrogen_uptake` — CONFIRMED verbatim.
- `s59_nitrogen_uptake` at `input.gms:9` — CONFIRMED. Literal value is `0.2` (tN/ha); answer states "200 kg N/ha". These are numerically identical (0.2 tN = 200 kg N), and code comment `equations.gms:93` reads "maximum of 200 kg". module_59.md:237 frames it as "200 kg N/ha = 0.0002 Mt N/Mha". NOT a bug — correct unit conversion matching the doc and the code's own comment.
- "No C:P ratio, no SOM-P release variable" — CONFIRMED. `grep -i phosphor modules/59_som/` returns empty; declarations.gms:8-47 contains only C and N variables (`vm_nr_som`, `vm_nr_som_fertilizer`, `v59_som_pool`, `p59_carbon_density`).

**Mechanical checks:**
- M1 (file:line present): PASS.
- M2 (active realization stated): PASS — all four modules' realizations stated and correctly matched to default.
- M3 (variable prefixes valid): PASS.
- M4 (epistemic badges): PARTIAL — closing Source block carries 🟡 badges; body claims lack inline badges. Informational only.
- M5 (tier matches depth): PASS — answer is honestly self-tagged 🟡 "documented" (docs-only), citations are doc-sourced. Consistent.
- M6 (closing source statement): PASS — Source section present (paraphrased template; substance intact).

---

## Bugs Found

### Bug Q5-B1
- **Bug ID**: Q5-B1
- **Severity**: Minor
- **Class**: 3 (Suffix/dimension truncation)
- **Trigger**: §1 Major "Right concept, wrong detail that misleads about behavior" considered, then tie-breaker pulls to Minor (small blast radius; off-realization hypothetical context; AG half correct; answer's surrounding narrative is internally correct).
- **Claim in answer** (line 83): "The attribute dimension includes 'p' (phosphorus), so P content in aboveground **and belowground** residues is already computed — it simply has no downstream consumer while Module 54 is off."
- **Reality in code**: The belowground residue production equation `q18_prod_res_bg_reg(i2,kcr,dm_nr)` ranges over `dm_nr`, NOT `attributes`. `dm_nr = /dm, nr, c/` (`flexreg_apr16/sets.gms:11-12`) — it EXCLUDES phosphorus. Only the AG equation `q18_prod_res_ag_reg(i2,kcr,attributes)` ranges over the full `attributes` set (which contains p). Therefore P content in **belowground** residues is NOT computed; only AG-P is.
- **File evidence**:
  - `/tmp/magpie-develop-r28/modules/18_residues/flexreg_apr16/equations.gms:24` — `q18_prod_res_bg_reg(i2,kcr,dm_nr) ..`
  - `/tmp/magpie-develop-r28/modules/18_residues/flexreg_apr16/sets.gms:11-12` — `dm_nr(attributes) dry matter and nr /dm, nr, c/`
  - Contrast `equations.gms:14` — `q18_prod_res_ag_reg(i2,kcr,attributes) ..` (full attribute set, includes p at core/sets.gms:284-285).
- **Why Minor not Major**: (a) The AG half of the claim is correct. (b) The error sits in a hypothetical "when enabled" supporting detail, not in the default-state spine. (c) The answer's own adjacent text is correct and consistent with BG-P being absent: line 79 ("P/K from roots is treated as already in the soil") and line 134 ("a P budget would need to model soil P pools ... rather than inheriting"). (d) M54 is off, so no reader is wiring a BG-P flow into a live edit. No cascade, no wrong-file action.
- **tier_uncertainty**: true (defensibly Major under a strict reading of "misleads about behavior", since it overstates what M18 currently exposes; downgraded per tie-breaker).
- **Anchor reference**: Resembles the R16 suffix/dimension-handling family (set-member/dimension precision), but at far lower blast radius than the `ac140`-vs-`ac300` Critical anchor.

---

## Latent Doc Bugs (§1.5) — recorded independent of answer score

### Doc note D1 (NOT a scored bug; sub-load-bearing imprecision)
- **Root cause candidate**: `doc_error_answerer_beat_it`? — NO. The answer did not beat a wrong doc here; it inherited a benign gloss.
- **Doc claim**: `module_54.md:35` — "`vm_p_fert_costs(i)` ... Description: **Costs for mineral phosphorus fertilizers** (mio. USD17MER per yr)". Answer line 16 reproduces "costs for mineral **phosphorus** fertilizers".
- **Code**: `off/declarations.gms:10` — "`vm_p_fert_costs(i)` costs for mineral fertilizers (mio. USD17MER per yr)". The code description does NOT contain the word "phosphorus".
- **Assessment**: Informational, NOT recorded as a §1.5 Critical. The doc inserted an interpretive "phosphorus" into a variable description (the variable lives in the phosphorus module; the gloss is fair, not a fabricated name or wrong consumer set). It is not load-bearing (not an interface var/equation/consumer-set/realization/default error per the §1.5 mandate scope). No doc fix mandated; optional tightening only.
- **No other latent doc bugs found.** module_18.md (lines 89, 117, 121, 254-260, 270), module_50.md (lines 32, 88, 94, 241, 247, 255), and module_59.md (lines 176, 189, 199, 220, 225, 237) all match code exactly on the borrowed claims. Notably module_18.md:121 itself shows `q18_prod_res_bg_reg(i2,kcr,dm_nr)` (BG over dm_nr) — i.e., the doc is CORRECT on the BG dimension, and the answerer's B1 error is an answerer over-read, NOT a doc defect.

---

## Missing Nuances (non-bugs)

- The answer says `vm_p_fert_costs(i)` "would flow from Module 54 to Module 38 (Factor Costs) and Module 11 (Costs)". The M38 hop is speculative (the variable is fixed to zero and currently has no consumer); appropriately hedged as "would". The verified N analogue (`vm_nr_inorg_fert_costs` → M11) is correct. Fine as-is.
- Production-cost underestimate "~5-10%" / "P is 10-20% of fertilizer costs" is borrowed from module_54.md:160/198/361 and is clearly framed as an estimate, not a code output. Out of scope for code-accuracy scoring.

---

## Score computation

```
critical = 0, major = 0, minor = 1, informational = 1 (M4 badge gap, treated informational)
raw_severity_weighted = 4*0 + 2*0 + 1*1 + 0*1 = 1
score_0_10 = 10 - 1 = 9
```

**Score: 9/10 — MOSTLY ACCURATE (upper band).** The Critical OFF-by-default trigger explicitly does NOT fire (handled correctly). The sole content error is a Minor dimension over-read on BG residue phosphorus.
