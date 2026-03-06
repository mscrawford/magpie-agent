# Guide Command

**Purpose**: Show capabilities of the MAgPIE Agent

**When user says**: "/guide", "run command: guide", "show guide", "what can you do?", "help", etc.

**How to present**: Show the **Quick Start** section first. Then ask: "Want to see the full guide, or is this enough to get started?" Only show the Full Reference if they ask for it.

---

## 🚀 Quick Start

**I'm your AI assistant for MAgPIE**, with ~95,000 words of curated documentation about all 46 modules. Here's what you need to know:

### Just ask me anything
```
"How does livestock work?"           → I check module docs, cite equations & line numbers
"Can I safely modify Module 10?"     → I check dependencies, warn about conservation laws
"My model is infeasible"             → I load a debugging helper and walk you through it
"What does this GAMS code mean?"     → I explain using MAgPIE-specific GAMS references
"Where does this data come from?"    → I trace it through the data pipeline
```

### What happens behind the scenes
I'm not just a chatbot — I have structured knowledge and active behaviors:

- 🔍 **I check docs first** — I read curated AI documentation before touching raw GAMS code. Faster and more accurate.
- 📋 **I auto-load helpers** — For common tasks (debugging, scenario setup, code modification), I silently load specialized step-by-step guides.
- ⚠️ **I check warnings** — Each module has a notes file with known pitfalls. I read these before answering.
- 📊 **I know your environment** — I check your MAgPIE version, branch, and whether docs are current at session start.
- 🧠 **I learn from you** — When you correct me or share insights, I record them so future sessions benefit. You'll see a summary at session end.

### Commands
Type these to access specific features:

| Command | What it does |
|---------|-------------|
| `/guide` | This guide |
| `/sync` | Update docs after MAgPIE code changes |
| `/update` | Pull latest agent documentation |
| `/feedback` | Submit feedback to improve the agent |

### Tips for best results
1. **Be specific** — "How does Module 70 calculate feed demand?" beats "tell me about livestock"
2. **Mention your goal** — "I want to modify X" triggers safety checks automatically
3. **Correct me** — If I'm wrong, say so. I'll record the correction for future sessions.

---

*Want the full reference guide? Just say "show full guide" for detailed documentation of all capabilities, scripts, response standards, and maintainer commands.*

---

## 📖 Full Reference Guide

*The sections below provide complete details. Most users don't need to read past the Quick Start above.*

This guide explains everything the agent can do to help you understand, modify, and work with MAgPIE.

---

## 🌟 What is MAgPIE Agent?

The magpie-agent is an AI assistant with **~95,000 words of comprehensive documentation** about the MAgPIE model, including:
- All 46 modules documented in detail
- Complete architecture and dependency maps
- Conservation laws and safety protocols
- GAMS programming reference
- User feedback and lessons learned

**Key Principle**: The agent checks AI documentation FIRST before reading raw GAMS code, providing faster and more accurate answers.

---

## 📚 Core Capabilities

### 1. **Answer Questions About MAgPIE**

Ask anything about the MAgPIE model:

**Module Questions**:
- "How does livestock work in MAgPIE?"
- "Explain the yield calculation"
- "What controls land allocation?"
- "How is water managed?"

**Architecture Questions**:
- "How does MAgPIE execute?"
- "What's the folder structure?"
- "What does vm_X mean?"
- "How do modules interact?"

**Dependency Questions**:
- "What modules depend on Module 10?"
- "Can I modify Module X without breaking Y?"
- "Why is my solution oscillating?"
- "How does carbon pricing affect forests?"

**Data Questions**:
- "Where does this data file come from?"
- "How is input processed?"
- "What's the spatial aggregation?"

**The agent will**:
- ✅ Check comprehensive AI documentation first (30 seconds)
- ✅ Cite specific files and line numbers
- ✅ Include warnings from user feedback
- ✅ State assumptions and limitations
- ✅ Only read raw GAMS code if docs insufficient

