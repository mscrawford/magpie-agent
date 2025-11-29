# Integrate Feedback Command

**Purpose**: Validate and integrate pending user feedback into module documentation

**When to use**: Weekly or monthly, whenever feedback accumulates in `feedback/pending/`

**What it does**:
- Validates pending feedback against current code
- Routes corrections → `module_XX.md` (fixes errors)
- Routes warnings/lessons → `module_XX_notes.md` (user experience)
- Archives integrated feedback for later compression

**What it does NOT do**: Compress or consolidate documentation (use `command: compress-documentation` for that)

---

## 🎯 Quick Start

```bash
command: integrate-feedback module_10     # Single module
command: integrate-feedback all           # All pending feedback
command: integrate-feedback               # Interactive mode
```

---

## Step 1: Scan Pending Feedback

```bash
# List pending feedback (flat structure in pending/)
ls feedback/pending/*.md 2>/dev/null | grep -v README.md

# Count pending items
ls feedback/pending/*.md 2>/dev/null | grep -v README.md | wc -l
```

**Present to user**:
```
📊 Pending Feedback Summary:

Found 4 pending feedback items:
- 20251101_warning_module_10_land.md
- 20251102_correction_module_52_carbon.md
- 20251105_lesson_module_70_feed.md
- 20251110_global_agent_behavior.md

Total: 4 pending items
```

---

## Step 2: Validate Each Feedback Item

For each pending feedback file:

### 2a. Read the feedback
```bash
cat feedback/pending/20251101_warning_module_10_land.md
```

### 2b. Validate against current code
- Check if the module code still exists at referenced location
- Verify equation names/numbers are current
- Confirm parameter names are accurate
- Flag outdated or incorrect claims

### 2c. Determine target file based on feedback type

**Extract type from feedback header** (in YAML frontmatter):
```yaml
---
type: correction | missing_content | warning | lesson_learned | global
target: module_XX.md
---
```

**Routing logic**:
```
correction      → modules/module_XX.md (fixes errors in core docs)
missing_content → modules/module_XX.md (adds missing content to core docs)
warning         → modules/module_XX_notes.md (user warnings and cautions)
lesson_learned  → modules/module_XX_notes.md (practical insights)
global          → feedback/global/agent_lessons.md (system-wide lessons)
```

**Why this matters**:
- **Corrections and missing content** fix errors or gaps in authoritative documentation
- **Warnings and lessons** capture user experience and practical wisdom
- This prevents "notes purgatory" - corrections actually fix the source docs!

### 2d. Categorize validation status
- **Valid**: Feedback applies to current code
- **Outdated**: Code has changed, feedback needs updating
- **Incorrect**: Feedback contains errors

**Flag issues**:
```markdown
✅ VALID: Feedback applies to current code
⚠️  OUTDATED: Code has changed, feedback needs updating
❌ INCORRECT: Feedback contains errors
```

---

## Step 3: Integration Proposal

Present consolidated integration plan to user:

```markdown
## Integration Proposal: Module 10

**Pending items**: 4
**Valid**: 3
**Outdated**: 1 (will skip with note)
**Incorrect**: 0

### Item 1: 20251101_correction_module_10_dependency.md
**Status**: ✅ VALID
**Type**: correction
**Target**: modules/module_10.md (core documentation)
**Section**: Dependencies section
**Action**: Update dependency count from 23 → 24 dependents
**Summary**: Module 80 now consumes vm_land, increasing dependent count

### Item 2: 20251102_warning_module_10_land.md
**Status**: ✅ VALID
**Type**: warning
**Target**: modules/module_10_notes.md (user experience)
**Section**: Warnings & Common Mistakes
**Action**: Add warning about land balance infeasibility
**Summary**: Land balance infeasibility when modifying vm_land bounds

### Item 3: 20251105_lesson_module_10_age_class.md
**Status**: ✅ VALID
**Type**: lesson
**Target**: modules/module_10_notes.md (user experience)
**Section**: Lessons Learned
**Action**: Add lesson about age class distribution
**Summary**: Age class distribution affects carbon calculations

### Item 4: 20251103_correction_module_10_equation.md
**Status**: ⚠️ OUTDATED
**Reason**: Equation was fixed in recent code update
**Action**: Skip integration, archive with note

---

**Integration changes**:
- Update: modules/module_10.md (1 correction applied)
- Createcommand: update: modules/module_10_notes.md (1 warning, 1 lesson added)
- Archive to: feedback/integrated/20251026_batch_module_10.md
- Update timestamps:
  - module_10.md: Last Verified: 2025-10-26
  - module_10_notes.md: Last Feedback Integration: 2025-10-26

Proceed with integration? [y/n/revise]
```

