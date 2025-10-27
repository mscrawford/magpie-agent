# MAgPIE Agent Query Handling Flowchart

**Purpose**: Visual guide showing how the agent routes and answers different types of MAgPIE questions.

**Audience**: For humans (developers, users) to understand agent behavior. NOT loaded by the agent during operation.

---

## Complete Query Routing Flowchart

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          USER ASKS A QUESTION                               │
└────────────────────────────────┬────────────────────────────────────────────┘
                                 │
                                 ▼
                    ┌────────────────────────┐
                    │  What type of question? │
                    └────────────────────────┘
                                 │
         ┌───────────────────────┼───────────────────────┐
         │                       │                       │
         ▼                       ▼                       ▼
┌────────────────┐    ┌──────────────────┐    ┌──────────────────┐
│ MODULE-SPECIFIC│    │  CROSS-MODULE    │    │ PARAMETERIZATION │
│ "How does X    │    │ "How does X      │    │ "Is X modeled?"  │
│  work?"        │    │  affect Y?"      │    │ "Does MAgPIE     │
└────────┬───────┘    └────────┬─────────┘    │  account for Y?" │
         │                     │               └────────┬─────────┘
         ▼                     ▼                        │
  Read module_XX.md     Read Query_Patterns            │
         │              Reference.md (Pattern 2)        │
         ▼                     │                        ▼
  Read module_XX_       Read Phase2_Module      Read Query_Patterns
  notes.md              Dependencies.md         Reference.md
  (warnings)                   │                (Pattern 1 + Appendix)
         │                     ▼                        │
         ▼              Trace mechanism chain:          ▼
  Docs answer           X → intermediate → Y     Apply 3-check
  question?                    │                 verification:
    │    │                     ▼                        │
  Yes   No             Read module docs for       ┌─────┴─────┐
    │    │             each step in chain         │           │
    │    ▼                     │                  ▼           ▼
    │  Read GAMS         ┌─────┴──────┐    Check 1:    Check 2:
    │  code              │            │    Equation    Parameter
    │    │               ▼            ▼    structure   source
    │    │           Cite all    Cite all      │           │
    ▼    ▼           modules     cross-module  └─────┬─────┘
  Cite:            in chain     + Phase2             │
  module doc                         │               ▼
  + notes                            │         Check 3:
    │                                │         Dynamic feedback?
    │                                │               │
    │                                │         ┌─────┴──────┐
    └────────────────────────────────┼─────────┤            │
                                     │         ▼            ▼
                                     │   MECHANISTIC  PARAMETERIZED
                                     │   (models       (applies
                                     │    process)     fixed rates)
                                     │         │            │
                                     └─────────┴────────────┘
                                               │
         ┌─────────────────────────────────────┼─────────────────────────┐
         │                                     │                         │
         ▼                                     ▼                         ▼
┌────────────────┐                  ┌──────────────────┐      ┌────────────────┐
│   TEMPORAL     │                  │  MODIFICATION    │      │  CONSERVATION  │
│ "What happens  │                  │   SAFETY         │      │ "Is land/water/│
│  after X?"     │                  │ "Can I modify    │      │  carbon        │
└────────┬───────┘                  │  Module X?"      │      │  conserved?"   │
         │                          └────────┬─────────┘      └────────┬───────┘
         ▼                                   │                         │
  Read Query_Patterns                       ▼                         ▼
  Reference.md                    Read modification_         Read cross_module/
  (Pattern 3)                     safety_guide.md            *_balance_
         │                                   │               conservation.md
         ▼                                   ▼                         │
  Trace 5 steps:                  Read Phase2_Module          ┌────────┴────────┐
  1. Initial state                Dependencies.md             │                 │
  2. Transition                          │                    ▼                 ▼
  3. Convergence                         ▼               Land balance    Water balance
  4. Equilibrium                   Is module in          (strict         (inequality
  5. Timeframe                     top 4 centrality?     equality)       + buffer)
         │                           │         │              │                 │
         ▼                         Yes        No              │                 │
  Read relevant                     │          │              │                 │
  modules for                       ▼          ▼              ▼                 ▼
  each stage               HIGH RISK    Read specific    Carbon          Nitrogen
         │                 (17+ deps)   dependents       balance         + food
         │                      │          │                 │           balance
         │                      └──────────┤                 │                 │
         │                                 ▼                 │                 │
         │                          List all affected       │                 │
         │                          modules + conservation  │                 │
         │                          law impacts             │                 │
         │                                 │                 │                 │
         └─────────────────────────────────┴─────────────────┴─────────────────┘
                                           │
         ┌─────────────────────────────────┼─────────────────────────┐
         │                                 │                         │
         ▼                                 ▼                         ▼
