# Documentation Quality: Bug Taxonomy & Prevention

**Purpose**: Catalog recurring documentation error patterns so that future sessions
can avoid them and automated checks can catch them.

This document is the product of iterative audit-analyze-record-prevent cycles.
Each pattern includes: what it looks like, why it happens, and how to prevent it.

---

## The Improvement Flywheel

```
  ┌──────────┐
  │  AUDIT   │ ← Find bugs (new angles each pass)
  └────┬─────┘
       ↓
  ┌──────────┐
  │ ANALYZE  │ ← Why did this class of bug emerge?
  └────┬─────┘
       ↓
  ┌──────────┐
  │  RECORD  │ ← Add pattern to this document
  └────┬─────┘
       ↓
  ┌──────────┐
  │ PREVENT  │ ← Add automated check + update guidance
  └────┬─────┘
       ↓
  ┌──────────┐
  │  REPEAT  │ ← New angles, deeper checks
  └──────────┘
```

Each pass should both fix immediate bugs AND strengthen the system against
that class of bugs recurring.

---

## Bug Patterns

### Pattern 1: GAMS Prefix Confusion

**What**: Wrong prefix on variable/parameter names. MAgPIE uses a strict naming
convention where the prefix encodes scope and type:

| Prefix | Meaning | Scope |
|--------|---------|-------|
| `vm_` | Variable | Interface (cross-module) |
| `v{N}_` | Variable | Local to module N |
| `pm_` | Parameter | Interface |
| `p{N}_` | Parameter | Local to module N |
| `fm_` | File input | Interface |
| `f{N}_` | File input | Local to module N |
| `im_` | Input (calculated) | Interface |
| `i{N}_` | Input (calculated) | Local |
| `s{N}_` | Scalar | Local |
| `pcm_` | Previous-timestep param | Interface |

**Examples found**:
- `p15_waste_scen` → `s15_waste_scen` (scalar, not parameter)
- `vm_nr_surplus` → `v50_nr_surplus_cropland` (local, not interface)
- `f22_conservation_fader` → `p22_conservation_fader` (calculated, not file input)
- `p14_yields_calib` → `i14_yields_calib` (calculated input, not parameter)

**Why it happens**: AI generates plausible names using the right module number
but wrong prefix. The prefix carries semantic meaning (scope + type) that
requires checking declarations.gms.

**Prevention**:
- ✅ Automated: `scripts/check_gams_variables.sh` (Check 14 in validator)
- 📝 Manual: When writing variable names, verify prefix against declarations.gms
- 🧠 Rule: If unsure, check `modules/{N}_{name}/*/declarations.gms`

---

### Pattern 2: Hallucinated Variable Names in Advisory Text

**What**: Troubleshooting tips, "safe modifications" sections, and debugging
advice use plausible-sounding but non-existent variable names.

**Examples found**:
- `s13_tau_response` — no such scalar in Module 13
- `s14_yld_bioen_scaling` — no such scalar in Module 14
- `s30_rotation_scenario_speed` — close to `s30_rotation_scenario_start` but wrong
- `s42_pumping_cost` — confused with `ic42_pumping_cost`

**Why it happens**: Advisory text is written from understanding of the module's
purpose, not copied from code. The AI constructs a "reasonable" parameter name
from context. These sections are highest-risk because they're furthest from
direct code transcription.

**Prevention**:
- ✅ Automated: Check 14 catches these
- 📝 Manual: Every backtick-quoted variable in advisory text must be verified
- 🧠 Rule: NEVER invent a variable name. Always copy from declarations.gms or input.gms

---

### Pattern 3: Suffix Truncation

**What**: Long compound variable names get shortened, dropping meaningful suffixes.

**Examples found**:
- `pm_carbon_density_secdforest` → missing `_ac` suffix
- `im_gdp_pc_ppp` → missing `_iso` suffix

**Why it happens**: Names like `pm_carbon_density_secdforest_ac` are long. The AI
(or human writer) unconsciously drops the final qualifier when it seems "obvious"
from context. But in GAMS, the full name is the identifier.

**Prevention**:
- ✅ Automated: Check 14 catches these
- 📝 Manual: Copy-paste full variable names; never type from memory
- 🧠 Rule: GAMS names are exact identifiers. `_ac`, `_iso`, `_reg` suffixes
  indicate different dimensional indexing and MUST be preserved

---

### Pattern 4: Conceptual Pseudo-Code

**What**: Explanatory sections use "intuitive" variable names that don't exist
in the actual implementation, because the code uses a different abstraction.

**Examples found**:
- `vm_import`/`vm_export` — trade module uses self-sufficiency constraints, not
  explicit import/export variables
