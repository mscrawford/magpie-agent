# Feedback Status Tracking System - Design

**Problem**: Users submit feedback but have no visibility into whether it was integrated, when, or if rejected.

**Goal**: Make feedback lifecycle transparent from submission through integration.

---

## 📊 Proposed Solution: Multi-Level Tracking

### Level 1: File-Based Status (Immediate - No Code Changes)

**Add status footer to archived feedback files**:

```markdown
---
**INTEGRATION STATUS**: ✅ Integrated | ⚠️ Outdated | ❌ Rejected | ⏸️ Deferred
**Integration Date**: 2025-10-26
**Integrated Into**: modules/module_10_notes.md (lines 45-60)
**Feedback ID**: 20251101_warning_land_infeasibility
**Contributed by**: [username if available]
**Validation Notes**: [why integrated, rejected, or deferred]
```

**Benefits**:
- ✅ Simple - just append footer during integration
- ✅ Traceable - every feedback file has clear status
- ✅ Git history - users can see status in repo
- ❌ Requires users to check integrated/ directory

---

### Level 2: Status Command (Easy Addition)

**Create `command: feedback-status` command** (or enhance existing `command: feedback`):

```bash
run command: feedback-status
# Or
run command: feedback status
```

**Output**:
```
📊 Feedback Status Summary

📝 **Your pending feedback**: 3 items
  - module_10/warning_land_2025-10-24.md (waiting)
  - module_70/lesson_ssp2_2025-10-25.md (waiting)
  - global/improvement_routing_2025-10-26.md (waiting)

✅ **Recently integrated**: 2 items
  - module_52/correction_equation_2025-10-15.md → integrated 2025-10-22
  - module_10/warning_water_2025-10-18.md → integrated 2025-10-22

⏱️ **Next integration**: Typically weekly/monthly (check with maintainer)

Run `command: feedback status module_10` for details on specific module
```

**Benefits**:
- ✅ Quick overview of all feedback
- ✅ Shows what's pending vs integrated
- ✅ Easy to implement (just list files + check archives)
- ❌ Still requires checking command

---

### Level 3: Integration Report (Medium Effort)

**Automatically generate integration report after `command: integrate-feedback`**:

**File**: `feedback/integrated/INTEGRATION_REPORT_2025-10-26.md`

```markdown
# Integration Report: 2025-10-26

**Modules processed**: 3 (10, 52, 70)
**Items integrated**: 6
**Items skipped**: 2

---

## ✅ Integrated

### Module 10 (Land)

**Feedback #1**: warning_land_infeasibility_2025-10-24.md
- **Type**: Warning
- **Status**: ✅ Integrated
- **Target**: modules/module_10_notes.md (lines 45-60)
- **Contributed by**: [username]
- **Summary**: Warning about land balance infeasibility when modifying bounds

**Feedback #2**: correction_dependency_count_2025-10-20.md
- **Type**: Correction
- **Status**: ✅ Integrated
- **Target**: modules/module_10.md (line 123)
- **Contributed by**: [username]
- **Summary**: Updated dependency count from 23 → 24

### Module 52 (Carbon)

...

---

## ⚠️ Skipped

**Feedback #7**: correction_equation_typo_2025-10-15.md
- **Reason**: Outdated - equation already fixed in recent code update
- **Archived**: feedback/integrated/20251026_outdated_module_52.md

---

## 📬 Notify Contributors

**If contributors have email/GitHub usernames** (optional):
- @user1: 2 items integrated (module_10: warning, correction)
- @user2: 1 item integrated (module_52: lesson)
- @user3: 1 item skipped (outdated)

---

**Next integration**: Typically in 1-4 weeks
**Pending feedback**: 15 items remaining in feedback/pending/
```

**Benefits**:
- ✅ Complete transparency
- ✅ Comprehensive record of all changes
- ✅ Can be posted to discussion board / sent as summary
- ✅ Contributors see their impact
- ❌ Requires more work to generate

---

## 🚀 Recommended Implementation Plan

### Phase 1: Quick Wins (Implement Now)

1. **Add status footers to integration workflow**
   - Update `command: integrate-feedback` to append status footer to archived files
   - Include: status, date, target file, validation notes
   - Effort: ~15 minutes (just template addition)

2. **Create `command: feedback-status` command**
   - List pending feedback (read feedback/pending/)
   - List recently integrated (read feedback/integrated/ with status)
   - Show summary counts
   - Effort: ~30 minutes (simple script)

