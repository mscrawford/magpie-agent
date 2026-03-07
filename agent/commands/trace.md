# Trace Command

**Purpose**: Trace a variable's complete flow through the MAgPIE model — where it's defined, constrained, and consumed

**When user says**: "/trace", "trace variable", "where does vm_land come from", "what uses vm_land", "dependency graph for", "flow of"

---

## Overview

This command performs a **complete dependency trace** for a given MAgPIE symbol (variable, parameter, or set). It searches declarations, equations, bounds, postsolve updates, and AI documentation to build a full picture of how the symbol flows through the model.

## Workflow

### Step 1: Parse the Symbol Name

Extract the variable/parameter name from user input.

Examples:
- `/trace vm_land` → symbol is `vm_land`
- `where does vm_cost_glo come from?` → symbol is `vm_cost_glo`
- `/trace v35_secdforest --downstream` → symbol is `v35_secdforest`, mode is `--downstream`

Also detect optional flags:
- `--cost` — follow cost pathway to objective function (Module 11)
- `--carbon` — follow carbon-related impacts only
- `--upstream` — show only what feeds into this variable
- `--downstream` — show only what this variable feeds

### Step 2: Classify the Symbol by Prefix

Determine the symbol's scope and type from its prefix:

| Prefix | Type | Scope | Search Path |
|--------|------|-------|-------------|
| `vm_` | Variable (global interface) | All modules | `../modules/*/declarations.gms` |
| `v{NN}_` | Variable (local to module NN) | Module NN only | `../modules/NN_*/declarations.gms` |
| `pm_` | Parameter (global interface) | All modules | `../modules/*/declarations.gms` |
| `p{NN}_` | Parameter (local to module NN) | Module NN only | `../modules/NN_*/declarations.gms` |
| `im_` | Input parameter (global) | All modules | `../modules/*/input.gms` |
| `i{NN}_` | Input parameter (local) | Module NN only | `../modules/NN_*/input.gms` |
| `sm_` | Scalar (global) | All modules | `../modules/*/declarations.gms` |
| `s{NN}_` | Scalar (local to module NN) | Module NN only | `../modules/NN_*/declarations.gms` |
| `fm_` | Input parameter from file | All modules | `../modules/*/input.gms` |
| `pcm_` | Previous-period copy | All modules | `../modules/*/postsolve.gms` |
| `q_` / `q{NN}_` | Equation | Module NN | `../modules/NN_*/equations.gms` |

### Step 3: Find the Declaration

```bash
# For global variables (vm_)
grep -rn "^[[:space:]]*vm_NAME" ../modules/*/declarations.gms

# For local variables (vNN_)
grep -rn "^[[:space:]]*vNN_NAME" ../modules/NN_*/declarations.gms
```

Extract from the declaration:
- **Type**: Positive Variable, Variable, Parameter, etc.
- **Domain/sets**: e.g., `(j, land)`
- **Description string**: the quoted text after the domain
- **Units**: often in the description or in a nearby comment

### Step 4: Find All Equations Referencing the Symbol

```bash
# For global variables — search ALL modules
grep -rn "vm_NAME" ../modules/*/equations.gms | grep -v "^\*"

# For local variables — search only the owning module
grep -rn "vNN_NAME" ../modules/NN_*/equations.gms | grep -v "^\*"
```

**Important**: Exclude comment lines (those starting with `*` in GAMS).

### Step 5: Determine the Variable's Role in Each Equation

For each equation found, determine if the symbol appears on the **left-hand side** or **right-hand side** of the equation operator:

- **LHS** (left of `=e=`, `=g=`, `=l=`) → this equation **DEFINES** or **CONSTRAINS** the variable
- **RHS** (right of `=e=`, `=g=`, `=l=`) → this equation **USES** the variable as input

**Equation operators**:
- `=e=` — equality constraint (defines the variable exactly)
- `=g=` — greater-than-or-equal constraint (sets a lower bound)
- `=l=` — less-than-or-equal constraint (sets an upper bound)

### Step 6: Find Bounds and Fixes

```bash
grep -rn "vm_NAME\.\(lo\|up\|fx\|l\)" ../modules/*/presolve.gms ../modules/*/postsolve.gms
```

Look for:
- `.lo` — lower bound
- `.up` — upper bound
- `.fx` — fixed value (pinned)
- `.l` — level value (current solution)

### Step 7: Find Postsolve / Timestep Updates

```bash
grep -rn "vm_NAME\.l\|pcm_NAME" ../modules/*/postsolve.gms
```

These reveal **inter-timestep dynamics**: where the current solution is saved for use in the next period. The `pcm_` prefix denotes "previous-period copy" parameters.

### Step 8: Check AI Documentation for Context