- `vm_prod_calibrated`/`vm_prod_initial` — conceptual names for explaining an
  offline calibration procedure
- `vm_demand` — no such aggregation exists; code uses `vm_supply`

**Why it happens**: The documentation explains the *concept* (trade flows) using
intuitive names, but the *implementation* uses a different mathematical formulation
(self-sufficiency ratios). The gap between mental model and code creates phantom variables.

**Prevention**:
- 📝 Manual: When explaining concepts, use the actual GAMS variables with explanation
- 🧠 Rule: If using a conceptual name, annotate: "(conceptual, not actual GAMS variable)"
- ✅ Automated: Check 14 allowlist for known annotated conceptual vars

---

### Pattern 5: Stale References After Renames

**What**: When a convention is renamed (e.g., "command:" → "/" syntax), not all
files get updated. The rename creates N bugs across M files.

**Prevention**:
- ✅ Automated: Check 7 (convention linter) in validator
- 🧠 Rule: After ANY rename, `grep -r` the ENTIRE repo for the old name

---

### Pattern 6: Hardcoded Counts Drift

**What**: Prose like "Module 10 has 23 dependents" becomes stale when the
codebase changes.

**Prevention**:
- ✅ Automated: Check 1 (dependency counts) and Check 11 (hardcoded values)
- 🧠 Rule: Link don't duplicate. Reference `Module_Dependencies.md` instead of
  hardcoding numbers

---

### Pattern 7: Broken Cross-References

**What**: Markdown links to files or anchors that don't exist.

**Prevention**:
- ✅ Automated: Check 3 (cross-references) and Check 8 (markdown links)
- 🧠 Rule: Check both file existence AND anchor existence

---

### Pattern 8: Stale Realization Names in Verification Footers

**What it looks like**: "Verified Against" footer lines reference realization directories
that no longer exist (e.g., `glo_jan16` instead of `select_apr20`).

**Why it happens**: AI-generated documentation was created when a different realization
was active, or the AI invented plausible-sounding realization names by combining module
keywords with date suffixes. The verification footer was never actually verified.

**Examples**:
- `../modules/12_*/glo_jan16/*.gms` → actual: `select_apr20`
- `../modules/38_*/fixed_nov23/*.gms` → actual: `sticky_feb18`
- `../modules/73_*/static_jan21/*.gms` → actual: `default`

**Prevention**: ✅ Automated — Check 16 (check_gams_realizations.sh)

**Root cause insight**: This is a variation of **hallucination**, but specifically in
metadata/footer sections that receive less human review than main content. 12 of 15
mismatches were in "Verified Against" lines — ironic because these are the lines
meant to prove the document was verified.

### Pattern 9: Wrong Equation Names

**What it looks like**: Equation names (q{N}_*) in docs don't match actual GAMS declarations.

**Examples**:
- `q11_cost_tc` → actual: `q11_cost_reg` (the equation where vm_tech_cost feeds in)
- `q30_land_snv`, `q30_treecover` → no such equations exist in either realization
- `q15_bmi_shr` → should be `q15_bmi_shr_*` (family of equations)

**Why it happens**: AI constructs plausible equation names from context (cost + tc → q11_cost_tc)
rather than looking up the actual declaration. Similar to Pattern 2 but for equations instead of variables.

**Prevention**: ✅ Automated — Check 15 (check_gams_equations.sh)

### Pattern 10: Stale File:Line Citations

**What it looks like**: `equations.gms:74` points past end of file (file has 49 lines),
or `presolve.gms:20` references a file that doesn't exist (actual: `presolve_ini.gms`).

**Why it happens**: Documentation written against older/different versions of GAMS files
where the code was longer or structured differently. Also: wrong realization name in the
"Verified Against" footer propagates to all line citations (if the doc was "verified"
against a non-existent realization, all line numbers are fabricated).

**Scale**: 151 bugs found — the **largest single bug class** by count.
- 39 in module_22.md (wrong filename: presolve.gms → presolve_ini.gms)
- 46 in module_29.md (hallucinated line numbers past EOF)
- 23 in module_30.md, 18 in module_38.md

**Fix strategy**: Strip out-of-range line numbers rather than guess correct ones.
Keeping `equations.gms` without a line number is better than pointing to a wrong line.

**Prevention**: ✅ Automated — Check 17 (check_gams_citations.sh)

**Root cause insight**: This pattern correlates strongly with Pattern 8 (stale
realization names). Wrong realization → wrong file sizes → all line citations invalid.

### Pattern 11: Wrong GAMS Filename

**What it looks like**: Citation references `presolve.gms` but actual file is
`presolve_ini.gms`. File genuinely doesn't exist under that name.

