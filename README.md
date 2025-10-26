# 🤖 magpie-agent

**MAgPIE AI Documentation System**

Comprehensive, AI-optimized documentation for the MAgPIE land-use model.

**⚠️ FOR CURRENT STATUS: See `CURRENT_STATE.json` ⚠️**

---

## 🚀 Quick Start

### For New Claude Sessions

**Working on documentation project? Read these in order:**

1. **This file** (you're reading it!) - Setup & orientation
2. **`CURRENT_STATE.json`** - Single source of truth for ALL project status
3. **`CONSOLIDATION_PLAN.md`** - Current initiative (if active)
4. **Ask user**: "What should I work on?"

**Using MAgPIE with Claude Code? You're all set!** Claude automatically reads `CLAUDE.md` which contains all AI instructions for answering MAgPIE questions.

---

## 📦 Setup Instructions

### 1. Clone magpie-agent into your MAgPIE directory
```bash
cd /path/to/your/magpie/
git clone git@github.com:mscrawford/magpie-nest.git magpie-agent
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

### 3. Verify Setup
```bash
# You should now have:
ls -la CLAUDE.md          # ← In MAgPIE root (symlink or copy)
ls -la magpie-agent/       # ← Full documentation repo
```

Now Claude Code will automatically use the comprehensive documentation when working with MAgPIE! 🎉

---

## 📊 Project Status

**👉 For current progress numbers, check `CURRENT_STATE.json` 👈**

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

**Total**: ~95,000 words / ~25,000+ lines of verified documentation

### Current Work

See `CURRENT_STATE.json` → `current_initiative` for active projects

---

## 📁 Documentation Structure

```
magpie-agent/
├── README.md                  ← You are here (project overview)
├── CURRENT_STATE.json         ← ONLY file with status (UPDATE THIS)
├── CLAUDE.md                  ← AI agent instructions (SOURCE - edit here)
├── CONSOLIDATION_PLAN.md      ← Current initiative documentation
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
├── core_docs/                 ← Phase 0: Foundation (4 files) ✅
│   ├── Phase1_Core_Architecture.md
│   ├── Phase2_Module_Dependencies.md
│   ├── Phase3_Data_Flow.md
│   └── Tool_Usage_Patterns.md
│
├── reference/                 ← GAMS Programming (6 files)
│   ├── GAMS_Phase1_Fundamentals.md
│   ├── GAMS_Phase2_Control_Structures.md
│   ├── GAMS_Phase3_Advanced_Features.md
│   ├── GAMS_Phase4_Functions_Operations.md
│   ├── GAMS_Phase5_MAgPIE_Patterns.md
│   └── GAMS_Phase6_Best_Practices.md
│
├── feedback/                  ← User Feedback System
│   ├── README.md              System overview
│   ├── global/claude_lessons.md
│   └── integrated/            Archived feedback
│
├── .claude/                   ← Slash Commands
│   └── commands/              /guide, /update, /feedback, etc.
│
└── archive/                   ← Historical session logs
```

---

## ⚠️ CRITICAL: Code Truth Principle

**When analyzing MAgPIE, describe ONLY what is actually implemented in the code.**

- ✅ **DO**: Describe actual equations, parameters, and module implementations
- ❌ **DON'T**: Add ecological or economic reality, suggest improvements, or describe ideal features
- 📖 **Read**: `reference/Code_Truth_Principles.md` before any analysis

---

## 🎯 Session Continuity Protocol

**This ensures any Claude can pick up the project instantly and maintain quality standards.**

### Starting a New Session

**Step 1: Orient (2 minutes)**

1. Read this README (you're doing it!)
2. Check `CURRENT_STATE.json` for:
   - Current progress (what's completed)
   - Known issues (problems to avoid)
   - Priorities (what to work on next)
   - Current initiative (active multi-session project)
3. Ask user: **"What should I work on?"**

**Step 2: Choose Your Path**

**Path A: Documentation Project Work**
- Update `CURRENT_STATE.json` (the ONLY status file)
- Follow `CONSOLIDATION_PLAN.md` if that initiative is active
- Check `DOCUMENTATION_ECOSYSTEM_MAP.md` for file inventory

**Path B: MAgPIE Question Support**
- Follow instructions in `CLAUDE.md` (AI agent workflow)
- Check AI docs FIRST before reading GAMS code
- Use feedback system to improve documentation

**Path C: Module Documentation**
- Read `reference/Verification_Protocol.md`
- Follow verification checklist
- Update ONLY `CURRENT_STATE.json` for status

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

**🚨 ONLY UPDATE `CURRENT_STATE.json` - DO NOT UPDATE ANY OTHER FILES WITH STATUS 🚨**

Update `CURRENT_STATE.json` with:
1. Work completed (what you finished)
2. New issues found (problems discovered)
3. Recommended priorities for next session
4. Last session accomplishments
5. Update progress counters if applicable

**DO NOT UPDATE**:
- README.md (this file - static reference)
- CLAUDE.md (agent instructions - only update for new workflows)
- modules/README.md (static reference)

**Step 2: Archive Session Files (1 minute)**

Move dated log files to archive:
```bash
mv *_2025-10-*.md archive/
```

**Keep root clean!**

**Step 3: Create Lightweight Handover (50 lines MAX)**

**DO NOT** duplicate information from `CURRENT_STATE.json`

**DO** include:
- What was accomplished (bullet points)
- What failed (if anything)
- Recommended next steps (3-5 items)
- Any new lessons learned

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

### For New Claude Sessions

1. Read this README (2 min)
2. Check `CURRENT_STATE.json` (1 min)
3. If active initiative exists, read that plan document (5 min)
4. Ask user what to work on

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

- **Query routing**: `CLAUDE.md` (Advanced Query Patterns section)
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

Available in `core_docs/phase2_dependency_analysis/`:
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

## 📐 CRITICAL: Single Source of Truth

**`CURRENT_STATE.json` is the ONLY file tracking project status.**

**DO NOT update**:
- ❌ This README (static reference)
- ❌ CLAUDE.md (agent instructions)
- ❌ modules/README.md (static overview)

**DO update**:
- ✅ CURRENT_STATE.json (all progress, status, priorities)

**After EVERY session:**
1. Update `CURRENT_STATE.json` with progress
2. Archive dated log files to `archive/`
3. DO NOT update status in any other files

---

## 🔄 User Feedback System

MAgPIE developers can improve agent performance through feedback!

- Use `/feedback` command for complete system overview
- Submit feedback about agent behavior, documentation errors, or suggestions
- Review and compress integrated feedback with `/compress-feedback`

See `feedback/README.md` for details.

---

## 📞 What to Do When Stuck

**Problem**: Can't find equation
- **Solution**: Check `declarations.gms` with grep: `grep "^[ ]*qXX_" modules/XX_*/*/declarations.gms`

**Problem**: Wrong equation count
- **Solution**: Recount with grep (see command above)

**Problem**: Unknown interface variable
- **Solution**: Check `core_docs/Phase2_Module_Dependencies.md` for provider module

**Problem**: Not sure what to work on
- **Solution**: Check `CURRENT_STATE.json` → `priorities` section

**Problem**: Equation formula doesn't match source
- **Solution**: Mark module as needing verification, document the discrepancy

**Problem**: Need to understand agent workflow
- **Solution**: Read `CLAUDE.md` for complete AI instructions

**Problem**: File paths or tool usage issues
- **Solution**: Check `core_docs/Tool_Usage_Patterns.md`

---

## 🎯 Project Goals

1. **100% Code Truth**: Describe only what IS implemented
2. **Complete Coverage**: All 46 modules documented
3. **Full Verification**: Every equation, formula, parameter checked
4. **AI-Optimized**: Easy for any Claude to understand and use
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

**Goal**: Make it effortless for the next Claude (or yourself tomorrow) to pick up instantly.

**How**:
- Keep `CURRENT_STATE.json` current
- Archive dated files immediately
- Use the quality checklist
- Follow Code Truth principles

**If future Claude is confused**: This protocol needs improvement → submit feedback!

---

**Purpose**: Enable any AI to effectively work with MAgPIE without prior knowledge

**Principle**: Code Truth - Describe only what IS implemented in the code

**This is a STATIC reference document. For current project status, see `CURRENT_STATE.json`**
