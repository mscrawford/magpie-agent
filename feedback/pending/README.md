# Pending Feedback Directory

**Purpose**: Staging area for user feedback before validation and integration

---

## 📂 Directory Structure

```
feedback/pending/
├── README.md                              ← You are here
└── YYYYMMDD_HHMMSS_type_target.md        ← Feedback files (flat structure)
```

**Feedback files use a flat structure** with timestamps and type in the filename.

**Example files**:
- `20251101_143022_warning_module_10.md`
- `20251102_091500_correction_module_52.md`
- `20251105_160830_lesson_module_70.md`
- `20251110_142200_global_agent_behavior.md`

---

## 🔄 Staged Feedback Workflow

### 1. **Submission** (Users)

```bash
./scripts/submit_feedback.sh
```

**Creates**: `feedback/pending/YYYYMMDD_HHMMSS_type_target.md`

**Core docs**: UNTOUCHED (remain stable)

**Benefits**:
- ✅ No barriers to feedback submission
- ✅ Core technical docs stay stable
- ✅ Feedback accumulates without disruption

---

### 2. **Validation & Integration** (Periodic, via `/integrate-feedback`)

**When**: Periodic sessions (weekly, monthly, or as needed)

**Command**:
```bash
/integrate-feedback all           # All pending feedback
/integrate-feedback               # Interactive mode
```

**Process**:
1. Read all pending feedback files
2. Validate against current code (is it still accurate?)
3. **Route by feedback type** (from YAML frontmatter):
   - `correction` → Update `module_XX.md` (fixes errors in core docs!)
   - `missing_content` → Update `module_XX.md` (adds missing content)
   - `warning` → Update `module_XX_notes.md` (user warnings)
   - `lesson_learned` → Update `module_XX_notes.md` (practical lessons)
   - `global` → Update global lessons or CLAUDE.md
4. Archive to `feedback/integrated/`
5. Update appropriate timestamps (Last Verified vs. Last Feedback Integration)
6. Delete from pending/

**Output**: Batch integration report

---

### 3. **Module Structure** (Separation of Concerns)

**Core Technical Docs** (`module_XX.md`):
- ✅ STABLE - changes when code changes OR user corrections applied
- Contains: Equations, parameters, interface variables
- Verified against: Actual GAMS source code
- Updated by: Code changes OR `correction`/`missing` feedback types
- Last Verified: [timestamp]

**User Experience Docs** (`module_XX_notes.md`):
- ⚡ DYNAMIC - updated during feedback integration
- Contains: Warnings, lessons learned, practical examples
- Updated by: `warning`/`lesson` feedback types
- Source: User feedback, real-world experience
- Last Feedback Integration: [timestamp]
- Pending feedback: [count] items in `feedback/pending/`

**Key Insight**: Type-based routing ensures corrections reach authoritative docs, preventing "notes purgatory"!

---

## 📝 Feedback File Naming

**Pattern**: `{YYYYMMDD}_{HHMMSS}_{type}_{target}.md`

**Types**:
- `warning` - Caution about common mistakes
- `lesson_learned` - Practical lessons from experience
- `correction` - Documentation error corrections
- `missing` - Information gaps in docs
- `global` - System-wide improvements

**Examples**:
- `20251101_143022_warning_module_10.md`
- `20251105_091530_lesson_learned_module_52.md`
- `20251110_160845_correction_module_70.md`
- `20251115_142200_global_agent_behavior.md`

---

## 🔍 Checking Pending Feedback

**Count pending items**:
```bash
# Count all pending feedback
ls feedback/pending/*.md 2>/dev/null | grep -v README.md | wc -l

# List all pending
ls feedback/pending/*.md 2>/dev/null | grep -v README.md
```

**Review pending items**:
```bash
./scripts/review_feedback.sh
```

---

## ⚙️ Integration Process Details

### Step 1: Read Pending Feedback
Agent reads all `.md` files in `pending/` (excluding README.md)

### Step 2: Validate
- Check if feedback still applies to current code
- Verify claims against actual GAMS source
- Flag outdated or incorrect feedback

### Step 3: Route by Feedback Type

**Read type from feedback YAML frontmatter**:
```yaml
---
type: correction | missing_content | warning | lesson_learned | global
target: module_XX.md
---
```

**Routing decision**:

**A. Corrections & Missing Content** → `module_XX.md` (core docs)
- **correction**: Fixes errors in equations, parameters, dependencies
- **missing**: Adds content that should have been in core docs
- Updates "Last Verified" timestamp
- Adds footnote: `*Updated YYYY-MM-DD based on user feedback*`

