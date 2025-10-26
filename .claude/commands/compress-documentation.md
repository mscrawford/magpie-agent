# Compress Documentation Command

**Purpose**: Consolidate accumulated feedback to reduce documentation bloat and improve organization

**When to use**: Quarterly, or when notes files feel verbose/redundant (AFTER multiple `/integrate-feedback` sessions)

**What it compresses**:
- ✅ `module_XX_notes.md` (user experience - warnings, lessons, examples)
- ✅ `CLAUDE.md` (agent instructions - if bloated)
- ✅ `feedback/global/claude_lessons.md` (global lessons)
- ❌ **NEVER** `module_XX.md` (core docs - facts are sacred!)

**What it does**:
- Identifies patterns and redundancy in integrated feedback
- Merges similar warnings/lessons into comprehensive versions
- Reorganizes scattered guidance into logical sections
- Preserves ALL unique insights (no information loss)

**Prerequisites**: You MUST have integrated feedback first (use `/integrate-feedback`)

---

## 🎯 Quick Start

```bash
/compress-documentation     # Analyze and compress integrated feedback
```

---

## ⚠️ CRITICAL: What Gets Compressed

**COMPRESS** (user experience, can be reorganized):
- ✅ `modules/module_XX_notes.md` - User warnings, lessons, examples
- ✅ `CLAUDE.md` - Agent behavioral guidance (if verbose)
- ✅ `feedback/global/claude_lessons.md` - System-wide lessons

**NEVER COMPRESS** (code truth, facts are sacred):
- ❌ `modules/module_XX.md` - Core technical documentation (verified against code)
- ❌ Equation formulas, parameter definitions, interface variables
- ❌ Any factual claims about what the code does

**Why this matters**: Code truth is immutable. Only user experience and guidance can be reorganized.

---

## Step 1: Identify Recent Feedback

Check which feedback has been integrated since last compression:

```bash
# Check compression metadata
if [ -f feedback/.compression_metadata.json ]; then
  cat feedback/.compression_metadata.json
else
  echo "No previous compression - will analyze all integrated feedback"
fi

# List all integrated feedback files
ls -lt feedback/integrated/
```

---

## Step 2: Analyze Patterns

Read all integrated feedback files that haven't been compressed yet, looking for:

### Common Themes:
- Repeated warnings about the same modules/concepts
- Multiple examples illustrating the same principle
- Redundant corrections to the same documentation sections
- Similar lessons learned from different users

### Documentation Bloat Indicators:
- CLAUDE.md sections growing too long (>500 lines for a section)
- Repetitive examples or warnings
- Overlapping guidance in multiple sections
- Verbose explanations that could be condensed

### Consolidation Opportunities:
- Multiple warnings → Single comprehensive warning with examples
- Scattered lessons → Unified best practice section
- Redundant corrections → Single authoritative statement
- Module-specific feedback → Cross-module pattern documentation

---

## Step 3: Generate Synthesis Proposal

For each consolidation opportunity, create a proposal showing:

```markdown
## Consolidation Proposal #1

**Theme**: Module 10 modification safety patterns

**Source Feedback Files**:
- feedback/integrated/20251015_warning_module_10_water.md
- feedback/integrated/20251018_lesson_module_10_carbon.md
- feedback/integrated/20251022_warning_module_10_dependencies.md

**Current State** (total: ~150 lines across 3 entries in module_10_notes.md):

⚠️ W001: Don't modify vm_land without checking water (20 lines)
💡 L005: Check carbon impacts when modifying land (30 lines)
⚠️ W007: Module 10 has 23 dependents - review all (40 lines)

**Proposed Change** (~60 lines consolidated):

⚠️ **CRITICAL: Module 10 Modification Safety** (W001, W007, L005)

Module 10 has **23 dependents** including water (Module 42), costs (Module 11), and carbon (Module 52).

**Before modifying**:
1. Check Phase2_Module_Dependencies.md for full dependency list
2. Review modification_safety_guide.md (Module 10 section)
3. Verify impact on conservation laws (especially land and water)

**Common cascading effects**:
- vm_land changes → water allocation (Module 42)
- vm_land changes → carbon stocks (Module 52)
- vm_land changes → total costs (Module 11)

See feedback W001, W007, L005 for detailed incidents.

**Files Affected**:
- modules/module_10_notes.md: Section "Warnings & Common Mistakes" (lines 45-195 → 45-105)

**Impact**:
- Line reduction: ~150 lines → ~60 lines (60% reduction)
- Clarity improvement: Scattered warnings unified into single actionable checklist
- Preserves all unique insights: W001 water details, W007 dependency count, L005 carbon impacts
- Improves navigation: Single "modification safety" section instead of 3 separate entries

**Verification**: All original feedback IDs (W001, W007, L005) remain referenced in consolidated version
```

