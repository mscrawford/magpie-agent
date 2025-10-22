#!/bin/bash

# integrate_feedback.sh - Helper for integrating feedback into documentation
# Usage: ./scripts/integrate_feedback.sh <feedback_file>

set -e

if [ $# -ne 1 ]; then
  echo "Usage: ./scripts/integrate_feedback.sh <feedback_file>"
  echo ""
  echo "Example:"
  echo "  ./scripts/integrate_feedback.sh feedback/pending/20251022_correction_module_70.md"
  exit 1
fi

FEEDBACK_FILE="$1"

if [ ! -f "$FEEDBACK_FILE" ]; then
  echo "❌ File not found: $FEEDBACK_FILE"
  exit 1
fi

# Extract metadata
TYPE=$(grep "^type:" "$FEEDBACK_FILE" | cut -d: -f2 | tr -d ' ')
TARGET=$(grep "^target:" "$FEEDBACK_FILE" | cut -d: -f2 | tr -d ' ')
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

echo "🔧 Feedback Integration Helper"
echo "=============================="
echo ""
echo "Feedback file: $(basename $FEEDBACK_FILE)"
echo "   Type: $TYPE"
echo "   Target: $TARGET"
echo ""

# Determine destination
if [[ "$TARGET" == "CLAUDE.md" ]] || [[ "$TARGET" == "global" ]] || [[ "$TARGET" == "system-wide" ]] || [[ "$TARGET" == *"AI_Agent_Behavior"* ]]; then
  DEST="feedback/global/claude_lessons.md"
  echo "→ This is GLOBAL feedback (affects agent behavior)"
  echo "→ Will be added to: $DEST"
  echo ""

  # Create global lessons file if doesn't exist
  if [ ! -f "$DEST" ]; then
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
echo "   **Source**: $FEEDBACK_FILE"
echo "   "
echo "   [Content from feedback file]"
echo ""
echo "5. Update 'Last updated' date in $DEST"
echo ""
echo "6. Move feedback to integrated:"
echo "   mv $FEEDBACK_FILE feedback/integrated/"
echo ""
echo "7. Commit changes:"
echo "   git add $DEST $TARGET feedback/integrated/"
echo "   git commit -m 'Integrate feedback: [brief description]'"
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
read -p "Mark as integrated (move to integrated/)? [y/n]: " MARK_INTEGRATED

if [ "$MARK_INTEGRATED" = "y" ] || [ "$MARK_INTEGRATED" = "Y" ]; then
  mv "$FEEDBACK_FILE" "feedback/integrated/"
  echo "✅ Moved to feedback/integrated/"
  echo ""
  echo "Don't forget to commit your changes to $DEST!"
else
  echo "ℹ️  Feedback remains in pending/ for now"
fi