```bash
# Check which module docs mention this variable
grep -l "vm_NAME" modules/module_*.md

# Also check notes files for user-contributed insights
grep -l "vm_NAME" modules/module_*_notes.md

# Check cross-module docs for conservation/balance context
grep -l "vm_NAME" cross_module/*.md
```

Read matched documentation for narrative context, known pitfalls, and user warnings.

### Step 9: Build and Present the Trace Diagram

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
## Trace: vm_land(j, land)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📋 Type: Positive Variable | Module 10 (land)
📏 Units: million hectares

### 🔵 DEFINED/CONSTRAINED BY (equations where vm_land appears on LHS)
┌─ q10_land_area (Module 10) — Total area conservation [=e=]
├─ q29_avl_cropland (Module 29) — Cropland upper bound [=l=]
├─ q35_min_forest (Module 35) — Minimum forest area [=g=]
└─ q35_natveg_conservation (Module 35) — Natural vegetation floor [=g=]

### 🟢 FEEDS INTO (equations where vm_land appears on RHS)
┌─ q30_rotation_penalty (Module 30) — Crop rotation constraints
├─ q59_som_target (Module 59) — Soil organic matter target
├─ q52_carbon_stock (Module 52) — Carbon accounting
└─ ...

### 🔴 BOUNDS/FIXES (presolve/postsolve)
├─ Module 10 presolve: vm_land.lo(j,"urban") = pcm_land(j,"urban")
└─ Module 10 postsolve: pcm_land(j,land) = vm_land.l(j,land)

### 🔄 TIMESTEP DYNAMICS
Current: vm_land(j,land) → postsolve → pcm_land(j,land) → next period's q10_land_area RHS

### 📊 UPSTREAM CHAIN (what determines this variable)
[List the key variables that feed into the constraining equations]

### 📊 DOWNSTREAM CHAIN (what this variable affects)
[List the key variables/costs that depend on this variable]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

## Special Trace Modes

### `--cost`: Follow to Objective Function

Trace the variable through every cost pathway until reaching `vm_cost_glo` in Module 11.

Present as a cost chain:
```
💰 Cost pathway: vm_land → ... → vm_cost_glo
┌─ vm_land(j,"crop") → q30_cost(j) → v30_penalty(j)
├─ v30_penalty(j) → q30_cost_sum → vm_rotation_penalty(j)
├─ vm_rotation_penalty(j) → q11_cost_reg → vm_cost_reg(i)
└─ vm_cost_reg(i) → q11_cost_glo → vm_cost_glo
```

### `--carbon`: Follow Carbon Impacts

Filter to only equations/variables related to carbon accounting (Module 52, 56, 35, etc.).

### `--upstream`: Upstream Only

Show only Steps 5 (LHS equations) and the upstream chain. Omit downstream/feeds-into.

### `--downstream`: Downstream Only

Show only Steps 5 (RHS equations) and the downstream chain. Omit upstream/constraining equations.

---

## Tips for the Agent

1. **For `vm_` variables**: Always search ALL modules — they are global interface variables
2. **For `v{NN}_` variables**: Only search module NN — they are local
3. **The objective function chain** always ends at `vm_cost_glo` in Module 11
4. **`pcm_` variables** create inter-timestep links — always highlight these
5. **Some variables appear in 20+ equations** — group by module for readability
6. **Check `realization/` subdirectories** — the active realization matters:
   ```bash
   grep "cfg\$gms\$<module_name>" ../config/default.cfg
   ```
7. **Read AI docs first** for context — they often explain *why* a variable exists, not just where

---

## Error Handling

### Variable Not Found

If the symbol is not found in any declaration:

```
⚠️ Variable "vm_lnad" not found in any module declaration.

Did you mean one of these?
  • vm_land (Module 10) — Land area by type
  • vm_landdiff (Module 10) — Land area change
```

Use fuzzy matching to suggest alternatives:
```bash
# Find similar names
grep -rn "^[[:space:]]*vm_.*l.*n.*d" ../modules/*/declarations.gms | head -10
```

### Too Many Results

If a variable appears in more than ~15 equations:

1. **Show a grouped summary first**:
   ```
   vm_land appears in 24 equations across 8 modules:
     Module 10 (land): 3 equations
     Module 29 (cropland): 2 equations
     Module 30 (crop): 4 equations
     ...
   ```
2. **Ask user**: "Want me to expand a specific module, or show the full trace?"

---

## Related Files

- `modules/module_XX.md` — AI documentation for each module
- `modules/module_XX_notes.md` — User feedback and warnings
- `core_docs/Module_Dependencies.md` — Cross-module dependency map
- `cross_module/modification_safety_guide.md` — Safety info for high-centrality variables
- `cross_module/land_balance_conservation.md` — Land balance context
- `cross_module/carbon_balance_conservation.md` — Carbon balance context

---

**Remember**: The goal is to give the user a complete mental model of how a variable flows through MAgPIE. Start with the structured trace, then offer to drill into any section.