---

## Step 4: Present to User

**CRITICAL**: Before making ANY changes, show the user:

### 1. Summary Statistics:
```
📊 Compression Analysis Summary:

Integrated feedback analyzed: 12 files
Compression opportunities: 4
Potential line reduction: ~220 lines (35%)
Files affected:
  - modules/module_10_notes.md
  - modules/module_70_notes.md
  - feedback/global/claude_lessons.md

Themes identified:
  - Module 10 modification safety: 3 feedback files
  - SSP2 testing best practices: 3 feedback files
  - Livestock feed basket lessons: 2 feedback files
  - GAMS debugging patterns: 4 feedback files
```

### 2. All Consolidation Proposals (detailed view from Step 3)

### 3. Ask for Approval:
```
May I proceed with these consolidations?

Options:
1. Approve all
2. Approve selected proposals (specify which)
3. Reject (no changes)
4. Request revisions (explain)
```

---

## Step 5: Apply Changes (ONLY if approved)

For each approved proposal:

### 5a. Backup current state
```bash
# Create backup branch
git checkout -b backup-pre-compression-$(date +%Y%m%d_%H%M%S)
git checkout develop  # or current branch
```

### 5b. Update documentation files
Use Edit tool to replace scattered content with consolidated version

**Example** (module_10_notes.md):
```markdown
# BEFORE (150 lines, 3 separate warnings)
## ⚠️ Warnings & Common Mistakes

### W001: Water Impact (2025-10-15)
[20 lines of content]

### W007: Dependency Chain (2025-10-22)
[40 lines of content]

## 💡 Lessons Learned

### L005: Carbon Effects (2025-10-18)
[30 lines of content]

# AFTER (60 lines, 1 consolidated warning)
## ⚠️ Warnings & Common Mistakes

### CRITICAL: Module 10 Modification Safety (W001, W007, L005)
[60 lines of consolidated, organized content]
```

### 5c. Update compression metadata
```bash
# Create/update feedback/.compression_metadata.json
{
  "last_compression_date": "2025-10-26",
  "compression_id": "compress_20251026_150000",
  "compressed_feedback": [
    "20251015_warning_module_10_water.md",
    "20251018_lesson_module_10_carbon.md",
    "20251022_warning_module_10_dependencies.md"
  ],
  "consolidations": [
    {
      "theme": "Module 10 modification safety",
      "source_files": ["20251015_warning_module_10_water.md", "20251022_warning_module_10_dependencies.md"],
      "target_files": ["modules/module_10_notes.md"],
      "line_reduction": 90
    },
    {
      "theme": "SSP2 testing best practices",
      "source_files": ["20251016_lesson_ssp2_testing.md", "20251019_lesson_ssp2_stability.md"],
      "target_files": ["feedback/global/claude_lessons.md"],
      "line_reduction": 60
    }
  ],
  "total_line_reduction": 220,
  "compression_count": 1
}
```

### 5d. Add compression markers to integrated feedback
Add footer to each compressed feedback file:
```markdown
---
**COMPRESSION STATUS**: ✅ Compressed into modules/module_10_notes.md
**Compression ID**: compress_20251026_150000
**Consolidated with**: W001, W007, L005
**Theme**: Module 10 modification safety
```

