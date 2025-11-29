# Feedback Command

**Purpose**: Learn about and use the user feedback system

**When user says**: "run command: feedback", "how do I give feedback", "feedback system", etc.

---

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
2. **High-centrality modules** - Always mention if module 11 is involved (27 dependents) or modules 10, 17, 56 (13-15 dependents each)
3. **Conservation laws** - Reference conservation law docs for land, water, carbon, food queries
4. **Token efficiency** - Don't read entire notes file; skim sections and read only relevant parts

---

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
- Integration happens **weekly or monthly** via `command: integrate-feedback`
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

## 🔄 FEEDBACK SUBMISSION WORKFLOW (STEP 1)

**When you have feedback to submit, follow this workflow:**

### Step 1: Create Feedback File

```bash
# Write feedback file to pending/
# File: feedback/pending/YYYYMMDD_HHMMSS_type_target.md

# Follow template structure (see feedback/templates/)
```

### Step 2: Commit and Push Pending File

```bash
# Stage ONLY the pending feedback file
git add feedback/pending/[file].md

# Commit
git commit -m "Feedback: [description]

- Type: [correction/warning/lesson/missing/global]
- Target: [module/command]
- Submitted for future integration"

# Pull latest changes to avoid conflicts (rebase to keep history clean)
git pull --rebase origin main

# Push
git push
```

### Step 3: Notify User

> "✅ **Feedback Submitted!**
>
> I've saved your feedback to the pending queue. It will be reviewed by a maintainer and integrated into the documentation during the next maintenance cycle.
>
> **Note**: This feedback won't be active in the agent until it is integrated."

---

## ⚠️ CRITICAL: DO NOT EDIT CORE DOCS

**During the feedback submission step:**

- ❌ **DO NOT** edit `modules/module_XX.md`
- ❌ **DO NOT** edit `AGENT.md`
- ❌ **DO NOT** move file to `integrated/`

**Why?** Feedback must be reviewed by a human maintainer before changing the core documentation. The pending queue allows for this review.

---

## ⚙️ INTEGRATION WORKFLOW (STEP 2 - MAINTAINER ONLY)

**To process pending feedback, use `command: integrate-feedback`.**

This separate process will:
1. Read pending files
2. Update documentation (AGENT.md, module notes, etc.)
3. Move files from `pending/` to `integrated/`
4. Commit the integration

---

## ✅ CORRECT: Submitting Feedback

```bash
# 1. Create pending file
# Write to: feedback/pending/mistake.md

# 2. Commit and Push
git add feedback/pending/mistake.md
git commit -m "Feedback: mistake"
git push
```

## ❌ WRONG: Integrating Immediately

**DON'T DO THIS:**
```bash
# Create feedback
# Write to: feedback/pending/mistake.md
# Edit docs immediately
# Edit: modules/module_10.md
# Move to integrated
mv feedback/pending/mistake.md feedback/integrated/
# Push
git push
```

**Problem:** This bypasses the review process and modifies core documentation without approval.

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
