# AI Instruction Refinement Plan
## Leveraging MAgPIE Knowledge Base for Intelligent Agent Assistance

**Date**: October 11, 2025
**Status**: Integrated into Phases 4-8

---

## Executive Summary

This document outlines a systematic approach to refining AI agent instructions throughout the remaining documentation phases. The goal is to create a self-improving system where each documentation phase not only adds knowledge but also teaches the AI agent **how to use that knowledge cleverly**.

### Key Principles:
1. **Context-aware responses**: AI adapts based on question type and user expertise
2. **Efficient navigation**: AI quickly routes to relevant documentation sections
3. **Code-first answers**: Provide specific file/line references, not general knowledge
4. **Pattern recognition**: Identify common tasks and provide templated solutions
5. **Validation-driven**: AI checks its own responses against known patterns

---

## Cross-Phase AI Instruction Components

### Component 1: Intelligent Query Routing

**Objective**: AI instantly recognizes query type and routes to appropriate documentation

**Implementation across phases**:

| Query Type | Documentation Source | AI Routing Logic |
|-----------|---------------------|------------------|
| "How does X work?" | Phase 1 (Architecture) | Check if X is module → module overview, else → execution flow |
| "X depends on what?" | Phase 2 (Dependencies) | Use dependency matrix → list upstream modules |
| "Where is X defined?" | Phase 3 (Data Flow) | Search parameter → trace f_→i_→p_ path |
| "How to modify X?" | Phase 4 (Module Deep Dives) | Find module tier → provide appropriate detail level |
| "X is broken, why?" | Phase 5 (Debugging) | Match error pattern → diagnostic flowchart |
| "How to set up X scenario?" | Phase 6 (Configuration) | Config template library → parameter guide |
| "What does output X mean?" | Phase 7 (Outputs) | Output catalog → interpretation guide |

**AI Instruction Example**:
```
When user asks about module dependencies:
1. Check Phase 2 dependency matrix
2. If circular dependency involved → warn about testing entire cycle
3. If high-centrality module → warn about broader impact
4. Provide specific vm_/pm_/im_ variables that connect modules
5. Reference specific file locations for integration points
```

---

### Component 2: Progressive Disclosure

**Objective**: AI provides appropriate detail level based on question specificity

**Tiered Response Strategy**:

**Level 1: Quick Answer** (for broad questions)
- One-sentence model behavior
- Reference to detailed doc section
- Example: "MAgPIE optimizes land use via 46 modules. See Phase 1 for architecture."

**Level 2: Conceptual Explanation** (for "how" questions)
- 2-3 paragraphs on mechanism
- Key equations or variables involved
- Module interaction diagram
- Example: "Forest harvest in Module 35 uses vm_land bounds..."

**Level 3: Implementation Details** (for "code" questions)
- Specific file paths and line numbers
- Complete code snippets
- Parameter values and units
- Example: "modules/35_natveg/pot_forest_may24/presolve.gms:132-160 sets harvest constraints..."

**Level 4: Full Context** (for debugging or modification)
- Dependency chain
- All related variables
- Testing requirements
- Validation checklist

**AI Instruction Example**:
```
Progressive response logic:
IF question contains "how", "what", "why" → Level 2 (conceptual)
IF question contains "where", "which file", "line" → Level 3 (implementation)
IF question contains "modify", "change", "add" → Level 4 (full context)
IF question is vague → Level 1 (quick answer) + clarifying questions
```

---

### Component 3: Pattern-Based Code Generation

**Objective**: AI recognizes common tasks and applies proven templates

**Pattern Library** (built across phases):

#### Pattern Category 1: Module Analysis (Phase 4)
```
Task: "Explain how module X works"
Template:
1. Purpose: [from realization.gms header]
2. Key equations: [list q_ equations]
3. Key variables: [list vm_ variables]
4. Dependencies: [from Phase 2 matrix]
5. Important switches: [list s_ scalars]
6. Typical modifications: [common use cases]
```

