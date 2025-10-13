# MAgPIE Model - Key Systems Reference

## 🚀 QUICK START: OVERARCHING INTERACTION PRINCIPLES

### PRIMARY DIRECTIVE
**When analyzing MAgPIE, describe ONLY what is actually implemented in the code.**

### Core Principles for Our Interaction:
1. **CODE TRUTH**: I want to know what MAgPIE DOES, not what it SHOULD do or what happens in the real world
2. **PRECISION**: Reference specific files, equations, and line numbers when possible
3. **CLARITY**: Clearly state when something is NOT modeled or simplified
4. **HONESTY**: If unsure, check the code rather than making assumptions
5. **FOCUS**: Answer about the model's implementation, not general knowledge

### What This Means:
- ✅ "MAgPIE calculates yields using equation q14_yield_crop with tau factors"
- ❌ "MAgPIE accounts for climate variability in yields" (unless it actually does)
- ✅ "The model uses uniform BII factors globally"
- ❌ "African savannas have higher biodiversity" (that's ecology, not model code)

### Before Answering Any Question:
1. Check actual module files
2. Verify in equations.gms
3. Confirm parameters exist
4. State limitations explicitly

### 🚨 CRITICAL: Examples vs. Actual Data

**When providing numerical examples, ALWAYS explicitly state the source:**

**✅ CORRECT - Illustrative Example (clearly labeled):**
> "To illustrate the water allocation, consider a **hypothetical cell** in India's Punjab region:
> - Available water: 100 km³ (illustrative number)
> - Environmental flows: 40 km³ (example - actual values vary by cell)
> - Manufacturing (50% of available): 50 km³
> - Available for irrigation: 10 km³
>
> *Note: These are made-up numbers for pedagogical purposes. Actual values require reading the LPJmL input data files (`lpj_airrig.cs2`, `lpj_envflow_grper.cs2`) which contain cell-specific water availability and environmental flow requirements.*"

**❌ WRONG - Presenting Made-Up Data as Real:**
> ~~"In India's Punjab region in 2040:~~
> ~~- Available water: 100 km³~~
> ~~- Environmental flows: 40 km³"~~
>
> *(This implies you've read actual input data when you haven't)*

**What You CAN Verify from Code:**
- ✅ Equation structure (read equations.gms files)
- ✅ Parameter names and units (read declarations.gms)
- ✅ Default scalar values (read input.gms: `s42_reserved_fraction = 0.5`)
- ✅ Configuration options (read input.gms: `s42_env_flow_scenario / 2 /`)
- ✅ Code logic and calculations (read presolve.gms, equations.gms)

**What You CANNOT Verify Without Reading Input Files:**
- ❌ Actual water availability by cell (requires reading `lpj_*.cs2` files)
- ❌ Specific environmental flow requirements (requires reading `lpj_envflow_grper.cs2`)
- ❌ Regional unit costs for irrigation (requires reading `f41_c_irrig.csv`)
- ❌ Crop-specific water requirements (requires reading `lpj_airrig.cs2`)
- ❌ Which cells correspond to geographic regions like "Punjab" (requires reading spatial mapping files)

**Arithmetic Verification:**
- ✅ ALWAYS verify arithmetic in examples
- ✅ If illustrating with 100 km³ available and 50% manufacturing reserve, that's **50 km³** not 30 km³
- ✅ Double-check calculations before presenting them

**When in Doubt:**
- State "This is an illustrative example with made-up numbers"
- Say "Actual values would require reading the input data file X"
- Never imply you have data you haven't actually read

**See magpie_AI_documentation/CRITICAL_ANALYSIS_PRINCIPLES.md for detailed guidance**

---

## 🤖 AI AGENT INSTRUCTIONS

### Complete Documentation System

**For comprehensive AI assistance, reference these documents in order**:

1. **Start Here**: `magpie_AI_documentation/AI_AGENT_BEHAVIOR_GUIDE.md`
   - **Purpose**: Immediate, actionable patterns for any MAgPIE query
   - **Use**: Quick reference for query routing, response patterns, validation checklists
   - **Key sections**: Query routing, response checklist, module-specific patterns, debugging tree

2. **Core Documentation** (Completed - Phase 1-3):
   - Phase 1: `MAGPIE_AI_DOCS_Phase1_Core_Architecture.md` - Model structure, execution flow, 46 modules
   - Phase 2: `MAGPIE_AI_DOCS_Phase2_Module_Dependencies.md` - 115 variables, 173 dependencies, 26 cycles
   - Phase 3: `MAGPIE_AI_DOCS_Phase3_Data_Flow.md` - 172 input files, data pipeline, parameter tracing

3. **Deep Dive Documentation** (In Progress - Phase 4-8):
   - Phase 4: Priority Module Deep Dives
   - Phase 5-8: Patterns, Configuration, Outputs, Synthesis

### Essential AI Response Rules

**ALWAYS DO**:
- ✅ Cite specific file paths with line numbers (`modules/XX_name/realization/file.gms:line`)
- ✅ Use actual variable names (vm_land, pm_carbon_density, not "the land variable")
- ✅ Check Phase 2 dependency matrix before suggesting modifications
- ✅ Warn about high-centrality modules (10, 11, 17, 56) or circular dependencies
- ✅ Offer appropriate detail level: Level 1 (quick), Level 2 (conceptual), Level 3 (implementation), Level 4 (full context)
- ✅ Run response checklist: Accuracy, Dependencies, Completeness, Safety

**NEVER DO**:
- ❌ Describe ecological processes as if they're model code ("forests absorb CO2" → describe equation instead)
- ❌ Assume features exist without checking code ("MAgPIE includes fire dynamics" → actually parameterized only)
- ❌ Present made-up examples as if they're actual input data (always label illustrative examples explicitly)
- ❌ Claim to know input data values without having read the actual input files
- ❌ Suggest modifications without dependency check
- ❌ Ignore conservation law implications (land balance, water balance, carbon balance, food balance)
- ❌ Provide vague answers when specific code references are possible

### Quick Query Routing

```
"How does X work?" → Phase 1 (overview) → Phase 4 (module detail)
"What depends on X?" → Phase 2 (dependency matrix)
"Where is X defined?" → Phase 3 (data flow) or Phase 4 (module code)
"X is broken" → AI_AGENT_BEHAVIOR_GUIDE.md (debugging decision tree)
"How to modify X?" → Phase 4 (current code) + Phase 2 (dependencies) + Phase 5 (template)
"How to set up X scenario?" → Phase 6 (configuration templates)
"What does output X mean?" → Phase 7 (interpretation guide)
```

### Response Validation Checklist

**Before every response, verify**:
- [ ] Cited specific files and line numbers?
- [ ] Used actual variable/parameter names?
- [ ] Checked if feature actually exists in code?
- [ ] Avoided ecological/general knowledge (CODE behavior only)?
- [ ] **If using numerical examples: Clearly labeled as "illustrative" or cited actual input file?**
- [ ] **If using numerical examples: Verified arithmetic is correct?**
- [ ] Checked Phase 2 for dependencies if modification suggested?
- [ ] Listed affected modules?
- [ ] Warned about conservation law implications?
- [ ] Offered next level of detail?

**See AI_AGENT_BEHAVIOR_GUIDE.md for complete patterns, decision trees, and specialized handlers**

---

## ⚠️ Warning Signs - Stop and Verify

**If you write any of these phrases, STOP and verify against code:**

- "MAgPIE accounts for..." (does it really? Check equations.gms)
- "The model considers..." (verify in actual code, not assumptions)
- "Climate change impacts..." (static or dynamic? Check presolve.gms)
- "Biodiversity responds to..." (or does it just track? Check equations)
- "Forests absorb CO2..." (ecological fact ≠ model implementation)
- "Water availability affects..." (direct equation or external input?)
- "The model optimizes..." (check if there's actually a variable being optimized)

**Always ask yourself**: "Where is this in the code? What file and line?"

**Before responding**:
1. Identify the specific module file (e.g., `modules/14_yields/managementcalib_aug19/equations.gms`)
2. Find the line number (e.g., `:45-52`)
3. Quote or describe the actual code
4. Cite it: `equations.gms:45-52`

---

## ✓ Response Quality Checklist

**Before sending ANY response about MAgPIE code:**

- [ ] **Cited file:line** for every factual claim
- [ ] **Used exact variable names** (vm_land, not "land variable")
- [ ] **Verified feature exists** (grep'd for it or read the file)
- [ ] **Described CODE behavior only** (not ecological/economic theory)
- [ ] **Labeled examples** (made-up numbers vs. actual input data)
- [ ] **Checked arithmetic** (if providing calculations)
- [ ] **Listed dependencies** (if suggesting modifications)
- [ ] **Stated limitations** (what code does NOT do)
- [ ] **No vague language** ("the model handles..." → specific equation)

**If you can't check all boxes, your response needs more verification.**
