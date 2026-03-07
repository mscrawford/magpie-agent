# 🤖 magpie-agent

**MAgPIE AI Documentation System**

Comprehensive, AI-optimized documentation for the MAgPIE land-use model. Works with any AI assistant.

**⚠️ FOR CURRENT STATUS: See `project/CURRENT_STATE.json` ⚠️**

---

## 🚀 Quick Start

### For New AI Sessions

**Working on documentation project? Read these in order:**

1. **This file** (you're reading it!) - Setup & orientation
2. **`project/CURRENT_STATE.json`** - Single source of truth (status, plans, history)
3. **Ask user**: "What should I work on?"

**🚨 CRITICAL: When working on the project, update ONLY `project/CURRENT_STATE.json` 🚨**
- **DO NOT** update README.md, AGENT.md, or any other file with project status
- **ALL** project information goes in the JSON (status, plans, handoffs, next steps)

**Using MAgPIE with an AI assistant?** Configure your AI to read `AGENT.md` which contains all instructions for answering MAgPIE questions.

---

## 📦 Setup Instructions

### 1. Clone magpie-agent into your MAgPIE directory
```bash
cd /path/to/your/magpie/
git clone git@github.com:mscrawford/magpie-agent.git magpie-agent
```

### 2. ⚠️ IMPORTANT: Deploy AGENT.md to MAgPIE root

**Your AI assistant needs `AGENT.md` in the working directory** (the MAgPIE root) to read it.

```bash
cd /path/to/your/magpie/
cp magpie-agent/AGENT.md AGENT.md
```

### 3. Configure Your AI Assistant

Point your AI tool to read `AGENT.md` at session start. Tool-specific instructions:

**Claude Code**: Add AGENT.md to your project context or workspace settings.

**GitHub Copilot**: Point to AGENT.md in your workspace configuration.

**Cursor**: Add AGENT.md to your AI context settings.

**Other tools**: Consult your tool's documentation for providing context files.

### 4. Verify Setup
```bash
# You should now have:
ls -la AGENT.md           # ← In MAgPIE root
ls -la magpie-agent/      # ← Full documentation repo
```

Now your AI assistant will use the comprehensive documentation when working with MAgPIE! 🎉

---

## 📊 Project Status

**👉 For current progress numbers, check `project/CURRENT_STATE.json` 👈**

### Completed Work

**Phase 0 - Foundation** (~70,000 words) ✅
- Model architecture, execution flow, folder structure
- 173 dependencies mapped, 26 circular cycles identified
- 172 input files cataloged with sources

**Phase 1 - Modules** (~20,000+ lines) ✅
- All 46 modules documented with verified equations
- Complete parameter descriptions
- Interface variables and dependencies mapped

**Phase 2 - Cross-Module Analysis** (~5,400 lines) ✅
- 5 conservation laws (land, water, carbon, nitrogen, food)
- Safety protocols for high-risk modifications
- Circular dependency resolution mechanisms

**Total**: ~290,000 words / ~64,000 lines of verified documentation

### Current Work

See `project/CURRENT_STATE.json` → `current_initiative` for active projects

---

## 📁 Documentation Structure

```
magpie-agent/
├── README.md                  ← You are here (project overview)
├── AGENT.md                   ← AI agent instructions (SOURCE - edit here)
│
├── agent/                     ← AGENT SYSTEM
│   ├── commands/              ← Slash command definitions (6 commands)
│   └── helpers/               ← Auto-loading context helpers (9 helpers)
│
├── project/                   ← PROJECT MANAGEMENT (maintainers only)
│   ├── README.md              ← What's in this folder
│   └── CURRENT_STATE.json     ← EVERYTHING (status, plans, history)
│
├── modules/                   ← Phase 1: Module Docs (46 files) ✅
│   ├── module_09.md           Drivers
│   ├── module_10.md           Land (critical hub)
│   └── ...                    (all 46 modules documented)
│
├── cross_module/              ← Phase 2: System Analysis (6 files) ✅
│   ├── land_balance_conservation.md
│   ├── water_balance_conservation.md
│   ├── carbon_balance_conservation.md
│   ├── nitrogen_food_balance.md
│   ├── modification_safety_guide.md
│   └── circular_dependency_resolution.md
│
├── core_docs/                 ← Architecture & Guidelines (6 files) ✅
│   ├── Core_Architecture.md
│   ├── Module_Dependencies.md
│   ├── Data_Flow.md
│   ├── Query_Patterns_Reference.md
│   ├── Response_Guidelines.md
│   └── Tool_Usage_Patterns.md
│
├── reference/                 ← GAMS Programming & Guides (9 files)
│   ├── GAMS_Fundamentals.md
│   ├── GAMS_Control_Structures.md
│   ├── GAMS_Advanced_Features.md
│   ├── GAMS_Functions_Operations.md
│   ├── GAMS_MAgPIE_Patterns.md
│   ├── GAMS_Best_Practices.md
│   ├── Code_Truth_Principles.md
│   ├── Infeasibility_Debugging_Guide.md
│   └── Verification_Protocol.md
│
├── feedback/                  ← User Feedback System
│   ├── README.md              System overview
│   ├── global/agent_lessons.md
│   └── integrated/            Archived feedback
│
└── scripts/                   ← Validation scripts
    └── validate_consistency.sh
```

---

## ⚠️ CRITICAL: Code Truth Principle

**When analyzing MAgPIE, describe ONLY what is actually implemented in the code.**

- ✅ **DO**: Describe actual equations, parameters, and module implementations
- ❌ **DON'T**: Add ecological or economic reality, suggest improvements, or describe ideal features
- 📖 **Read**: `reference/Code_Truth_Principles.md` before any analysis

---

## 🎯 Session Continuity Protocol

**This ensures any AI assistant can pick up the project instantly and maintain quality standards.**

### Starting a New Session

**Step 1: Orient (2 minutes)**

1. Read this README (you're doing it!)
2. Check `project/CURRENT_STATE.json` for:
   - Current progress (what's completed)
   - Known issues (problems to avoid)
   - Priorities (what to work on next)
   - Current initiative (active multi-session project)
3. Ask user: **"What should I work on?"**

**Step 2: Choose Your Path**

**Path A: Documentation Project Work**
- Update `project/CURRENT_STATE.json` (the ONLY file you modify - contains status, plans, history)
- Check `current_initiative` and `phase_3` sections in the JSON for active work

**Path B: MAgPIE Question Support**
- Follow instructions in `AGENT.md` (AI agent workflow)
- Check AI docs FIRST before reading GAMS code
- Use feedback system to improve documentation

**Path C: Module Documentation**
- Read `reference/Verification_Protocol.md`
- Follow verification checklist
- Update ONLY `project/CURRENT_STATE.json` for status

### During Work: Quality Standards

**The Golden Rule: CODE TRUTH**

**Describe ONLY what IS implemented in the code.**

**Always ask yourself**: "Where is this in the code? What file and line?"

**Mandatory Citation Format**

Every factual claim MUST cite source:
- ✅ `equations.gms:45` or `equations.gms:45-52`
- ✅ `presolve.gms:123`
- ✅ `input.gms:67`

**Use Exact Variable Names**
- ✅ `vm_land(j,land)` - correct
- ❌ "the land variable" - wrong
- ✅ `pm_carbon_density(t,j,land,c_pools)` - correct
- ❌ "carbon density parameter" - wrong

**State Limitations Explicitly**
- ✅ "Does NOT model fire dynamics"
- ✅ "Climate impacts are parameterized, not dynamically modeled"
- ✅ "Uses uniform BII factors globally"

**Distinguish Examples from Data**

When providing numerical examples:

✅ **CORRECT** - Clearly labeled as illustrative:
```markdown
To illustrate, consider a **hypothetical cell**:
- Available water: 100 km³ (made-up number for illustration)
- Environmental flows: 40 km³ (example value)

*Note: These are made-up numbers for pedagogical purposes.
Actual values require reading input file lpj_airrig.cs2*
```

❌ **WRONG** - Implies actual data:
```markdown
In Punjab region:
- Available water: 100 km³
- Environmental flows: 40 km³
```

**Verify Arithmetic**

If you provide calculations, **double-check the math**:
- ✅ 100 km³ × 50% = 50 km³ (correct)
- ❌ 100 km³ × 50% = 30 km³ (wrong - rejected)

### Ending a Session

**Step 1: Update State (5 minutes) - CRITICAL**

**🚨 ONLY UPDATE `project/CURRENT_STATE.json` - DO NOT UPDATE ANY OTHER FILES WITH STATUS 🚨**

Update `project/CURRENT_STATE.json` with:
1. Work completed (what you finished)
2. New issues found (problems discovered)
3. Recommended priorities for next session
4. Last session accomplishments
5. Update progress counters if applicable

**DO NOT UPDATE**:
- README.md (this file - static reference)
- AGENT.md (agent instructions - only update for new workflows)
- modules/README.md (static reference)

**Step 2: Commit and Push (if changes were made)**

If documentation was updated, commit to the magpie-agent repo:
```bash
git add -A && git commit -m "learn: session learnings — [brief description]"
git push origin main
```

---

## ✓ Quality Checklist

**Before finishing ANY module, verify:**

- [ ] **Cited file:line** for every factual claim
- [ ] **Used exact variable names** (vm_land, not "land variable")
- [ ] **Verified feature exists** (grep'd for it or read the file)
- [ ] **Described CODE behavior only** (not ecological/economic theory)
- [ ] **Labeled examples** (made-up numbers vs. actual input data)
- [ ] **Checked arithmetic** (if providing calculations)
- [ ] **Listed dependencies** (if suggesting modifications)
- [ ] **Stated limitations** (what code does NOT do)
- [ ] **No vague language** ("the model handles..." → specific equation)
- [ ] **Updated CURRENT_STATE.json**

**If you can't check all boxes, your response needs more verification.**

---

## 💡 How to Use This Documentation

### For New AI Sessions

1. Read this README (2 min)
2. Check `project/CURRENT_STATE.json` (1 min)
3. If active initiative exists, read that plan document (5 min)
4. Ask user what to work on

### For Understanding MAgPIE

1. **Model Overview**: `core_docs/Core_Architecture.md`
2. **Specific Module**: `modules/module_XX.md`
3. **Module Interactions**: `core_docs/Module_Dependencies.md`
4. **Data Sources**: `core_docs/Data_Flow.md`

### For Modifying MAgPIE Code

1. Read target module documentation in `modules/`
2. **Always check dependencies** in `core_docs/Module_Dependencies.md`
3. Verify interface variables in source code
4. Follow "Common Modifications" section in module doc
5. Test affected downstream modules

### For AI Agents

- **Query routing**: `AGENT.md` (Advanced Query Patterns section)
- **Response patterns**: Module-specific sections in each `module_XX.md`
- **Quality standards**: This README (Quality Checklist section)
- **Verification**: `reference/Verification_Protocol.md`

---

## 🔧 Common Commands

```bash
# Count documented modules
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

## 📚 Visualization & Data Files

### Dependency Graphs

Available in `reference/phase2_dependency_analysis/`:
- `core_dependencies.dot` - Top 20 modules
- `degradation_system.dot` - Degradation subsystem
- `forestry_system.dot` - Forestry/timber system
- `full_dependencies.dot` - All 46 modules

Generate PNG:
```bash
cd reference/phase2_dependency_analysis
dot -Tpng core_dependencies.dot -o core_dependencies.png
```

### Key Data Files

- `dependency_report.txt` - Complete 46×46 dependency matrix
- `dependency_analysis.json` - Machine-readable dependencies
- `detailed_module_analysis.txt` - Deep dive into hub modules

---

## 📐 CRITICAL: Single Source of Truth

**🚨 `project/CURRENT_STATE.json` IS THE ONLY FILE YOU MODIFY FOR PROJECT WORK 🚨**

**This file contains EVERYTHING:**
- ✅ Current status and progress
- ✅ All session accomplishments (no separate handoff docs!)
- ✅ Future plans and priorities (no separate plan docs!)
- ✅ Phase 3 task details
- ✅ Next steps

**NEVER UPDATE THESE FILES WITH PROJECT STATUS:**
- ❌ This README (static reference - DO NOT TOUCH)
- ❌ AGENT.md (AI instructions - DO NOT TOUCH)
- ❌ project/README.md (static reference - DO NOT TOUCH)
- ❌ modules/README.md (static overview - DO NOT TOUCH)
- ❌ **NO HANDOFF DOCUMENTS** - everything goes in CURRENT_STATE.json
- ❌ **NO PLAN DOCUMENTS** - everything goes in CURRENT_STATE.json

**After EVERY session:**
1. Update `project/CURRENT_STATE.json` with ALL progress/plans/status
2. Archive dated log files if any (usually none needed - use the JSON!)
3. **DO NOT** update status in README, AGENT.md, or create handoff docs

---

## 🔄 User Feedback System

MAgPIE developers can improve agent performance through feedback!

- Say "/feedback" for complete system overview
- Submit corrections, warnings, and lessons via feedback templates
- The agent also records corrections automatically during sessions

See `feedback/README.md` for details.

---

## 📞 What to Do When Stuck

**Problem**: Can't find equation
- **Solution**: Check `declarations.gms` with grep: `grep "^[ ]*qXX_" modules/XX_*/*/declarations.gms`

**Problem**: Wrong equation count
- **Solution**: Recount with grep (see command above)

**Problem**: Unknown interface variable
- **Solution**: Check `core_docs/Module_Dependencies.md` for provider module

**Problem**: Not sure what to work on
- **Solution**: Check `project/CURRENT_STATE.json` → `priorities` section

**Problem**: Equation formula doesn't match source
- **Solution**: Mark module as needing verification, document the discrepancy

**Problem**: Need to understand agent workflow
- **Solution**: Read `AGENT.md` for complete AI instructions

**Problem**: File paths or tool usage issues
- **Solution**: Check `core_docs/Tool_Usage_Patterns.md`

---

## 🎯 Project Goals

1. **100% Code Truth**: Describe only what IS implemented
2. **Complete Coverage**: All 46 modules documented
3. **Full Verification**: Every equation, formula, parameter checked
4. **AI-Optimized**: Easy for any AI assistant to understand and use
5. **Maintainable**: Clear structure, version control, protocols

---

## 📝 Key Lessons from Past Sessions

### 1. ALWAYS Verify Before Writing Comprehensive Docs

**Cost**: 2 hours wasted when fresh attempt had 10+ critical errors

**Lesson**: Read source files FIRST, verify EVERY equation, THEN write

### 2. Spot-Verification Is Efficient

**Method**:
1. Count equations: `grep "^[ ]*qXX_" declarations.gms | wc -l`
2. Verify 2-3 equation names
3. Check 1-2 interface variables
4. Confirm limitations stated

**Lesson**: 5 min/module for high-confidence check

### 3. Citation Density Predicts Quality

**Pattern**:
- 40+ citations = likely good
- 60+ citations = very good
- <20 citations = suspicious, needs review

**Lesson**: Citation count is a quick quality proxy

### 4. Reject Bad Modules Early

**Lesson**: Don't waste time trying to fix fundamentally flawed documentation

---

## 🌟 Remember

**You are a key part of trying to improve the MAgPIE model and address the crises of climate change and unsustainable land-use. Thank you!**

**Goal**: Make it effortless for the next AI session (or yourself tomorrow) to pick up instantly.

**How**:
- Keep `project/CURRENT_STATE.json` current
- Archive dated files immediately
- Use the quality checklist
- Follow Code Truth principles

**If future AI is confused**: This protocol needs improvement → submit feedback!

---

**Purpose**: Enable any AI to effectively work with MAgPIE without prior knowledge

**Principle**: Code Truth - Describe only what IS implemented in the code

**This is a STATIC reference document. For current project status, see `project/CURRENT_STATE.json`**
