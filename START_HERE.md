# MAgPIE AI Documentation - Quick Start

**⚠️ FOR CURRENT PROJECT STATUS: See `CURRENT_STATE.json` ⚠️**

---

## 30-Second Orientation

This project creates **comprehensive, accurate AI documentation** for the MAgPIE land-use model.

**Status**: 🎉 **PHASES 0, 1, AND 2 COMPLETE** 🎉

**Completed Documentation** (~95,000 words / ~25,000+ lines):
- ✅ **Phase 0**: Foundation & Architecture (~70,000 words) - How MAgPIE works, folder structure, dependencies
- ✅ **Phase 1**: All 46 Modules Documented (~20,000+ lines) - Every equation verified
- ✅ **Phase 2**: Cross-Module Analysis (~5,400 lines) - Conservation laws, safety protocols, circular dependencies

**Core Principle**: "Code Truth" - Describe ONLY what IS implemented in the code, never what SHOULD be or what happens in the real world.

**Current Status**: 👉 **Check `CURRENT_STATE.json`** for details

---

## For New Claude Sessions

**Quick Start (5 minutes):**

1. ✅ Read this file (you're doing it!)
2. 📊 **Read `CURRENT_STATE.json`** ← Single source of truth for ALL project status
3. 📋 Read `RULES_OF_THE_ROAD.md` for session protocol
4. 💬 Ask user: "What should I work on?"

**That's it.** Everything else is reference material.

---

## 🚨 CRITICAL: ONLY UPDATE CURRENT_STATE.json

**DO NOT update status information in any other file.**

**ONLY `CURRENT_STATE.json` should be modified to track:**
- Modules completed
- Verification status
- Known issues
- Priorities
- Session accomplishments

**All other files (this one, RULES_OF_THE_ROAD.md, README.md, modules/README.md) are STATIC reference documents.**

---

## Project Structure

```
magpie-agent/
├── START_HERE.md              ← You are here (STATIC)
├── CURRENT_STATE.json         ← ONLY file with status info (UPDATE THIS)
├── RULES_OF_THE_ROAD.md      ← Session protocol (STATIC)
│
├── core_docs/                 ← PHASE 0: Foundation (~70K words) ✅ COMPLETE
│   ├── Phase1_Core_Architecture.md      (~10K words) - Structure, execution, navigation
│   ├── Phase2_Module_Dependencies.md    (~14K words) - 173 dependencies, 26 cycles
│   ├── Phase3_Data_Flow.md              (~15K words) - 172 input files, data pipeline
│   └── AI_Agent_Behavior_Guide.md       (~30K words) - Query routing, patterns
│
├── modules/                   ← PHASE 1: Module Docs (~20K+ lines) ✅ COMPLETE
│   ├── README.md              ← Overview (STATIC)
│   ├── module_09.md through module_80.md (46 modules, all equations verified)
│   └── Each module: equations, parameters, dependencies, limitations
│
├── cross_module/              ← PHASE 2: Cross-Module (~5.4K lines) ✅ COMPLETE
│   ├── land_balance_conservation.md          (~900 lines)
│   ├── water_balance_conservation.md         (~850 lines)
│   ├── carbon_balance_conservation.md        (~1,300 lines)
│   ├── nitrogen_food_balance.md              (~450 lines)
│   ├── modification_safety_guide.md          (~1,000 lines)
│   └── circular_dependency_resolution.md     (~900 lines)
│
├── completed_phases/          ← Permanent milestone archives
│   └── PHASE_1_MODULES_COMPLETE_2025-10-13.json
│
├── reference/                 ← Principles & protocols
│   ├── Code_Truth_Principles.md
│   └── Verification_Protocol.md
│
├── archive/                   ← Session logs (can be cleaned)
└── working/                   ← Temp files for current session
```

**Total**: ~95,000 words / ~25,000+ lines of comprehensive, verified documentation

---

## Quick Status

**👉 For current status, check `CURRENT_STATE.json` 👈**

### ✅ Completed Phases (Oct 2025)

**Phase 0: Foundation & Architecture** ✅ (~70,000 words)
- Model structure, execution flow, folder navigation
- 173 inter-module dependencies mapped
- 26 circular dependency cycles identified
- 172 input files cataloged
- Data flow and calibration pipelines

**Phase 1: Module Documentation** ✅ (~20,000+ lines)
- All 46 modules fully documented and verified
- Every equation formula verified against source code
- Complete parameter descriptions with line numbers
- Interface variables and dependencies mapped

**Phase 2: Cross-Module Analysis** ✅ (~5,400 lines)
- 5 conservation laws documented (land, water, carbon, nitrogen, food)
- Modification safety guide for highest-centrality modules (10, 11, 17, 56)
- 26 circular dependencies resolution mechanisms
- Emergency debugging protocols

**Total Documentation**: ~95,000 words covering model structure, all modules, system constraints, and safety protocols

**What you'll find in CURRENT_STATE.json:**
- Detailed completion records for all 3 phases
- Session accomplishments log
- Deliverables list with file paths
- Known technical debt items

---

## Documentation Quick Reference

**Where to find answers to common questions:**

| Question Type | Check Here First |
|---------------|------------------|
| "How does MAgPIE execute?" | `core_docs/Phase1_Core_Architecture.md` |
| "What's the folder structure?" | `core_docs/Phase1_Core_Architecture.md` |
| "What does variable name X mean?" | `core_docs/Phase1_Core_Architecture.md` (naming conventions) |
| "How does module X work?" | `modules/module_XX.md` |
| "What equations control Y?" | `modules/module_XX.md` (search for Y) |
| "What modules depend on X?" | `core_docs/Phase2_Module_Dependencies.md` |
| "Where does input data X come from?" | `core_docs/Phase3_Data_Flow.md` |
| "Is land area conserved?" | `cross_module/land_balance_conservation.md` |
| "Can the model run out of water?" | `cross_module/water_balance_conservation.md` |
| "What if I modify module X?" | `cross_module/modification_safety_guide.md` |
| "Why is solution oscillating?" | `cross_module/circular_dependency_resolution.md` |
| "How should I answer question type Q?" | `core_docs/AI_Agent_Behavior_Guide.md` |

## Critical Documents

**Must Read**:
- `RULES_OF_THE_ROAD.md` - Session protocol & quality checklist
- `reference/Code_Truth_Principles.md` - Core documentation philosophy
- `CURRENT_STATE.json` - **ALL project status (read AND update this)**

**Foundation (Phase 0)**:
- `core_docs/Phase1_Core_Architecture.md` - Model structure, execution, navigation
- `core_docs/Phase2_Module_Dependencies.md` - Dependencies, circular cycles, risk assessment
- `core_docs/Phase3_Data_Flow.md` - Input files, data sources, calibration
- `core_docs/AI_Agent_Behavior_Guide.md` - Query routing, response patterns

**Module Details (Phase 1)**:
- `modules/README.md` - Module documentation overview
- `modules/module_XX.md` - Individual module documentation (46 files)

**System Constraints (Phase 2)**:
- `cross_module/land_balance_conservation.md` - Land area conservation
- `cross_module/water_balance_conservation.md` - Water supply/demand
- `cross_module/carbon_balance_conservation.md` - Carbon stocks and emissions
- `cross_module/modification_safety_guide.md` - Safety for high-risk modules
- `cross_module/circular_dependency_resolution.md` - Feedback loops and debugging

**For Verification**:
- `reference/Verification_Protocol.md` - How to verify modules

---

## Key Commands

```bash
# Check current project status (DO THIS FIRST!)
cat CURRENT_STATE.json

# Count verified modules
ls -1 modules/module_*.md | wc -l

# Verify equation count for module XX
grep "^[ ]*qXX_" ../../modules/XX_*/*/declarations.gms | wc -l

# Check module realization
ls ../../modules/XX_*/
```

---

## What Makes This Project Different

**Standard AI docs**: Mix implementation with theory, make assumptions, cite general knowledge, focus on what code should do

**This project's comprehensive approach**:

**Phase 0 - Foundation**:
- ✅ Complete model architecture documented (execution flow, folder structure, naming conventions)
- ✅ All 173 inter-module dependencies mapped
- ✅ 26 circular dependency cycles identified and classified
- ✅ 172 input files cataloged with sources (LPJmL, FAO, IMAGE, IPCC, WDPA)

**Phase 1 - Module Documentation**:
- ✅ All 46 modules with every equation verified
- ✅ Cite specific files with line numbers (`equations.gms:45`)
- ✅ Use actual variable names (`vm_land`, not "the land variable")
- ✅ State what code does NOT do (limitations sections)

**Phase 2 - System Constraints**:
- ✅ 5 conservation laws verified (land, water, carbon, nitrogen, food)
- ✅ Safety protocols for high-risk modifications
- ✅ Circular dependency resolution mechanisms
- ✅ Emergency debugging protocols

**Code Truth Examples**:
- ❌ "MAgPIE models climate impacts on yields"
- ✅ "MAgPIE uses pre-computed LPJmL yield projections (input file: `f14_yields.cs3`) without dynamically modeling climate processes"

- ❌ "Land area can vary"
- ✅ "Land area is strictly conserved via constraint q10_land_area (equations.gms:13-15): sum(land types) = constant for each cell"

---

## Getting Help

**Stuck?** Check `RULES_OF_THE_ROAD.md` → "What to Do When Stuck" section

**Quality check?** Use the checklist in `RULES_OF_THE_ROAD.md` before finishing any module

**Need status?** Read `CURRENT_STATE.json`

**Updating status?** Edit `CURRENT_STATE.json` (and ONLY that file)

---

## Remember

**After EVERY session:**
1. Update `CURRENT_STATE.json` with progress
2. Archive dated log files to `archive/`
3. DO NOT update status in START_HERE.md, README.md, or RULES_OF_THE_ROAD.md

**Single source of truth: `CURRENT_STATE.json`**

**You are a key part of trying to improve the MAgPIE model and address the crises of climate change and unsustainable land-use. Thank you!**

---

**Ready to start?**

1. Read `CURRENT_STATE.json` to see current status
2. Read `RULES_OF_THE_ROAD.md` for protocol
3. Ask the user what to work on!