**B. Warnings & Lessons** → `module_XX_notes.md` (user experience)
- **warning**: Critical cautions about usage, modifications, pitfalls
- **lesson_learned**: Practical insights, best practices, real-world patterns
- Updates "Last Feedback Integration" timestamp
- Creates notes file if doesn't exist

**C. Global Feedback** → System-wide docs
- Updates `feedback/global/claude_lessons.md` or `CLAUDE.md`

**Why this matters**: Corrections reach authoritative docs instead of getting stuck in "notes purgatory"!

### Step 4: Integrate

**For type=correction or type=missing_content**:
- Use Edit tool to update `module_XX.md`
- Maintain module structure and verification standards
- Update "Last Verified" timestamp

**For type=warning or type=lesson_learned**:
- Create or update `module_XX_notes.md`
- Append to appropriate section (Warnings, Lessons, Examples)
- Update "Last Feedback Integration" timestamp

### Step 5: Archive
- Move to `feedback/integrated/YYYYMMDD_HHMMSS_module_XX_batch.md`
- Include integration report (what was added, what was skipped)
- Keep audit trail

### Step 6: Cleanup
- Remove files from `pending/module_XX/`
- Update module footer with integration timestamp

---

## 📐 Design Principles

### 1. **Separation of "Code Truth" vs. "User Experience"**

**Code Truth** (module_XX.md):
- What IS implemented in the code
- Verified against source
- Changes only when code changes
- Authoritative technical reference

**User Experience** (module_XX_notes.md):
- How code behaves in practice
- Common pitfalls and solutions
- Real-world examples
- Community knowledge

### 2. **Continuous Flow, Controlled Integration**

**Flow**: Users can submit feedback anytime → accumulates in pending/

**Control**: Periodic integration sessions with validation → maintains quality

**Benefits**:
- No submission barriers
- Quality control maintained
- Clear audit trail
- Batch efficiency

### 3. **Type-Based Routing** (Prevents "Notes Purgatory")

**Problem**: If ALL feedback goes to notes files, corrections never reach core docs!

**Solution**: Route by feedback type using existing `**Type**:` field:

```
correction/missing → module_XX.md (authoritative source gets fixed!)
warning/lesson     → module_XX_notes.md (user wisdom)
global             → system-wide docs (CLAUDE.md, claude_lessons.md)
```

**Result**: Corrections actually fix documentation errors instead of being buried in notes files.

### 4. **Explicit Status Tracking**

Every module knows:
- When it was last verified against code (module_XX.md footer)
- When feedback was last integrated (module_XX_notes.md header)
- How many pending items exist (link to pending/ directory)

---

## 🚨 Important Notes

### DO NOT Edit Pending Files Directly

**Why**: Pending files are submitted by users and should be preserved as-is until integration

**Instead**: Use `/integrate-feedback` to validate and integrate

### DO NOT Integrate Without Validation

**Why**: User feedback may become outdated as code evolves

**Always**:
1. Check feedback against current code
2. Verify claims are still accurate
3. Flag or skip outdated items

### DO Route Feedback by Type

**Type-based routing prevents errors**:

✅ **DO**:
- `correction` → module_XX.md (fixes errors in core docs)
- `missing` → module_XX.md (adds missing technical content)
- `warning` → module_XX_notes.md (user cautions)
- `lesson` → module_XX_notes.md (practical wisdom)

❌ **DON'T**:
- Put corrections in notes files (they won't fix the source!)
- Put warnings in core docs (mixes code truth with experience)
- Ignore the feedback type field (it determines routing!)

---

## ✅ Success Criteria

**This system is working when:**
- ✅ Users submit feedback easily (no friction)
- ✅ Core docs remain stable (unchanged unless code changes)
- ✅ Feedback gets integrated periodically (not immediately, not never)
- ✅ Integration includes validation (against current code)
- ✅ Clear timestamps show freshness (verification vs. integration dates)
- ✅ Audit trail exists (archived integrated feedback)

---

## 📚 Related Documentation

- `feedback/README.md` - Complete feedback system overview
- `feedback/WORKFLOW_GUIDE.md` - When to use which command
- `CONSOLIDATION_PLAN.md` - Phase 2, Task 2.1 details
- `CURRENT_STATE.json` - Project status
- `scripts/submit_feedback.sh` - Submission script
- `/integrate-feedback` command - Integration command
- `/compress-documentation` command - Compression command (use AFTER integration)

---

**Created**: 2025-10-26
**Purpose**: Enable continuous feedback flow with controlled, validated integration
**Principle**: Separate "code truth" (stable) from "user experience" (dynamic)
