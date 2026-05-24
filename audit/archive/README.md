# audit/archive/ — historical infrastructure for the removed /feedback system

This directory holds **historical** design documents and scripts for the formal user-feedback submission system that was removed from the magpie-agent on 2026-05-24.

**The machinery described in these files no longer exists.** They are preserved for:
- Understanding why the simplification happened (commit `327116c` `simplify: remove /feedback command + external-submission machinery`)
- Reference if anyone considers re-introducing a similar pipeline
- Maintaining the integrity of pre-simplification commit history

**Do not use** the workflows, scripts, or paths these files describe. References to `audit/pending/`, `submit_feedback.sh`, etc. are all historical — they no longer map to anything in the live tree.

**Live equivalents** of the workflows these documents describe:
- For internal lesson recording → AGENT.md "Internal iteration loop" section + helper Lessons Learned sections + `audit/global/agent_lessons.md`.
- For validation flywheel → `agent/commands/validate-semantic.md` + `audit/validation_rounds.json` + `audit/flywheel_rubric.md`.
- For structural audit → `agent/commands/pipeline-audit.md` + `audit/pipeline_audit_rounds.json`.

**Contents**:

| File | Originally documented |
|---|---|
| `FEEDBACK_STATUS_TRACKING_DESIGN.md` | A proposed `/feedback-status` command (never built) |
| `FUTURE_ENHANCEMENTS.md` | Wishlist for the formal-submission pipeline |
| `WORKFLOW_GUIDE.md` | Multi-step workflow for users submitting feedback |
| `COMPRESSION_GUIDE.md` + `compress-documentation.md` + `compress_feedback.sh` | Heuristic compression of integrated feedback files |
| `integrate-feedback.md` + `integrate_feedback.sh` | Maintainer review-and-integrate flow |
| `review_feedback.sh` | Helper to display pending feedback for review |
| `search_feedback.sh` | Search across integrated/ for past feedback by topic |
| `submit_feedback.sh` | User-facing wrapper for creating a new pending/ entry |

**Disclaimer added 2026-05-24 (R5 audit, Cluster K)** following the simplification two commits earlier. If this archive begins to confuse new contributors more than it informs them, delete it — git history is the canonical record.
