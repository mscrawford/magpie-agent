# Response Guidelines for MAgPIE Agent

**Purpose**: Detailed guidelines for crafting high-quality responses, managing token efficiency, and ensuring accuracy.

**When to read this**: Before answering complex questions, when optimizing response quality, or when uncertain about best practices.

---

## 📖 COMPLETE EXAMPLE: Answering a MAgPIE Question

**Let's walk through how to efficiently answer: "How does carbon pricing affect forest growth?"**

### Step 1: Route the Query (5 seconds)

Read the Quick Reference table in CLAUDE.md → This involves circular dependencies between carbon and forestry.

**Decision**: Check `cross_module/circular_dependency_resolution.md` first.

### Step 2: Read Targeted Documentation (30 seconds)

Open `cross_module/circular_dependency_resolution.md` and search for "Forest-Carbon".

**What you find** (Section 3.4 - Forest-Carbon Cycle):
- 5-module feedback loop: Modules 56 (GHG policy) → 32 (forestry) → 52 (carbon) → 56
- Carbon pricing (vm_carbon_price) affects afforestation decisions in Module 32
- Growing forests increase carbon stocks (Module 52), which affects future carbon costs
- Resolution: Sequential execution with temporal feedback

### Step 3: Get Module-Specific Details (1-2 minutes)

Now that you know the cycle, check the specific modules:

1. **Read `modules/module_56.md`** → Find carbon pricing implementation
2. **Read `modules/module_32.md`** → Find how price affects afforestation
3. **Read `modules/module_52.md`** → Find carbon stock growth equations

**Key findings**:
- Module 56: `vm_carbon_price(t,i)` derived from GHG policy (equations.gms:15-18)
- Module 32: Afforestation cost includes `vm_carbon_price * s32_carbon_price_factor` (equations.gms:45)
- Module 52: Carbon growth follows Chapman-Richards equation (equations.gms:23-28)

### Step 4: Construct Answer with Citations (30 seconds)

**Your response**:

> "Carbon pricing affects forest growth through a 5-module feedback cycle (documented in circular_dependency_resolution.md Section 3.4):
>
> 1. **Carbon Price Impact on Afforestation** (Module 56 → Module 32):
>    - GHG policy sets `vm_carbon_price(t,i)` (module_56.md, equations.gms:15-18)
>    - This price is factored into afforestation costs via `s32_carbon_price_factor` (module_32.md, equations.gms:45)
>    - Higher carbon prices make afforestation more economically attractive
>
> 2. **Forest Growth and Carbon Sequestration** (Module 32 → Module 52):
>    - New forest area (`vm_land(j,"primforest")` + `vm_land(j,"secdforest")`) grows carbon stocks
>    - Carbon growth follows Chapman-Richards: `pm_carbon_density_ac(t,j,ac,ag_pools)` (module_52.md, equations.gms:23-28)
>
> 3. **Feedback to Carbon Accounting** (Module 52 → Module 56):
>    - Increased forest carbon stocks affect total emissions calculations
>    - This influences future carbon pricing in subsequent time steps
>
> **Resolution Mechanism**: The cycle resolves through temporal feedback - decisions in time step t affect carbon stocks that influence pricing in t+1.
>
> 🟡 Based on: circular_dependency_resolution.md, module_32.md, module_52.md, module_56.md"

### Step 5: Token Efficiency Analysis

**Total tokens used**: ~2,000-3,000 (reading 4 targeted docs)
**Alternative approach** (reading raw GAMS code): ~10,000-15,000 tokens (parsing 5+ modules)
**Time saved**: 5 minutes → 2 minutes

**Key efficiency principle**: The quick reference table directed you to exactly the right starting point, avoiding unnecessary exploration.

---

## ⚡ TOKEN EFFICIENCY GUIDELINES

**Critical Rule**: Read ONLY what you need to answer the question. Don't read "just in case."

### When to STOP Reading (You Have Enough)

✅ **STOP and answer if you have**:
- The equation or mechanism that directly answers the question
- Clear understanding of the implementation from module docs
- Sufficient context to cite sources properly
- Enough detail to answer at the requested level

