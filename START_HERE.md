# MAgPIE AI Documentation - Quick Start

**⚠️ FOR CURRENT PROJECT STATUS: See `CURRENT_STATE.json` ⚠️**

---

## 30-Second Orientation

This project creates **comprehensive, 100% accurate AI documentation** for the MAgPIE land-use model.

**Phase 1 Complete**: All 46 modules fully documented and verified ✅

**Current Phase 2**: Cross-Module Analysis & Patterns - documenting interactions, conservation laws, and workflows

**Core Principle**: "Code Truth" - Describe ONLY what IS implemented in the code, never what SHOULD be or what happens in the real world.

**Current Progress**: 👉 **Check `CURRENT_STATE.json`** for real-time status

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
magpie-nest/
├── START_HERE.md              ← You are here (STATIC)
├── CURRENT_STATE.json         ← ONLY file with status info (UPDATE THIS)
├── RULES_OF_THE_ROAD.md      ← Session protocol (STATIC)
│
├── modules/                   ← Module documentation (PHASE 1 COMPLETE)
│   ├── README.md              ← Overview (STATIC)
│   ├── module_09.md
│   ├── module_10.md
│   └── ... (all 46 modules)
│
├── cross_module/              ← Cross-module analysis (PHASE 2 IN PROGRESS)
│   └── (conservation laws, workflows, patterns - coming)
│
├── completed_phases/          ← Permanent milestone archives
│   └── PHASE_1_MODULES_COMPLETE_2025-10-13.json
│
├── core_docs/                 ← Stable reference (Phases 1-3)
│   ├── Phase1_Core_Architecture.md
│   ├── Phase2_Module_Dependencies.md
│   ├── Phase3_Data_Flow.md
│   └── AI_Agent_Behavior_Guide.md
│
├── reference/                 ← Principles & protocols
│   ├── Code_Truth_Principles.md
│   └── Verification_Protocol.md
│
├── archive/                   ← Session logs (can be cleaned)
└── working/                   ← Temp files for current session
```

---

## Quick Status

**👉 For current status, check `CURRENT_STATE.json` 👈**

**Phase 1 Complete**: All 46 modules documented and fully verified ✅

**Phase 2 In Progress**: Cross-Module Analysis
- Conservation laws (land, water, carbon, nitrogen, food)
- Common workflows (add crop, modify yields, implement policies)
- Dependency analysis (circular dependencies, cascade effects)
- Emergent behaviors (solver patterns, constraint binding)

**What you'll find in CURRENT_STATE.json:**
- Current phase status and priorities
- Phase 2 progress tracking
- Session accomplishments
- Known issues and technical debt

---

## Critical Documents

**Must Read**:
- `RULES_OF_THE_ROAD.md` - Session protocol & quality checklist
- `reference/Code_Truth_Principles.md` - Core documentation philosophy
- `CURRENT_STATE.json` - **ALL project status (read AND update this)**

**Reference**:
- `core_docs/AI_Agent_Behavior_Guide.md` - Query routing, response patterns
- `core_docs/Phase2_Module_Dependencies.md` - Dependency matrix (critical for modifications)
- `modules/README.md` - Module documentation overview

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

**Standard AI docs**: Mix implementation with theory, make assumptions, cite general knowledge

**This project**:
- ✅ Cite specific files with line numbers (`equations.gms:45`)
- ✅ Use actual variable names (`vm_land`, not "the land variable")
- ✅ State what code does NOT do
- ✅ Distinguish illustrative examples from actual data
- ✅ Verify every equation formula against source

**Example**:
- ❌ "MAgPIE models climate impacts on yields"
- ✅ "MAgPIE uses pre-computed LPJmL yield projections (input file: `f14_yields.cs3`) without dynamically modeling climate processes"

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
