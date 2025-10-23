# User Feedback System

**MAgPIE developers can improve agent performance through feedback!**

## What Are Notes Files?

Alongside each `module_XX.md`, there may be a `module_XX_notes.md` file containing:
- ⚠️ **Warnings** - Common mistakes to avoid
- 💡 **Lessons Learned** - Practical insights from real users
- ✏️ **Corrections** - Updates and clarifications
- 🧪 **Examples** - Real-world scenarios and how-tos

These files are **user-contributed** and **continuously updated** based on practical experience.

## When to Use Notes Files

**DO read notes files when query involves:**
- Modifications ("Can I change Module X?")
- Troubleshooting ("Why is X not working?")
- How-to questions ("How do I set up Y?")
- Warnings ("What should I avoid?")
- Practical guidance ("What's the best approach?")

**SKIP notes files for:**
- Simple factual queries ("What equation calculates X?")
- Equation lookups ("Show me the formula")
- Code truth only requests
- When user explicitly asks for just the implementation

## Response Pattern With User Feedback

When using notes files, structure your response like this:

```markdown
[Main answer based on module_XX.md - CODE TRUTH]

[Technical details, equations, parameters...]

---

⚠️ **Important Warnings** (from user feedback):
[If relevant warnings exist in module_XX_notes.md, mention them prominently]

💡 **Practical Lessons** (from user experience):
[If applicable to query type, include relevant lessons]

🧪 **Example**:
[If notes file has relevant example and user asked how-to, offer it]

---

📚 Sources:
- 🟡 module_XX.md (main documentation)
- 💬 module_XX_notes.md (user feedback) ← if used
- 🟢 Verified in equations.gms:123 ← if verified
```

## Priority Rules for Notes Files

1. **Warnings come first** - If user is asking about modifications, mention warnings BEFORE providing how-to
2. **High-centrality modules** - Always mention if modules 10, 11, 17, or 56 are involved (they have 20+ dependents)
3. **Conservation laws** - Reference conservation law docs for land, water, carbon, food queries
4. **Token efficiency** - Don't read entire notes file; skim sections and read only relevant parts

## Submitting Feedback (For Users)

MAgPIE developers can improve the agent by submitting feedback:

```bash
# Easy way: Run the interactive script
./scripts/submit_feedback.sh

# Choose type: correction, warning, lesson, missing content, or global
# Fill in the template
# Commit and push
```

**Feedback types:**
- **Correction**: Fix errors in documentation
- **Warning**: Share common mistakes to avoid
- **Lesson**: Practical insights from experience
- **Missing**: Document gaps in existing docs
- **Global**: Agent behavior improvements

See `feedback/README.md` for complete details.

---

## 🤖 AI Agent: When to Create Feedback

**As an AI agent, you should create feedback when you:**

1. **Make a mistake that the user corrects**
   - User points out error in your understanding
   - User clarifies what code actually does vs. what you thought
   - Example: "I don't think that's modeling fire, just generic disturbance"
   - **Action**: Create global feedback with type 5

2. **Learn something important from the user**
   - User explains a pattern or principle you should know
   - User shows how modules interact in ways not documented
   - User provides critical context about model behavior
   - **Action**: Create lesson or global feedback

3. **Discover gaps in documentation**
   - You can't answer a question because docs are incomplete
   - User asks about something that should be documented but isn't
   - Cross-module interaction not explained
   - **Action**: Create "missing content" feedback with type 4

**How to create feedback during a session:**

```bash
# 1. Write feedback file directly
Write: /path/to/magpie/magpie-agent/feedback/pending/YYYYMMDD_HHMMSS_type_target.md

# 2. Follow template structure (see feedback/templates/)

# 3. Commit with descriptive message
Bash: git -C /path/to/magpie/magpie-agent add feedback/pending/[file]
Bash: git -C /path/to/magpie/magpie-agent commit -m "Feedback: [description]"
```

**Priority guide:**
- **HIGH**: Fundamental mistakes about model architecture (parameterization vs. modeling)
- **MEDIUM**: Module-specific corrections, important warnings
- **LOW**: Minor clarifications, additional examples

**Remember**: Future AI agents will benefit from your feedback. If the user had to correct you, document it so it doesn't happen again!
