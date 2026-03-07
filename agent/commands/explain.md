# Explain Command

**Purpose**: Explain a GAMS equation, variable, or parameter from MAgPIE source code

**When user says**: "/explain", "explain equation", "explain variable", "what does q30_prod do", "break down this equation", etc.

---

## Overview

This command gives an instant breakdown of any GAMS equation, variable, or parameter. The user provides a symbol name (e.g., `q30_prod`, `vm_land`, `pm_interest`) and receives a structured explanation with context, dependencies, and plain-English meaning.

---

## Quick Reference: GAMS Naming Prefixes

Before looking anything up, identify the symbol type from its prefix:

| Prefix | Type | Scope |
|--------|------|-------|
| `vm_` | Positive variable | Global (cross-module) |
| `v{NN}_` | Variable | Local to module NN |
| `pm_` | Parameter | Global (cross-module) |
| `p{NN}_` | Parameter | Local to module NN |
| `im_` | Interface parameter | Passed between modules |
| `i{NN}_` | Internal parameter | Local to module NN |
| `fm_` | Fixed parameter | Global (from input files) |
| `f{NN}_` | Fixed parameter | Local (from input files) |
| `s{NN}_` | Scalar | Local to module NN |
| `pcm_` | Previous-period carry | Value from prior timestep |
| `q{NN}_` | Equation | Defined in module NN |

---

## Workflow: Equations (names starting with q)

When the symbol name starts with `q` followed by digits (e.g., `q30_prod`, `q10_land`):

### Step 1: Parse the Equation Name

Extract the module number from the name:
- `q30_prod` → module number **30**
- `q10_land` → module number **10**

### Step 2: Identify the Module Directory

```bash
# Find the module directory (module number → directory name)
ls ../modules/ | grep "^30_"
```

### Step 3: Find the Active Realization

```bash
# Check which realization is active (look for the default line)
cat ../modules/XX_name/module.gms | grep "default"
```

Also check the user's config if available:
```bash
grep "cfg\$gms\$XX_name" ../config/default.cfg 2>/dev/null
```

### Step 4: Find the Equation Definition

```bash
# Search for the equation in the active realization's equations file
grep -n "equation_name" ../modules/XX_name/realization/equations.gms
```

### Step 5: Read the Equation and Context

Read the equation definition plus 5–10 lines of surrounding context to capture the full formula (multi-line equations are common in GAMS).

### Step 6: Identify All Symbols in the Equation

For each variable/parameter used in the equation:

1. **Identify its type** from the prefix table above
2. **Find its declaration**:
   ```bash
   grep -rn "variable_name" ../modules/*/declarations.gms
   ```
3. **Note its dimensions** (the sets in parentheses)
4. **Find its description** (the quoted string after the declaration)

### Step 7: Check AI Documentation

```bash
# Read the curated module documentation for additional context
cat modules/module_XX.md
```

Look for:
- The equation's role in the module's logic
- Plain-English explanation
- Known caveats or gotchas

Also check `modules/module_XX_notes.md` if it exists for user-reported warnings.

### Step 8: Present to User

```
## q30_prod — [Short Descriptive Title]
📁 Module 30 (crop) | Realization: [active_realization]
📄 equations.gms:[line_start]-[line_end]

### GAMS Code
```gams
[actual equation code from the file]
```

### In Plain English
[1-2 sentence explanation of what this equation does and why it matters]

### Variables & Parameters
| Name | Type | Dimensions | Description | Defined In |
|------|------|------------|-------------|------------|
| vm_prod | Positive Variable | (j, k) | Production quantity | Module 30 |
| vm_land | Positive Variable | (j, land) | Land area allocation | Module 10 |
| ...  | ...  | ...        | ...         | ...        |

### Upstream Dependencies
[What feeds into this equation — which modules supply the input variables/parameters]

### Downstream Effects
[What this equation feeds — which modules consume its output]
```

---

## Workflow: Variables & Parameters (vm_, v_, pm_, p_, im_, fm_, f_, s_, pcm_)

When the symbol is a variable, parameter, scalar, or fixed parameter:

### Step 1: Parse the Name and Identify Type

