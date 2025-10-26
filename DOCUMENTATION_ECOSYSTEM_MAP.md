# MAgPIE Agent - Complete Documentation Ecosystem Map

**Purpose**: Comprehensive inventory of ALL documentation, their roles, and inconsistency risks.

**Last Updated**: 2025-10-26

---

## 📊 COMPLETE INVENTORY (ALL 82+ FILES)

```
CATEGORY                        FILES    ~LINES    ROLE
══════════════════════════════════════════════════════════════════

🎯 META-PROJECT (Documentation Project Itself)
├─ START_HERE.md                  1        250    NEW SESSION ENTRY POINT
├─ RULES_OF_THE_ROAD.md           1        300    Session continuity protocol
├─ README.md                      1        250    Project overview (GitHub)
├─ CURRENT_STATE.json             1        209    SINGLE SOURCE OF TRUTH (status)
└─ DIRECTORY_AUDIT_REPORT.md      1        ???    Audit report (reference)

🤖 PRIMARY AGENT INSTRUCTIONS
├─ CLAUDE.md                      1        974    AGENT SYSTEM PROMPT (always loaded)
└─ AI_Agent_Behavior_Guide.md     1        994    Query routing & response patterns

🏗️ CORE ARCHITECTURE REFERENCE
├─ Phase1_Core_Architecture       1        366    Model structure, execution flow
├─ Phase2_Module_Dependencies     1        415    173 dependencies, centrality
├─ Phase3_Data_Flow               1        460    172 input files, data pipeline
└─ Tool_Usage_Patterns            1        716    Bash/Read/Write best practices

📦 MODULE DOCUMENTATION (Single Source of Truth)
├─ module_09.md through           46    43,883    ALL MODULE DETAILS
│  module_80.md                                   - Equations (verified)
│                                                 - Parameters
│                                                 - Dependencies
│                                                 - Limitations
└─ modules/README.md              1        ???    Overview (STATIC)

💬 MODULE NOTES (User Feedback Overlay)
├─ module_10_notes.md             1        296    Warnings, lessons, examples
├─ module_52_notes.md             1         82    (overlay, not replacement)
├─ module_70_notes.md             1        176
└─ (can grow as feedback integrated)

🔗 CROSS-MODULE ANALYSIS
├─ land_balance_conservation      1        820    7 land types, conservation
├─ water_balance_conservation     1        972    5 sectors, 4 sources
├─ carbon_balance_conservation    1        970    3 pools, Chapman-Richards
├─ nitrogen_food_balance          1        331    N tracking, food balance
├─ modification_safety_guide      1      1,102    Safety for Modules 10,11,17,56
├─ circular_dependency_resolution 1      1,034    26 cycles, resolution mechanisms
└─ cross_module/README.md         1        ???    Overview

📘 GAMS PROGRAMMING REFERENCE
├─ GAMS_Phase1_Fundamentals       1      1,585    Sets, parameters, equations
├─ GAMS_Phase2_Control_Structures 1      1,085    Dollar conditions, loops
├─ GAMS_Phase3_Advanced_Features  1      1,297    Macros, attributes
├─ GAMS_Phase4_Functions          1        898    Math, aggregation
├─ GAMS_Phase5_MAgPIE_Patterns    1      1,004    Naming, module structure
├─ GAMS_Phase6_Best_Practices     1        794    Debugging, performance
└─ GAMS_Programming_Reference_Plan 1       959    Plan document

🔄 FEEDBACK SYSTEM
├─ feedback/README.md              1       263    System overview
├─ feedback/COMPRESSION_GUIDE.md   1       ???    How to compress
├─ feedback/FUTURE_ENHANCEMENTS.md 1       ???    Planned improvements
├─ global/claude_lessons.md        1       241    Global behavior lessons
├─ integrated/*.md                 5       ???    Archived feedback (historical)
└─ templates/*.md                  5       ???    Submission templates

⚡ SLASH COMMANDS (Operational Workflows)
├─ /guide                          1       493    Complete capabilities
├─ /update                         1       171    Pull latest docs
├─ /feedback                       1       230    Feedback system
├─ /compress-feedback              1       412    Synthesize feedback
└─ /update-claude-md               1       120    Git workflow

📚 REFERENCE MATERIALS
├─ Code_Truth_Principles.md        1       ???    Core principle docs
├─ Verification_Protocol.md        1       ???    How to verify modules
└─ AI_Instruction_Refinement_Plan  1       ???    Plan document

📦 ARCHIVES (Historical)
└─ archive/*.md, working/*.md    ~10+      ???    Old session logs, temp files

══════════════════════════════════════════════════════════════════
TOTAL                            ~82+   ~65,000+ lines
```

