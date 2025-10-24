#!/bin/bash

# integrate_feedback.sh - Helper for integrating feedback into documentation
# Enhanced with automatic git pull, merge, and push workflow
# Usage: ./scripts/integrate_feedback.sh <feedback_file> [--no-git]
#
# This script operates within the magpie-agent git repository

set -e

# Configuration - defaults for magpie-agent repository
GIT_REMOTE="${FEEDBACK_GIT_REMOTE:-origin}"
GIT_BRANCH="${FEEDBACK_GIT_BRANCH:-main}"
PUSH_REMOTE="${FEEDBACK_PUSH_REMOTE:-origin}"
AUTO_GIT="${FEEDBACK_AUTO_GIT:-true}"

# Find magpie-agent root directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MAGPIE_AGENT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Parse arguments
NO_GIT=false
if [ "$2" = "--no-git" ]; then
  NO_GIT=true
fi

if [ $# -lt 1 ]; then
  echo "Usage: ./scripts/integrate_feedback.sh <feedback_file> [--no-git]"
  echo ""
  echo "Example:"
  echo "  ./scripts/integrate_feedback.sh feedback/pending/20251022_correction_module_70.md"
  echo ""
  echo "Options:"
  echo "  --no-git    Skip git pull/push operations (manual mode)"
  echo ""
  echo "Environment variables:"
  echo "  FEEDBACK_GIT_REMOTE   Remote to pull from (default: origin)"
  echo "  FEEDBACK_GIT_BRANCH   Branch to use (default: main)"
  echo "  FEEDBACK_PUSH_REMOTE  Remote to push to (default: origin)"
  echo "  FEEDBACK_AUTO_GIT     Enable auto git operations (default: true)"
  exit 1
fi

FEEDBACK_FILE="$1"

# Convert to absolute path if relative
if [[ ! "$FEEDBACK_FILE" = /* ]]; then
  FEEDBACK_FILE="$MAGPIE_AGENT_ROOT/$FEEDBACK_FILE"
fi

if [ ! -f "$FEEDBACK_FILE" ]; then
  echo "❌ File not found: $FEEDBACK_FILE"
  exit 1
fi

# Change to magpie-agent root directory
cd "$MAGPIE_AGENT_ROOT"

# Extract metadata
TYPE=$(grep "^type:" "$FEEDBACK_FILE" | cut -d: -f2 | tr -d ' ')
TARGET=$(grep "^target:" "$FEEDBACK_FILE" | cut -d: -f2 | tr -d ' ')
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

echo "🔧 Feedback Integration Helper (Enhanced)"
echo "=========================================="
echo ""
echo "Working directory: $MAGPIE_AGENT_ROOT"
echo "Feedback file: $(basename $FEEDBACK_FILE)"
echo "   Type: $TYPE"
echo "   Target: $TARGET"
echo ""

# ============================================================================
# GIT PRE-FLIGHT CHECKS AND SYNC
# ============================================================================

if [ "$NO_GIT" = false ] && [ "$AUTO_GIT" = "true" ]; then
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  echo "📡 Git Sync: Pulling latest changes from magpie-agent repo"
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  echo ""

  # Verify we're in a git repository
  if ! git rev-parse --git-dir > /dev/null 2>&1; then
    echo "❌ Error: Not in a git repository"
    echo "   Expected to be in magpie-agent repository at: $MAGPIE_AGENT_ROOT"
    exit 1
  fi

  # Check we're on the right branch
  CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)
  if [ "$CURRENT_BRANCH" != "$GIT_BRANCH" ]; then
    echo "⚠️  Warning: You're on branch '$CURRENT_BRANCH', expected '$GIT_BRANCH'"
    read -p "Switch to $GIT_BRANCH? [y/n]: " SWITCH_BRANCH
    if [ "$SWITCH_BRANCH" = "y" ] || [ "$SWITCH_BRANCH" = "Y" ]; then
      git checkout "$GIT_BRANCH"
    else
      echo "❌ Aborting. Please switch to $GIT_BRANCH manually."
      exit 1
    fi
  fi

  # Check for uncommitted changes (except feedback files)
  if ! git diff --quiet HEAD -- . ':!feedback/'; then
    echo "⚠️  Warning: You have uncommitted changes outside feedback/"
    echo ""
    git status --short
    echo ""
    read -p "Stash changes and continue? [y/n]: " STASH_CHANGES
    if [ "$STASH_CHANGES" = "y" ] || [ "$STASH_CHANGES" = "Y" ]; then
      git stash push -m "Auto-stash before feedback integration at $TIMESTAMP"
      echo "✅ Changes stashed"
      STASHED=true
    else
      echo "❌ Please commit or stash your changes first"
      exit 1
    fi
  else
    STASHED=false
  fi

  # Pull from remote
  echo "Pulling from $GIT_REMOTE/$GIT_BRANCH..."
  if git pull "$GIT_REMOTE" "$GIT_BRANCH" --no-edit; then
    echo "✅ Successfully synced with $GIT_REMOTE/$GIT_BRANCH"
  else
    echo "❌ Merge conflict detected!"
    echo ""
    echo "Conflicted files:"
    git status --short | grep "^UU\|^AA\|^DD"
    echo ""
    echo "Please resolve conflicts manually:"
    echo "  1. Edit conflicted files"
    echo "  2. Run: git add <resolved-files>"
    echo "  3. Run: git commit"
    echo "  4. Re-run this script"
    echo ""

    if [ "$STASHED" = true ]; then
      echo "Note: Your previous changes are stashed. Restore with: git stash pop"
    fi

    exit 1
  fi

  # Restore stashed changes if any
  if [ "$STASHED" = true ]; then
    echo "Restoring stashed changes..."
    if git stash pop; then
      echo "✅ Stashed changes restored"
    else
      echo "⚠️  Conflict while restoring stash. Please resolve manually."
      exit 1
    fi
  fi

  echo ""
fi

# ============================================================================
# DETERMINE DESTINATION FILE
# ============================================================================

# Determine destination (paths relative to magpie-agent root)
if [[ "$TARGET" == "CLAUDE.md" ]] || [[ "$TARGET" == "global" ]] || [[ "$TARGET" == "system-wide" ]] || [[ "$TARGET" == *"AI_Agent_Behavior"* ]]; then
  DEST="feedback/global/claude_lessons.md"
  echo "→ This is GLOBAL feedback (affects agent behavior)"
  echo "→ Will be added to: $DEST"
  echo ""

  # Create global lessons file if doesn't exist
  if [ ! -f "$DEST" ]; then
    mkdir -p "$(dirname "$DEST")"
    cat > "$DEST" <<'EOF'
# Global Lessons for Agent Behavior

**📌 System-wide feedback affecting CLAUDE.md and agent workflow**

Last updated: DATE_PLACEHOLDER

This file contains feedback that affects how the agent operates across all modules:
- Query routing improvements
- Token efficiency enhancements
- Workflow modifications
- Response pattern updates

---

## Agent Behavior Improvements

---

## Token Efficiency Lessons

---

## Query Routing Enhancements

---

## Workflow Modifications

EOF
    sed -i.bak "s/DATE_PLACEHOLDER/$(date +%Y-%m-%d)/" "$DEST" && rm "$DEST.bak"
    echo "✨ Created new global lessons file"
  fi

elif [[ "$TARGET" == module_*.md ]]; then
  # Module-specific feedback
  MODULE_NUM=$(echo "$TARGET" | sed 's/module_\([0-9]*\).*/\1/')
  NOTES_FILE="modules/module_${MODULE_NUM}_notes.md"

  echo "→ This is MODULE-SPECIFIC feedback"
  echo "→ Will be added to: $NOTES_FILE"
  echo ""

  # Create notes file if doesn't exist
  if [ ! -f "$NOTES_FILE" ]; then
    cat > "$NOTES_FILE" <<EOF
# module_${MODULE_NUM}_notes.md

**📌 User Feedback & Lessons Learned**

This file contains practical insights, warnings, and lessons from users working with Module ${MODULE_NUM}.

Last updated: $(date +%Y-%m-%d)

---

## ⚠️ Warnings - Don't Do This

---

## 💡 Lessons Learned

---

## ✏️ Corrections & Clarifications

---

## 📖 Missing Content - Now Documented

---

## 🧪 Practical Examples

EOF
    echo "✨ Created new notes file: $NOTES_FILE"
  fi

  DEST="$NOTES_FILE"

else
  # Cross-module or other
  DEST="feedback/global/cross_module_lessons.md"
  echo "→ This is CROSS-MODULE or OTHER feedback"
  echo "→ Will be added to: $DEST"
  echo ""

  if [ ! -f "$DEST" ]; then
    mkdir -p "$(dirname "$DEST")"
    cat > "$DEST" <<'EOF'
# Cross-Module Lessons

**📌 Feedback affecting multiple modules or cross-module interactions**

Last updated: DATE_PLACEHOLDER

---

## Cross-Module Interactions

---

## System-Level Insights

EOF
    sed -i.bak "s/DATE_PLACEHOLDER/$(date +%Y-%m-%d)/" "$DEST" && rm "$DEST.bak"
    echo "✨ Created new cross-module lessons file"
  fi
fi

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📝 Integration Steps:"
echo ""
echo "1. Review the feedback content:"
echo "   cat $FEEDBACK_FILE"
echo ""
echo "2. Open the destination file:"
echo "   \$EDITOR $DEST"
echo ""
echo "3. Determine the appropriate section based on type:"

case $TYPE in
  warning)
    echo "   → Add to section: ## ⚠️ Warnings - Don't Do This"
    echo "   → Assign ID: [W001], [W002], etc."
    ;;
  lesson_learned)
    echo "   → Add to section: ## 💡 Lessons Learned"
    echo "   → Assign ID: [L001], [L002], etc."
    ;;
  correction)
    echo "   → Add to section: ## ✏️ Corrections & Clarifications"
    echo "   → Assign ID: [C001], [C002], etc."
    echo "   → ALSO update main documentation: $TARGET"
    ;;
  missing)
    echo "   → Add to section: ## 📖 Missing Content - Now Documented"
    echo "   → Assign ID: [M001], [M002], etc."
    echo "   → Consider updating main doc: $TARGET"
    ;;
  global)
    echo "   → Choose appropriate section in global lessons file"
    echo "   → May require updating CLAUDE.md or AI_Agent_Behavior_Guide.md"
    ;;
