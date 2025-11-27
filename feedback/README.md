# Feedback System for MAgPIE Agent

This directory contains a **user-driven feedback system** to continuously improve the MAgPIE AI agent's performance.

## 🎯 Purpose

Enable MAgPIE developers and users to easily:
- Report errors in documentation
- Share warnings about common mistakes
- Contribute lessons learned from practical experience
- Suggest agent behavior improvements
- Document missing content

All feedback gets integrated into the documentation, making the agent smarter over time.

---

## 📁 Directory Structure

```
feedback/
├── pending/              ← Staged feedback awaiting validation & integration
│   ├── README.md         ← Staged workflow documentation
│   └── *.md              ← Feedback files (flat structure with timestamps)
├── integrated/           ← Archive of validated & integrated feedback
├── global/               ← System-wide lessons (claude_lessons.md)
├── templates/            ← Easy-to-fill submission templates
└── README.md             ← You are here
```

---

## 🚀 Quick Start

### ⚡ Quick Reference Card

| Task | Command | When |
|------|---------|------|
| Submit feedback | `scripts/submit_feedback.sh` | Anytime you have feedback |
| Process pending feedback | `/integrate-feedback all` | Weekly/monthly |
| Reduce bloat | `/compress-documentation` | Quarterly (optional) |

**📖 New user?** See [WORKFLOW_GUIDE.md](WORKFLOW_GUIDE.md) for complete workflow explanation

---

### Submit Feedback (Easy Way)

```bash
# Run the interactive script
./scripts/submit_feedback.sh

# Follow the prompts:
# 1. Choose feedback type (correction, warning, lesson, missing, global)
# 2. Specify target document (e.g., module_70.md)
# 3. Fill in the template
# 4. Commit and push
```

### Submit Feedback (Manual Way)

```bash
# 1. Copy a template
cp feedback/templates/warning.md feedback/pending/20251022_warning_module_10.md

# 2. Edit the file (fill in all sections)
nano feedback/pending/20251022_warning_module_10.md

# 3. Commit
git add feedback/pending/20251022_warning_module_10.md
git commit -m "Feedback: Warning about Module 10 modifications"
git push
```

---

## 📝 Feedback Types

### 1. Correction
**Use when:** Documentation has errors, outdated info, or inaccuracies

**Template:** `templates/correction.md`

**Example:** "Module 70 docs say 8 equations, but there are actually 7"

### 2. Warning
**Use when:** You discovered something dangerous or a common mistake

**Template:** `templates/warning.md`

**Example:** "Don't modify Module 10 without checking water implications"

### 3. Lesson Learned
**Use when:** You figured something out that others should know

**Template:** `templates/lesson_learned.md`

**Example:** "SSP2 feed baskets are most stable for testing"

### 4. Missing Content
**Use when:** Documentation has gaps or missing important information

**Template:** `templates/missing.md`

**Example:** "Module 35 doesn't explain the protection mechanism interaction"

### 5. Global Feedback
**Use when:** Agent behavior or workflow needs improvement

**Template:** `templates/global.md`

**Example:** "Agent should check conservation laws when answering cross-module questions"

---

## 🔄 Integration Workflow (Staged Approach)

### **NEW: Staged Workflow** ✨

Feedback now flows through a **staged validation process** to maintain stability of core docs while enabling continuous feedback flow.

### For Contributors (Unchanged)

1. **Submit** feedback using script or template
   ```bash
   ./scripts/submit_feedback.sh
   ```
2. **Feedback goes to**: `feedback/pending/module_XX/` (core docs untouched)
3. **Commit** and push
4. Done! Your feedback is now pending integration

### For Maintainers (Enhanced)

**Periodic Integration Sessions** (weekly, monthly, or as needed):

1. **Scan pending feedback**:
   ```bash
   /integrate-feedback              # Interactive mode
   # OR
   /integrate-feedback all          # All pending feedback
   ```

2. **Agent validates** each item:
   - ✅ Valid: Applies to current code
   - ⚠️ Outdated: Code changed, needs updating
   - ❌ Incorrect: Contains errors

3. **Review integration proposal**:
   - See what will be integrated
   - Which files will be updated (module_XX.md or module_XX_notes.md)
   - What will be archived

4. **Approve and execute**:
   - Agent routes corrections → `module_XX.md` (fixes errors)
   - Agent routes warnings/lessons → `module_XX_notes.md` (user experience)
   - Archives to `integrated/`
   - Updates timestamps
   - Removes from `pending/`

5. **Commit** batch integration

### Key Differences from Old Workflow

**OLD**: Submit → Immediate review → Immediate integration → Update docs
- Risk: Core docs could become unstable
- Friction: Every submission needs immediate attention

**NEW**: Submit → Accumulate in pending/ → Periodic batch integration → Update notes files
- ✅ Core docs (`module_XX.md`) stay stable (only change when code changes)
- ✅ User feedback (`module_XX_notes.md`) updated in validated batches
- ✅ No submission friction
- ✅ Controlled integration with validation

---

## 📊 Where Feedback Goes

### Module-Specific Feedback
- **Submission**: `feedback/pending/` (e.g., `pending/20251026_143000_warning_module_10.md`)
- **After Integration**: `modules/module_XX_notes.md` (for warnings/lessons) or `modules/module_XX.md` (for corrections)
- **Contains:** Warnings, lessons, corrections specific to that module
- **Agent reads:** When answering questions about Module XX (if how-to/troubleshooting)

### Global Feedback
- **Submission**: `feedback/pending/` (e.g., `pending/20251026_150000_global_agent_behavior.md`)
- **After Integration**: `feedback/global/claude_lessons.md`
- **Contains:** Agent behavior improvements, workflow enhancements
- **Used to update:** CLAUDE.md (agent instructions)