---

## 🎯 DOCUMENT ROLES & WHEN THEY'RE READ

### **ALWAYS READ (Every Session)**

```
CLAUDE.md (974 lines)
├─ Loaded automatically by Claude Code as system prompt
├─ Contains: Workflow rules, routing logic, response patterns
└─ Agent reads: ALWAYS (part of system context)
```

### **PROJECT ORIENTATION (Documentation Project Work)**

```
When agent works on documentation project itself:

START_HERE.md → CURRENT_STATE.json → RULES_OF_THE_ROAD.md
     ↓                ↓                        ↓
  Entry point    Status tracker         Session protocol

Agent reads: ONLY when working on documentation project
NOT read: When answering MAgPIE questions (would be noise)
```

### **QUERY-SPECIFIC LOOKUPS**

#### Simple Query: "What equation calculates X?"
```
CLAUDE.md (routing) → modules/module_XX.md → DONE
(2 files, ~1,000 lines)
```

#### Module Modification: "Can I change Module 10?"
```
CLAUDE.md (routing)
  → modules/module_10.md (understand module)
  → Phase2_Module_Dependencies.md (23 dependents!)
  → modification_safety_guide.md (safety protocols)
  → module_10_notes.md (user warnings)
  → land_balance_conservation.md (conservation law)
(6 files, ~4,000 lines)
```

#### GAMS Code Work: "Write equation for Module 56"
```
CLAUDE.md (routing)
  → reference/GAMS_Phase5_MAgPIE_Patterns.md (naming)
  → reference/GAMS_Phase2_Control_Structures.md (syntax)
  → modules/module_56.md (context)
(4 files, ~3,000 lines)
```

---

## ⚠️ INCONSISTENCY RISK ANALYSIS (UPDATED)

### 🔴 **CRITICAL RISK: Information in Multiple Places**

#### **1. Project Status/Instructions**
```
PROBLEM: Instructions scattered across 5 files

STORED IN:
├─ START_HERE.md (says: "Read CURRENT_STATE.json")
├─ RULES_OF_THE_ROAD.md (says: "Read CURRENT_STATE.json")
├─ CLAUDE.md (says: "Read START_HERE.md if doc project")
├─ README.md (says: "Read START_HERE.md")
└─ CURRENT_STATE.json (actual status data)

RISK: If workflow changes, need to update 4 files
MITIGATION: All 4 explicitly declare themselves STATIC
```

#### **2. Module Dependencies**
```
STORED IN:
├─ Phase2_Module_Dependencies.md (AUTHORITATIVE: dependency graph)
├─ modification_safety_guide.md (Module 10: 23 dependents)
├─ module_10.md (Section: Modules that depend on this)
├─ module_10_notes.md (W003: "23 dependents")
└─ cross_module/*_conservation.md (specific dependency chains)

RISK: Dependency count changes → need to update 5 files
WORST CASE: Different counts in different files (user confusion)
```

#### **3. Conservation Laws**
```
STORED IN:
├─ cross_module/land_balance_conservation.md (AUTHORITATIVE)
├─ module_10.md (mentions q10_land_area)
├─ modification_safety_guide.md (Module 10 section)
├─ Phase1_Core_Architecture.md (overview mention)

RISK: Equation details change → update 4 files
```

