# Helper: Link Don't Duplicate (doc-editing policy)

**Auto-load triggers**: "update doc", "edit module_XX.md", "add to documentation", "doc edit", "duplicate this", "where does this belong", "linking vs duplicating", "writing docs"
**Lessons count**: 0 entries

---

## Purpose

Doc-author policy: when updating or creating documentation, avoid information drift by linking to single sources of truth instead of duplicating facts. Hoisted from AGENT.md in R6 to free always-loaded surface (the section was ~80 lines of editorial guidance loading on every session, including pure Q&A sessions).

---

## Authoritative Sources (Single Source of Truth)

Never duplicate these — always link instead:

| Information Type | Authoritative Source | Link Format |
|-----------------|---------------------|-------------|
| Module equations, parameters, variables | `modules/module_XX.md` | `modules/module_XX.md#equation-name` |
| Dependency counts & lists | `core_docs/Module_Dependencies.md` | `core_docs/Module_Dependencies.md` §2.1 (centrality table) |
| Conservation law equations | `cross_module/*_balance.md` | `cross_module/land_balance_conservation.md` |
| GAMS syntax & patterns | `reference/GAMS_*.md` | `reference/GAMS_MAgPIE_Patterns.md#topic` |
| Data file sources | `core_docs/Data_Flow.md` | `core_docs/Data_Flow.md#file-name` |
| Helper / command inventories | `AGENT.md` Auto-Loading + Available Commands tables | (do NOT duplicate; link only) |
| Aggregate counts (rounds, bugs, helpers, commands, etc.) | `<!--count:KEY-->N<!--/count-->` markers fed from `scripts/refresh_aggregate_counts.py` | wrap the literal in the marker |

## When to Link vs When to Duplicate

✅ **ALWAYS LINK** (never duplicate):
- Dependency counts ("Module X has 23 dependents") → link to `Module_Dependencies.md`
- Equation formulas from other modules → link to authoritative `module_XX.md`
- Data file sources and formats → link to `Data_Flow.md`
- Exact numerical values that must stay synchronized
- Inventories: helpers, commands, files in a directory

✅ **LEGITIMATE DUPLICATION** (different contexts, different purposes):
- **Conservation law equations** in both `modules/module_XX.md` (technical doc: "This is equation 1 of Module X") AND `cross_module/*_balance.md` (system-level doc: "This is THE conservation constraint").
- **Different levels of explanation**: overview vs detailed, pedagogical vs reference.

## Examples

❌ **WRONG** — Hardcoded dependency count:
```markdown
**Risk Level**: HIGH (Module 10 has 23 dependents)
```

✅ **CORRECT** — Link to authoritative source:
```markdown
**Risk Level**: HIGH (see `core_docs/Module_Dependencies.md#module-10` for dependency list)
```

❌ **WRONG** — Duplicate equation from another module:
```markdown
Module 29 uses land allocation:
q10_land_area(j2) .. sum(land, vm_land(j2,land)) =e= ...
```

✅ **CORRECT** — Link to authoritative source:
```markdown
Module 29 uses land allocation from Module 10 (see `modules/module_10.md` §1 — Equation 1: Land Area Conservation)
```

✅ **ACCEPTABLE** — Legitimate pedagogical duplication:
```markdown
# In module_10.md (technical documentation)
**Equation 1**: q10_land_area enforces land conservation
[full formula]

# In cross_module/land_balance_conservation.md (system-level analysis)
**The Core Conservation Constraint**: q10_land_area ensures total land remains constant
[same formula shown for pedagogical clarity]
```

## Enforcement During Updates

Before adding information to documentation:
1. **Check if it already exists** — search for existing coverage.
2. **Identify authoritative source** — where does this information live?
3. **Link don't duplicate** — reference the authoritative source.
4. **If duplicating** — ensure different context/purpose justifies it.

**Red flags that indicate duplication**:
- Writing the same equation formula seen elsewhere.
- Listing dependency counts already in `Module_Dependencies.md`.
- Describing data files already documented in `Data_Flow.md`.
- Copying exact parameter descriptions from another module doc.
- Enumerating helpers / commands in a non-AGENT.md doc.

## Subordinate-README inventory rule (R6 G1)

Subordinate READMEs MUST NOT include inventories that are maintained elsewhere — only pointers. Class-level rule documented in `agent/helpers/maintenance_protocol.md` §5.

---

## Lessons Learned

<!-- APPEND-ONLY -->
