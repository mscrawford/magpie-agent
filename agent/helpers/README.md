# Auto-Loading AI Context Helpers

## Overview

This directory contains **context helpers** — focused knowledge files that the AI agent automatically loads when it detects specific user situations. Unlike slash commands (user-invoked), helpers are **silently loaded** based on intent detection.

Each helper is a **self-improving document**: its "Lessons Learned" section accumulates practical wisdom from real usage, making the agent smarter over time.

---

## How Auto-Loading Works

### Detection → Load → Cite

1. **Detect**: The agent recognizes intent from the user's question (keywords, context, error messages)
2. **Load**: The agent silently reads the relevant helper file(s) into its context
3. **Cite**: The agent mentions which helper was loaded: `📋 Loaded helper: debugging_infeasibility`

### Auto-Load Rules

Each helper defines its own trigger patterns. The master routing is in `AGENT.md` under the `## Auto-Loading Context Helpers` section.

| Trigger Pattern | Helper File | Description |
|----------------|-------------|-------------|
| **ALWAYS** (every session start) | `session_startup.md` | Checks MAgPIE version, git state, sync freshness, recent runs |
| "infeasible", "won't solve", "modelstat", "error 4" | `debugging_infeasibility.md` | Diagnosing and fixing model infeasibilities |
| "carbon price", "carbon tax", "GHG policy", "emission pricing" | `scenario_carbon_pricing.md` | Setting up carbon pricing scenarios |
| "diet", "EAT-Lancet", "food demand change", "livestock reduction" | `scenario_diet_change.md` | Configuring diet change scenarios |
| "modify", "change", "what breaks", "impact of changing" | `modification_impact_analysis.md` | Assessing modification safety and impacts |
| "model output", "run results", "fulldata.gdx", "what does this mean" | `interpreting_outputs.md` | Understanding model outputs |
| "which realization", "choose realization", "realization comparison", "default realization", "switch realization", "alternative realization" | `realization_selection.md` | Comparing and choosing realizations |
| "add crop", "new crop type", "extend crops" | `adding_new_crop.md` | Cross-module walkthrough for adding crops |

### When NOT to auto-load

- Simple factual questions ("What equation calculates X?") → Module docs are sufficient
- Questions about the agent itself → Use `/guide`
- Documentation maintenance → Use slash commands

---

## Helper File Template

Every helper follows this structure:

```markdown
# Helper: [Title]

**Auto-load triggers**: [keyword list]
**Last updated**: [date]
**Lessons count**: [N entries]

---

## Quick Reference
[Most critical info — always fits in ~50 lines. This section is the "cheat sheet".]

## Step-by-Step Guidance
[Detailed walkthrough for the task.]

## Common Pitfalls
[Known issues, misconfigurations, and how to avoid them.]

## Module Cross-References
[Which module docs to consult for details.]

## Lessons Learned
<!-- APPEND-ONLY: Add new entries at the bottom. Never remove old ones. -->
<!-- Format: - YYYY-MM-DD: [lesson] (source: [user feedback | session experience]) -->
```

---

## Self-Improvement Mechanism

### Adding Lessons

When a helper is used and:
- The user encounters a problem NOT covered by the helper → append to "Lessons Learned"
- The user corrects the agent's advice → append the correction
- A new pattern is discovered → append the pattern

### Promoting Lessons

**Trigger**: When a helper's Lessons Learned section reaches **5+ entries**, review them during the next session that loads the helper:
1. If a lesson is widely applicable, move its content into the relevant main section (Quick Reference, Pitfalls, etc.)
2. Mark the original entry: `[PROMOTED to Quick Reference]`
3. If a lesson is narrow/situational, leave it in place — it's still useful context

**The agent should check lesson count** (in the header `Lessons count: N entries`) each time it loads a helper. When N ≥ 5, scan for promotion candidates before answering.

### Feedback Integration

The `/integrate-feedback` command can route feedback to helpers:
- Feedback type `helper_improvement` → Append to relevant helper's Lessons Learned
- Feedback type `new_helper` → Flag for new helper creation

---

## Design Principles

1. **Token-efficient**: Each helper should be 200-400 lines. The agent loads them into context, so brevity matters.
2. **Task-oriented**: Helpers answer "how do I DO X?" not "what IS X?" (module docs handle the latter).
3. **Self-improving**: Lessons Learned grows with use. The system gets smarter over time.
4. **Transparent**: Always cite which helper was loaded so users understand the system.
5. **Complementary**: Helpers reference module docs, not replace them. They provide the workflow; module docs provide the facts.