#### **4. Workflow Instructions**
```
STORED IN:
├─ CLAUDE.md (check AI docs FIRST workflow)
├─ AI_Agent_Behavior_Guide.md (detailed routing patterns)
├─ START_HERE.md (project workflow)
├─ RULES_OF_THE_ROAD.md (session protocol)
├─ feedback/global/claude_lessons.md (behavior lessons)

RISK: Conflicting workflows if not synchronized
```

### 🟡 **MEDIUM RISK: Overlapping Content**

#### **5. Agent Behavior Guidance**
```
STORED IN:
├─ CLAUDE.md (primary instructions)
├─ AI_Agent_Behavior_Guide.md (detailed patterns)
├─ RULES_OF_THE_ROAD.md (session rules - for doc project)
└─ feedback/global/claude_lessons.md (learned corrections)

RISK: Contradictory guidance
CURRENT STATE: Mostly hierarchical, but growing
```

#### **6. Setup Instructions**
```
STORED IN:
├─ README.md (GitHub setup instructions)
├─ CLAUDE.md (bootstrap section)
└─ START_HERE.md (mentions setup)

RISK: Outdated setup steps in one file
```

### 🟢 **LOW RISK: Complementary Roles**

#### **7. GAMS Reference**
```
STORED IN:
├─ reference/GAMS_Phase*.md (6 files - comprehensive)
├─ Phase1_Core_Architecture.md (brief naming overview)

COMPLEMENTARY: Architecture gives overview, GAMS deep dive
```

---

## 🔍 **SPECIFIC INCONSISTENCIES FOUND**

### **Issue 1: Conflicting Entry Points**

```
README.md says:        "Read START_HERE.md"
CLAUDE.md says:        "If doc project: Read START_HERE.md"
START_HERE.md says:    "Read CURRENT_STATE.json"
RULES_OF_THE_ROAD says: "Read START_HERE.md then CURRENT_STATE.json"

CONFUSING: Multiple paths to same info
SOLUTION: Clarify context (doc project vs. MAgPIE questions)
```

### **Issue 2: Two "Agent Behavior Guides"**

```
CLAUDE.md (974 lines):
- Primary agent instructions
- Workflow rules
- Response patterns

AI_Agent_Behavior_Guide.md (994 lines):
- Detailed query routing
- Response patterns
- Token efficiency

OVERLAP: Both have response patterns, workflow guidance
RISK: Conflicting advice
```

### **Issue 3: Multiple "Status" Declarations**

```
START_HERE.md: "⚠️ FOR CURRENT PROJECT STATUS: See CURRENT_STATE.json ⚠️"
README.md:     "⚠️ FOR CURRENT STATUS: See CURRENT_STATE.json ⚠️"
RULES_OF_THE_ROAD: "⚠️ THIS IS A STATIC REFERENCE DOCUMENT ⚠️"
CLAUDE.md:     "CURRENT_STATE.json is the ONLY file tracking project status"

REDUNDANT: Same warning in 4 places
RESULT: Low risk (all point to same place, but verbose)
```

---

## 💡 **CONCRETE RECOMMENDATIONS**

### **Option 1: Document Role Hierarchy (Add to CLAUDE.md)**

```markdown
## 📐 DOCUMENT ROLES & PRECEDENCE

### When Answering MAgPIE Questions:
1. CLAUDE.md → routing logic
2. modules/module_XX.md → facts (SINGLE SOURCE OF TRUTH)
3. cross_module/*.md → system analysis
4. Phase*.md → architecture reference
5. module_XX_notes.md → warnings/lessons (may be outdated)

### When Working on Documentation Project:
1. START_HERE.md → entry point
2. CURRENT_STATE.json → status (SINGLE SOURCE OF TRUTH)
3. RULES_OF_THE_ROAD.md → protocol
4. CLAUDE.md → agent instructions

### If Information Conflicts:
Priority order:
1. Code itself (../modules/XX_name/realization/*.gms)
2. module_XX.md (verified against code)
3. cross_module/*.md (derived from modules)
4. Phase*.md (overview only)
5. notes files (user experience, may lag)

Action: Create feedback about the conflict
```