┌────────────────┐             ┌──────────────────┐      ┌────────────────┐
│  DATA SOURCE   │             │  ARCHITECTURE    │      │   DEBUGGING    │
│ "Where does X  │             │ "How does MAgPIE │      │ "Model failed  │
│  come from?"   │             │  execute?"       │      │  - why?"       │
└────────┬───────┘             └────────┬─────────┘      └────────┬───────┘
         │                              │                         │
         ▼                              ▼                         ▼
  Read Phase3_               Read Phase1_             Read Query_Patterns
  Data_Flow.md               Core_Architecture.md     Reference.md
         │                              │              (Pattern 5: Debug Tree)
         ▼                              │                         │
  Find specific                         │                         ▼
  file + data source                    │                   Check modelstat:
         │                              │                         │
         ▼                              │              ┌──────────┼──────────┐
  Cite: file path                       │              │          │          │
  + source                              │              ▼          ▼          ▼
  + calibration method                  │         4=Infeas  3=Unbound  13=Error
         │                              │              │          │          │
         │                              │              ▼          ▼          ▼
         │                              │         Check     Missing    Check
         │                              │         binding   costs/     .lst file
         │                              │         constraints bounds    for errors
         │                              │              │          │          │
         └──────────────────────────────┴──────────────┴──────────┴──────────┘
                                        │
                                        ▼
                         ┌──────────────────────────────┐
                         │  APPLY RESPONSE GUIDELINES   │
                         │  (Response_Guidelines.md)    │
                         └──────────────┬───────────────┘
                                        │
                                        ▼
                         ┌──────────────────────────────┐
                         │   RUN QUALITY CHECKLIST      │
                         └──────────────┬───────────────┘
                                        │
                         ┌──────────────┴───────────────┐
                         │                              │
                         ▼                              ▼
                 ✓ Checked AI docs first?    ✓ Cited sources?
                         │                              │
                         ▼                              ▼
                 ✓ Used exact var names?     ✓ Described CODE only?
                         │                              │
                         ▼                              ▼
                 ✓ If "models X": 3-check?   ✓ Stated limitations?
                         │                              │
                         └──────────────┬───────────────┘
                                        │
                                        ▼
                         ┌──────────────────────────────┐
                         │   SEND RESPONSE WITH         │
                         │   VERIFICATION LEVEL         │
                         │   🟢 Verified (code)          │
                         │   🟡 Documented (AI docs)     │
                         │   🔵 General knowledge        │
                         └──────────────────────────────┘
