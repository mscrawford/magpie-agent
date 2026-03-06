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

## Audit Angles Registry

Track which audit angles have been attempted, their yield, and when to repeat.

| Angle | First Run | Bugs Found | Automated? | Re-run Trigger |
|-------|-----------|------------|------------|----------------|
| GAMS variable names | 2026-03-06 | 17 | ✅ Check 14 | After module doc updates |
| Dependency counts | Previous | Multiple | ✅ Check 1 | After code changes |
| Cross-references | Previous | Multiple | ✅ Check 3, 8 | After file renames |
| Convention renames | Previous | Multiple | ✅ Check 7 | After convention changes |
| Path prefixes | Previous | 43 | ✅ Check 12 | After restructuring |
| Equation names | Not yet | — | ❌ | — |
| Set names | Not yet | — | ❌ | — |
| Realization names | Previous | 1 (fbask) | ❌ | After code merges |
| File:line citations | Not yet | — | ❌ | After code merges |

---

## Adding New Patterns

When you discover a new bug class:

1. **Describe it**: What does it look like? Give 2-3 examples
2. **Explain why**: What aspect of the documentation process causes it?
3. **Prevention**: Can it be automated? What manual rule prevents it?
4. **Add to validator**: If automatable, add a check to `validate_consistency.sh`
5. **Update this document**: Add the pattern with examples