#### Pattern Category 2: Debugging (Phase 5)
```
Task: "Model is infeasible at timestep T"
Template:
1. Check: modelstat value (display sequence)
2. Identify: binding constraints (.m > 0)
3. Diagnose: which constraint type (land balance? water? food?)
4. Isolate: reduce timesteps to T-1, T-2...
5. Fix: apply appropriate relaxation
6. Validate: check conservation laws
```

#### Pattern Category 3: Configuration (Phase 6)
```
Task: "Set up climate policy scenario"
Template:
1. Base config: cfg <- loadConfig("default.cfg")
2. Set policy: cfg$gms$c56_pollutant_prices <- "coupling"
3. Set carbon price: cfg$gms$c56_price_schedule <- "...csv"
4. Adjust forest policy: cfg$gms$s35_natveg_harvest_shr <- 0.1
5. Set biodiversity: cfg$gms$s44_bii_policy <- "2030target"
6. Run: start_run(cfg=cfg, codeCheck=FALSE)
```

#### Pattern Category 4: Output Analysis (Phase 7)
```
Task: "Analyze forest cover changes"
Template:
1. Read: gdx <- readGDX("fulldata.gdx", "ov_land")
2. Filter: forest <- gdx[,,c("primforest","secdforest","forestry")]
3. Aggregate: forest_reg <- dimSums(forest, dim="j")
4. Plot: plotMap(forest, year=2050)
5. Validate: Check against FAO data
6. Report: Convert to IAMC format
```

---

### Component 4: Context-Aware Validation

**Objective**: AI self-validates responses using known patterns

**Validation Checklist** (AI internal):

✓ **Response Accuracy Check**:
- [ ] Did I cite specific file paths?
- [ ] Did I provide line numbers for code references?
- [ ] Did I check Phase 2 for dependencies before suggesting modification?
- [ ] Did I warn about high-centrality modules if applicable?
- [ ] Did I reference actual variable names (vm_, pm_, im_)?

✓ **Code Safety Check** (for modification suggestions):
- [ ] Will this break conservation laws? (land, water, mass balance)
- [ ] Did I identify all dependent modules?
- [ ] Did I suggest appropriate testing scope?
- [ ] Did I recommend scaling if new variable?
- [ ] Did I warn about circular dependencies if applicable?

✓ **Completeness Check**:
- [ ] Did I address all parts of the question?
- [ ] Did I provide next steps or follow-up actions?
- [ ] Did I reference additional documentation if needed?
- [ ] Did I offer to dive deeper if answer was high-level?

**AI Instruction Example**:
```
Before providing final response:
1. Run internal validation checklist
2. If any check fails, revise response
3. If uncertain about code location, explicitly state: "I believe X is in module Y, but let me verify..."
4. If suggesting code changes, ALWAYS list affected modules from Phase 2 dependency matrix
```

---

## Phase-Specific AI Instruction Refinements

### Phase 4: Module Deep Dives

**New AI Capabilities**:

1. **Module Tier Recognition**
   ```
   IF user asks about module in Tier 1 → provide full detail
   IF user asks about module in Tier 4 → provide summary + "see code for details"
   ```

2. **Subsystem Navigation**
   ```
   Degradation subsystem = modules 58, 59, 35, 14
   Forestry subsystem = modules 32, 73, 35, 28
   IF question touches multiple subsystem modules → provide integrated explanation
   ```

3. **Equation Explanation**
   ```
   When explaining equation:
   1. Purpose: What does this equation calculate?
   2. Components: Break down RHS terms
   3. Variables: List all vm_, pm_ with descriptions
   4. Constraints: =e=, =g=, =l= and what they mean
   5. Conditionals: Any $ conditions that filter
   ```