### **Option 2: Consolidate Overlapping Files**

**Candidate for Merger:**
```
AI_Agent_Behavior_Guide.md (994 lines)
                 ↓
        Merge into CLAUDE.md?
                 ↓
   Or: Keep separate but clarify roles:
   - CLAUDE.md = Quick reference (routing, workflows)
   - AI_Agent_Behavior_Guide.md = Deep dive (detailed patterns)
```

**Candidate for Simplification:**
```
START_HERE.md + README.md + RULES_OF_THE_ROAD
                 ↓
All say: "Read CURRENT_STATE.json"
                 ↓
Simplify to: README → START_HERE → CURRENT_STATE
```

### **Option 3: Create Consistency Validation Script**

```bash
#!/bin/bash
# scripts/validate_consistency.sh

echo "=== Documentation Consistency Check ==="

# Check 1: Dependency count consistency
echo "Checking Module 10 dependent count..."
grep -r "23 dependents" magpie-agent/ 2>/dev/null
# Should appear in: Phase2, module_10.md, module_10_notes, safety_guide

# Check 2: Chapman-Richards parameter count
echo "Checking Chapman-Richards parameters..."
grep -r "3 parameters\|3-parameter" magpie-agent/ 2>/dev/null
# Should be consistent across module_52.md, carbon_balance, notes

# Check 3: Entry point instructions
echo "Checking entry point consistency..."
grep -r "START_HERE.md\|CURRENT_STATE" README.md START_HERE.md RULES_OF_THE_ROAD.md

# Check 4: Cross-references
echo "Checking broken cross-references..."
# Extract all "see module_XX.md" references, verify files exist

# Check 5: Equation duplicates
echo "Checking for duplicate equation definitions..."
# Flag if same equation appears with different formulas
```

---

## 🎯 **IMMEDIATE ACTION ITEMS**

### **Priority 1: Clarify Document Roles**

**Add to CLAUDE.md:**
- Document hierarchy section
- Precedence rules for conflicts
- Clear separation: "Doc project work" vs. "MAgPIE questions"

### **Priority 2: Reduce Entry Point Confusion**

**Simplify:**
```
README.md: "Using MAgPIE with Claude? The agent reads CLAUDE.md automatically."
START_HERE.md: "Working on documentation project? Read CURRENT_STATE.json"
```

### **Priority 3: Flag High-Risk Duplicates**

**Create markers:**
```markdown
## Module Dependencies (⚠️ SYNC WITH Phase2_Module_Dependencies.md)

Module 10 has **23 dependents** (last updated: 2025-10-22, from Phase2)
```

### **Priority 4: Create Validation Script**

**Track in next compression:**
- Dependency counts
- Equation parameter counts
- Cross-references
- Entry point instructions

---

## 📊 **UPDATED SUMMARY**

**Total Documentation:**
- **82+ files**, ~65,000+ lines
- **5 meta-project files** (START_HERE, RULES, README, CURRENT_STATE, AUDIT)
- **46 module docs** (single source of truth)
- **3 notes files** (growing with feedback)
- **6 cross-module analyses**
- **6 GAMS reference guides**
- **5 slash commands**

**Inconsistency Risks:**
- **HIGH**: Module dependencies (5 locations)
- **HIGH**: Conservation laws (4 locations)
- **MEDIUM**: Workflow instructions (5 locations)
- **MEDIUM**: Entry point confusion (4 files)
- **LOW**: Most other content is complementary

**Mitigation Strategy:**
1. ✅ Add document role hierarchy to CLAUDE.md
2. ✅ Create validation script
3. ✅ Use compression to eliminate duplicates
4. ✅ Maintain "link don't duplicate" culture

---

**Thank you for catching this! The meta-project files are critical and I should have included them in the original analysis.**