**Example**: User asks "What equation calculates livestock feed demand?"
- ✅ Read `module_70.md` → Find `q70_feed` equation → STOP and answer
- ❌ Don't also read Module 17, 14, 38 "just in case"

### When to READ MORE (You Need Context)

🔍 **READ MORE if you need to**:
- Understand a circular dependency or cross-module interaction
- Trace where a parameter comes from (check Phase3_Data_Flow.md)
- Assess modification safety (check Phase2_Module_Dependencies.md)
- Clarify how modules connect (check module "Interface Variables" sections)

**Example**: User asks "Can I modify Module 10 without affecting water?"
- ✅ Read `module_10.md` (interface variables) → See vm_land exported
- ✅ Read `Phase2_Module_Dependencies.md` → Check Module 10 dependents
- ✅ Read `modification_safety_guide.md` → Module 10 has 23 dependents including Module 42 (water)
- ✅ STOP and answer: "No, Module 10 affects water through land allocation"

### Progressive Depth Strategy

**Start shallow, go deeper ONLY if needed:**

**Level 1 - Quick Answer (30 seconds, ~500 tokens)**:
- Read module doc's "Overview" section or quick reference table
- Cite equation name and module
- Answer: "Module X calculates Y using equation qXX_name (module_XX.md)"

**Level 2 - Conceptual Answer (1-2 minutes, ~2,000 tokens)**:
- Read module doc's equation section
- Understand mechanism without full detail
- Answer with equation structure: "qXX_name sums A over B subject to constraint C"

**Level 3 - Implementation Answer (2-3 minutes, ~5,000 tokens)**:
- Read module doc's full equation + parameters + interface sections
- Understand all variables and their sources
- Answer with complete details: "Equation uses vm_A (from Module Y), pm_B (input file Z), multiplied by..."

**Level 4 - Full Context Answer (5+ minutes, ~10,000+ tokens)**:
- Read multiple module docs + cross-module docs
- Read raw GAMS code if docs insufficient
- Understand circular dependencies, conservation laws, modification impacts
- Provide comprehensive answer with safety warnings

**Default to Level 2 unless user requests more detail.**

### Quick Reference Table Usage

**The table at the top is your token-saving tool:**

```
"How does module X work?" → module_XX.md (ONE file, ~3,000 tokens)
NOT: Read Phase1 + Phase2 + Phase3 + module_XX.md (FOUR files, ~15,000 tokens)
```

**Before reading ANY documentation, check the table first.** It will direct you to the minimal set of files needed.

### Token Budget Examples

**Simple Query** ("What's Module 70?"):
- ✅ Read: `module_70.md` → 3,000 tokens
- ⏱️ Time: 30 seconds

**Moderate Query** ("How does livestock affect costs?"):
- ✅ Read: `module_70.md` + `module_11.md` → 6,000 tokens
- ⏱️ Time: 2 minutes

**Complex Query** ("Can I safely modify Module 10?"):
- ✅ Read: `module_10.md` + `Phase2_Module_Dependencies.md` + `modification_safety_guide.md` → 10,000 tokens
- ⏱️ Time: 3-4 minutes

**Exploratory Query** ("How does the whole model work?"):
- ⚠️ This requires Phase1_Core_Architecture.md → 10,000+ tokens
- ✅ But suggest: "Would you like an overview, or specific aspect details?" to reduce scope

### Red Flags: You're Reading Too Much

🚩 **STOP if you find yourself**:
- Reading more than 3 files for a simple "how does X work" question
- Reading cross-module docs when question is about single module
- Reading raw GAMS code when module doc already has the answer
- Reading Phase 0 docs when you just need one equation

**Remember**: The docs exist to PREVENT you from reading everything. Trust them.

---

## 🚨 CRITICAL: Examples vs. Actual Data

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

---

## ⚠️ WARNING SIGNS - Stop and Verify

**If you write any of these phrases, STOP and verify against code:**

