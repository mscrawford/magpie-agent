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
├── pending/          ← New submissions awaiting review
├── integrated/       ← Archive of feedback that's been applied
├── global/          ← System-wide lessons (affects CLAUDE.md, agent behavior)
├── templates/       ← Easy-to-fill templates for submitting feedback
└── README.md        ← You are here
```

---

## 🚀 Quick Start

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

## 🔄 Integration Workflow

### For Contributors

1. **Submit** feedback using script or template
2. **Commit** to your branch
3. **Push** or create PR
4. Wait for review

### For Maintainers

1. **Review** pending feedback:
   ```bash
   ./scripts/review_feedback.sh
   ```

2. **Integrate** each item:
   ```bash
   ./scripts/integrate_feedback.sh feedback/pending/[filename]
   ```

3. **Follow prompts** to add content to appropriate locations

4. **Commit** integrated changes

---

## 📊 Where Feedback Goes

### Module-Specific Feedback
- **Destination:** `modules/module_XX_notes.md`
- **Contains:** Warnings, lessons, corrections specific to that module
- **Agent reads:** When answering questions about Module XX

### Global Feedback
- **Destination:** `feedback/global/claude_lessons.md`
- **Contains:** Agent behavior improvements, workflow enhancements
- **Used to update:** CLAUDE.md, AI_Agent_Behavior_Guide.md

### Cross-Module Feedback
- **Destination:** `feedback/global/cross_module_lessons.md`
- **Contains:** Interactions between modules, system-level insights

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

## 🗜️ Feedback Compression

As feedback accumulates, documentation can become bloated. The **compression system** synthesizes integrated feedback to maintain streamlined docs without losing information.

### When to Compress

Consider compression when:
- CLAUDE.md or notes files exceed 500 lines per section
- Multiple feedback items address the same issue
- Warnings/lessons become redundant
- Documentation feels verbose or scattered

### How to Compress

```bash
# Check compression status
./scripts/compress_feedback.sh status

# See uncompressed feedback
./scripts/compress_feedback.sh list

# Run compression (AI-assisted)
# Use the /compress-feedback command in Claude Code
```

### Compression Workflow

1. **Analyze**: AI identifies patterns in integrated feedback
2. **Propose**: AI shows consolidation proposals with before/after
3. **Approve**: User reviews and approves changes
4. **Apply**: AI updates documentation files
5. **Track**: Compression metadata records what was consolidated

### What Compression Does

✅ **Consolidates** redundant warnings into comprehensive versions
✅ **Organizes** scattered lessons into coherent sections
✅ **Streamlines** verbose examples into concise references
✅ **Preserves** all unique insights with traceability
✅ **Maintains** feedback IDs for historical tracking

### What Compression Does NOT Do

❌ Delete unique information
❌ Remove important warnings
❌ Lose attribution or context
❌ Break traceability to original feedback

See `/compress-feedback` command for complete workflow.

---

**Thank you for helping improve the MAgPIE agent!** 🎉
