# Feedback Workflow Guide

**For**: MAgPIE developers using the feedback system
**Purpose**: Understand when to use `command: integrate-feedback` vs `command: compress-documentation`

---

## 🎯 Quick Answer

**Use `command: integrate-feedback`** (weekly/monthly) to process new user submissions
**Use `command: compress-documentation`** (quarterly) to reduce bloat AFTER multiple integrations

**They are SEQUENTIAL, not alternatives**: You integrate first (always), then compress later (sometimes).

---

## 📊 The Two Commands

### `command: integrate-feedback` - Process New Submissions

**What it does**:
- Takes new feedback from `feedback/pending/`
- Validates against current code
- Routes corrections → `module_XX.md` (fixes errors)
- Routes warnings/lessons → `module_XX_notes.md` (user experience)
- Archives integrated feedback

**When to use**: Weekly or monthly, whenever feedback accumulates

**Input**: `feedback/pending/*.md` (new submissions)
**Output**: Updated docs + `feedback/integrated/` archives

**Example workflow**:
```bash
# User submits 3 warnings about Module 10
scripts/submit_feedback.sh

# Later (weekly/monthly):
command: integrate-feedback all

# Result: Warnings added to module_10_notes.md
```

---

### `command: compress-documentation` - Reduce Bloat

**What it does**:
- Analyzes accumulated feedback in `feedback/integrated/`
- Identifies redundant or scattered content
- Consolidates similar warnings/lessons
- Reorganizes for clarity

**When to use**: Quarterly, or when notes files feel bloated

**Input**: `feedback/integrated/` archives (from past integrations)
**Output**: Consolidated notes files with reduced redundancy

**Example workflow**:
```bash
# After 10+ integration sessions over 3 months:
command: compress-documentation

# Result: 3 similar warnings merged into 1 comprehensive section
```

---

## 🔄 The Full Workflow

```
┌─────────────────────────────────────────────────────────────┐
│ STEP 1: Users submit feedback (anytime)                     │
│ scripts/submit_feedback.sh                                   │
│ → feedback/pending/20251101_143000_warning_module_10.md     │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ STEP 2: Weekly/monthly integration                          │
│ command: integrate-feedback all                                      │
│ → Validates feedback                                        │
│ → Updates module_10_notes.md                                │
│ → Archives to feedback/integrated/                          │
└─────────────────────────────────────────────────────────────┘
                            ↓ (repeat 10+ times)
┌─────────────────────────────────────────────────────────────┐
│ STEP 3: Quarterly compression (optional)                    │
│ command: compress-documentation                                      │
│ → Analyzes feedback/integrated/                             │
│ → Merges 3 similar warnings → 1 comprehensive version       │
│ → Reduces bloat in module_10_notes.md                       │
└─────────────────────────────────────────────────────────────┘
                            ↓
                    Back to STEP 1
```

**Timeline example**:
- Week 1: Submit feedback → `command: integrate-feedback`
- Week 2: Submit feedback → `command: integrate-feedback`
- Week 3: Submit feedback → `command: integrate-feedback`
- ...
- Month 3: Notes files getting long → `command: compress-documentation`
- Month 4: Submit feedback → `command: integrate-feedback` (cycle continues)

---

## ❓ When to Use Which Command

### Use `command: integrate-feedback` when:
- ✅ New feedback has accumulated in `feedback/pending/`
- ✅ You want to add user submissions to documentation
- ✅ You're doing weekly/monthly maintenance
- ✅ You want corrections to reach `module_XX.md`
- ✅ You want warnings/lessons to reach `module_XX_notes.md`

### Use `command: compress-documentation` when:
- ✅ After multiple integration sessions (10+)
- ✅ Notes files feel bloated or redundant
- ✅ Similar warnings are scattered across files
- ✅ Quarterly documentation cleanup time
- ⚠️ **ONLY AFTER** you've integrated feedback (not before!)

### DON'T use `command: compress-documentation` when:
- ❌ You have pending feedback that hasn't been integrated yet
- ❌ You just want to process new submissions (use `command: integrate-feedback`)
- ❌ Notes files are short and organized
- ❌ Less than 3 months since last compression

---

## 🎨 What Gets Compressed?

### ✅ COMPRESS (user experience):
- `modules/module_XX_notes.md` - User warnings, lessons, examples
- `AGENT.md` - Agent behavioral guidance (if bloated)
- `feedback/global/agent_lessons.md` - System-wide lessons

### ❌ NEVER COMPRESS (code truth):
- `modules/module_XX.md` - Core technical documentation
- Equation formulas, parameter definitions
- Any factual claims about what code does

**Why?**
- **Code truth** is immutable - facts don't get "compressed"
- **User experience** can be reorganized for clarity
- Compression is about organization, not changing facts

---

## 🌳 Decision Tree

```
Do you have new feedback submissions?
├─ YES → Use command: integrate-feedback
│         │
│         └─ After integration, do notes files feel bloated?
│            ├─ YES → Consider command: compress-documentation
│            └─ NO → Done! Wait for more feedback
│
└─ NO → Do notes files have redundant content?
         ├─ YES → Use command: compress-documentation
         └─ NO → Nothing to do! Wait for feedback
```

**Simplified**:
1. New feedback? → `command: integrate-feedback`
2. Notes bloated? → `command: compress-documentation`
3. Both? → `command: integrate-feedback` FIRST, THEN `command: compress-documentation`

---

## 📋 Quick Reference Card

| Command | Frequency | Input | Output | Purpose |
|---------|-----------|-------|--------|---------|
| `command: integrate-feedback` | Weekly/monthly | `pending/` | `integrated/` + notes | Add new feedback |
| `command: compress-documentation` | Quarterly | `integrated/` | Consolidated notes | Reduce bloat |