---

### 2. **Understand Model Modifications Safely**

Before modifying MAgPIE, get safety guidance:

**Ask**:
- "Is it safe to modify Module X?"
- "What will break if I change Y?"
- "What are the circular dependencies?"
- "Will changing Z affect water allocation?"

**The agent provides**:
- ✅ List of dependent modules (e.g., "Module 10 has 23 dependents")
- ✅ Conservation law implications (land, water, carbon, nitrogen, food)
- ✅ Circular dependency warnings and resolution strategies
- ✅ Testing protocols for high-risk changes
- ✅ Common mistakes to avoid (from user feedback)

**Documentation includes**:
- `modification_safety_guide.md` - Safety protocols for high-centrality modules
- `circular_dependency_resolution.md` - 26 circular cycles documented
- Conservation law docs - What must be preserved

---

### 3. **Learn GAMS Programming**

Get help writing or understanding GAMS code:

**Available Resources**:
- `GAMS_Phase1_Fundamentals.md` - GAMS basics, syntax, data types
- `GAMS_Phase2_Control_Structures.md` - Dollar conditions, loops, if statements
- `GAMS_Phase3_Advanced_Features.md` - Macros, variable attributes, time indexing
- `GAMS_Phase4_Functions_Operations.md` - Math functions, aggregation
- `GAMS_Phase5_MAgPIE_Patterns.md` - Module structure, naming conventions, MAgPIE idioms
- `GAMS_Phase6_Best_Practices.md` - Scaling, debugging, performance

**The agent will**:
- ✅ Explain GAMS syntax and semantics
- ✅ Provide MAgPIE-specific patterns
- ✅ Debug compilation errors
- ✅ Optimize model performance
- ✅ Follow MAgPIE naming conventions

---

### 4. **Navigate Documentation Efficiently**

**Comprehensive documentation structure**:

**Core Documentation** (~70,000 words)
- `Core_Architecture.md` - Model structure, execution flow
- `Module_Dependencies.md` - 173 dependencies mapped
- `Data_Flow.md` - 172 input files cataloged
- `Query_Patterns_Reference.md` - Complex query patterns
- `Response_Guidelines.md` - Token efficiency, quality checklist

**Module Documentation** (~20,000+ lines)
- All 46 modules: `module_09.md` through `module_80.md`
- Each includes: equations, parameters, interface variables, dependencies, limitations

**Cross-Module Analysis** (~5,400 lines)
- `land_balance_conservation.md` - Land conservation (strict equality)
- `water_balance_conservation.md` - Water supply/demand
- `carbon_balance_conservation.md` - Carbon stocks and emissions
- `nitrogen_food_balance.md` - Nitrogen tracking + food balance
- `modification_safety_guide.md` - Safety protocols
- `circular_dependency_resolution.md` - Feedback loops

**Reference Materials**:
- 6 GAMS programming guides (38,000+ words)
- Code truth principles
- Verification protocols

---

### 5. **Submit and Review Feedback**

Help improve the agent by sharing your experience:

**Feedback Types**:
- **Correction** - Fix errors in documentation
- **Warning** - Share mistakes to avoid
- **Lesson** - Practical insights from experience
- **Missing** - Document gaps in existing docs
- **Global** - Agent behavior improvements

**How to Submit**:
```bash
./scripts/submit_feedback.sh
```

**Interactive script will**:
- ✅ Guide you through feedback template
- ✅ Help you categorize the feedback
- ✅ Create properly formatted file
- ✅ Provide git commit instructions

**Review Pending Feedback**:
```bash
./scripts/review_feedback.sh
```

**Search Feedback**:
```bash
./scripts/search_feedback.sh "Module 70"
```

Type `/feedback` for complete details.

---

### 6. **Integrate Feedback Automatically**

Automated feedback integration with git workflow:

