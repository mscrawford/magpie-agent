# Verifiers — MANDATEs for anti-confabulation

**Purpose**: 20 binding rules that prevent the recurring confabulation patterns identified across the semantic-validation rounds (see `audit/validation_rounds.json.cumulative_stats` for current bug and round totals). Each MANDATE has a trigger (when it applies), a binding rule (what is FORBIDDEN or REQUIRED), and a worked example (a real failure that motivated it).

**Auto-load**: this file is loaded automatically when the user asks about specific GAMS modules, variables, equations, realizations, or default values. See `AGENT.md` Auto-Loading Context Helpers table.

**Auto-load triggers**: "vm_", "pm_", "v<N>_", "p<N>_", "s<N>_", "c<N>_", "q<N>_", "realization", "default value", "default realization", "modify code", "variable name", "equation name", "M_X uses vm_", "M_X consumes"

**Binding language**: MUST, FORBIDDEN, NEVER, ALWAYS are normative. If you cannot satisfy a MANDATE, state that explicitly rather than constructing a plausible workaround.

**Cross-references**: each MANDATE references `audit/validation_rounds.json` round R-numbers and `core_docs/Bug_Taxonomy.md` patterns. See `audit/flywheel_rubric.md` for severity scoring.

**Lessons count**: 0 entries

---

## Origin (read once)