Use the prefix table to determine:
- **Scope**: global vs. local
- **Type**: variable, parameter, fixed parameter, scalar, etc.
- **Module number** (if local, from the digits in the prefix)

### Step 2: Find the Declaration

```bash
# Search across all module declarations
grep -rn "variable_name" ../modules/*/declarations.gms
```

Note: global symbols (vm_, pm_, fm_) may be declared in one module but used in many.

### Step 3: Find All Equations Using This Symbol

```bash
# Find every equation file that references this symbol
grep -rn "variable_name" ../modules/*/realization/*/equations.gms
```

### Step 4: Check for Bounds, Fixes, and Presolve Logic

```bash
# Check presolve and preloop files for bounds/fixes
grep -rn "variable_name" ../modules/*/realization/*/presolve.gms
grep -rn "variable_name" ../modules/*/realization/*/preloop.gms
```

### Step 5: Check AI Documentation

Read `modules/module_XX.md` for the declaring module, plus docs for any heavily-using modules.

Also check `modules/module_XX_notes.md` if it exists.

### Step 6: Present to User

```
## vm_land — [Short Descriptive Title]
📋 Type: Positive Variable (global)
📁 Declared in: Module 10 (land)
📐 Dimensions: (j, land)
📏 Units: [units from documentation or declaration comment]

### Description
[2-3 sentence explanation of what this variable represents and its role in the model]

### Used in Equations
| Equation | Module | Role (LHS/RHS) |
|----------|--------|-----------------|
| q10_land | 10 (land) | LHS — defined here |
| q30_prod | 30 (crop) | RHS — consumed |
| ...      | ...    | ...             |

### Key Constraints
[Any bounds, fixes, or conditional logic applied in presolve/preloop files]

### Data Flow
[upstream sources] → **this variable** → [downstream consumers]
```

---

## Error Handling

### Symbol Not Found

If the equation/variable name doesn't match anything:

1. **Search for partial matches**:
   ```bash
   grep -rn "partial_name" ../modules/*/declarations.gms ../modules/*/realization/*/equations.gms | head -20
   ```
2. **Suggest similar names** to the user:
   ```
   ⚠️ Could not find "q30_prodd". Did you mean one of these?
     • q30_prod (Module 30 — crop)
     • q30_prod_reg (Module 30 — crop)
   ```

### Multiple Matches

If the symbol appears in multiple realizations or modules:

1. **Show all matches** with their locations
2. **Highlight the active realization** (check `module.gms` for default)
3. **Ask the user to pick** if ambiguity remains:
   ```
   Found "v30_cost" in multiple realizations:
     1. ✅ simple_apr24 (active)
     2. detailed_jan22
   Showing the active realization. Want to see another?
   ```

### Module Has Multiple Realizations

Always check which realization is active before presenting code:

```bash
cat ../modules/XX_name/module.gms | grep "default"
```

If the user's config overrides the default, note it:
```
⚠️ Default realization is "simple_apr24", but your config uses "detailed_jan22".
Showing: detailed_jan22 (your active config)
```

---

## Examples

### Example 1: `/explain q30_prod`
→ Triggers the **Equation workflow**: parse `q30` → module 30 → find directory `30_crop` → find active realization → read equation → identify symbols → present breakdown.

### Example 2: `/explain vm_land`
→ Triggers the **Variable workflow**: prefix `vm_` → global positive variable → find declaration → find all equation uses → present breakdown.

### Example 3: `/explain p35_distcoeff`
→ Triggers the **Variable workflow**: prefix `p35_` → local parameter in module 35 → find declaration in `35_natveg` → find uses → present breakdown.

### Example 4: `/explain something_unknown`
→ Triggers **Error handling**: search for partial matches, suggest similar names.

---

## Related Files

- `modules/module_XX.md` — AI documentation for each module
- `modules/module_XX_notes.md` — User feedback and known pitfalls
- `core_docs/Module_Dependencies.md` — Cross-module dependency info
- `core_docs/Data_Flow.md` — Data pipeline documentation

---

**Remember**: Always check AI documentation (`modules/module_XX.md`) first — it often has the plain-English explanation already written. Only dig into raw GAMS code for details the docs don't cover.