```bash
./scripts/integrate_feedback.sh feedback/pending/[file].md
```

**The script will**:
- ✅ Pull latest changes from magpie-agent repo
- ✅ Detect and help resolve merge conflicts
- ✅ Guide you through integration
- ✅ Move feedback to integrated/
- ✅ Commit with descriptive message
- ✅ Push to remote repository

**Manual mode**:
```bash
./scripts/integrate_feedback.sh [file].md --no-git
```

---

## 🚀 Available Commands

### For Everyone

| Command | What It Does |
|---------|-------------|
| `guide` | Show this capabilities guide |
| `sync` | Check MAgPIE code for changes, update documentation |
| `update` | Pull latest agent documentation from repository |
| `feedback` | Submit feedback to improve the agent |
| `bootstrap` | First-time setup for new installations |

### For Maintainers

| Command | What It Does |
|---------|-------------|
| `validate` | Check documentation consistency across all files |
| `validate-module` | Validate a specific module's documentation |
| `integrate-feedback` | Process pending user feedback |
| `compress-documentation` | Consolidate accumulated feedback (quarterly) |
| `update-agent-md` | Git workflow for documentation updates |

---

## Command Details

### `guide`
Show this comprehensive capabilities guide. Use at session start or for quick reference.

### `sync`
**Most important for keeping docs accurate!**

Checks MAgPIE develop branch for code changes and updates documentation:
- Compares against last sync commit
- Identifies GAMS equation/parameter changes
- Updates affected module_XX.md files
- Logs sync status in `project/sync_log.json`

**Use**: After MAgPIE code updates, or weekly maintenance.

### `update`
Pulls latest agent documentation from the magpie-agent repository:
- Fetches from git remote
- Handles merge conflicts
- Copies AGENT.md to parent directory
- Reports what changed

**Use**: Start of session, or after team members update docs.

### `feedback`
Learn about and use the feedback system:
- How to submit corrections, warnings, lessons
- Understanding notes files (module_XX_notes.md)
- When feedback gets integrated

**Use**: When you find errors or have insights to share.

---

## 🛠️ Helper Scripts

Located in `scripts/` directory:

### `submit_feedback.sh`
**Purpose**: Interactive feedback submission
**Usage**: `./scripts/submit_feedback.sh`

### `review_feedback.sh`
**Purpose**: Review pending feedback
**Usage**: `./scripts/review_feedback.sh`

### `search_feedback.sh`
**Purpose**: Search feedback and notes files
**Usage**: `./scripts/search_feedback.sh "search term"`

### `integrate_feedback.sh`
**Purpose**: Integrate feedback with git automation
**Usage**: `./scripts/integrate_feedback.sh feedback/pending/[file].md`

---

## 📊 Documentation Statistics

**Total Coverage**: ~95,000 words

**Module Documentation**:
- 46 modules fully documented
- All equations with verified formulas and line numbers
- Complete parameter descriptions
- Interface variables cataloged
- Dependencies mapped
- Assumptions and limitations stated

**Architecture Documentation**:
- 173 inter-module dependencies
- 26 circular dependencies explained
- 172 input files cataloged
- 5 conservation laws verified
- 115 interface variables

**GAMS Reference**:
- 38,000+ words across 6 guides
- Fundamentals to best practices
- MAgPIE-specific patterns
- Debugging and optimization

---

## 💡 Quick Start Examples

### Example 1: Understanding a Module
**You**: "How does livestock work in MAgPIE?"

**Agent will**:
1. Read `magpie-agent/modules/module_70.md` (30 seconds)
2. Read `magpie-agent/modules/module_70_notes.md` (user feedback)
3. Provide comprehensive answer with:
   - All 7 equations with formulas
   - Feed basket methodology
   - Interface variables
   - Limitations
   - ⚠️ Warnings from user feedback

**Time**: 2 minutes (vs. 10 minutes reading raw GAMS code)

