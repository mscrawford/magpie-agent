# Module Documentation

This directory contains comprehensive documentation for MAgPIE's 46 modules. All documentation follows the "Code Truth" principle: describing ONLY what IS implemented in the code, verified against source files.

For current state of the agent and ongoing work, see `../audit/validation_rounds.json`, `../audit/pipeline_audit_rounds.json`, and the git commit log. (Historical v1.0 snapshot at `../project/archive/CURRENT_STATE.v1.0_frozen_2026-03-07.json`.)

---

## Coverage

**46/46 modules documented and verified.**

Each module has:
- `module_XX.md` — the main documentation (purpose, equations, parameters, dependencies, limitations)
- `module_XX_notes.md` — sidecar for user-feedback warnings/lessons/examples (only created for modules where notes exist; absence is the correct signal)

---

## Documentation Standard

Each module documentation includes:

1. **Purpose & Overview** — What the module does
2. **Mechanisms & Equations** — How it works (with file:line citations)
3. **Parameters & Data** — Input data and defaults
4. **Dependencies** — Interface variables (cross-referenced with `../core_docs/Module_Dependencies.md`)
5. **Code Truth: What Module DOES** — Actual implementation
6. **Code Truth: What Module Does NOT** — Explicit limitations
7. **Common Modifications** — How to modify behavior
8. **Testing & Validation** — Verification approaches
9. **Summary** — Quick reference
10. **AI Agent Response Patterns** — Query routing

Doc-vs-code accuracy is mechanically guarded by `scripts/validate_consistency.sh` (40 checks across naming, citations, realizations, variables, equations, dependencies). The semantic-flywheel rounds (`../audit/validation_rounds.json`) probe doc accuracy from the answer side.

---

## How to Use This Documentation

### For understanding modules
1. Read `module_XX.md`.
2. Also read `module_XX_notes.md` if it exists (it carries user-feedback warnings).
3. Note limitations in the "Code Truth: What Module Does NOT" section.

### For modifying code
1. Read `module_XX.md`.
2. Check `../core_docs/Module_Dependencies.md` for downstream consumers.
3. Check `../cross_module/modification_safety_guide.md` for high-centrality modules.
4. Verify interface variables in source code.
5. Use "Common Modifications" as a starting point.

### For AI agents
- Follow `AGENT.md` workflow.
- Always cite `file:line` from the underlying GAMS source for high-stakes claims (not just from the doc, which can drift).
- Check the active realization before answering about modules with multiple realizations (`AGENT.md` Step 1c).

---

## Module Categories (Reference)

- **Drivers & Land**: 09, 10
- **Economics**: 11, 12, 36, 37, 38, 39
- **Food**: 15, 16
- **Environmental**: 22, 35, 50, 58, 59
- **Forestry**: 32, 73
- **Core Hubs**: 11, 17, 56
- **Water Cluster**: 40, 41, 42, 43, 44
- **Emissions**: 51-57
- **Other**: 13, 14, 18, 20, 21, 28-31, 34, 60, 62, 70-71, 80

(Full canonical list with descriptions in `../core_docs/Core_Architecture.md` §4.2.)

---

## Quick Commands

```bash
# Count module files
ls -1 module_*.md | wc -l   # 46 plus _notes.md sidecars

# List all modules
ls -1 module_*.md

# Verify equation count for module XX
grep "^[ ]*qXX_" ../../modules/XX_*/*/declarations.gms | wc -l

# Run the consistency validator
bash ../scripts/validate_consistency.sh
```

---

**Quality Standard**: "Code Truth" — describe only what IS implemented in the code, verified by `file:line` against the GAMS source.
