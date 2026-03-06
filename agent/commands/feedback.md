# Feedback Command

**Purpose**: Learn about and use the user feedback system

**When user says**: "/feedback", "run command: feedback", "how do I give feedback", "feedback system", etc.

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

MAgPIE developers can improve the agent by submitting feedback. Create a file in `feedback/pending/` following this format:

```markdown
# Feedback: [Title]

**Type**: correction / warning / lesson / missing / global
**Module**: [XX or "global"]
**Date**: YYYY-MM-DD
**Author**: [your name]

## Description
[What you found / what should change]

## Evidence
[Code reference, run output, or other supporting info]
```

Commit and push to the magpie-agent repo.

**Feedback types:**
- **Correction**: Fix errors in documentation
- **Warning**: Share common mistakes to avoid
- **Lesson**: Practical insights from experience
- **Missing**: Document gaps in existing docs
- **Global**: Agent behavior improvements

**⏱️ When will my feedback be integrated?**
- Feedback accumulates in `feedback/pending/`
- The agent also records corrections directly to `module_XX_notes.md` and helper Lessons Learned during sessions
- Maintainers review pending feedback periodically and integrate into module docs

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

- ❌ **DO NOT** edit `modules/module_XX.md` (main documentation — requires review)
- ❌ **DO NOT** edit `AGENT.md` (agent instructions — requires review)
- ❌ **DO NOT** move file to `integrated/`

**What you CAN edit immediately** (no review needed):
- ✅ `modules/module_XX_notes.md` — append warnings, corrections, lessons
- ✅ `agent/helpers/*.md` `## Lessons Learned` sections — append new entries
- ✅ `feedback/global/agent_lessons.md` — append system-wide lessons

**Why the distinction?** Notes files and Lessons Learned sections are **append-only logs** of practical experience. They supplement core docs without changing authoritative content. Core docs (`module_XX.md`, `AGENT.md`) define the canonical truth and require human review before modification.

---

## ⚙️ INTEGRATION WORKFLOW (MAINTAINER ONLY)

**To process pending feedback manually:**
1. Read pending files in `feedback/pending/`
2. Update relevant module docs (`modules/module_XX.md`) or notes (`modules/module_XX_notes.md`)
3. Move processed files from `pending/` to `integrated/`
4. Commit the integration

**Note**: Most corrections and lessons are now recorded directly by the agent during sessions. The formal pending feedback pipeline is for user-submitted feedback that requires maintainer review.

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