Semantic validation across many rounds (R1 began 2026-03-07; see `audit/validation_rounds.json` for the current count and dates) revealed that **~56% of bugs are plausible confabulations** — the agent invents correct-sounding but wrong details. Scores improved from 6.7→8.2 after rules 1-6 were drafted, but R3 showed an 85% confabulation rate when probing less-familiar modules. R16 added rules 10-12 (set-sum expansion, range truncation, label generalization) after critical confabulations recurred. R20 added rules 13-16 (interface-parameter consumer grep, deprecated-name italics, post-rename grep, citation full-path) after 13 line-drift bugs and a Major consumer-omission bug in a single sync. R33-R37 (the 35-doc high-centrality sweep) added rules 18-20 (producer/declaration attribution; realization-structure from the SPECIFIC realization's files; solution-level `.l/.lo` grep) and extended rule 16 (citation CONTENT, not just range) after the dominant residual vein proved to be DECLARED-vs-POPULATED-vs-READ confusion + correlated cross-realization confabulation + paren-restricted greps missing `.l` reads.

These are NOT preferences. They are evidence-derived rules. Violating them silently was the failure mode the rules close.

---

## MANDATE 1 — Formula provenance

**Trigger**: any answer that includes a mathematical formula, equation, or numerical expression.

**Rule**: NEVER construct formulas from memory. If the docs don't contain the exact formula, you MUST say "The docs don't include this formula — let me check the source code" and then read the actual `.gms` file before answering.

**Worked example**: agents have repeatedly invented plausible-looking algebraic expressions that don't appear in any `.gms` file. The rule was added after multiple Critical-severity bugs where the user would have implemented the fabricated formula.

**Verification**: cite `modules/XX_name/realization/equations.gms:NN` for every formula you write. A formula without a citation is presumed fabricated.

**Verified by**: human review (no mechanical guard — formula-presence detection is a candidate for future mechanization; see R1 audit Cluster 4).

---

## MANDATE 2 — Causal-mechanism provenance

**Trigger**: any cross-module interaction description ("X affects Y", "when X changes, Y responds").

**Rule**: NEVER invent causal mechanisms. Cite specific variables and equations from docs or code that connect the modules. If you cannot find the connecting mechanism, say so explicitly.

**Worked example**: cross-module answers are highest-confabulation territory because the connecting variable name is often pattern-matched rather than looked up. R3 had a 85% confabulation rate on cross-module questions until this rule landed.

**Verified by**: human review (no mechanical guard).

---

## MANDATE 3 — Default-parameter verification

**Trigger**: any claim about a default value for a scenario switch (`c<N>_*`), scalar (`s<N>_*`), or year threshold (`sm_*`).

**Rule**: ALWAYS verify against `../config/default.cfg` before citing. Default values change across MAgPIE versions; memorized or doc-stated values may be stale.

**Verification command**: `grep "cfg\$gms\$<switch_name>" ../config/default.cfg` for scenario switches; `grep "<scalar_name>" ../config/default.cfg` for scalars.

**Worked example**: `s42_pumping` was widely assumed to default to 1; default is 0 (water cost disabled). Several Critical-severity bugs where the agent described a feature as active when it's OFF by default.

**Verified by**: `scripts/check_default_realizations.py` (default realizations only); for scalar/scenario defaults — human review (candidate for future Pattern 13 mechanization; see R1 audit Cluster 4).

---

## MANDATE 4 — Capability vs default

**Trigger**: any answer that describes a feature, mechanism, or scenario.

**Rule**: ALWAYS state the default state of the mechanism. If a feature requires a non-default switch, the answer MUST say: "This feature exists but is **disabled by default** (`<switch> = 0`)" or similar.

**Worked example**: water pumping costs (`s42_pumping`) — present in the code, OFF by default. Without this MANDATE, the agent describes the mechanism as if it were always active, leading users to assume their default runs include it.

**Verified by**: human review.

---

## MANDATE 5 — Pseudocode labeling

**Trigger**: any code-like illustration in an answer.

**Rule**: NEVER present pseudocode as real code. If you are illustrating a concept, you MUST label it: "Conceptually: ..." not "The code does: ...".

**Worked example**: agents have written `if (vm_X > threshold) then activate(Y)` style pseudocode that looks like GAMS but isn't. Readers acting on pseudocode try to copy-paste it into the model and fail in ways that are hard to debug.

**Verified by**: human review.

---

## MANDATE 6 — Module characterization lookup

**Trigger**: ANY characterization of a module's purpose, behavior, or scope — even one-sentence descriptions.

**Rule**: NEVER characterize a module you haven't just looked up. Before writing "Module XX handles Y", you MUST read `modules/module_XX.md`. R2 validation found wrong module characterizations were the #1 remaining bug class after the first cycle of fixes.

**Worked example**: "Module 38 handles factor costs for all crops, livestock, residues" — actually only `vm_cost_prod_crop` is Module 38; livestock costs are Module 70, residues Module 18, pasture Module 31 (see MANDATE 9).

**Verified by**: human review.

---

## MANDATE 7 — Variable-name lookup

**Trigger**: any GAMS variable, parameter, scalar, or input name in an answer (`vm_*`, `pm_*`, `v<N>_*`, `p<N>_*`, `s<N>_*`, `f<N>_*`, `i<N>_*`, `pcm_*`, etc.).

**Rule**: NEVER construct variable or parameter names from patterns. ALWAYS look up the actual name in `modules/module_XX.md` or by grepping the GAMS code: `grep -rn "<candidate_name>" ../modules/*/declarations.gms`. If you cannot find it, state that the name was not located.

<!-- check-gams-vars: allow vm_water_available, vm_water_demand, pcm_AEI -->
**Worked example** (R3, 2026-03-07): the agent invented `vm_water_available`, `vm_water_demand`, `pcm_AEI` — combining MAgPIE naming conventions (vm_ for interface, water domain, AEI = Area Equipped for Irrigation). None exist. The actual variables are different.

**Verification**: `python3 scripts/check_gams_variables.py` after writing; it greps for every backtick-quoted variable name against the actual declarations.

**Verified by**: `scripts/check_gams_variables.py` (Python) — backtick-quoted vm_/pm_/v<N>_/p<N>_/s<N>_/f<N>_/i<N>_/pcm_/c<N>_/cm_/sm_ names only (R2 follow-up extended the prefix coverage). **Gap**: unbacktiked prose names (~82% of references) are NOT checked.

**Per-doc allowlist marker**: legitimate placeholders that can't be resolved at validation time (e.g., MACC type-templated names like `f57_maccs_<type>`, or external references not yet committed) can be exempted with an HTML comment marker placed anywhere in the doc:
```html
<!-- check-gams-vars: allow vm_imagined_xyzzy -->
<!-- check-gams-vars: allow im_gdp_pc_ppp -->
```
Use sparingly — every allowlist entry is a verification escape hatch. The marker is parsed strictly (`<!-- check-gams-vars: allow NAME -->`); typos like `<!--check_gams_vars: allow X-->` silently fail.

---

## MANDATE 8 — Realization-name verification

**Trigger**: any realization name (e.g., `managementcalib_aug19`, `endo_jun13`, `all_sectors_aug13`).

**Rule**: NEVER guess realization names from module keywords + date suffixes. ALWAYS verify:
- For the default: `grep "cfg\$gms\$<module>" ../config/default.cfg`
- For all realizations: `ls ../modules/XX_name/`

**Worked example**: agents have invented `fbask_aug21` for livestock (does NOT exist — only `fbask_jan16` and `fbask_jan16_sticky` exist; default is `fbask_jan16`), `croparea_nov24` for croparea (does NOT exist — only `simple_apr24` and `detail_apr24` exist). They have also confused `agr_sector_aug13` with `all_sectors_aug13` for water_demand — both are real but only `all_sectors_aug13` is default. Cascading bugs follow because non-default realizations have different equations.

**Verification**: `python3 scripts/check_gams_realizations.py` greps backtick-quoted realization names against the actual directory listings. The realization regex matches month-format names only (e.g., `fbask_aug21`); non-month names (`default`, `static`, `off`, `nlp_ipopt`, `bii_target`) are NOT extracted by the regex.

**Verified by**: `scripts/check_gams_realizations.py` (month-format names only) + `scripts/check_module_realizations.py` (post-R1: cross-references each module doc's claimed realization against config/default.cfg + verifies the directory exists, covering both month and non-month names).

---

## MANDATE 9 — Cost-variable attribution

**Trigger**: any claim about which module provides a `vm_cost_*` variable.

**Rule**: NEVER attribute a cost variable to a module without checking. R3 found 5 cost variables wrongly attributed to Module 38. The actual provenance:
- `vm_cost_prod_crop` → Module 38 (factor_costs)
- Livestock / fish production costs → Module 70 (livestock)
- Pasture costs → Module 31 (past)
- Residue costs → Module 18 (residues)
- Forestry costs → Module 32 (forestry)

**Verification**: `grep -rn "<variable_name>" ../modules/*/declarations.gms` to find the actual declaring module.

**Verified by**: human review (no mechanical guard for module-attribution claims).

---

## MANDATE 10 — Set-sum non-expansion

**Trigger**: any equation containing a `sum(<set>, ...)` or `prod(<set>, ...)` expression.

**Rule**: NEVER expand set-based sums into explicit member lists. If code uses `sum(land, vm_land(j,land))`, report it as-is. Do NOT rewrite as `vm_land(j,"crop") + vm_land(j,"past") + ...` — set-based sums are intentionally generic; expansion risks omitting members or inventing non-existent ones.

**Worked example** (R16 Q4): agent rewrote `sum(land, vm_land(j2,land))` as `vm_land(j2,"crop") + vm_land(j2,"past") + vm_land(j2,"forestry") + vm_land(j2,"urban") + vm_land(j2,"other")`. Missed `primforest` and `secdforest`. The set-based form preserved the actual member list; the expansion truncated it (see also MANDATE 11).

**Verified by**: human review.

---

## MANDATE 11 — Range non-truncation

**Trigger**: any GAMS set with a numerical range (e.g., age classes, year ranges, region lists).

**Rule**: NEVER truncate or abbreviate ranges. If docs say a set spans "ac0, ac5, ..., ac300, acx" (62 elements), report the full range. Do NOT shorten to "ac0, ..., ac140, acx".

**Worked example** (R16 Q3, Critical): agent truncated the age-class range to `ac0...ac140, acx`. Actual range is `ac0...ac300, acx` (62 elements). The docs (line 443) had the correct range; the agent shortened it from a mental shortcut. Downstream calculations off by a factor of ~2 in element count.

**Verified by**: human review.

---

## MANDATE 12 — Exact set-member labels

**Trigger**: any GAMS set member referenced by name.

**Rule**: NEVER generalize GAMS set member labels. Use exact set element names from code, not natural-language renames:
- `livst_rum` not "beef" or "ruminants"
- `total_wood_products` not "all wood products"
- `begr` not "grassy bioenergy" or "second-gen energy crops"

**Worked example**: agent wrote "the model tracks beef, pork, poultry, eggs" — actual set is `livst_rum`, `livst_pig`, `livst_chick`, `livst_egg`, `livst_milk`. Generalized labels can't be traced back to code, and may conflate distinct elements (`livst_rum` includes beef AND mutton, not just beef).

**Verified by**: human review.

---

## MANDATE 13 — Interface-parameter consumer grep

**Trigger**: documenting a new interface parameter (`pm_*`, `vm_*`, `im_*`) — usually as part of a sync or new-module documentation.

**Rule**: ALWAYS grep ALL consumers across the codebase BEFORE writing. Documenting only the one consumer mentioned in a commit message misses other consumers that already existed or were added in the same PR.

**Verification command**:
```bash
grep -rn "<new_parameter_name>" ../modules/ ../core/ --include="*.gms"
```
Enumerate EVERY consumer in the documentation.

**Worked example** (R20, 2026-04-20, Major): when `pm_carbon_density_*_ac_uncalib` was introduced, the doc listed only M29 (tree cover) as a consumer. Actually consumed by M32 (afforestation) and NDC at `modules/29_cropland/detail_apr24/presolve.gms:59,61,68` as well. A user refactoring the parameter would have missed two modules.

**Verified by**: human review (no mechanical guard for consumer-set completeness; partially mitigated by `scripts/check_gams_variables.py` flagging cross-module variable mentions).

---

## MANDATE 14 — Deprecated-name italics

**Trigger**: referring to a variable, equation, or parameter that has been renamed (historical context).

**Rule**: For deprecated names, use `*italics*` (NOT backticks). The GAMS variable and equation checkers (`scripts/check_gams_variables.py`, `scripts/check_gams_equations.py`) match backtick-wrapped names against current GAMS code. Sentences like ``"renamed from `old_name`"`` flag forever as missing.

**Convention**:
- Current name: `` `new_name` `` (backticks)
- Deprecated name: `*old_name*` (italics)

**Example**: "formerly `*pm_timber_yield*`, now `` `im_growing_stock` ``"

**Verified by**: `scripts/check_gams_variables.py` indirectly — italicized names are not checked (escape from the backtick-pattern regex). Italicizing a CURRENT variable name (stylistic mistake) escapes detection; partial coverage gap (R1 audit Cluster 4).

---

## MANDATE 15 — Post-rename global grep

**Trigger**: any global rename in the docs (variable, equation, realization, parameter).

**Rule**: After renaming, grep EVERY affected doc for the old name. The first-pass update often touches only the "primary" sections; secondary sections (advisory text, troubleshooting, examples) retain stale references.

**Verification commands**:
```bash
grep -rn "<old_name>" modules/module_*.md
# fix all hits
python3 scripts/check_gams_variables.py  # confirm zero stale references
```

**Worked example** (R20 post-sync): 10 stale backtick references survived a global rename because the rename only touched the formal "Variables" sections of module docs; advisory text and footers retained the old name. Running the variable checker after the global grep is what catches the remainder.

**Verified by**: `scripts/check_gams_variables.py` (post-rename: zero stale backtick references must remain).

---

## MANDATE 16 — Citation full-path + post-merge line numbers

**Trigger**: any `file:line` citation in an answer or doc.

**Rule**: For file:line citations, ALWAYS use the FULL relative path (`modules/XX_name/realization_dir/file.gms:NN`). The citation checker resolves bare filenames by "first match within module number" — if a module has both `simple_apr24/preloop.gms` and `detail_apr24/preloop.gms`, the first is picked even if you meant the second.

**Also**: draft line numbers from the FINAL merged code (post `git pull`), NOT from diff output during triage.

**Content (R33-R37)**: the cited line MUST CONTAIN the claimed identifier/token — confirm by reading the EXACT line, not merely that the file and line-range exist. A line that exists but lacks the claimed content is a mis-sourced citation; a file that does not exist is a fabricated one. Both are unsafe.

**Worked example** (R20, Major × 13): line numbers drafted from diff context drifted from final merged code by 5-20 lines. The citation checker flagged 13 drifted citations after the doc landed. The fix: always re-read the merged file post-merge and update line numbers. **R34 module_21**: an auditor's proposed fix pointed at lines 97-99 of the bilateral22 equations file, which is only 91 lines long (out of range), and named a presolve file that does not hold the claim — both fabricated/mis-sourced. Only the out-of-range case tripped the gate (by luck); the content check is what catches an in-range-but-wrong-content citation.

**Verified by**: `scripts/check_gams_citations.sh` + `scripts/check_gams_citations_impl.py` — line-range validity (error) + a Pattern-12 content-mismatch advisory. The engine's adversarial verifier now performs the content check per-bug PRE-fix (Step A → `CITATION_FAILED` → fixer defers), which is the proactive guard against the module_21 class. **Coverage gap remaining**: the gate's content check stays advisory (FP-prone on multi-line constructs); the verifier is the authoritative content gate.

---

## MANDATE 17 — One-hop reads (direct vs transitive consumer)

<!-- check-gams-vars: allow vm_FOO, vm_FOO_aggregate, vm_FOO_component -->
**Trigger**: any claim of the form "M_X uses `vm_*` / `pm_*` / `im_*`" or "M_X consumes / reads / depends on [variable]".

**Rule**: NEVER attribute consumption to a module that does not directly read the variable. Before writing "M_X uses `vm_FOO`" (pedagogical placeholder), verify direct consumption with:

```bash
grep -ln "vm_FOO" ../modules/XX_*/*/equations.gms ../modules/XX_*/*/presolve.gms ../modules/XX_*/*/postsolve.gms ../modules/XX_*/*/preloop.gms
```

If `vm_FOO` is **not** directly grep-hit in M_X's files but M_X reads an aggregate (e.g., `vm_carbon_stock`) that is in turn populated by M_X's contribution, the doc MUST say: "M_X contributes to `vm_FOO_aggregate` via `vm_FOO_component`; `vm_FOO_aggregate` is the direct interface variable". One-hop reads MUST be labeled as such.

**Worked example** (R24, Q4-B3, Major doc_error): `module_30.md:360` stated `vm_carbon_stock_croparea` is consumed directly by M52 and M56. Actual data path: M30 → M29 (`q29_carbon` aggregates) → `vm_carbon_stock` → M52/M56. M52 and M56 read the aggregated `vm_carbon_stock`, NOT `vm_carbon_stock_croparea`. The mis-attribution misleads modification-safety reasoning: a user editing M30 would not expect the change to ripple to M52/M56 via M29.

**Asymmetry to watch**: "X uses Y" is doc-side shorthand. Code-side, only direct equation-level reads count. Aggregate populators (M30/M29 in the example) are upstream contributors, NOT consumers of the aggregate they help populate.

**Verified by**: human review for now (G2 anchor logic in `audit/validation_rounds.json` regression questions tests this prospectively each round). Mechanization candidate: extend `scripts/check_consumer_attribution.py` to flag attributions where the named module does NOT contain a direct grep-hit for the cited variable. See Phase 1 1c plan entry in `audit/get_under_control_plan.md`.

---

## MANDATE 18 — Producer / declaration attribution (DECLARED vs POPULATED vs READ)

**Trigger**: any claim about which module DECLARES or PRODUCES/POPULATES an interface variable or parameter (`vm_*`, `pm_*`, `im_*`) — "X comes from M_Y", "M_Y provides X", "X is declared in M_Y".

**Rule**: NEVER attribute the source of an interface variable without checking the THREE distinct roles separately. A variable is often DECLARED in one module, POPULATED by several others, and READ by yet others — conflating them is the dominant R33-R37 error vein.
- **DECLARED**: the `name(...)` declaration line in a module's `declarations.gms`.
- **POPULATED**: assigned on an equation LHS, or via `.fx`/`.l` assignment, in that module.
- **READ**: appears on an equation RHS in that module.

**Verification commands**:
```bash
grep -rn "<name>(" ../modules/*/*/declarations.gms        # DECLARED (which module)
grep -rln "<name>" ../modules/*/*/equations.gms            # POPULATED (LHS) / READ (RHS) — inspect each
```

**Worked examples** (R33-R37): `vm_prod_reg` documented "from Module 70" but DECLARED in M17 (M70 only reads it); `im_maccs_mitigation` attributed to M56 but DECLARED in M57; `pm_prod_init` attributed to M30 but declared+populated in M17; `vm_p_fert_costs` routed M54→M38→M11 but wired DIRECTLY into M11. The `vm_carbon_stock` G2 pattern is the canonical case: DECLARED in M56, POPULATED by M29/31/32/34/35/59, READ by M52. Generalizes MANDATE 9 (cost variables) to ALL interface variables.

**Verified by**: the engine's adversarial verifier (`producer_declaration` class) re-derives DECLARED/POPULATED/READ mechanically against develop; human review otherwise. See also MANDATE 20 (grep both `name(` and `name.` forms).

---

## MANDATE 19 — Realization structure from the SPECIFIC realization's files

**Trigger**: any claim about a NON-DEFAULT realization's structure — its equation COUNT, which equations it defines, or which files it contains.

**Rule**: NEVER describe a realization's structure by pattern-completing from a sibling/family realization. Read THAT realization's ACTUAL files: `ls ../modules/XX_name/<realization>/` and read its `equations.gms` directly. Sibling realizations in the same family (e.g., `selfsuff_reduced` vs `selfsuff_reduced_bilateral22`) routinely DROP or ADD equations and files; those differences are exactly what gets confabulated. ALWAYS label non-default realization claims: "(realization NAME, non-default; default is X)".

**Worked example** (R34, Critical regression): an auditor claimed the non-default `selfsuff_reduced_bilateral22` trade realization had 9 equations including an active `q21_cost_trade_feasibility` and NO presolve.gms — pattern-completing from the sibling `selfsuff_reduced`, which DOES define that equation. Ground truth: bilateral22 has 8 equations, no `q21_cost_trade_feasibility` (it fixes the penalty to 0 in its presolve.gms, which DOES exist). A fresh agent independently reproduced the SAME wrong claim — these confabulations are CORRELATED across LLM agents, so more agents/voters do NOT help; only MECHANICAL verification (`ls` + `wc -l` + read the specific file) is reliable.

**Verified by**: the engine's adversarial verifier (`realization_structure` class) reads the specific realization's files mechanically; human review otherwise.

---

## MANDATE 20 — Solution-level (`.l`/`.lo`) reads in consumer/producer greps

**Trigger**: any grep to determine whether a module consumes or produces an interface variable.

**Rule**: a paren-restricted grep (`name(`) MISSES solution-level reads (`name.l`, `name.lo`, `name.up`, `name.fx`, `name.m`) in presolve/postsolve. ALWAYS grep BOTH the equation form `name(` AND the attribute form `name.` before concluding consume/not-consume. A module reading only `name.l` is a REAL consumer that the equation-form grep reports as a phantom.

**Worked example** (R33): module 32 reads `vm_area.l`/`.lo` in `modules/32_forestry/dynamic_may24/presolve.gms:17` (afforestation potential) — invisible to a `vm_area(` grep, which nearly caused a correct consumer listing to be deleted as a phantom. Applies to MANDATEs 13, 17, and 18.

**Verified by**: the engine's `GREP_GUARD` requires both forms; see project memory `bash-grep-r-unreliable-magpie`; human review otherwise.

---

## Verification one-liner

After writing any answer that references GAMS code, run (from the magpie-agent directory):
```bash
bash scripts/validate_consistency.sh
```
This invokes the variable, equation, realization, and citation checkers. Any failure here is presumed to be a MANDATE violation; fix before responding.

---

## Lessons Learned

<!-- Append new MANDATEs or worked examples as future rounds surface them. Each entry: date, MANDATE number, what was found, source round. -->

- **2026-05-23 (origin)**: hoisted from AGENT.md Step 1d. 16 MANDATEs preserved verbatim from the prior in-place version, with binding language tightened and worked examples drawn from the rounds named in each rule's text. R1-R21 validation history is the empirical foundation.
- **2026-05-25 (R6 Phase 1 1c)**: added MANDATE 17 (one-hop reads / direct vs transitive consumer). Motivating bug: R24 Q4-B3 (Major doc_error) — `module_30.md:360` claimed `vm_carbon_stock_croparea` is directly consumed by M52/M56; actual chain is M30 → M29 aggregate → M52/M56. Mechanization via `check_consumer_attribution.py` extension is Phase 1 1c follow-up.
- **2026-05-30 (R33-R37 high-centrality sweep + consolidation)**: added MANDATE 18 (producer/declaration DECLARED-vs-POPULATED-vs-READ), 19 (realization-structure from the specific realization's files), 20 (solution-level `.l/.lo` grep); extended MANDATE 16 with the citation-CONTENT rule. Motivating bugs: the module_21 cross-realization regression (a fresh forensics agent reproduced the auditor's exact error — correlated confabulation, only mechanical checks catch it), the `vm_prod_reg`/`im_maccs_mitigation`/`pm_prod_init` producer mis-attributions, and the `vm_area.l` solution-level near-miss. Mechanized by the engine's adversarial verifier (`producer_declaration` + `realization_structure` classes + the Step-A citation check) and `scripts/check_scaling.py` (the 10eN-vs-1eN class). Total now 20 MANDATEs.


---

**Hub status (R6 2026-05-25)**: verifiers.md is auto-loaded into every session that hits a GAMS identifier (vm_/pm_/q_/realization/etc.) and is referenced from AGENT.md as the binding source for the MANDATEs. If you add a MANDATE, change its trigger language, or renumber, update AGENT.md Step 1d short-index table (and the deployed copies) in the same commit to avoid index drift.