3. **Update `command: integrate-feedback` to generate integration report**
   - Create INTEGRATION_REPORT_YYYY-MM-DD.md after each integration session
   - Include all integrated/skipped items with details
   - Effort: ~20 minutes (part of integration workflow)

### Phase 2: Enhanced Features (Later)

4. **Add contributor tracking** (if users want it)
   - Optional: Parse author from git commits or feedback files
   - Add attribution to notes files
   - Generate contributor stats
   - Effort: ~1 hour

5. **Email notifications** (if requested)
   - Requires email addresses in feedback files or git config
   - Send summary after integration: "Your feedback was integrated!"
   - Effort: ~2 hours + email config

6. **Web dashboard** (nice to have, far future)
   - Visual status page showing all feedback
   - Filter by module, status, date
   - Contributor leaderboard
   - Effort: ~4-8 hours

---

## 📝 Implementation Templates

### Template 1: Status Footer (Add to Integration Workflow)

```markdown
---
**INTEGRATION STATUS**: {{ status }}
**Integration Date**: {{ date }}
**Integrated Into**: {{ target_file }} ({{ lines }})
**Feedback ID**: {{ filename }}
**Validation Notes**: {{ notes }}
```

**Status values**:
- `✅ Integrated` - Successfully added to documentation
- `⚠️ Outdated` - Code changed, feedback no longer applies
- `❌ Rejected` - Feedback incorrect or not applicable
- `⏸️ Deferred` - Valid but waiting for related changes

### Template 2: command: feedback-status Command

**File**: `agent/commandscommand: feedback-status.md`

```markdown
# Feedback Status Command

Check the status of your submitted feedback.

## Usage

```bash
command: feedback-status              # Overview of all feedback
command: feedback-status module_10    # Details for specific module
command: feedback-status pending      # Show only pending items
command: feedback-status integrated   # Show only integrated items
```

## What It Shows

**Pending feedback**:
- All items in `feedback/pending/` waiting for integration
- When next integration typically happens (weekly/monthly)

**Integrated feedback**:
- Items from `feedback/integrated/` with status
- What file they were integrated into
- When integration happened

**Integration reports**:
- Recent INTEGRATION_REPORT files
- Summary of latest integration session

## Output Format

[Example output shown above in Level 2]
```

### Template 3: Integration Report Generator

**Add to `command: integrate-feedback` Step 5**:

```markdown
### Step 6: Generate Integration Report

Create comprehensive report:

```bash
# File: feedback/integrated/INTEGRATION_REPORT_YYYYMMDD.md
```

Include:
1. **Summary**: Modules processed, items integrated, items skipped
2. **Integrated section**: Each feedback with target file and lines
3. **Skipped section**: Each skipped item with reason
4. **Optional**: Contributor mentions (if attribution available)
5. **Next steps**: Timeline for next integration

**Benefits**:
- Transparency for all contributors
- Complete audit trail
- Can be posted to team chat/email
- Shows impact of feedback system
```

---

## ✅ Success Criteria

**This system succeeds when**:
- ✅ User can easily see if their feedback was integrated
- ✅ User knows WHEN it was integrated
- ✅ User knows WHERE to find their contribution (which file, which lines)
- ✅ User knows WHY if feedback was skipped (outdated, incorrect, deferred)
- ✅ User feels recognized for contributions (optional attribution)
- ✅ Maintainers have clear audit trail of all integrations

---

## 🎯 Next Steps for Implementation

**To implement Phase 1 (recommended)**:

1. Update `agent/commandscommand: integrate-feedback.md`:
   - Add Step 4d: "Add status footer to archived feedback"
   - Include template with status, date, target file, validation notes

2. Create `agent/commandscommand: feedback-status.md`:
   - Command to list pending and integrated feedback
   - Show summary counts and recent integrations

3. Update integration workflow (Step 5):
   - Generate INTEGRATION_REPORT_YYYY-MM-DD.md
   - Include all integrated/skipped items with details

**Estimated total effort**: ~1 hour for full Phase 1 implementation

**Recommendation**: Start with status footers (15 min), then add status command (30 min), then reports (20 min). Can be done incrementally.

---

**Created**: 2025-10-26
**Purpose**: Solve user visibility gap in feedback workflow
**Status**: Design complete, ready for implementation
