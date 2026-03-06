# Feedback Compression Quick Start Guide

## 🎯 What is Feedback Compression?

As the MAgPIE agent receives feedback and improves, documentation files (AGENT.md, module notes, etc.) can grow too long. **Compression** synthesizes integrated feedback into streamlined documentation while preserving all unique insights.

**Goal**: Keep docs concise and navigable WITHOUT sacrificing the integrity of user feedback.

---

## 📊 When to Run Compression

### Indicators You Need Compression:

- ✅ AGENT.md sections exceeding 500 lines
- ✅ Multiple warnings/lessons about the same topic
- ✅ Feedback accumulation > 20-30 integrated items
- ✅ Documentation feeling repetitive or verbose
- ✅ Users complaining docs are "too long to read"

### Recommended Frequency:

- **After major feedback batches** (10+ items integrated)
- **Monthly maintenance** if actively collecting feedback
- **Before releases** to ensure docs are streamlined
- **When requested** by documentation maintainers

---

## 🚀 Quick Workflow (5 Steps)

### Step 1: Check Status
```bash
./scripts/compress_feedback.sh status
```

**Output shows:**
- How many integrated feedback files exist
- How many have been compressed vs. pending
- Last compression date
- Current documentation state

### Step 2: Review Pending Items
```bash
./scripts/compress_feedback.sh list
```

**Output shows:**
- ✓ Files already compressed (green)
- ○ Files needing compression (yellow)

### Step 3: Create Backup
```bash
./scripts/compress_feedback.sh backup
```

**Creates:** `backup-pre-compression-YYYYMMDD_HHMMSS` branch
**Safety:** Easy rollback if compression has issues

### Step 4: Run AI Compression

**Tell your AI assistant:**
```
/compress-documentation
```

**The AI will:**
1. Read all uncompressed feedback
2. Identify patterns and themes
3. Generate consolidation proposals
4. Show you EXACTLY what will change
5. Ask for your approval

**CRITICAL**: Review proposals carefully! The AI shows before/after for each change.

### Step 5: Verify Results

**Check:**
- Documentation is more concise
- No information lost
- Warnings still prominent
- Cross-references updated
- Compression metadata created

**If issues found:**
```bash
git checkout backup-pre-compression-YYYYMMDD_HHMMSS
```

---

## 📋 Example Compression Session

### Before Compression:

**Files analyzed:** 25 integrated feedback items

**Found themes:**
- Module 10 safety warnings (5 items)
- SSP2 testing recommendations (3 items)
- Chapman-Richards corrections (4 items)
- Water allocation warnings (3 items)

**Current state:**
- AGENT.md: 1,200 lines (Section "Warnings" has 400 lines)
- module_10_notes.md: 350 lines (8 separate warnings)
- module_52_notes.md: 200 lines (4 corrections about same equation)

### AI Proposals:

**Proposal #1: Consolidate Module 10 Warnings**
- Source: 8 separate warnings (W001, W003, W005, W007, W009, W012, W015, W018)
- Target: Single "Module 10 Modification Safety" section
- Reduction: ~150 lines → ~60 lines (60% reduction)
- Preserves: All unique dependency chains, all examples

**Proposal #2: Unify SSP2 Testing Guidance**
- Source: 3 lessons scattered across module_70, module_14, module_17 notes
- Target: New "Testing Best Practices" section in AGENT.md
- Reduction: ~80 lines → ~30 lines (63% reduction)
- Preserves: All scenario comparisons, all stability notes

**Proposal #3: Chapman-Richards Single Truth**
- Source: 4 corrections (C001, C008, C012, C015)
- Target: Update module_52.md main doc, add historical note
- Reduction: ~70 lines → ~15 lines (79% reduction)
- Preserves: Attribution to original reporters

### User Review:

```
You are shown each proposal with:
- Exact before/after text
- Line reduction metrics
- List of preserved unique insights
- Files that will be modified

Approve? [y/n/partial]
```

### After Compression:

**Results:**
- Total reduction: ~300 lines → ~105 lines (65% overall)
- Files modified: AGENT.md, module_10_notes.md, module_52.md, AGENT.md
- Unique insights preserved: 42 (100%)
- Feedback items marked compressed: 25
- Metadata created: `.compression_metadata.json`

**Quality check:**
- ✅ All warnings still prominent
- ✅ Examples consolidated but not removed
- ✅ Cross-references updated
- ✅ Traceability maintained (feedback IDs)
- ✅ Documentation MORE readable

---

## 🛡️ Safety Guarantees

### What Compression NEVER Does:

❌ **Delete unique information** - Every unique insight preserved
❌ **Remove critical warnings** - Warnings remain prominent
❌ **Lose attribution** - Feedback IDs always referenced
❌ **Break traceability** - Original feedback files marked, not deleted
❌ **Proceed without approval** - User MUST approve all changes

### What Compression ALWAYS Does:

✅ **Create backup branch** - Easy rollback
✅ **Show before/after** - Complete transparency
✅ **Preserve uniqueness** - All distinct insights kept
✅ **Maintain IDs** - Feedback references traceable
✅ **Improve readability** - Better organization

---

## 📊 Compression Metadata

After compression, `.compression_metadata.json` tracks:

```json
{
  "last_compression_date": "2025-10-26",
  "compression_id": "compress_20251026_143022",
  "compressed_feedback": [
    "20251024_120000_warning_module_10.md",
    "20251024_130000_lesson_module_10.md"
  ],
  "consolidations": [
    {
      "theme": "Module 10 modification safety",
      "source_files": ["W001", "W003", "W005"],
      "target_files": ["module_10_notes.md"],
      "line_reduction": 150
    }
  ],
  "total_line_reduction": 300,
  "compression_count": 1
}
```

**Purpose:**
- Track what's been compressed (avoid re-processing)
- Record consolidation decisions
- Measure impact (line reduction)
- Enable traceability

---

## 🎯 Best Practices

### DO:
- ✅ Run compression regularly (monthly or after 10+ items)
- ✅ Review proposals carefully before approving
- ✅ Create backup branch first
- ✅ Test documentation after compression
- ✅ Keep compression metadata in version control

### DON'T:
- ❌ Skip reviewing proposals ("just approve everything")
- ❌ Compress without backup
- ❌ Delete original feedback files (they're marked, not removed)
- ❌ Over-compress (some redundancy is okay for emphasis)
- ❌ Compress too aggressively (quality > brevity)

---

## 🔍 Troubleshooting

### Issue: "Compression metadata not found"
**Solution:**
```bash
./scripts/compress_feedback.sh init
```

### Issue: "Too aggressive - lost important detail"
**Solution:**
```bash
# Rollback to backup
git checkout backup-pre-compression-YYYYMMDD_HHMMSS

# Re-run with more conservative approach
# Review individual proposals more carefully
```

### Issue: "Compression didn't reduce much"
**Possible reasons:**
- Feedback already well-organized
- Not enough redundancy to consolidate
- Most items are unique (good!)

**Action:** This is fine! Not every compression yields big reductions.

### Issue: "Can't find original feedback after compression"
**Solution:**
Original files are in `feedback/integrated/` with compression markers:
```markdown
---
**COMPRESSION STATUS**: ✅ Compressed into [files]
**Compression ID**: compress_YYYYMMDD_HHMMSS
```

---

## 📚 See Also

- `agent/commands/compress-documentation.md` - Complete workflow details
- `feedback/README.md` - Feedback system overview
- `scripts/compress_feedback.sh` - Helper script reference
- `AGENT.md` - Agent behavior documentation

---

## 💡 Philosophy

**Compression is NOT about deleting feedback.**

It's about **organizing** accumulated knowledge into **coherent, navigable documentation** while **preserving every unique insight** contributed by users.

**Good compression makes docs:**
- ✅ Easier to navigate
- ✅ Faster to read
- ✅ More actionable
- ✅ Better organized

**...WITHOUT sacrificing:**
- ❌ Completeness
- ❌ Accuracy
- ❌ Attribution
- ❌ Traceability

---

**Happy compressing! 🗜️**
