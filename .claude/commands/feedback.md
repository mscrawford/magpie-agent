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
# Easy way: Run the interactive script (from magpie-agent/ directory)
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

**⏱️ When will my feedback be integrated?**
- Feedback accumulates in `feedback/pending/`
- Integration happens **weekly or monthly** via `/integrate-feedback`
- You'll see your corrections in `module_XX.md` or warnings/lessons in `module_XX_notes.md`
- Timeline: Typically integrated within 1-4 weeks of submission

See `feedback/README.md` and `feedback/WORKFLOW_GUIDE.md` for complete details.

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

---

## 🔄 COMPLETE FEEDBACK WORKFLOW (CRITICAL!)

**⚠️ Creating a feedback file is only STEP 1 - you MUST also integrate it!**

### Step 1: Create Feedback File

```bash
# Write feedback file to pending/
Write: /path/to/magpie/magpie-agent/feedback/pending/YYYYMMDD_HHMMSS_type_target.md

# Follow template structure (see feedback/templates/)
```

### Step 2: Explain Proposed Changes to User

**BEFORE integrating, tell the user:**

> "I've documented this mistake in a feedback file. To prevent this from happening again, I propose the following changes:
>
> 1. **Update [file/command]** to add [specific change]
> 2. **Add [warning/check/example]** to [location]
> 3. **Move feedback** from pending/ to integrated/
>
> This will ensure future agents [benefit of the change].
>
> May I proceed with integrating these changes?"

**Wait for user approval before proceeding!**

### Step 3: Integrate the Feedback

**Determine where to integrate based on feedback type:**

- **Global behavior/workflow** → Update CLAUDE.md or relevant `/command`
- **Module-specific** → Update `module_XX_notes.md`
- **GAMS patterns** → Update `reference/GAMS_Phase*.md`
- **Cross-module** → Update `cross_module/*.md`
- **Agent behavior** → Update `core_docs/AI_Agent_Behavior_Guide.md`

**Examples:**
- Git workflow mistake → Update `/update-claude-md` command
- Module 52 misunderstanding → Update `modules/module_52_notes.md`
- GAMS syntax error → Update `reference/GAMS_Phase2_Control_Structures.md`

### Step 4: Move Feedback to Integrated

```bash
# Move from pending to integrated
mv feedback/pending/[file].md feedback/integrated/[file].md
```

### Step 5: Commit Everything Together

```bash
# Stage all changes (feedback + integrated changes)
git add feedback/pending/[file].md feedback/integrated/[file].md [other changed files]

# Commit with descriptive message
git commit -m "Integrate feedback: [description]

- Created feedback documenting [issue]
- Updated [files] to incorporate lessons learned
- Moved feedback to integrated/
- Future agents will now [benefit]"

# Push
git push
```

---

## ❌ WRONG: Creating Feedback Without Integrating

**DON'T DO THIS:**
```bash
# Create feedback
Write: feedback/pending/mistake.md
git add feedback/pending/mistake.md
git commit -m "Created feedback"
git push
# STOP HERE ← WRONG! Feedback not integrated!
```

**Problem:** The feedback just sits in pending/ forever. Future agents won't benefit because the instructions haven't been updated!

## ✅ CORRECT: Complete Feedback Loop

```bash
# 1. Create feedback
Write: feedback/pending/20251023_mistake.md

# 2. Explain to user what you'll change
# (get approval)

# 3. Integrate into actual instructions
Edit: [appropriate file based on feedback type]

# 4. Move to integrated
mv feedback/pending/20251023_mistake.md feedback/integrated/

# 5. Commit everything together
git add feedback/integrated/20251023_mistake.md [changed files]
git commit -m "Integrate feedback: [description]"
git push
```

---

**Priority guide:**
- **HIGH**: Fundamental mistakes about model architecture (parameterization vs. modeling)
- **MEDIUM**: Module-specific corrections, important warnings
- **LOW**: Minor clarifications, additional examples

**Remember**:
1. Creating feedback is STEP 1, not the complete task
2. Always explain proposed changes to user first
3. Integrate before pushing
4. Move to integrated/ to mark as complete