### 5e. Commit everything together
```bash
git add -A
git commit -m "Compress feedback: Module 10 safety, SSP2 testing, livestock lessons

Analyzed 12 integrated feedback files
Created 4 consolidations reducing ~220 lines (35%)

Themes addressed:
- Module 10 modification safety (W001, W007, L005)
- SSP2 testing best practices (L008, L012, L014)
- Livestock feed basket lessons (L002, L009)
- GAMS debugging patterns (4 feedback items)

Files updated:
- modules/module_10_notes.md (warnings consolidated)
- modules/module_70_notes.md (lessons unified)
- feedback/global/claude_lessons.md (testing patterns added)

All original feedback preserved with compression markers.
Compression ID: compress_20251026_150000"

git push
```

---

## Step 6: Compression Summary

After completing compression:

```markdown
✅ Compression Complete

**Integrated feedback analyzed**: 12 files
**Consolidations created**: 4
**Line reduction**: ~220 lines (35% reduction)

**Files modified**:
- modules/module_10_notes.md (3 warnings → 1 comprehensive safety section)
- modules/module_70_notes.md (2 lessons → 1 unified best practice)
- feedback/global/claude_lessons.md (3 scattered lessons → 1 testing guide)

**Compression metadata**:
- Compression ID: compress_20251026_150000
- Metadata file: feedback/.compression_metadata.json

**Quality metrics**:
- ✅ All unique insights preserved
- ✅ All feedback IDs traceable
- ✅ Documentation more organized
- ✅ Reduced redundancy without information loss

**Next compression recommended**: After ~10 more feedback integrations (or quarterly)
```

---

## 📋 Compression Patterns

### Pattern 1: Multiple Warnings → Unified Warning Section

**Before** (3 separate warnings in module_10_notes.md, 90 lines):
```markdown
⚠️ W001: Don't modify vm_land without checking water (30 lines)
⚠️ W003: Module 10 has 23 dependents (20 lines)
⚠️ W007: Land allocation changes cascade to Module 42 (40 lines)
```

**After** (consolidated, 60 lines):
```markdown
⚠️ **CRITICAL: Module 10 Modification Safety** (W001, W003, W007)

Module 10 has **23 dependents** including water (Module 42), costs (Module 11), and carbon (Module 52).

**Before modifying**:
1. Check Phase2_Module_Dependencies.md for full dependency list
2. Review modification_safety_guide.md (Module 10 section)
3. Verify impact on conservation laws (especially land and water)

**Common cascading effects**:
- vm_land changes → water allocation (Module 42)
- vm_land changes → carbon stocks (Module 52)
- vm_land changes → total costs (Module 11)

See feedback W001, W003, W007 for detailed incidents.
```

**Result**: 30% reduction, improved clarity, all unique insights preserved

### Pattern 2: Scattered Lessons → Best Practice Section

**Before** (lessons in multiple module notes files, 120 lines total):
```markdown
# In module_70_notes.md
💡 L001: Use SSP2 feed baskets for testing (40 lines)

# In module_14_notes.md
💡 L005: SSP2 scenarios are most stable (35 lines)

# In module_17_notes.md
💡 L009: Start testing with SSP2 baseline (45 lines)
```

**After** (in feedback/global/claude_lessons.md, 70 lines):
```markdown
## Testing Best Practices (L001, L005, L009)

**Default scenario for testing**: SSP2 baseline
- Most stable across modules (70, 14, 17)
- Well-balanced parameterization
- Good for verifying modifications work

**Progressive testing approach**:
1. SSP2 baseline (stability check)
2. SSP5 (high-demand stress test)
3. SSP1 (sustainability scenario)

**Module-specific notes**:
- Module 70 (Livestock): SSP2 feed baskets well-calibrated
- Module 14 (Yields): SSP2 tau factors stable
- Module 17 (Production): SSP2 provides good baseline

See module_70_notes.md (L001), module_14_notes.md (L005), module_17_notes.md (L009).
```

**Result**: 42% reduction, cross-module pattern identified, actionable guidance

---

## 🎨 Compression Principles

### Preserve Integrity

