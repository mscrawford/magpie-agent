# Global Lessons for Agent Behavior

**📌 System-wide feedback affecting CLAUDE.md and agent workflow**

Last updated: 2025-10-22

This file contains feedback that affects how the agent operates across all modules:
- Query routing improvements
- Token efficiency enhancements
- Workflow modifications
- Response pattern updates

---

## Agent Behavior Improvements

### [AB001] Always Check Module Notes Files When They Exist
**Priority**: High | **Added**: 2025-10-22 (example)

**Current behavior**: Agent reads module_XX.md but doesn't always check for module_XX_notes.md.

**Improved behavior**: When reading any module documentation, ALSO check if module_XX_notes.md exists and read it when appropriate.

**When to read notes files**:
- User asks "how to" or "can I modify" (practical guidance needed)
- User asks about warnings or common mistakes
- Main doc doesn't fully answer the query
- Query involves troubleshooting or debugging

**When to skip notes files** (token efficiency):
- Simple factual queries ("what equation", "which module")
- Just need equation formulas
- User explicitly asks for "code truth only"

**Implementation in CLAUDE.md**:
```markdown
Step 1: Check AI Documentation
  1. Read module_XX.md (main docs)
  2. Check for module_XX_notes.md (user feedback)  ← ADD THIS
     - Read if query needs practical context
     - Skip for simple factual queries
```

**Token impact**: Adds ~1,500 tokens when needed, but saves user time by providing warnings/lessons upfront.

---

### [AB002] Prioritize Warnings Over Lessons When Safety Is a Concern
**Priority**: High | **Added**: 2025-10-22 (example)

**Issue**: When module_XX_notes.md contains multiple sections (warnings, lessons, examples), agent should triage based on query type.

**Rule**: If query involves modification or troubleshooting, read "Warnings" section FIRST.

**Why**: Prevent users from making high-risk mistakes before showing them how-to examples.

**Example**:
```
User: "How do I modify Module 10?"

Agent workflow:
1. Read module_10.md (understand current behavior)
2. Read module_10_notes.md "Warnings" section → Mention high-centrality risk
3. Then provide modification approach
4. Offer lessons/examples if helpful
```

**Implementation**: Update response pattern to include warnings prominently when relevant.

---

### [AB003] Always Mention High-Centrality Warning for Modules 10, 11, 17, 56
**Priority**: High | **Added**: 2025-10-22 (example)

**Context**: Modules 10 (land), 11 (costs), 17 (production), 56 (GHG policy) have 20+ dependents each.

**Rule**: When user asks about modifying any of these modules, ALWAYS mention:
1. This is a high-centrality module
2. Number of dependent modules
3. Pointer to modification_safety_guide.md

**Example phrasing**:
```
⚠️ Important: Module 10 is a high-centrality module with 23 dependents.
Changes here affect water, carbon, biodiversity, costs, and more.
See modification_safety_guide.md for safety protocols before proceeding.
```

**Where to implement**: Add to "Response Validation Checklist" in CLAUDE.md.

---

## Token Efficiency Lessons

### [TE001] Don't Read Full Notes File - Skim Sections First
**Priority**: Medium | **Added**: 2025-10-22 (example)

**Lesson**: Notes files can be long (1,000+ lines). Don't read the entire file for every query.

**Strategy**:
1. Read the section headers to see what's available
2. Identify relevant sections based on query type
3. Read ONLY those sections

**Example**:
```
User: "What common mistakes should I avoid with Module 70?"

Agent:
1. Read module_70_notes.md section headers
2. See "## ⚠️ Warnings - Don't Do This"
3. Read ONLY that section (skip lessons, examples, etc.)
4. Token savings: ~1,200 tokens
```

**Implementation**: Update CLAUDE.md token efficiency guidelines to include selective notes file reading.

---

## Query Routing Enhancements

### [QR001] Auto-Check Conservation Laws for Cross-Module Questions
**Priority**: Medium | **Added**: 2025-10-22 (example)

**Issue**: When user asks "How does X affect Y?" (cross-module), agent doesn't always check conservation law docs.

**Improved routing**:
```
"How does [X] affect [Y]?" (across modules)
  → Read module_XX.md for X
  → Read module_YY.md for Y
  → Check cross_module/ docs for conservation laws  ← ADD THIS
  → Especially if X or Y involve: land (10), water (42,43), carbon (52), food (15,21)
```

**Example**:
```
User: "How does cropland expansion affect water availability?"

Agent should automatically check:
- module_29.md (cropland)
- module_43.md (water availability)
- water_balance_conservation.md ← Don't miss this!
```

**Implementation**: Update "Quick Query Routing" in CLAUDE.md.

---

### [QR002] Link Module Numbers to Topics in Query Routing
**Priority**: Low | **Added**: 2025-10-22 (example)

**Observation**: Users often ask about topics without knowing module numbers ("How does livestock work?").

**Current solution**: Quick Module Finder in CLAUDE.md works well.

**Enhancement**: When user asks about a topic, agent should explicitly mention the module number in response.

**Example**:
```
User: "How does livestock feed demand work?"

Agent: "Livestock feed demand is calculated in Module 70 (Livestock)..."
       [Then provide details from module_70.md]
```

**Why**: Helps users learn the module structure, makes future queries easier.

---

## Workflow Modifications

### [WF001] Response Pattern Should Include Warnings Section
**Priority**: High | **Added**: 2025-10-22 (example)

**Current pattern**:
```
[Answer from module docs]

📚 Sources: module_XX.md
```

**Improved pattern**:
```
[Answer from module docs]

⚠️ Important Warnings (from user feedback):
[If relevant warnings exist in module_XX_notes.md]

💡 Practical Lessons:
[If applicable to query type]

📚 Sources:
- 🟡 module_XX.md (main documentation)
- 🟢 module_XX_notes.md (user feedback)
```

**When to include warnings/lessons**: Use judgment based on query type and relevance.

---

## Response Pattern Updates

### [RP001] Always Cite Notes File When Used
**Priority**: Medium | **Added**: 2025-10-22 (example)

**Rule**: If information comes from module_XX_notes.md, cite it explicitly.

**Format**:
```
See: module_70_notes.md [W001] (Warning about feed baskets)
See: module_10_notes.md [L002] (Lesson on spatial resolution)
```

**Why**:
- Shows sources clearly
- Helps users navigate to detailed info
- Distinguishes "code truth" from "user experience"

---

## Integration Suggestions

### [IS001] Periodic Review of Feedback Stats
**Priority**: Low | **Added**: 2025-10-22 (example)

**Suggestion**: Monthly review of which feedback items are most cited by agent.

**Metrics to track**:
- Which warnings are mentioned most often
- Which lessons are most relevant
- Which modules have most feedback items
- Token impact of notes files

**Goal**: Identify high-value feedback that should be promoted to main docs.

**Example**: If [W001] feed basket warning is cited 50+ times, consider adding warning to module_70.md main docs.

---

**To add global feedback:** Run `./scripts/submit_feedback.sh` and select [5] Global feedback.