```

---

## Simplified Decision Tree (Compact Version)

```
User Question
│
├─ MODULE-SPECIFIC ("How does X work?")
│  1. Read: modules/module_XX.md
│  2. Read: modules/module_XX_notes.md (warnings)
│  3. If needed: Read GAMS code
│  4. Cite: 🟡 module_XX.md (+ notes if used)
│
├─ CROSS-MODULE ("How does X affect Y?")
│  1. Read: Query_Patterns_Reference.md (Pattern 2)
│  2. Read: Module_Dependencies.md
│  3. Trace: X → intermediate steps → Y
│  4. Read: relevant module_XX.md for each step
│  5. Cite: 🟡 all modules in chain
│
├─ PARAMETERIZATION ("Is X modeled?")
│  1. Read: Query_Patterns_Reference.md (Pattern 1 + Appendix)
│  2. Apply 3-check verification:
│     ├─ Check 1: Equation structure (first principles or rates?)
│     ├─ Check 2: Parameter source (calculated or input?)
│     └─ Check 3: Dynamic feedback (state affects rate?)
│  3. Classify: MECHANISTIC / PARAMETERIZED / HYBRID
│  4. Cite: 🟢 code verification or 🟡 module docs
│
├─ TEMPORAL ("What happens after X?")
│  1. Read: Query_Patterns_Reference.md (Pattern 3)
│  2. Trace 5 steps:
│     ├─ Initial state
│     ├─ Transition mechanism
│     ├─ Convergence dynamics
│     ├─ New equilibrium
│     └─ Timeframe
│  3. Read: relevant modules for each stage
│  4. Cite: 🟡 complete temporal chain
│
├─ MODIFICATION SAFETY ("Can I modify Module X?")
│  1. Read: modification_safety_guide.md
│  2. Read: Module_Dependencies.md
│  3. Check: Is module in top 4 centrality?
│     ├─ Yes → HIGH RISK (17+ dependents, read safety protocols)
│     └─ No → Read specific dependents
│  4. List: All affected modules + conservation law impacts
│  5. Warn: Testing recommendations
│  6. Cite: 🟡 safety guide + Module_Dependencies
│
├─ CONSERVATION ("Is land/water/carbon conserved?")
│  1. Read: cross_module/*_balance_conservation.md
│     ├─ land_balance_conservation.md (strict equality)
│     ├─ water_balance_conservation.md (inequality + buffer)
│     ├─ carbon_balance_conservation.md (stock + emission)
│     └─ nitrogen_food_balance.md (N tracking + food)
│  2. Cite: 🟡 relevant balance doc
│
├─ DATA SOURCE ("Where does X come from?")
│  1. Read: Data_Flow.md (172 input files)
│  2. Find: specific file + data source
│  3. Cite: 🟡 file path + source + calibration method
│
├─ ARCHITECTURE ("How does MAgPIE execute?")
│  1. Read: Core_Architecture.md
│  2. Cite: 🟡 Core_Architecture sections
│
└─ DEBUGGING ("Model failed - why?")
   1. Read: Query_Patterns_Reference.md (Pattern 5: Debug Tree)
   2. Check modelstat:
      ├─ 4 (Infeasible) → Check binding constraints (land/water/food)
      ├─ 3 (Unbounded) → Check missing costs or bounds
      ├─ 13 (Error) → Check .lst file for GAMS errors
      └─ 1-2 but unrealistic → Check conservation laws
   3. Cite: 🟡 debugging pattern + relevant modules

═══════════════════════════════════════════════════════════════

ALL PATHS CONVERGE ON:

1. Apply Response_Guidelines.md
   ├─ Token efficiency (read only what's needed)
   ├─ Examples (clearly label illustrative vs. actual data)
   └─ Verification (3-check for "models X" claims)

2. Run Quality Checklist
   ├─ ✓ Checked AI docs first?
   ├─ ✓ Cited sources?
   ├─ ✓ Used exact variable names?
   ├─ ✓ Described CODE behavior only?
   ├─ ✓ If "models X": 3-check verification?
   └─ ✓ Stated limitations?

3. Send Response
   └─ Include verification level:
      • 🟢 Verified (read actual GAMS code this session)
      • 🟡 Documented (read AI docs this session)
      • 🔵 General (domain knowledge, not model-specific)
```

---

## Query Type Examples

### 1. Module-Specific Query
```
User: "How does livestock work in MAgPIE?"

Agent Path:
1. Read modules/module_70.md → 7 equations, feed baskets
2. Read modules/module_70_notes.md → warnings about feed constraints
3. Answer with equations and limitations
4. Cite: 🟡 "Based on module_70.md and module_70_notes.md"

Tokens: ~19K (16K CLAUDE.md + 3K module doc)
Time: 30-60 seconds
```

### 2. Cross-Module Query
```
User: "How does carbon pricing affect forests?"

Agent Path:
1. Check Query_Patterns_Reference.md Pattern 2
2. Read circular_dependency_resolution.md → Forest-Carbon cycle
3. Read module_56.md (GHG policy) → vm_carbon_price
4. Read module_32.md (forestry) → afforestation costs
5. Read module_52.md (carbon) → Chapman-Richards growth
6. Trace: vm_carbon_price → afforestation cost → carbon stock growth
7. Cite: 🟡 "Based on circular_dependency_resolution.md, module_32/52/56.md"

Tokens: ~24K (16K + 8K module docs)
Time: 2 minutes
```

### 3. Parameterization Query
```
User: "Does MAgPIE model tillage effects on soil organic matter?"

Agent Path:
1. Check Query_Patterns_Reference.md Pattern 1 + Appendix
2. Apply 3-check verification:
   • Check 1: Equation applies IPCC factors (not first principles)
   • Check 2: f59_cratio_tillage from input files
   • Check 3: Hardcoded to 100% full_tillage (no dynamic feedback)
3. Classify: PARAMETERIZED but NOT IMPLEMENTED
4. Answer: "Infrastructure exists but hardcoded to defaults"
5. Cite: 🟢 "Verified in module_59.md + preloop.gms:52"

Tokens: ~34K (16K + 15K patterns + 3K module)
Time: 2 minutes
```

### 4. Modification Safety Query
```
User: "Can I modify Module 10 (land) without breaking things?"

Agent Path:
1. Read modification_safety_guide.md → Module 10 is HIGHEST centrality
2. Read Module_Dependencies.md → 23 dependents
3. List affected: Modules 11,14,17,18,29-32,35,38-40,42,52,56,58-59,70-71,73
4. Warn: Affects ALL conservation laws (land, water, carbon, nitrogen)
5. Recommend: Extensive testing, check all dependents
6. Cite: 🟡 "Based on modification_safety_guide.md, Module_Dependencies.md"

Tokens: ~41K (16K + 20K guidelines + 5K safety)
Time: 3-4 minutes
```

---

## Token Budget by Query Type

| Query Type           | Docs Read                    | Token Budget | Time   |
|---------------------|------------------------------|--------------|--------|
| Simple module       | 1 module doc                 | ~19K         | 30s    |
| Module + notes      | module + notes               | ~20K         | 1min   |
| Cross-module        | 3-4 modules                  | ~24K         | 2min   |
| Parameterization    | pattern + module             | ~34K         | 2min   |
| Modification safety | safety + Module_Dependencies | ~41K         | 3min   |
| Temporal mechanism  | pattern + modules            | ~24K         | 2min   |
| Conservation laws   | balance docs                 | ~21K         | 2min   |
| Architecture        | Core_Architecture            | ~26K         | 3min   |

**Key principle**: Agent loads 16K CLAUDE.md always, then reads only what's needed for the specific question.

---

## Verification Levels

Every response includes verification status:

- 🟢 **Verified**: Read actual GAMS code this session (`file.gms:123`)
- 🟡 **Documented**: Read AI docs this session (`module_XX.md`)
- 🟠 **Literature**: Published papers (`Author et al. YEAR`)
- 🔵 **General**: Domain knowledge (not model-specific)
- 🔴 **Inferred**: Training data (lowest confidence - avoid for MAgPIE)

**Default for MAgPIE questions**: 🟡 (documented) or 🟢 (verified against code)

---

## Summary

**The agent uses a decision tree approach:**

1. **Classify** the question type (module, cross-module, parameterization, etc.)
2. **Route** to appropriate documentation (specific module_XX.md, patterns, cross-module)
3. **Apply** relevant pattern if complex (3-check, tracing, debugging tree)
4. **Verify** with quality checklist (7+ checks)
5. **Cite** sources with verification level (🟢🟡🔵)

**All paths converge on**: Quality checklist → Verified response → Proper citation

**Token efficiency**: Agent loads 16K core + only what's needed (avg 30-50% savings vs. old 48K)