**Remember**: Integrate (always) → Compress (sometimes)

---

## 💡 Examples

### Example 1: Weekly Workflow
```bash
# Monday: 5 users submitted feedback over the weekend
ls feedback/pending/*.md | grep -v README  # → 5 new files

# Use integrate command
command: integrate-feedback all

# Result:
# - 5 items validated and integrated
# - module_10_notes.md updated
# - feedback/pending/ cleared
# - feedback/integrated/ archives created
```

### Example 2: Quarterly Compression
```bash
# After 3 months and 15 integration sessions:
ls feedback/integrated/  # → 45 archived feedback files

# Notes file is getting long
wc -l modules/module_10_notes.md  # → 320 lines (was 80)

# Notice redundancy:
# - 3 warnings about land modification
# - 2 lessons about SSP2 testing
# - 4 examples of dependency chains

# Use compress command
command: compress-documentation

# Claude proposes:
# - Merge 3 land warnings → 1 comprehensive section (90 → 60 lines)
# - Merge 2 SSP2 lessons → 1 best practice (50 → 30 lines)
# - Organize 4 examples under "Common Patterns" (120 → 80 lines)
# Total: 320 → 240 lines (25% reduction)

# You approve, Claude applies changes

# Result:
# - module_10_notes.md is now 240 lines (more organized)
# - All unique insights preserved
# - Easier to navigate
```

### Example 3: What NOT to Do
```bash
# ❌ WRONG: Compressing before integrating
ls feedback/pending/module_10/  # → 5 new files
command: compress-documentation  # ← WRONG! Nothing to compress yet

# ✅ CORRECT: Integrate first, compress later
command: integrate-feedback all  # Process pending first
# ... wait for more feedback over weeks/months ...
command: compress-documentation  # Then compress when needed
```

---

## 🔍 How to Tell If You Need Compression

**Signs you need `command: compress-documentation`**:
- ✅ Multiple warnings saying similar things
- ✅ Lessons scattered across different sections
- ✅ Examples that could be grouped under patterns
- ✅ Notes file over 300 lines
- ✅ Hard to find specific warnings in the clutter

**Signs you DON'T need compression yet**:
- ❌ Notes file under 200 lines
- ❌ Each warning/lesson is unique
- ❌ Well-organized already
- ❌ Less than 10 integrated feedback items
- ❌ Less than 3 months since last compression

---

## 🚀 Best Practices

### For Integration (`command: integrate-feedback`):
1. **Do it regularly** (weekly or monthly) to avoid backlog
2. **Review the proposal** before approving (validate feedback)
3. **Check routing** (corrections → core docs, warnings → notes)
4. **Verify timestamps** are updated correctly

### For Compression (`command: compress-documentation`):
1. **Wait for accumulation** (10+ integrations before compressing)
2. **Review ALL proposals** carefully before approving
3. **Verify no information loss** (all unique insights preserved?)
4. **Check traceability** (feedback IDs still referenced?)

### General:
1. **Sequential workflow**: Always integrate before compressing
2. **Protect core docs**: Never compress `module_XX.md`
3. **Preserve insights**: Compression is reorganization, not deletion
4. **Trust the process**: Integration is automatic, compression requires judgment

---

## ⚠️ Common Mistakes

### Mistake 1: Compressing Before Integrating
```bash
# ❌ WRONG
command: compress-documentation  # Nothing integrated yet!

# ✅ CORRECT
command: integrate-feedback all  # Process pending feedback first
```

### Mistake 2: Over-Compressing
```bash
# ❌ WRONG: Compressing after every integration
command: integrate-feedback all
command: compress-documentation  # Too soon! Only 1 integration

# ✅ CORRECT: Compress quarterly or when bloated
command: integrate-feedback all  # Week 1
command: integrate-feedback all  # Week 2
# ... (weeks pass) ...
command: compress-documentation  # Month 3 - now it's worth it
```

### Mistake 3: Confusing the Commands
```bash
# ❌ WRONG: Using compress to add new feedback
# New feedback arrives...
command: compress-documentation  # This won't add it!

# ✅ CORRECT: Use integrate for new feedback
command: integrate-feedback all  # This adds new feedback
```

---

## 📚 Related Documentation

- `feedback/README.md` - Complete feedback system overview
- `feedback/pending/README.md` - Staged workflow details
- `.claude/commandscommand: integrate-feedback.md` - Integration command details
- `.claude/commandscommand: compress-documentation.md` - Compression command details
- `scripts/submit_feedback.sh` - How to submit feedback

---

## ❓ FAQ

**Q: Do I have to compress?**
A: No! Compression is optional. If notes stay organized, you can skip it.

**Q: How often should I integrate?**
A: Weekly or monthly, whenever feedback accumulates.

**Q: How often should I compress?**
A: Quarterly, or when notes feel bloated. Not every time.

**Q: Can I compress core docs (`module_XX.md`)?**
A: **NO!** Core docs contain facts verified against code. Only compress notes/lessons.

**Q: Will compression lose information?**
A: No! All unique insights are preserved. We merge redundant content, not delete it.

**Q: What if I'm not sure if I need compression?**
A: Check the "How to Tell" section above. When in doubt, wait - compression is optional.

**Q: Can I integrate and compress in one session?**
A: Yes, but integrate first, THEN compress (if needed).

---

**Remember**: `command: integrate-feedback` (weekly) adds new content. `command: compress-documentation` (quarterly) organizes accumulated content. They work together to keep documentation fresh AND readable.
