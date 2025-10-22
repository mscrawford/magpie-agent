#!/bin/bash

# review_feedback.sh - Review pending feedback submissions
# Usage: ./scripts/review_feedback.sh

set -e

echo "📋 Pending Feedback Review"
echo "=========================="
echo ""

# Count pending items
PENDING_COUNT=$(find feedback/pending -name "*.md" 2>/dev/null | wc -l | tr -d ' ')

if [ "$PENDING_COUNT" -eq 0 ]; then
  echo "✅ No pending feedback items"
  echo ""
  echo "To submit new feedback, run: ./scripts/submit_feedback.sh"
  exit 0
fi

echo "Found $PENDING_COUNT pending feedback item(s):"
echo ""

# List all pending items with metadata
for file in feedback/pending/*.md; do
  if [ ! -f "$file" ]; then
    continue
  fi

  BASENAME=$(basename "$file")
  TYPE=$(grep "^type:" "$file" | cut -d: -f2 | tr -d ' ' || echo "unknown")
  TARGET=$(grep "^target:" "$file" | cut -d: -f2 | tr -d ' ' || echo "unknown")
  SEVERITY=$(grep "^severity:" "$file" | cut -d: -f2 | tr -d ' ' || echo "n/a")
  PRIORITY=$(grep "^priority:" "$file" | cut -d: -f2 | tr -d ' ' || echo "n/a")
  DATE=$(grep "^date:" "$file" | cut -d: -f2 | tr -d ' ' || echo "unknown")

  echo "📄 $BASENAME"
  echo "   Type: $TYPE"
  echo "   Target: $TARGET"

  if [ "$SEVERITY" != "n/a" ]; then
    echo "   Severity: $SEVERITY"
  fi

  if [ "$PRIORITY" != "n/a" ]; then
    echo "   Priority: $PRIORITY"
  fi

  echo "   Date: $DATE"
  echo ""
done

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "To integrate feedback:"
echo "  1. Review each file: cat feedback/pending/[filename]"
echo "  2. Integrate: ./scripts/integrate_feedback.sh feedback/pending/[filename]"
echo ""
echo "To see this week's stats:"
echo "  ./scripts/feedback_stats.sh"
echo ""