esac

echo ""
echo "4. Format the entry:"
echo "   ### [ID] Title"
echo "   **Added**: $(date +%Y-%m-%d) | **Severity/Tags**: [as appropriate]"
echo "   **Source**: $(basename $FEEDBACK_FILE)"
echo "   "
echo "   [Content from feedback file]"
echo ""
echo "5. Update 'Last updated' date in $DEST"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Quick integration option
read -p "Would you like guidance on the content to integrate? [y/n]: " SHOW_CONTENT

if [ "$SHOW_CONTENT" = "y" ] || [ "$SHOW_CONTENT" = "Y" ]; then
  echo ""
  echo "📄 Feedback Content:"
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  cat "$FEEDBACK_FILE"
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
fi

echo ""
read -p "Mark as integrated (move to integrated/ and commit)? [y/n]: " MARK_INTEGRATED

if [ "$MARK_INTEGRATED" = "y" ] || [ "$MARK_INTEGRATED" = "Y" ]; then
  # Create integrated directory if doesn't exist
  mkdir -p "feedback/integrated/"

  # Get relative path for feedback file
  FEEDBACK_RELATIVE=$(realpath --relative-to="$MAGPIE_AGENT_ROOT" "$FEEDBACK_FILE" 2>/dev/null || python3 -c "import os; print(os.path.relpath('$FEEDBACK_FILE', '$MAGPIE_AGENT_ROOT'))")

  # Move feedback file
  mv "$FEEDBACK_FILE" "feedback/integrated/"
  INTEGRATED_FILE="feedback/integrated/$(basename $FEEDBACK_FILE)"
  echo "✅ Moved to $INTEGRATED_FILE"
  echo ""

  # ============================================================================
  # GIT COMMIT AND PUSH
  # ============================================================================

  if [ "$NO_GIT" = false ] && [ "$AUTO_GIT" = "true" ]; then
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "📤 Git Commit & Push"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""

    # Generate commit message
    FEEDBACK_BASENAME=$(basename "$INTEGRATED_FILE" .md)
    COMMIT_MSG="Integrate feedback: $TYPE for $TARGET

