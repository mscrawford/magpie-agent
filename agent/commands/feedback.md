# Feedback Command

**Purpose**: Learn about and use the user feedback system

**When user says**: "/feedback", "how do I give feedback", "feedback system", etc.

---

## What Are Notes Files?

Alongside each `module_XX.md`, there may be a `module_XX_notes.md` file containing:
- ⚠️ **Warnings** — Common mistakes to avoid
- 💡 **Lessons Learned** — Practical insights from real users
- ✏️ **Corrections** — Updates and clarifications
- 🧪 **Examples** — Real-world scenarios and how-tos

The agent **always reads** notes files when answering about a module.

## Two Feedback Channels

### 1. Automatic (during sessions)
The agent records corrections and lessons **directly** to:
- ✅ `modules/module_XX_notes.md` — Module-specific warnings, corrections, lessons
- ✅ `agent/helpers/*.md` `## Lessons Learned` sections — Helper improvements
- ✅ `feedback/global/agent_lessons.md` — System-wide lessons

These are **append-only logs** of practical experience. They supplement core docs without changing authoritative content.

### 2. Formal submission (for changes requiring review)
For corrections to **core documentation** (`module_XX.md`, `AGENT.md`, `core_docs/`), submit formal feedback:

1. Create a file in `feedback/pending/` following templates in `feedback/templates/`
2. Commit and push to the magpie-agent repo
3. A maintainer reviews and integrates

**Why the distinction?** Notes files and Lessons Learned are safe to append automatically. Core docs define canonical truth and require human review.

## When to Use Notes Files vs Formal Feedback

| Situation | Channel | Why |
|-----------|---------|-----|
| Agent gave wrong info | Auto → notes file | Immediate safety; supplements core doc |
| Useful debugging insight | Auto → helper Lessons Learned | Available next session |
| Core doc has wrong equation | Formal → `feedback/pending/` | Needs verification against code |
| AGENT.md workflow is flawed | Formal → `feedback/pending/` | Needs maintainer review |
| Module doc is missing a section | Formal → `feedback/pending/` | Structural change to core doc |

## 🤖 AI Agent: Recording Feedback

**Record automatically when:**
1. User corrects you → append to `module_XX_notes.md` or helper Lessons Learned
2. You discover a warning → append to `module_XX_notes.md`
3. System-wide insight → append to `feedback/global/agent_lessons.md`

**Always check for duplicates** before appending (search for key terms in the target file).

**Tell the user**: "✅ Recorded — I've saved this so future sessions get it right."

**Submit formally when:**
- The correction requires changing `module_XX.md`, `AGENT.md`, or `core_docs/` files
- Create file in `feedback/pending/`, commit, push

## Feedback Types

| Type | Priority | Example |
|------|----------|---------|
| **Correction** | HIGH | Wrong equation in module doc |
| **Warning** | MEDIUM | Configuration combo causes infeasibility |
| **Lesson** | MEDIUM | Practical insight from debugging |
| **Missing** | LOW | Gap in existing documentation |
| **Global** | VARIES | Agent behavior improvement |

## See Also

- `feedback/README.md` — System overview
- `feedback/templates/` — Submission templates
- `feedback/pending/` — Pending feedback queue
