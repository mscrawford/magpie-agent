# Helper: Modification Impact Analysis

**Auto-load triggers**: "modify", "change module", "what breaks", "impact of changing", "safe to modify", "can I change", "extend", "add to module"
**Last updated**: 2026-03-06
**Lessons count**: 0 entries

---

## Quick Reference

### Before modifying ANY module, answer these 3 questions:

1. **What depends on this module?** → Check `core_docs/Module_Dependencies.md`
2. **Does it enforce a conservation law?** → Check `cross_module/*_balance.md`
3. **Is it in a circular dependency?** → Check `cross_module/circular_dependency_resolution.md`

### Risk levels at a glance

| Risk | Modules | Why |
|------|---------|-----|
| 🔴 CRITICAL | 10 (land), 11 (costs), 17 (production) | Conservation law enforcers, 20+ dependents |
| 🔴 HIGH | 15 (food), 16 (demand), 21 (trade), 56 (GHG) | Demand/supply chain, coupled feedback |
| 🟡 MEDIUM | 14 (yields), 29 (cropland), 30 (croparea), 32 (forestry), 52 (carbon) | Multiple dependents, equation changes propagate |
| 🟢 LOW | 12 (interest), 34 (urban), 36 (employment), 40 (transport), 54 (phosphorus) | Few dependents, peripheral modules |

### The golden rule
**Never modify an equation's LHS dimensions or a variable's dimensions without checking ALL modules that use that variable.** Dimension mismatches cause GAMS compilation errors.

---

## Step-by-Step Impact Analysis

### Step 1: Identify what you're changing

| Change type | Risk multiplier | Why |
|---|---|---|
| Add new equation (not touching existing) | Low | Additive, no existing dependencies |
| Modify equation formula (keep dimensions) | Medium | Affects results but not compilation |
| Change variable dimensions | HIGH | All using modules must update |
| Add new set element | HIGH | Cascades through all sum() operations |
| Change parameter values in input.gms | Low | Usually safe, just changes behaviour |
| Switch realization | Low-Medium | Self-contained if interface unchanged |

### Step 2: Check the dependency chain

```bash
# Quick check: who uses variables from Module XX?
# In the MAgPIE root directory:
grep -r "vm_VARNAME\|pm_VARNAME" modules/ --include="*.gms" -l | grep -v "XX_modulename"
```

Or consult `core_docs/Module_Dependencies.md` which has pre-computed dependency counts.

### Step 3: Check conservation law impact

If your module participates in a conservation law, your change MUST preserve the balance:

| Conservation Law | Core Equation | File |
|---|---|---|
| Land balance | `q10_land_area: Σ(land) vm_land(j,land) =e= f10_land(j)` | `cross_module/land_balance_conservation.md` |
| Water balance | `q43_water: water_demand ≤ water_supply` | `cross_module/water_balance_conservation.md` |
| Carbon balance | `vm_carbon_stock` tracking across pools | `cross_module/carbon_balance_conservation.md` |
| Nitrogen balance | `vm_nr_som` + fertilizer + manure | `cross_module/nitrogen_food_balance.md` |
| Food balance | `vm_prod_reg + imports - exports ≥ demand` | `cross_module/nitrogen_food_balance.md` |

### Step 4: Test your change

```r
# Minimum test: does the model still solve?
# Run default scenario + your change, check:

# 1. Model status
readGDX(gdx, "p80_modelstat")  # All timesteps should be 1 or 2

# 2. Land balance preserved
land <- land(gdx)
# Total land should be constant across timesteps

# 3. Food balance met
demand <- demand(gdx)
production <- production(gdx)
# Global production ≥ global demand (trade adjusts)

# 4. No extreme slack variable activation
readGDX(gdx, "v44_bii_missing")  # Should be ~0
readGDX(gdx, "v32_land_missing") # Should be ~0
```

---

## Common Modification Patterns

### Adding a new variable to a module

1. Declare in `declarations.gms` (positive variable, equation, parameter)
2. Initialize in `preloop.gms` or `presolve.gms`
3. Define equation in `equations.gms`
4. If interface variable (`vm_`/`pm_`): update `not_used.txt` in ALL modules that don't use it

### Modifying an existing equation

1. Check current equation in `equations.gms`
2. Identify ALL variables used — grep for them across modules
3. Make the change
4. Test with default scenario first
5. Test with ambitious policy scenario (more constraints binding)

### Adding a new land type

**⚠️ VERY HIGH RISK** — affects Module 10's conservation law directly

1. Add to set `land` in `core/sets.gms`
2. Module 10: update `q10_land_area` to include new type
3. Every module using `sum(land, ...)` must handle the new type
4. Initialize land area data for new type
5. Carbon, biodiversity, and cost modules must support it

### Adding a new crop type

1. Add to set `kcr` in `core/sets.gms`
2. Module 14 (yields): provide yield data for new crop
3. Module 30 (croparea): include in area allocation
4. Module 17 (production): include in production calculation
5. Module 21 (trade): set self-sufficiency ratios
6. Module 38 (factor costs): provide cost data

See also `agent/helpers/adding_new_crop.md` (if available).

---

## Common Pitfalls

### 1. Forgetting `not_used.txt`
Every `vm_` and `pm_` variable must be listed in `not_used.txt` for modules that don't use it. Missing entries cause GAMS warnings or errors.

### 2. Changing presolve bounds without understanding why they exist
Bounds in `presolve.gms` (`.lo`, `.up`, `.fx`) often prevent infeasibility. Removing a bound "to be safe" can make the model infeasible or produce nonsensical results.

### 3. Testing only with default scenario
Default scenarios are designed to be easy to solve. Ambitious policy scenarios (high carbon price, tight conservation) stress-test your changes. Always test with at least one ambitious scenario.

### 4. Modifying a high-centrality module without checking cascade
Changing Module 17 (production) affects 15+ downstream modules. Check `core_docs/Module_Dependencies.md` for the full impact.

### 5. Breaking the recursive time step assumption
MAgPIE solves one time step at a time. Variables from previous time steps are parameters (`p*_` or `pc*_`), not variables. Don't reference `v_XXX(t-1)` — use `pcXX_` instead.

---

## Module Cross-References

| Topic | Read |
|---|---|
| Full dependency graph | `core_docs/Module_Dependencies.md` |
| Safety protocols for critical modules | `cross_module/modification_safety_guide.md` |
| Conservation laws | `cross_module/land_balance_conservation.md` (and other `*_balance.md`) |
| Circular dependencies | `cross_module/circular_dependency_resolution.md` |
| GAMS coding patterns | `reference/GAMS_Phase5_MAgPIE_Patterns.md` |
| Module architecture | `core_docs/Core_Architecture.md` |

---

## Lessons Learned
<!-- APPEND-ONLY: Add new entries at the bottom. Never remove old ones. -->
<!-- Format: - YYYY-MM-DD: [lesson] (source: [user feedback | session experience]) -->