---

### Example 2: Safe Modification
**You**: "Can I modify Module 10 without affecting water?"

**Agent will**:
1. Read `module_10.md` (interface variables)
2. Read `Module_Dependencies.md` (dependents)
3. Read `modification_safety_guide.md` (safety protocols)
4. Answer: "No - Module 10 exports vm_land which affects Module 42 (water demand). You'll need to test water allocation after changes."

**Time**: 1-2 minutes

---

### Example 3: Update Documentation
**You**: "/update"

**Agent will**:
1. Pull latest from magpie-agent repo
2. Copy AGENT.md to parent
3. Report: "Updated files: module_70_notes.md (added new warning), GAMS_Phase2.md (syntax examples)"

**Time**: 10 seconds

---

## 🎯 Response Quality Standards

**Every response includes**:
- 🟡 Documentation source ("Based on module_XX.md")
- 🟢 Code verification ("Verified in equations.gms:123")
- 🟠 Code-only flag ("Module docs don't cover this, checked raw GAMS code")
- 💬 User feedback ("Includes warnings from module_XX_notes.md")
- 📘 GAMS reference ("Consulted GAMS_Phase2 for syntax")

**The agent will**:
- ✅ Cite specific files and line numbers
- ✅ State what MAgPIE DOES (not what it should do)
- ✅ Clearly label made-up examples vs. actual data
- ✅ Verify arithmetic in calculations
- ✅ State limitations explicitly
- ✅ Provide next level of detail option

---

## 🔄 Continuous Improvement

**Your feedback makes the agent better**:

When you encounter:
- ❌ Incorrect information → Submit correction
- ⚠️ Common mistake → Submit warning
- 💡 Useful insight → Submit lesson
- 📖 Missing content → Submit gap report
- 🤖 Agent error → Submit global feedback

**Your feedback will**:
- Be reviewed and integrated
- Update notes files (module_XX_notes.md)
- Improve agent instructions (AGENT.md)
- Help future users avoid the same issues
- Build institutional knowledge

---

## 📞 Getting Help

**For questions about the agent itself**:
- Type `/guide` (this comprehensive guide)
- Read `README.md` in magpie-agent/
- Check `project/CURRENT_STATE.json` for project status

**For questions about MAgPIE**:
- Just ask! The agent has comprehensive documentation
- Use Quick Reference table in AGENT.md
- Check module index for module numbers

**For issues or suggestions**:
- Submit feedback via `./scripts/submit_feedback.sh`
- Create GitHub issue (if applicable)
- Talk to your team's MAgPIE expert

---

## 🎓 Best Practices

### For Efficient Answers
1. **Be specific** - "How does Module 70 calculate feed demand?" vs. "Tell me about livestock"
2. **Ask follow-ups** - Agent offers deeper detail if needed
3. **Mention context** - "I want to modify X" triggers safety checks
4. **Request code** - "Show me the equation" for implementation details

### For Learning
1. **Start with guide** - Understand capabilities
2. **Run update regularly** - Stay current
3. **Read notes files** - Learn from others' experience
4. **Ask "what if" questions** - Explore consequences safely

### For Contributing
1. **Submit feedback** - Share your learning
2. **Be specific** - Include file names, line numbers, examples
3. **Explain impact** - Why is this important?
4. **Follow templates** - Makes integration easier

---

## 🚀 Ready to Start!

**First steps**:
1. **Ask a question** - Try the agent on something you're working on
2. **Run update** - Get the latest documentation
3. **Explore documentation** - Browse modules/ or core_docs/
4. **Submit feedback** - Share your first experience

**Remember**:
- The agent checks comprehensive docs FIRST (saves time!)
- All answers include citations (verify yourself)
- User feedback prevents common mistakes
- Continuous improvement through feedback loop

---

**Welcome to the MAgPIE Agent community!** 🎉

Got questions? Just ask - that's what I'm here for!
