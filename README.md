# 🤖 magpie-agent

**MAgPIE AI Documentation System**

Comprehensive, AI-optimized documentation for the MAgPIE land-use model.

**⚠️ FOR CURRENT STATUS: See `CURRENT_STATE.json` ⚠️**

---

## 🚀 Setup Instructions

**If you're setting up MAgPIE with Claude Code:**

### 1. Clone magpie-agent into your MAgPIE directory
```bash
cd /path/to/your/magpie/
git clone git@github.com:mscrawford/magpie-agent.git
```

### 2. ⚠️ IMPORTANT: Copy CLAUDE.md to MAgPIE root

**Claude Code needs `CLAUDE.md` in the working directory** (the MAgPIE root) to automatically read it.

**Option A: Symlink** (recommended - stays in sync):
```bash
cd /path/to/your/magpie/
ln -s magpie-agent/CLAUDE.md CLAUDE.md
```

**Option B: Copy** (simpler, but needs manual updates):
```bash
cd /path/to/your/magpie/
cp magpie-agent/CLAUDE.md CLAUDE.md
```

**Why this matters**: Claude Code looks for `CLAUDE.md` in your current working directory, not in subdirectories. Without this step, Claude won't automatically load the AI instructions when you start working with MAgPIE.

### 3. Verify Setup
```bash
# You should now have:
ls -la CLAUDE.md          # ← In MAgPIE root (symlink or copy)
ls -la magpie-agent/       # ← Full documentation repo
```

Now Claude Code will automatically use the comprehensive documentation when working with MAgPIE! 🎉

---

## ⚠️ CRITICAL PRINCIPLE FOR AI ANALYSIS

**When analyzing MAgPIE, describe ONLY what is actually implemented in the code.**

- ✅ **DO**: Describe actual equations, parameters, and module implementations
- ❌ **DON'T**: Add ecological or economic reality, suggest improvements, or describe ideal features
- 📖 **Read**: `reference/Code_Truth_Principles.md` before any analysis

---

## 🚀 Quick Start

**→ NEW SESSION? START HERE: [START_HERE.md](START_HERE.md)**

This is your entry point. It will orient you in 2-5 minutes and tell you:
- Where everything is
- What's done
- What to work on next
- How to follow the rules

**Then read**: [RULES_OF_THE_ROAD.md](RULES_OF_THE_ROAD.md) (5 min) for session protocol.

---

## 📁 Documentation Structure

```
magpie-agent/
├── START_HERE.md              ⭐ Read this first!
├── CURRENT_STATE.json         📊 Real-time project status
├── RULES_OF_THE_ROAD.md      📋 Session continuity protocol
│
├── modules/                   📚 Module documentation (PHASE 1 COMPLETE ✅)
│   ├── README.md              Overview (STATIC)
│   ├── module_09.md           Drivers
│   ├── module_10.md           Land (critical hub)
│   ├── module_12.md           Interest Rate
│   └── ...                    (all 46 modules documented)
│
├── cross_module/              🔄 Cross-module analysis (PHASE 2 IN PROGRESS)
│   └── (conservation laws, workflows, patterns - coming)
│
├── completed_phases/          ⭐ Permanent milestone archives
│   └── PHASE_1_MODULES_COMPLETE_2025-10-13.json
│
├── core_docs/                 📖 Stable reference documentation
│   ├── Phase1_Core_Architecture.md
│   ├── Phase2_Module_Dependencies.md  ← Check before modifications!
│   ├── Phase3_Data_Flow.md
│   ├── AI_Agent_Behavior_Guide.md
│   └── phase2_dependency_analysis/    (dependency matrices & graphs)
│
├── reference/                 📝 Principles & protocols
│   ├── Code_Truth_Principles.md
│   ├── Verification_Protocol.md
│   └── AI_Instruction_Refinement_Plan.md
│
├── archive/                   📦 Historical session logs
└── working/                   🔧 Current session work (temp files)
```

---

## 📊 Project Status

**👉 For current progress numbers, check `CURRENT_STATE.json` 👈**

| Phase | Status | Description | Location |
|-------|--------|-------------|----------|
| Phase 1 | ✅ Complete | Module Documentation | `modules/` (46/46 complete) |
| Core Docs | ✅ Complete | Architecture, Dependencies, Data Flow | `core_docs/` |
| **Phase 2** | **🔄 In Progress** | **Cross-Module Analysis** | **`cross_module/` (new)** |
| Future | ⏳ TBD | Additional analysis as needed | - |

**Current Focus**: Phase 2 - Cross-Module Analysis & Patterns
- Conservation laws (land, water, carbon, nitrogen, food)
- Common workflows (add crop, modify yields, implement policies)
- Dependency analysis (circular dependencies, cascade effects)
- Emergent behaviors (solver patterns, constraint binding)

**Current Progress**: See `CURRENT_STATE.json` for detailed status and priorities

---

## 🔑 Key Information

**For module completion status, priorities, and issues → See `CURRENT_STATE.json`**