4. **Module Modification Guidance**
   ```
   Standard workflow for "How to modify module X":
   1. Current behavior: [from code analysis]
   2. Modification target: [based on user request]
   3. Files to change: [list with line numbers]
   4. Dependent modules to test: [from Phase 2]
   5. Validation steps: [conservation checks]
   ```

**Deliverables** (in Phase 4 documentation):
- Module-specific query patterns document
- Decision tree for module selection
- Flowcharts for module interaction
- Specialized workflows for degradation and forestry

---

### Phase 5: Common Patterns & Debugging

**New AI Capabilities**:

1. **Error Pattern Matching**
   ```
   Error patterns library:
   - "modelstat = 4" → infeasibility diagnostic tree
   - "modelstat = 3" → unbounded variable search
   - "Domain violation" → set membership check
   - "Div by zero" → data integrity check
   - "Memory exceeded" → problem size reduction

   IF user reports error → match pattern → apply diagnostic workflow
   ```

2. **Automated Debugging Workflow**
   ```
   Standard debugging sequence:
   1. Identify error type (modelstat, GAMS error, numerical issue)
   2. Isolate problem (timestep, region, module)
   3. Display relevant variables (use display, execute_unload)
   4. Check data integrity (NaN, Inf, reasonable ranges)
   5. Test fix with reduced problem
   6. Validate solution (conservation, shadow prices)
   ```

3. **Code Pattern Recognition**
   ```
   Common patterns library:
   - Variable bounds: .fx, .lo, .up usage
   - Conditional equations: $ operator patterns
   - Scaling: typical scale values by variable type
   - Time conditions: m_year(t), sameas(t,t_past)
   - Region conditions: cell(i,j), sameas(i,"EUR")
   ```

4. **Modification Templates**
   ```
   Template library for common tasks:
   - Add new variable (5-step template)
   - Add new equation (6-step template)
   - Add new module realization (file structure + registration)
   - Modify existing constraint (preserve original as comment)
   - Add new scenario (config modification template)
   ```

**Deliverables** (in Phase 5 documentation):
- Diagnostic decision trees for each error type
- Automated debugging workflow scripts
- Pattern-matching templates for modifications
- Troubleshooting flowcharts with code references

---

### Phase 6: Configuration & Practical Usage

**New AI Capabilities**:

1. **Configuration Parameter Intelligence**
   ```
   IF user asks to set parameter X:
   1. Look up X in config catalog
   2. Provide: Valid values, default, units, impact
   3. Warn: Any dependencies or conflicts
   4. Suggest: Related parameters often changed together
   ```

2. **Scenario Setup Guidance**
   ```
   Scenario archetypes:
   - Climate policy → c56_*, s56_*, c15_food (diet response)
   - Biodiversity → s44_*, s35_natveg_harvest, protected areas
   - Sustainable intensification → yields, tc, nr_soil_budget
   - Afforestation → c32_*, c56_ (carbon pricing)

   IF user describes scenario goal → map to archetype → provide full config
   ```

3. **Parameter Validation**
   ```
   Validation rules:
   - Prices: must be non-negative, reasonable magnitude (<1000 $/ton typical)
   - Shares: must be in [0,1] range
   - Years: must be within model time range
   - Regions: must match i/j sets

   IF user provides config → validate → warn about issues
   ```

4. **Scenario Comparison Framework**
   ```
   Standard comparison workflow:
   1. Define baseline (SSP2, no policy typical)
   2. Define scenario (list changed parameters)
   3. Key outputs to compare (land use, emissions, costs, production)
   4. Validation checks (mass balance, historical calibration)
   5. Interpretation guidance (expected directions, magnitudes)
   ```

**Deliverables** (in Phase 6 documentation):
- Scenario setup templates by goal type
- Configuration validation workflows
- Parameter suggestion system (based on goal)
- Scenario comparison analysis framework

---

### Phase 7: Output System & Reporting

**New AI Capabilities**:

1. **Output Variable Interpretation**
   ```
   Output catalog with metadata:
   - Variable name (ov_*, om_*, o_*)
   - Units (million ha, Mt C, USD MER)
   - Typical range (for validation)
   - Related variables (for cross-checks)
   - Common analysis tasks

   IF user asks about output X → provide full interpretation guide
   ```

2. **Result Validation Workflows**
   ```
   Standard validation checks:
   1. Mass balance: sum(land) = total_available
   2. Water balance: use = demand <= supply
   3. Food balance: production + trade >= demand
   4. Carbon balance: emissions = stock_loss + combustion
   5. Historical calibration: 2015 results match FAO

   IF user shows results → run validation checklist → flag issues
   ```

3. **Visualization Recommendations**
   ```
   Variable type → plot type mapping:
   - Land use (area) → Stacked area chart, map
   - Emissions (flow) → Line chart, comparison bars
   - Prices (marginal) → Line chart with scenarios
   - Spatial (j-level) → Map, regional aggregation
   - Temporal (t-level) → Time series, trend lines

   IF user has data type X → suggest appropriate visualizations
   ```

4. **Report Generation Workflows**
   ```
   Standard reports:
   - Land use report: magpie4::reportLandUse()
   - Emissions report: magpie4::reportEmissions()
   - IAMC format: magpie4::getReport() → IAMC conventions
   - Validation: magpie4::validateScenario()

   IF user needs report type X → provide magpie4 workflow
   ```

**Deliverables** (in Phase 7 documentation):
- Output interpretation guides by variable
- Result validation checklists
- Result analysis decision trees
- Visualization recommendation system

---

### Phase 8: Final AI Knowledge Synthesis

**Master AI Instruction System**:

This phase consolidates all previous refinements into a unified, intelligent assistance system.

#### 1. **Master Decision Tree**

```
User Query → Classification → Route to Appropriate System

Query Types:
├─ ARCHITECTURE ("How does MAgPIE work?")
│  └─ Phase 1 → execution flow, module overview
├─ DEPENDENCY ("What does X depend on?")
│  └─ Phase 2 → dependency matrix, circular deps
├─ DATA ("Where is X defined?")
│  └─ Phase 3 → parameter tracing, data sources
├─ MODULE ("How does module X work?")
│  └─ Phase 4 → tiered documentation, equations
├─ DEBUG ("X is broken")
│  └─ Phase 5 → error pattern matching, workflow
├─ CONFIG ("How to set up X?")
│  └─ Phase 6 → scenario templates, validation
├─ OUTPUT ("What does X mean?")
│  └─ Phase 7 → interpretation, visualization
└─ COMPLEX (touches multiple categories)
   └─ Intelligent routing → combine multiple phases
```

#### 2. **Comprehensive Prompt Library**

**Positive Examples** (what to do):
- ✅ "Module 35 calculates forest dynamics in `modules/35_natveg/pot_forest_may24/presolve.gms:12-33`..."
- ✅ "This depends on Module 10 (land balance) and Module 52 (carbon). See Phase 2 dependency matrix."
- ✅ "Before modifying this, test modules 11, 17, 56 which depend on it (high centrality)."

**Negative Examples** (what NOT to do):
- ❌ "MAgPIE has forest dynamics." (too vague, no file reference)
- ❌ "Forests sequester carbon through photosynthesis." (ecological reality, not model code)
- ❌ "You could add fire dynamics here." (suggestion without checking user wants it)

**Anti-Patterns** to Avoid:
- ❌ Describing what SHOULD be in the model (vs what IS)
- ❌ Providing general knowledge instead of code specifics
- ❌ Suggesting modifications without dependency check
- ❌ Missing conservation law implications
- ❌ Forgetting to reference actual variable names

#### 3. **Intelligent Multi-Module Routing**