### Cross-Module Feedback
- **Submission**: `feedback/pending/` (mark as cross-module in content)
- **After Integration**: `feedback/global/cross_module_lessons.md`
- **Contains:** Interactions between modules, system-level insights

### Flow Summary

```
User submits feedback
  ↓
feedback/pending/YYYYMMDD_HHMMSS_type_target.md
  ↓
Periodic integration session (/integrate-feedback all)
  ↓
Validation against current code
  ↓
Type-based routing:
  - correction/missing_content → module_XX.md (fixes errors)
  - warning/lesson_learned → module_XX_notes.md (user experience)
  ↓
Archive to feedback/integrated/
  ↓
Remove from pending/
```

---

## ✅ Integration Checklist

Before marking feedback as integrated:

- [ ] Content added to appropriate notes file or documentation
- [ ] Unique ID assigned (W001, L001, C001, etc.)
- [ ] Date and source recorded
- [ ] If correction: main doc also updated
- [ ] If global: CLAUDE.md or workflow updated
- [ ] Cross-references added
- [ ] "Last updated" date refreshed
- [ ] Feedback moved to `integrated/`
- [ ] Changes committed with descriptive message

---

## 💡 Tips for Good Feedback

### Be Specific
❌ "Module 70 is confusing"
✅ "Module 70 docs don't explain that q70_feed operates at regional level, not cell level"

### Provide Context
Include:
- What you were trying to do
- What went wrong or what you learned
- How to verify or reproduce

### Cite Sources
Reference:
- Specific code files and line numbers
- Papers or documentation
- Other modules or sections

### Make It Actionable
Suggest:
- What should change
- Where it should go
- How to implement

---

## 📈 Impact

This feedback system enables:

✅ **Continuous Improvement** - Agent gets smarter with each submission
✅ **Knowledge Sharing** - Community learns from each other's experience
✅ **Error Correction** - Docs stay accurate as code evolves
✅ **Safety Enhancement** - Warnings prevent common mistakes
✅ **Reduced Support Load** - Common issues get documented

---

## 🙋 Questions?

- See templates for detailed examples
- Run `./scripts/submit_feedback.sh` for guided submission
- Check `modules/module_70_notes.md` for example of integrated feedback
- Read `RULES_OF_THE_ROAD.md` for project guidelines

---

## 🗜️ Feedback Workflow: Two Commands

The feedback system uses **two sequential commands**:

### `/integrate-feedback` - Process Pending Submissions

**Purpose**: Validate and integrate new user feedback

**When to use**: Weekly or monthly, whenever feedback accumulates

**Command**:
```bash
/integrate-feedback module_10     # Single module
/integrate-feedback all           # All pending feedback
/integrate-feedback               # Interactive mode
```

**What it does**:
1. ✅ Scans `feedback/pending/` for new submissions
2. ✅ Validates each item against current code
3. ✅ Routes corrections/missing → `module_XX.md` (fixes errors in core docs)
4. ✅ Routes warnings/lessons → `module_XX_notes.md` (user experience)
5. ✅ Archives to `integrated/` with batch report
6. ✅ Updates timestamps
7. ✅ Removes from `pending/`

**Key principle**: Type-based routing prevents "notes purgatory" - corrections actually fix core docs!

---

### `/compress-documentation` - Reduce Bloat (Optional)

**Purpose**: Consolidate accumulated feedback to reduce bloat

**When to use**: Quarterly, or when notes files feel verbose (AFTER multiple integrations)

**Command**:
```bash
/compress-documentation     # Analyze and compress integrated feedback
```

**What it does**:
1. ✅ Analyzes patterns in `integrated/` feedback
2. ✅ Identifies consolidation opportunities (redundant warnings, scattered lessons)
3. ✅ Proposes before/after with line reductions
4. ✅ Updates `module_XX_notes.md`, `CLAUDE.md`, global lessons (with approval)
5. ✅ Maintains traceability with feedback IDs
6. ✅ Tracks compression metadata

**What gets compressed**:
- ✅ `module_XX_notes.md` - User warnings, lessons, examples
- ✅ `CLAUDE.md` - Agent behavioral guidance (if bloated)
- ✅ `feedback/global/claude_lessons.md` - System-wide lessons
- ❌ **NEVER** `module_XX.md` - Core docs (facts are sacred!)

**What compression does**:
- ✅ Consolidates redundant warnings into comprehensive versions
- ✅ Organizes scattered lessons into coherent sections
- ✅ Preserves all unique insights with traceability

**What compression does NOT do**:
- ❌ Delete unique information
- ❌ Remove important warnings
- ❌ Compress core technical documentation
- ❌ Break traceability to original feedback

---

### Recommended Workflow

**They are SEQUENTIAL, not alternatives**: Integrate first (always), then compress later (sometimes).

1. **Regular Integration** (weekly/monthly): `/integrate-feedback all`
   - Keeps `pending/` clean
   - Validates and integrates user feedback
   - Updates core docs (corrections) and notes files (warnings/lessons)

2. **Periodic Compression** (quarterly, optional): `/compress-documentation`
   - Reduces bloat in notes files and agent guidance
   - Organizes feedback into coherent sections
   - Maintains quality while reducing redundancy

**Timeline example**:
```
Week 1-4: Submit feedback → /integrate-feedback
Week 5-8: Submit feedback → /integrate-feedback
Week 9-12: Submit feedback → /integrate-feedback
Month 3: Notes feeling bloated → /compress-documentation
Month 4+: Back to /integrate-feedback (cycle continues)
```

**📖 See [WORKFLOW_GUIDE.md](WORKFLOW_GUIDE.md) for detailed workflow explanation and decision tree**

---

**Thank you for helping improve the MAgPIE agent!** 🎉
