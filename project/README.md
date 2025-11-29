# Project Management Directory

**⚠️ This directory is for documentation project maintainers only.**

If you're a MAgPIE developer looking to use the AI documentation, **you don't need anything in this folder**. Go back to the parent directory and see:
- `README.md` - Project overview and how to get started
- `AGENT.md` - AI agent instructions
- `modules/` - Module documentation
- `core_docs/` - Architecture documentation
- `feedback/` - User feedback system

---

## What's in this folder?

This directory contains **2 essential files** for the AI documentation project:

### 1. **`CURRENT_STATE.json`** - Single Source of Truth ⭐
- Current phase and completion status
- All session accomplishments (previous sessions tracked here)
- Next steps and priorities
- **Phase 3 plan details** (task 3.1, 3.2, 3.3, 3.4 with full specifications)
- **This is the ONLY file that tracks project progress**
- **All handoff information goes here** (no separate handoff docs)
- **All planning goes here** (no separate plan docs)

### 2. **`README.md`** - This File
- Explains what's in this folder
- Quick start for project maintainers

---

## Who should use these files?

**✅ Use these files if you are:**
- Working on the AI documentation project itself
- Continuing work from a previous session
- Planning new documentation features or improvements
- Managing the documentation consolidation initiative

**❌ Don't use these files if you are:**
- A MAgPIE developer using the AI agent
- Trying to understand how MAgPIE works
- Looking for module documentation
- Submitting user feedback

---

## Quick Start for Project Maintainers

If you're continuing work on the documentation project:

1. **Read** `CURRENT_STATE.json` - See where we are, what's been done, what's next
2. **Check** the `current_initiative` section for active work
3. **Check** the `phase_3` section for upcoming tasks (Link-Don't-Duplicate enforcement)
4. **Update** `CURRENT_STATE.json` when you finish work

**Important**: When working on the documentation project, ONLY update `CURRENT_STATE.json`. Do NOT update `README.md` or other static reference documents with status information.

---

## Project Structure

```
magpie-agent/
├── project/               ← YOU ARE HERE (project management - 2 files only)
│   ├── README.md          ← This file (explains folder)
│   └── CURRENT_STATE.json ← EVERYTHING: status, plans, history, next steps
│
├── README.md              ← User-facing: project overview
├── AGENT.md               ← User-facing: AI agent instructions
├── agent/                 ← Agent commands
├── modules/               ← User-facing: module documentation
├── core_docs/             ← User-facing: architecture docs
├── feedback/              ← User-facing: user feedback system
└── ...
```

**Remember**:
- Everything in `project/` is for maintainers
- Everything outside is for MAgPIE developers
- **All project information** (handoffs, plans, status) goes in `CURRENT_STATE.json`
- **One file to rule them all** - no separate handoff or plan docs