**Complex Query Handler**:
```
IF query touches:
- Multiple modules → Phase 2 (show interactions) + Phase 4 (detailed behavior)
- Modification + testing → Phase 4 (implementation) + Phase 5 (validation)
- Scenario + analysis → Phase 6 (setup) + Phase 7 (output interpretation)
- New feature + literature → Research docs + Phase 4 (integration points)
```

**Example Complex Query: "How to add edge effects to forest carbon accounting?"**

AI Response Structure:
1. **Understand Current** (Phase 4): Module 35 carbon density calculation (line X)
2. **Identify Dependencies** (Phase 2): Affects Module 52 (carbon), Module 56 (emissions)
3. **Locate Data** (Phase 3): Where to add spatial fragmentation parameters
4. **Implementation Pattern** (Phase 5): Template for adding distance-based factor
5. **Testing Strategy** (Phase 5): Which modules to validate
6. **Research Context** (Research docs): Edge effects quantification from literature
7. **Expected Impact** (Phase 7): How output variables will change

#### 4. **Adaptive Context Management**

**Long Conversation Handling**:
- Track what has been discussed (modules, variables, files)
- Reference previous answers: "As we discussed earlier about Module 35..."
- Maintain conversation coherence across multiple sub-questions
- Suggest related topics: "Would you also like to know about Module 32 (forestry) interaction?"

**Context Window Optimization**:
- Prioritize recent phase documentation in context
- Keep Phase 2 (dependencies) always accessible
- Dynamically load Phase 4 (module details) as needed
- Cache commonly referenced code snippets

#### 5. **AI-Generated Code Validation System**

**Before Suggesting Code**:
1. ✓ Check: Does this module exist? (Phase 1)
2. ✓ Check: Dependencies affected? (Phase 2)
3. ✓ Check: Data sources available? (Phase 3)
4. ✓ Check: Equation structure correct? (Phase 4)
5. ✓ Check: Scaling appropriate? (Phase 5)
6. ✓ Check: Config changes needed? (Phase 6)
7. ✓ Check: Output interpretation clear? (Phase 7)

**Code Suggestion Template**:
```
Here's how to implement X:

1. LOCATION: modules/YY_name/realization/file.gms:line
2. CURRENT CODE: [show existing]
3. PROPOSED CHANGE: [show modification]
4. DEPENDENCIES: Modules A, B, C affected (see Phase 2)
5. TESTING: Run with reduced timesteps, check [list variables]
6. VALIDATION: Ensure [list conservation laws] still hold
7. EXPECTED BEHAVIOR: [describe what should change in outputs]

Would you like me to:
- Explain the rationale?
- Show the dependency chain?
- Provide a complete test script?
```

#### 6. **Meta-Learning & Continuous Improvement**

**Feedback Integration**:
- Track which answers were helpful (user follow-up questions indicate confusion)
- Identify documentation gaps (if AI frequently says "let me check...")
- Update instruction patterns based on recurring question types
- Refine decision trees based on actual usage

**Quality Metrics**:
- Response accuracy: Did AI cite correct files/lines?
- Response completeness: Did AI address all sub-questions?
- Response efficiency: Was it appropriately concise/detailed?
- Code safety: Did AI check dependencies and conservation laws?

**Deliverables** (in Phase 8 documentation):
- Master decision tree diagram
- Comprehensive prompt library (with examples and anti-patterns)
- Intelligent routing system documentation
- Adaptive context management guide
- Code validation checklist
- Meta-learning framework

---

## Implementation Strategy

### Per-Phase Deliverables

Each phase (4-8) will produce:
1. **Documentation**: Core content (module details, patterns, etc.)
2. **AI Instructions**: How AI should use this documentation
3. **Decision Trees**: Visual guides for AI routing
4. **Examples**: Positive and negative example responses
5. **Validation**: Checklist for AI self-validation

### Integration Points

**AGENT.md Enhancement**:
Periodically update `AGENT.md` with:
- New decision trees
- Updated query routing logic
- Refined prompt patterns
- Recent examples

