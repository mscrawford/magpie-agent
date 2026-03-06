# Guide Command

**Purpose**: Show capabilities of the MAgPIE Agent

**When user says**: "/guide", "what can you do?", "help", etc.

**How to present**: Show the Quick Start below. If they want more, point them to AGENT.md (which has the full reference, module finder, document structure, and response guidelines).

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
| `/feedback` | Submit feedback to improve the agent |
| `/validate` | Check documentation consistency (maintainers) |
| `/validate-module` | Validate specific module docs (maintainers) |

### Tips for best results
1. **Be specific** — "How does Module 70 calculate feed demand?" beats "tell me about livestock"
2. **Mention your goal** — "I want to modify X" triggers safety checks automatically
3. **Correct me** — If I'm wrong, say so. I'll record the correction for future sessions.

---

*Want the full technical reference? AGENT.md has the complete module finder, document structure, epistemic hierarchy, and response guidelines.*