**Why it happens**: GAMS file naming isn't fully standardized — most modules have
`presolve.gms` but some use `presolve_ini.gms`, `preloop.gms`, etc. AI assumes
the common pattern.

**Examples**: Module 22 (`presolve.gms` → `presolve_ini.gms`, 39 citations)

**Prevention**: ✅ Automated — Check 17 catches missing files too

### Pattern 12: Content-Level Citation Mismatch

**What it looks like**: Citation has a valid line number (within file range) but
the cited line doesn't contain the claimed identifier. Often off by 1-5 lines.

**Why it happens**: Code evolves after documentation is written — lines are added
or removed, shifting all subsequent line numbers. Also occurs when input parameters
are reordered during refactoring.

**Examples**:
- `q52_emis_co2_actual` cited at `equations.gms:19` but actually at line 16 (3 lines off)
- `s14_carbon_fraction` cited at `input.gms:29` but actually at line 22 (7 lines off)
- `i20_processing_unitcosts` cited at `input.gms:25` — actually `f20_processing_unitcosts` there (wrong prefix)

**Discovery stats**: 26 bugs across 9 module docs (292 claims checked, 91% → 99.3%)

**Prevention**: Manual audit needed — too dependent on context parsing for reliable automation

### Pattern 13: Wrong Parameter Default Value

**What it looks like**: Documentation claims a parameter default that differs from
`config/default.cfg`. Common when docs describe scenario-specific values as if defaults.

**Examples**:
- `s56_cprice_red_factor` documented as default=0, actual default=1

**Prevention**: Manual audit. Most "default" claims in docs are correct (42/43 verified).

## Audit Angles Registry

Track which audit angles have been attempted, their yield, and when to repeat.

| Angle | First Run | Bugs Found | Automated? | Re-run Trigger |
|-------|-----------|------------|------------|----------------|
| GAMS variable names | 2026-03-06 | 17 | ✅ Check 14 | After module doc updates |
| Dependency counts | Previous | Multiple | ✅ Check 1 | After code changes |
| Cross-references | Previous | Multiple | ✅ Check 3, 8 | After file renames |
| Convention renames | Previous | Multiple | ✅ Check 7 | After convention changes |
| Path prefixes | Previous | 43 | ✅ Check 12 | After restructuring |
| Equation names | 2026-03-07 | 4 | ✅ Check 15 | After module doc updates |
| Set names | 2026-03-07 | 0 | N/A | Sets too distinctive to hallucinate |
| Realization names | 2026-03-07 | 12 | ✅ Check 16 | After code merges |
| File:line citations | 2026-03-07 | 151 | ✅ Check 17 | After code merges |
| Content-level citations | 2026-03-07 | 26 | Manual | After code merges |
| Parameter defaults | 2026-03-07 | 1 | Manual | After config changes |
| Data file existence | 2026-03-07 | 1 | Manual | After file renames |
| Equation formulas | 2026-03-07 | 0 | N/A | Formulas are reliable |
| Cross-module dependencies | 2026-03-07 | 0* | Manual | Style issue, not bugs |
| Deployment sync (CLAUDE.md) | 2026-03-07 | 1 critical | Manual | After AGENT.md edits |

\* Cross-module dependency claims mix code-level and conceptual dependencies.
Not bugs per se, but 13 modules claim "depends on Module 11 (costs)" which is
conceptually valid but code-direction-reversed (Module 11 reads THEIR costs).

### Pattern 14: Deployment Copy Drift

**What it looks like**: CLAUDE.md (loaded by Claude via convention) is months behind
AGENT.md (the source). All lessons, warnings, and quality guard sections missing.

**Why it happens**: Multiple deployment targets (AGENT.md, CLAUDE.md) but update
process only syncs one. CLAUDE.md was a legacy file from an earlier naming convention.

**Discovery**: CLAUDE.md was 461 lines (Nov 2023) while AGENT.md was 785 lines (Mar 2026)
— missing 4 months of quality improvements including the entire Quality Guard section.

**Prevention**: After editing AGENT.md, ALWAYS sync both:
```bash
cp AGENT.md ../AGENT.md && cp AGENT.md ../CLAUDE.md
```

**Severity**: CRITICAL — this is the #1 transmission failure. If CLAUDE.md isn't
synced, future Claude instances receive NONE of the documented lessons.

---

## Adding New Patterns

When you discover a new bug class:

1. **Describe it**: What does it look like? Give 2-3 examples
2. **Explain why**: What aspect of the documentation process causes it?
3. **Prevention**: Can it be automated? What manual rule prevents it?
4. **Add to validator**: If automatable, add a check to `validate_consistency.sh`
5. **Update this document**: Add the pattern with examples