### Most Critical Modules (for reference)

- **Module 11** (Costs): 27 dependencies - cost aggregator
- **Module 10** (Land): Provides to 15 modules - land hub
- **Module 56** (GHG Policy): Provides to 13 modules - carbon hub
- **Module 09** (Drivers): Pure source, 14 outputs

*This list is static reference. For current work status, check `CURRENT_STATE.json`*

---

## 💡 How to Use This Documentation

### For New Claude Sessions

1. Read `START_HERE.md` (2 min)
2. Check `CURRENT_STATE.json` (1 min)
3. Read `RULES_OF_THE_ROAD.md` (5 min)
4. Ask user what to work on
5. Follow verification protocol

### For Understanding MAgPIE

1. **Model Overview**: `core_docs/Phase1_Core_Architecture.md`
2. **Specific Module**: `modules/module_XX.md`
3. **Module Interactions**: `core_docs/Phase2_Module_Dependencies.md`
4. **Data Sources**: `core_docs/Phase3_Data_Flow.md`

### For Modifying MAgPIE Code

1. Read target module documentation in `modules/`
2. **Always check dependencies** in `core_docs/Phase2_Module_Dependencies.md`
3. Verify interface variables in source code
4. Follow "Common Modifications" section in module doc
5. Test affected downstream modules

### For AI Agents

- **Query routing**: `core_docs/AI_Agent_Behavior_Guide.md`
- **Response patterns**: Module-specific sections in each `module_XX.md`
- **Quality standards**: `RULES_OF_THE_ROAD.md` checklist
- **Verification**: `reference/Verification_Protocol.md`

---

## 🎯 Project Goals

1. **100% Code Truth**: Describe only what IS implemented
2. **Complete Coverage**: All 46 modules documented
3. **Full Verification**: Every equation, formula, parameter checked
4. **AI-Optimized**: Easy for any Claude to understand and use
5. **Maintainable**: Clear structure, version control, protocols

---

## 📝 Documentation Quality Standards

### Code Truth Principle

✅ **CORRECT**:
> "MAgPIE calculates BII using equation `q22_bii` with uniform land-type factors from `f22_bii.csv` (equations.gms:12)"

❌ **WRONG**:
> "MAgPIE models biodiversity impacts across ecosystems"

### Citation Standard

Every claim requires:
- File name (e.g., `equations.gms`)
- Line number (e.g., `:45` or `:45-52`)
- Exact variable names (e.g., `vm_land(j,land)`)

### Verification Levels

- **Fully Verified**: Every equation, formula, parameter checked
- **Spot-Verified**: Sample checked, needs full verification later
- **Not Started**: No documentation yet

See `reference/Verification_Protocol.md` for details.

---

## 🔧 Common Commands

```bash
# Count verified modules
ls -1 modules/module_*.md | wc -l

# Check project status
cat CURRENT_STATE.json

# Verify equation count for module XX
grep "^[ ]*qXX_" ../modules/XX_*/*/declarations.gms | wc -l

# List all modules
ls ../modules/

# Archive dated session files
mv *_2025-10-*.md archive/
```

---

## 📚 Additional Resources

### Visualization

Dependency graphs available in `core_docs/phase2_dependency_analysis/`:
- `core_dependencies.dot` - Top 20 modules
- `degradation_system.dot` - Degradation subsystem
- `forestry_system.dot` - Forestry/timber system
- `full_dependencies.dot` - All 46 modules

Generate PNG:
```bash
cd core_docs/phase2_dependency_analysis
dot -Tpng core_dependencies.dot -o core_dependencies.png
```

### Key Data Files

- `dependency_report.txt` - Complete 46×46 dependency matrix
- `dependency_analysis.json` - Machine-readable dependencies
- `detailed_module_analysis.txt` - Deep dive into hub modules

---

## 🔄 Session Continuity

**Starting a session**:
1. Read `START_HERE.md`
2. **Read `CURRENT_STATE.json`** for current status
3. Follow `RULES_OF_THE_ROAD.md`

**Ending a session**:
1. **Update `CURRENT_STATE.json` ONLY** (do not update any other files with status)
2. Archive dated files → `archive/`
3. Create brief handover note (50 lines max)

**Quality checklist**: See `RULES_OF_THE_ROAD.md`

**🚨 CRITICAL**: Only `CURRENT_STATE.json` should be updated with progress. All other files (README.md, START_HERE.md, RULES_OF_THE_ROAD.md, modules/README.md) are static reference documents.

---

## 📞 Support

**For issues or questions**:
- Check `RULES_OF_THE_ROAD.md` → "What to Do When Stuck"
- Review `reference/Verification_Protocol.md`
- Consult `core_docs/AI_Agent_Behavior_Guide.md`

---

**Purpose**: Enable any AI to effectively work with MAgPIE without prior knowledge
**Principle**: Code Truth - Describe only what IS implemented in the code

**This is a STATIC reference document. For current project status, see `CURRENT_STATE.json`**
