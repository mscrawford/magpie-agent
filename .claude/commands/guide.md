# 🤖 MAgPIE Agent - Complete Capabilities Guide

Welcome to the **magpie-agent** - your specialized AI assistant for the MAgPIE land-use model!

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

**Phase 0: Foundation & Architecture** (~70,000 words)
- `Phase1_Core_Architecture.md` - Model structure, execution flow
- `Phase2_Module_Dependencies.md` - 173 dependencies mapped
- `Phase3_Data_Flow.md` - 172 input files cataloged
- `AI_Agent_Behavior_Guide.md` - Query routing patterns

**Phase 1: Module Documentation** (~20,000+ lines)
- All 46 modules: `module_09.md` through `module_80.md`
- Each includes: equations, parameters, interface variables, dependencies, limitations

**Phase 2: Cross-Module Analysis** (~5,400 lines)
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

See `/feedback` command for complete details.

---

### 6. **Integrate Feedback Automatically**

New! Automated feedback integration with git workflow:

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

## 🚀 Slash Commands

Quick access to specialized help:

### `/guide` (this guide)
**Purpose**: Show complete capabilities guide
**Use**: Boot-time orientation or quick reference

**Note**: Don't confuse with built-in `/help` (Claude Code help) - use `/guide` for MAgPIE Agent capabilities.

### `/update`
**Purpose**: Pull latest documentation and re-deploy CLAUDE.md
**Use**:
- Start of session (get latest updates)
- After team members update docs
- Before answering questions (ensure current info)

**What it does**:
- Pulls from magpie-agent repo
- Handles merge conflicts
- Copies CLAUDE.md to parent directory
- Reports what changed

### `/feedback`
**Purpose**: Learn about the user feedback system
**Use**:
- Understand notes files (module_XX_notes.md)
- Learn when to read feedback
- Submit your own feedback
- Integration workflow

**Covers**:
- What are notes files?
- When to use them
- How to submit feedback
- AI agent feedback creation
- Complete integration workflow

### `/update-claude-md`
**Purpose**: Git workflow for AI documentation updates
**Use**: When updating CLAUDE.md or other AI docs

**Critical rules**:
- All AI docs live in magpie-agent directory
- Commit from magpie-agent repo only
- Never commit AI docs from main MAgPIE repo
- Copy CLAUDE.md to parent for convenience

---

## 🛠️ Helper Scripts

Located in `scripts/` directory:

### `submit_feedback.sh`
**Purpose**: Interactive feedback submission
**Usage**: `./scripts/submit_feedback.sh`
**Features**:
- Choose feedback type (1-5)
- Auto-fill template
- Pre-populate metadata
- Open in editor

### `review_feedback.sh`
**Purpose**: Review pending feedback
**Usage**: `./scripts/review_feedback.sh`
**Features**:
- List all pending items
- Show metadata (type, target, date)
- Count pending submissions

### `search_feedback.sh`
**Purpose**: Search feedback and notes files
**Usage**: `./scripts/search_feedback.sh "search term"`
**Features**:
- Search module notes
- Search global lessons
- Search pending feedback
- Search integrated archive

### `integrate_feedback.sh`
**Purpose**: Integrate feedback with git automation
**Usage**: `./scripts/integrate_feedback.sh feedback/pending/[file].md`
**Features**:
- Auto git pull before integration
- Merge conflict detection
- Auto commit with metadata
- Auto push to remote
- Manual mode with --no-git flag

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

**User Feedback**:
- Notes files for modules 10, 52, 70
- Global lessons
- Integrated feedback archive
- Continuous improvement system

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
2. Read `Phase2_Module_Dependencies.md` (dependents)
3. Read `modification_safety_guide.md` (safety protocols)
4. Answer: "No - Module 10 exports vm_land which affects Module 42 (water demand). You'll need to test water allocation after changes."

**Time**: 1-2 minutes

---

### Example 3: Update Documentation
**You**: `/update`

**Agent will**:
1. Pull latest from magpie-agent repo
2. Copy CLAUDE.md to parent
3. Report: "Updated files: module_70_notes.md (added new warning), GAMS_Phase2.md (syntax examples)"

**Time**: 10 seconds

---

### Example 4: Submit Feedback
**You**: `./scripts/submit_feedback.sh`

**Script will**:
1. Ask: "What type of feedback?" (correction, warning, lesson, missing, global)
2. Ask: "Target document?"
3. Create template
4. Open in editor
5. Provide git commit instructions

**Time**: 2 minutes to submit, helps all future users!

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
- Improve agent instructions (CLAUDE.md)
- Help future users avoid the same issues
- Build institutional knowledge

---

## 📞 Getting Help

**For questions about the agent itself**:
- Use `/guide` (this comprehensive guide)
- Read `README.md` in magpie-agent/
- Check `START_HERE.md` for project orientation
- Review `RULES_OF_THE_ROAD.md` for session protocol

**For questions about MAgPIE**:
- Just ask! The agent has comprehensive documentation
- Use Quick Reference table in CLAUDE.md
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
1. **Start with /guide** - Understand capabilities
2. **Use /update** regularly - Stay current
3. **Read notes files** - Learn from others' experience
4. **Ask "what if" questions** - Explore consequences safely

### For Contributing
1. **Submit feedback** - Share your learning
2. **Be specific** - Include file names, line numbers, examples
3. **Explain impact** - Why is this important?
4. **Follow templates** - Makes integration easier

---

## 📈 Success Metrics

**The agent helps you**:
- ⚡ Get answers in 30 seconds instead of 5 minutes
- 🎯 Avoid common mistakes (user feedback warnings)
- 🛡️ Modify safely (dependency and safety analysis)
- 📚 Learn GAMS efficiently (comprehensive reference)
- 🔄 Build institutional knowledge (feedback system)

**Documentation coverage**:
- ✅ 100% of modules (46/46)
- ✅ All conservation laws documented
- ✅ All circular dependencies explained
- ✅ Complete GAMS reference
- ✅ Growing user feedback library

---

## 🚀 Ready to Start!

**First steps**:
1. **Ask a question** - Try the agent on something you're working on
2. **Run /update** - Get the latest documentation
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
