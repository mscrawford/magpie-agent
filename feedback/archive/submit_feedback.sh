#!/bin/bash

# submit_feedback.sh - Easy feedback submission for MAgPIE Agent
# Usage: ./scripts/submit_feedback.sh (run from magpie-agent/ directory)

set -e

# Check if running from correct directory
if [ ! -d "feedback/templates" ]; then
  echo "❌ Error: Must run this script from the magpie-agent/ directory"
  echo ""
  echo "Current directory: $(pwd)"
  echo "Expected: .../magpie/magpie-agent/"
  echo ""
  echo "Please cd to magpie-agent/ and try again:"
  echo "  cd /path/to/magpie/magpie-agent/"
  echo "  ./scripts/submit_feedback.sh"
  exit 1
fi

echo "🔧 MAgPIE Agent Feedback Submission"
echo "===================================="
echo ""
echo "This tool helps you improve the MAgPIE agent by submitting:"
echo "  - Corrections (fix errors in docs)"
echo "  - Warnings (don't do this!)"
echo "  - Lessons (what you learned)"
echo "  - Missing content (gaps in documentation)"
echo "  - Global improvements (agent behavior)"
echo ""

# Select feedback type
echo "What type of feedback?"
echo "[1] Correction (something is wrong in the docs)"
echo "[2] Warning (don't do this - warn other users)"
echo "[3] Lesson learned (practical insight from experience)"
echo "[4] Missing content (something should be documented)"
echo "[5] Global feedback (agent behavior or AGENT.md)"
echo ""
read -p "Select [1-5]: " TYPE

case $TYPE in
  1) TEMPLATE="correction" ;;
  2) TEMPLATE="warning" ;;
  3) TEMPLATE="lesson_learned" ;;
  4) TEMPLATE="missing" ;;
  5) TEMPLATE="global" ;;
  *) echo "❌ Invalid choice"; exit 1 ;;
esac

echo ""

# Get target document
if [ "$TEMPLATE" = "global" ]; then
  echo "Global feedback affects:"
  echo "  - AGENT.md (agent instructions and behavior)"
  echo "  - feedback/global/agent_lessons.md (system-wide lessons)"
  echo "  - System-wide workflow"
  echo ""
  read -p "Target document (or 'system-wide'): " TARGET
else
  echo "Examples of target documents:"
  echo "  - module_70.md (specific module)"
  echo "  - Phase1_Core_Architecture.md"
  echo "  - land_balance_conservation.md"
  echo "  - AGENT.md"
  echo ""
  read -p "Target document: " TARGET
fi

# Generate filename
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
TARGET_CLEAN=$(echo "$TARGET" | sed 's/\.md$//' | sed 's/[^a-zA-Z0-9_]/_/g')
FILENAME="feedback/pending/${TIMESTAMP}_${TEMPLATE}_${TARGET_CLEAN}.md"

# Copy template
cp "feedback/templates/${TEMPLATE}.md" "$FILENAME"

# Pre-fill fields
if [[ "$OSTYPE" == "darwin"* ]]; then
  # macOS
  sed -i '' "s/YYYY-MM-DD/$(date +%Y-%m-%d)/" "$FILENAME"
  sed -i '' "s/target: \[.*\]/target: $TARGET/" "$FILENAME"
else
  # Linux
  sed -i "s/YYYY-MM-DD/$(date +%Y-%m-%d)/" "$FILENAME"
  sed -i "s/target: \[.*\]/target: $TARGET/" "$FILENAME"
fi

echo ""
echo "✅ Created feedback file:"
echo "   $FILENAME"
echo ""
echo "📝 Next steps:"
echo "   1. Open the file in your editor"
echo "   2. Fill in the sections (delete examples/guidance)"
echo "   3. Save the file"
echo "   4. Run: git add $FILENAME"
echo "   5. Run: git commit -m 'Feedback: [brief description]'"
echo "   6. Push to your branch or submit PR"
echo ""
echo "Your feedback will be reviewed and integrated to improve the agent!"
echo ""

# Optionally open in editor
read -p "Open in editor now? [y/n]: " OPEN
if [ "$OPEN" = "y" ] || [ "$OPEN" = "Y" ]; then
  if [ -n "$EDITOR" ]; then
    $EDITOR "$FILENAME"
  elif command -v nano &> /dev/null; then
    nano "$FILENAME"
  elif command -v vim &> /dev/null; then
    vim "$FILENAME"
  else
    echo "No editor found. Please open manually: $FILENAME"
  fi
fi