Feedback: $FEEDBACK_BASENAME
- Type: $TYPE
- Target: $TARGET
- Updated: $DEST

🤖 Generated with magpie-agent feedback system"

    # Stage changes
    echo "Staging changes..."
    git add "$DEST" "$INTEGRATED_FILE"

    # Also stage target if it was updated for corrections
    if [ "$TYPE" = "correction" ] && [ -f "$TARGET" ]; then
      git add "$TARGET"
      echo "Also staged: $TARGET (correction)"
    fi

    echo ""
    echo "Files to be committed:"
    git status --short
    echo ""

    read -p "Commit these changes? [y/n]: " DO_COMMIT

    if [ "$DO_COMMIT" = "y" ] || [ "$DO_COMMIT" = "Y" ]; then
      # Commit
      echo "$COMMIT_MSG" | git commit -F -
      echo "✅ Changes committed"
      echo ""

      # Push
      read -p "Push to $PUSH_REMOTE/$GIT_BRANCH? [y/n]: " DO_PUSH

      if [ "$DO_PUSH" = "y" ] || [ "$DO_PUSH" = "Y" ]; then
        echo "Pushing to $PUSH_REMOTE/$GIT_BRANCH..."
        if git push "$PUSH_REMOTE" "$GIT_BRANCH"; then
          echo "✅ Successfully pushed to $PUSH_REMOTE/$GIT_BRANCH"
          echo ""
          echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
          echo "✨ Feedback integration complete!"
          echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        else
          echo "❌ Push failed. Please check your remote configuration."
          echo "   You can push manually with: git push $PUSH_REMOTE $GIT_BRANCH"
        fi
      else
        echo "ℹ️  Changes committed but not pushed."
        echo "   Push manually with: git push $PUSH_REMOTE $GIT_BRANCH"
      fi
    else
      echo "ℹ️  Changes staged but not committed."
      echo "   Review with: git diff --staged"
      echo "   Commit with: git commit"
      git reset HEAD "$DEST" "$INTEGRATED_FILE" > /dev/null 2>&1
    fi
  else
    echo "Don't forget to commit your changes to $DEST!"
    if [ "$NO_GIT" = true ]; then
      echo "(Git operations disabled with --no-git flag)"
    fi
  fi
else
  echo "ℹ️  Feedback remains in pending/ for now"
fi