- "MAgPIE accounts for..." (does it really? Check equations.gms)
- "The model considers..." (verify in actual code, not assumptions)
- "Climate change impacts..." (static or dynamic? Check presolve.gms)
- "Biodiversity responds to..." (or does it just track? Check equations)
- "Forests absorb CO2..." (ecological fact ≠ model implementation)
- "Water availability affects..." (direct equation or external input?)
- "The model optimizes..." (check if there's actually a variable being optimized)
- "X is similar to Y..." (have you verified BOTH or just one?)
- "Other models also..." (verified or assumed?)
- "Standard practice is..." (in MAgPIE specifically or generally?)
- "X compares favorably to..." (based on what verification?)
- **"MAgPIE models X..."** → ⚠️ **CRITICAL CHECK**: Is this CALCULATED or from INPUT DATA?

**For detailed guidance on parameterization vs. mechanistic modeling, see `Query_Patterns_Reference.md`**

**Always ask yourself**: "Where is this in the code? What file and line?"

**Before responding**:
1. Identify the specific module file (e.g., `modules/14_yields/managementcalib_aug19/equations.gms`)
2. Find the line number (e.g., `:45-52`)
3. Quote or describe the actual code
4. Cite it: `equations.gms:45-52`

---

## ✓ RESPONSE QUALITY CHECKLIST

**Before sending ANY response about MAgPIE code:**

- [ ] **🎯 CHECKED AI DOCS FIRST** (magpie-agent/modules/module_XX.md or core_docs/)
- [ ] **Stated documentation source** (🟡 module docs / 🟢 verified in code / 🟠 code only)
- [ ] **Cited file:line** for every factual claim (or reference module doc line numbers)
- [ ] **Used exact variable names** (vm_land, not "land variable")
- [ ] **Verified feature exists** (in module docs or grep'd for it)
- [ ] **Described CODE behavior only** (not ecological/economic theory)
- [ ] **Labeled examples** (made-up numbers vs. actual input data)
- [ ] **Checked arithmetic** (if providing calculations)
- [ ] **Listed dependencies** (if suggesting modifications - use Phase 2 or module docs)
- [ ] **Stated limitations** (what code does NOT do - module docs have comprehensive sections)
- [ ] **No vague language** ("the model handles..." → specific equation with file:line)
- [ ] **If comparing systems: Stated verification status (🟢🟡🟠🔵🔴) for EACH?**
- [ ] **If asymmetric verification: Explicitly disclosed confidence difference?**
- [ ] **If unverified claim: Offered to verify or stated limitation?**
- [ ] **If using numerical examples: Clearly labeled as "illustrative" or cited actual input file?**
- [ ] **If using numerical examples: Verified arithmetic is correct?**
- [ ] Checked Phase 2 for dependencies if modification suggested?
- [ ] Listed affected modules?
- [ ] Warned about conservation law implications?
- [ ] Offered next level of detail?

**If you can't check all boxes, your response needs more verification.**

**Remember: The AI documentation exists to make your job easier AND more accurate. Use it!**

### Encouraging User Feedback

**Occasionally remind users they can submit feedback** (use sparingly, not every response):

**When to mention**:
- ✅ After explaining a complex module or mechanism
- ✅ When user asks detailed technical questions (shows engagement)
- ✅ If you notice a gap or potential error in documentation
- ✅ When user corrects you or provides additional context
- ❌ Not on simple factual queries
- ❌ Not more than once every 3-4 responses

**How to mention** (pick one style, keep it brief):
```
📝 Spot an error or have insights to share? Use /feedback to help improve the documentation!
```
Or:
```
💡 Your question revealed interesting details - consider using /feedback to document this for others!
```

**Goal**: Encourage quality feedback without being annoying. Users should feel invited, not pestered.

---

## 📐 DOCUMENT ROLE HIERARCHY

**MAgPIE has 82+ documentation files. To avoid confusion and inconsistency, follow this hierarchy:**

### **Two Contexts: MAgPIE Questions vs. Documentation Project**

#### **Context 1: Answering MAgPIE Questions** (most common)

**Document precedence** (if information conflicts):
1. **Code Truth**: `../modules/XX_name/realization/*.gms` (actual GAMS code)
2. **Module Docs**: `modules/module_XX.md` (SINGLE SOURCE OF TRUTH - verified against code)
3. **Cross-Module**: `cross_module/*.md` (system-level analysis, derived from modules)
4. **Architecture**: `core_docs/Phase*.md` (overview and reference)
5. **Module Notes**: `modules/module_XX_notes.md` (user experience, warnings - may lag behind code changes)
6. **Workflow**: `CLAUDE.md` (routing logic, not facts about modules)

**Read in this order:**
```
User asks MAgPIE question
  → CLAUDE.md (you're reading it - tells you WHERE to look)
  → modules/module_XX.md (FACTS about the module)
  → module_XX_notes.md (WARNINGS/LESSONS if how-to/troubleshooting)
  → cross_module/*.md (SYSTEM-LEVEL if safety/dependencies)
  → core_docs/Phase*.md (ARCHITECTURE if structural question)
  → reference/GAMS_Phase*.md (GAMS CODE if writing/debugging code)
```

**DO NOT read** (noise for MAgPIE questions):
- ❌ README.md (documentation project overview - only read if working on doc project)
- ❌ project/ directory (project management files - only read if working on doc project)

#### **Context 2: Working on Documentation Project** (rare)

**Read in this order:**
```
New documentation project session
  → README.md (orientation and session protocol)
  → project/CURRENT_STATE.json (SINGLE SOURCE OF TRUTH - status, plans, history)
  → Ask user: "What should I work on?"
```

**Update ONLY:**
- ✅ project/CURRENT_STATE.json (project status)
- ❌ NOT README.md (STATIC reference document)
- ❌ NOT modules/README.md (STATIC reference)

### **Handling Conflicts**

**If you find contradictory information:**

1. **Check precedence hierarchy** (above)
2. **Trust higher-precedence source** (code > module docs > cross-module > notes)
3. **Create feedback** if notes contradict main docs:
   ```bash
   # Use /feedback command to report inconsistency
   ```

**Example conflict resolution:**
```
module_52_notes.md says: "Chapman-Richards has 3 parameters"
module_52.md says: "Chapman-Richards: C(age) = A × (1-exp(-k×age))^m (3 parameters)"

Action: Trust module_52.md (higher precedence)
Reason: Notes may be outdated, main doc is verified against code
```

### **Special Cases**

**Module Dependencies:**
- **Authoritative source**: `Phase2_Module_Dependencies.md` (dependency graph)
- **Quick reference**: `modification_safety_guide.md` (top 4 modules)
- **Module-specific**: `module_XX.md` (lists dependents for that module)
- **User warnings**: `module_XX_notes.md` (practical lessons about dependencies)

**If counts differ** → Trust Phase2_Module_Dependencies.md, create feedback

**Conservation Laws:**
- **Authoritative source**: `cross_module/*_balance_conservation.md`
- **Quick reference**: `module_XX.md` (mentions relevant equations)

**If formulas differ** → Trust cross_module file (comprehensive analysis), verify against code

**GAMS Syntax:**
- **Authoritative source**: Official GAMS documentation (gams.com)
- **MAgPIE patterns**: `reference/GAMS_Phase5_MAgPIE_Patterns.md`
- **Quick reference**: `Phase1_Core_Architecture.md` (naming conventions overview)

**If patterns differ** → Trust GAMS_Phase5 for MAgPIE-specific patterns

### **Quality Assurance**

**Before citing information, verify:**
- [ ] Is this from the highest-precedence source?
- [ ] If multiple sources, do they agree?
- [ ] If conflict, did I use precedence hierarchy?
- [ ] If notes contradict main docs, did I trust main docs?
- [ ] If unsure, can I verify against code?

**When in doubt:**
- State: "I found conflicting information in [source A] and [source B]"
- Apply precedence hierarchy
- Offer to verify against actual GAMS code
- Create feedback for the inconsistency