**Testing AI Instructions**:
After each phase:
1. Provide test queries to AI
2. Evaluate responses against examples
3. Refine instructions based on results
4. Document lessons learned

### Success Criteria

**Phase 4-8 Complete When**:
- [ ] AI correctly routes 90%+ of queries to appropriate documentation
- [ ] AI provides file/line references in 100% of code questions
- [ ] AI checks dependencies before suggesting modifications
- [ ] AI validates conservation laws in modification suggestions
- [ ] AI adapts detail level to question specificity
- [ ] AI self-validates responses using checklists

---

## Example: Before & After AI Instructions

### BEFORE (Current State):
**User**: "How does forest harvest work?"

**AI Response**:
"MAgPIE models forest harvest through sustainable management practices. Forests store carbon and provide timber. Harvesting is constrained by environmental policies."

**Problems**:
- ❌ No code reference
- ❌ Ecological description, not model behavior
- ❌ Vague, not actionable

### AFTER (With Refined Instructions):

**User**: "How does forest harvest work?"

**AI Response** (Level 2 - Conceptual):
"Forest harvest in MAgPIE (Module 35 - natveg):

**Implementation** (`modules/35_natveg/pot_forest_may24/presolve.gms:132-160`):
- Maximum harvest: `s35_natveg_harvest_shr` × forest area (typically 10-30%)
- Harvested area must be ≤ forest reduction
- Primary forest: Higher cost ($3,690/ha) → preferred last
- Secondary forest: Lower cost ($2,460/ha) → preferred first

**Key variables**:
- `v35_hvarea_secdforest(j,ac)` - secondary forest harvest area
- `v35_hvarea_primforest(j)` - primary forest harvest area
- `vm_prod_natveg(j,land,kforestry)` - timber production

**Constraints**:
- Harvest ≤ reduction (equations q35_hvarea_secdforest, q35_hvarea_primforest)
- Youngest age classes (ac_est) cannot be harvested

**Dependencies** (Phase 2):
- Provides timber to Module 73 (timber)
- Carbon emissions calculated in Module 52 (carbon)
- Costs aggregated in Module 11 (costs)

Would you like:
- Specific equation details? (Level 3)
- How to modify harvest constraints? (Level 4)
- How this integrates with Module 32 (forestry plantations)?"

**Improvements**:
- ✅ Specific file and line references
- ✅ Model behavior (not ecology)
- ✅ Variable names with actual prefixes
- ✅ Dependencies identified
- ✅ Offers appropriate next levels of detail

---

## Maintenance & Evolution

### Regular Updates:
- After each phase completion: Update routing logic
- After user feedback: Refine response patterns
- After code changes: Update file references
- After research additions: Integrate new knowledge

### Version Control:
- Track instruction refinements in git
- Document reasoning for major changes
- Maintain backward compatibility
- Test against previous example queries

### Quality Assurance:
- Weekly: Review AI responses for accuracy
- Monthly: Update validation checklists
- Quarterly: Comprehensive instruction review
- Annually: Major refinement based on usage patterns

---

## Conclusion

This AI Instruction Refinement Plan transforms the MAgPIE documentation project from a static knowledge base into a **dynamic, self-improving AI assistance system**. By carefully designing how the AI uses the documentation at each phase, we create an agent that:

1. **Understands context** and adapts responses appropriately
2. **Navigates efficiently** through complex, interconnected documentation
3. **Provides actionable answers** with specific code references
4. **Validates itself** against known patterns and safety checks
5. **Improves continuously** through feedback and usage analysis

The result: An AI assistant that truly **understands** MAgPIE, not just parses text about it.

---

**Next Actions**:
1. Begin Phase 4 with AI instruction refinement component
2. Create first decision trees for module selection
3. Test routing logic with example queries
4. Iterate based on results

**Status**: Ready to implement in Phase 4 (Priority Module Deep Dives)