**NEVER lose information**:
- ✅ Consolidate redundant warnings into comprehensive version
- ✅ Merge similar examples while preserving unique details
- ✅ Reference all original feedback IDs in consolidated version
- ❌ Delete unique insights even if they seem minor
- ❌ Remove warnings even if they seem obvious

### Maximize Clarity

**Make documentation MORE useful**:
- ✅ Organize scattered guidance into logical sections
- ✅ Create clear hierarchies (general principle → specific examples)
- ✅ Add cross-references between related topics
- ✅ Use consistent formatting and structure
- ❌ Create dense walls of text
- ❌ Bury important warnings in verbose sections

### Maintain Traceability

**Every claim must be traceable**:
- ✅ Include feedback IDs in consolidated sections (W001, L005, etc.)
- ✅ Mark which feedback contributed which insights
- ✅ Preserve attribution when useful (e.g., "User X discovered...")
- ✅ Keep compression metadata for future reference

---

## ⚠️ Anti-Patterns (DON'T DO THIS)

### ❌ Over-Compression

**DON'T**: Merge unrelated feedback just to reduce lines
```markdown
⚠️ Module 10 is complex and water matters and also check carbon and test with SSP2
```

**DO**: Keep distinct topics separate even if they reference same module

### ❌ Losing Context

**DON'T**: Remove the "why" when consolidating
```markdown
⚠️ Don't modify Module 10
```

**DO**: Preserve reasoning and consequences
```markdown
⚠️ Don't modify Module 10 without dependency analysis - affects 23 modules including water/carbon/costs
```

### ❌ Compressing Core Docs

**DON'T**: Touch module_XX.md during compression
```markdown
# modules/module_10.md
## Equations (consolidated for brevity)  ← WRONG!
```

**DO**: Only compress notes/lessons/guidance
```markdown
# modules/module_10_notes.md
## Warnings & Common Mistakes (consolidated)  ← CORRECT!
```

---

## 🔍 Quality Checklist

Before completing compression:
- [ ] All unique insights preserved?
- [ ] Warnings still prominent?
- [ ] Examples still actionable?
- [ ] Cross-references updated?
- [ ] Feedback IDs traceable?
- [ ] Line count actually reduced?
- [ ] Documentation more readable?
- [ ] No information lost?
- [ ] NO changes to module_XX.md (core docs)?
- [ ] ONLY changes to module_XX_notes.md, CLAUDE.md, global lessons?
- [ ] Compression metadata complete?
- [ ] User approved changes?

---

## 🚀 Expected Outcomes

✅ **Reduced Bloat**: Notes files and agent guidance more concise
✅ **Improved Clarity**: Related feedback organized into coherent sections
✅ **Maintained Integrity**: All unique warnings/lessons/corrections preserved
✅ **Better Navigation**: Clear sections instead of scattered items
✅ **Traceable History**: Compression metadata links back to original feedback
✅ **Core Docs Untouched**: module_XX.md remains factually accurate
✅ **Continued Evolution**: System ready for next batch of feedback

---

## 📚 What's Next?

**After compression, you can**:
1. ✅ Continue using the improved documentation
2. ⏸️ Wait for more feedback to accumulate
3. 🔄 Eventually run `/integrate-feedback` again (when new feedback arrives)

**The workflow is**:
```
Submit feedback → /integrate-feedback (weekly) → [Repeat] →
/compress-documentation (quarterly) → [Repeat integration]
```

**Compression frequency**: Only when needed (quarterly or when bloat is noticeable)

---

## 📚 Related Documentation

- `feedback/README.md` - Complete feedback system overview
- `feedback/WORKFLOW_GUIDE.md` - When to use which command
- `/integrate-feedback` - Integration command (use BEFORE compression)
- `CONSOLIDATION_PLAN.md` - Phase 2, Task 2.1
- `scripts/submit_feedback.sh` - Submission script

---

**Remember**: Quality and completeness always trump brevity. The goal is to make documentation MORE useful, not just reduce line count. And NEVER compress core technical documentation (module_XX.md) - facts are sacred!