---

## Step 4: Execute Integration (if approved)

### 4a. Update module_XX.md (for corrections and missing content)

**For type=correction**:
- Use Edit tool to fix the error in module_XX.md
- Update "Last Verified" timestamp
- Add footnote: `*Updated 2025-10-26 based on user feedback*`

**Example correction**:
```markdown
## Dependencies

Module 10 is consumed by **24 modules** (updated 2025-10-26):
- Module 11 (Costs): Uses vm_land for cost aggregation
- Module 42 (Water Demand): Uses vm_land for irrigation demand
...

*Dependency count updated 2025-10-26 based on user feedback (Module 80 added)*
```

**For type=missing**:
- Use Edit tool to add missing content to appropriate section
- Maintain module doc structure and style
- Update "Last Verified" timestamp

### 4b. Create or update module_XX_notes.md (for warnings and lessons)

If file doesn't exist, create with template:

```markdown
# Module XX Notes - User Experience & Lessons

**Last Feedback Integration**: 2025-10-26
**Pending feedback**: 0 items
**Source**: User feedback and real-world experience

---

## ⚠️ Warnings & Common Mistakes

[Integrated warnings]

---

## 💡 Lessons Learned

[Integrated lessons]

---

## 🧪 Real-World Examples

[Integrated examples]
```

If file exists, append to appropriate section:

```markdown
## ⚠️ Warnings & Common Mistakes

### Land Balance Infeasibility (2025-11-01)
[Warning content from pending feedback]
**Source**: feedback 20251102_warning_module_10_land
**Contributed by**: [optional - username if available]
```

**Optional Attribution**:
- If feedback file includes author/contributor information, you MAY add attribution
- Format: `**Contributed by**: [username] via feedback #ID`
- Benefit: Recognition encourages continued participation
- When to use: Only if user explicitly provides their name/identifier
- When to skip: Anonymous submissions or if unclear who submitted

### 4c. Archive integrated feedback

Create batch archive:
```bash
# Archive file: feedback/integrated/20251026_150000_batch_module_10.md
```

Content:
```markdown
# Batch Integration: Module 10
**Date**: 2025-10-26 15:00:00
**Items integrated**: 2
**Items skipped**: 1
**Target**: modules/module_10_notes.md

---

## Integrated Items

### 1. 20251102_warning_module_10_land.md
**Status**: ✅ Integrated
**Section**: Warnings & Common Mistakes
[Original feedback content]

### 2. 20251105_lesson_module_10_age_class.md
**Status**: ✅ Integrated
**Section**: Lessons Learned
[Original feedback content]

---

## Skipped Items

### 3. 20251103_correction_module_10_equation.md
**Status**: ⚠️ Outdated
**Reason**: Dependency count changed 23→24
[Original feedback content]
```

### 4d. Remove from pending
```bash
rm feedback/pending/20251102_warning_module_10_land.md
rm feedback/pending/20251105_lesson_module_10_age_class.md
rm feedback/pending/20251103_correction_module_10_equation.md
```

### 4e. Update module footers

**For module_XX.md** (if corrections or missing content applied):
```markdown
---
**Last Verified**: 2025-10-26 (updated with user corrections)
```

**For module_XX_notes.md** (if warnings or lessons added):
```markdown
---
**Last Verified**: [When Module XX code was last verified]
**Last Feedback Integration**: 2025-10-26
**Pending feedback**: 0 items in feedback/pending/
```

---

## Step 5: Batch Summary

After processing all modules:

```markdown
✅ Integration Complete

**Modules processed**: 3 (10, 52, 70)
**Items integrated**: 6
**Items skipped**: 2
**Notes files created**: 2 (module_52_notes.md, module_70_notes.md)
**Notes files updated**: 1 (module_10_notes.md)

**Files modified**:
- modules/module_10_notes.md (2 warnings, 1 lesson added)
- modules/module_52_notes.md (created, 1 example added)
- modules/module_70_notes.md (created, 2 lessons added)

**Archives created**:
- feedback/integrated/20251026_150000_batch_module_10.md
- feedback/integrated/20251026_150005_batch_module_52.md
- feedback/integrated/20251026_150010_batch_module_70.md

**Pending feedback remaining**: 1 global item

Next step: Feedback is integrated! Come back later and use command: compress-documentation
to consolidate accumulated feedback and reduce bloat.
```

---

## Step 6: Deploy Changes (CRITICAL)

**After integration is complete, you MUST deploy the changes to the parent directory.**

```bash
# Run the update command to sync changes to parent
command: update
```

**Why?** The integration only updates files in the `magpie-agent` repo. The `command: update` command copies them to the parent `magpie` directory so the agent can actually use them.

---

## 🎨 Integration Principles

### Validate Before Integrating

**NEVER blindly integrate**:
- ✅ **Prove it**: Use `grep` or `read_file` to find the specific code referenced
- ✅ Check feedback against current code
- ✅ Verify equation names/numbers are current
- ✅ Confirm parameter names are accurate
- ✅ Flag and skip outdated items
- ❌ Integrate without validation

### Preserve User Voice

**Keep original phrasing when valuable**:
- ✅ "I discovered that..." gives context
- ✅ Specific incident reports are valuable
- ✅ Real-world examples resonate
- ❌ Don't sanitize everything to "official" tone

### Separate Code Truth from Experience

**module_XX.md** (Code Truth):
- ONLY verified technical facts
- Changes when code changes
- Last Verified: [date]

**module_XX_notes.md** (User Experience):
- Warnings, lessons, examples
- Changes when feedback integrated
- Last Feedback Integration: [date]

---

## ⚠️ Anti-Patterns (DON'T DO THIS)

### ❌ Integrating Without Validation

**DON'T**: Copy pending feedback to notes without checking code
```markdown
⚠️ Module 10 has 23 dependents  ← May be outdated!
```

**DO**: Validate first, skip if outdated
```markdown
✅ Validated against Module_Dependencies.md (24 dependents as of 2025-10-26)
```

---

## 🔍 Quality Checklist

Before completing integration:
- [ ] All pending feedback validated against current code?
- [ ] Outdated items flagged and skipped?
- [ ] Type-based routing applied correctly?
- [ ] Corrections went to module_XX.md?
- [ ] Warnings/lessons went to module_XX_notes.md?
- [ ] Timestamps updated?
- [ ] Feedback archived with proper metadata?
- [ ] User approved integration plan?

---

## 🚀 Expected Outcomes

✅ **Pending feedback cleared**: Moved to integrated/ with validation
✅ **Core docs updated**: Corrections fix errors in module_XX.md
✅ **Notes files updated**: Warnings/lessons added to module_XX_notes.md
✅ **Code truth separation maintained**: Facts vs. experience clearly separated
✅ **Timestamps current**: Integration dates reflect latest batch
✅ **Audit trail**: Archived feedback shows what was integrated when

---

## 📚 What's Next?

**After integration, you can**:
1. ✅ Continue using the documentation (feedback is now integrated!)
2. ⏸️ Wait for more feedback to accumulate (weeks/months)
3. 🗜️ Eventually run `command: compress-documentation` when notes feel bloated

**The workflow is**:
```
Submit feedback → command: integrate-feedback (weekly) → [Repeat] →
command: compress-documentation (quarterly) → [Repeat]
```

---

## 📚 Related Documentation

- `feedback/README.md` - Complete feedback system overview
- `feedback/pending/README.md` - Staged workflow details
- `feedback/WORKFLOW_GUIDE.md` - When to use which command
- `command: compress-documentation` - Consolidation command (use AFTER integration)
- `scripts/submit_feedback.sh` - Submission script

---

**Remember**: This command integrates individual feedback items. It does NOT compress or consolidate. Use `command: compress-documentation` for that (after multiple integration sessions).
