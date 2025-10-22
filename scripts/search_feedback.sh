#!/bin/bash

# search_feedback.sh - Search through feedback and notes files
# Usage: ./scripts/search_feedback.sh <search_term>

if [ $# -eq 0 ]; then
  echo "Usage: ./scripts/search_feedback.sh <search_term>"
  echo ""
  echo "Examples:"
  echo "  ./scripts/search_feedback.sh 'Module 70'"
  echo "  ./scripts/search_feedback.sh 'water'"
  echo "  ./scripts/search_feedback.sh 'feed baskets'"
  exit 1
fi

SEARCH_TERM="$*"

echo "🔍 Searching feedback for: '$SEARCH_TERM'"
echo "══════════════════════════════════════════════════════"
echo ""

# Search in notes files
echo "📝 Module Notes Files:"
echo "──────────────────────"
NOTES_FOUND=0
for file in modules/module_*_notes.md; do
  if [ ! -f "$file" ]; then
    continue
  fi

  if grep -qi "$SEARCH_TERM" "$file"; then
    echo "✓ Found in: $(basename $file)"
    grep -i -n -C 1 "$SEARCH_TERM" "$file" | head -5
    echo ""
    NOTES_FOUND=$((NOTES_FOUND + 1))
  fi
done

if [ $NOTES_FOUND -eq 0 ]; then
  echo "  (none found)"
  echo ""
fi

# Search in global lessons
echo "🌍 Global Lessons:"
echo "──────────────────"
if [ -f "feedback/global/claude_lessons.md" ]; then
  if grep -qi "$SEARCH_TERM" "feedback/global/claude_lessons.md"; then
    echo "✓ Found in: claude_lessons.md"
    grep -i -n -C 1 "$SEARCH_TERM" "feedback/global/claude_lessons.md" | head -5
    echo ""
  else
    echo "  (none found)"
    echo ""
  fi
fi

# Search in pending feedback
echo "⏳ Pending Feedback:"
echo "──────────────────"
PENDING_FOUND=0
for file in feedback/pending/*.md; do
  if [ ! -f "$file" ]; then
    continue
  fi

  if grep -qi "$SEARCH_TERM" "$file"; then
    echo "✓ Found in: $(basename $file)"
    grep -i -n -C 1 "$SEARCH_TERM" "$file" | head -3
    echo ""
    PENDING_FOUND=$((PENDING_FOUND + 1))
  fi
done

if [ $PENDING_FOUND -eq 0 ]; then
  echo "  (none found)"
  echo ""
fi

# Search in integrated feedback
echo "✅ Integrated Feedback (archive):"
echo "──────────────────────────────────"
INTEGRATED_FOUND=0
for file in feedback/integrated/*.md; do
  if [ ! -f "$file" ]; then
    continue
  fi

  if grep -qi "$SEARCH_TERM" "$file"; then
    INTEGRATED_FOUND=$((INTEGRATED_FOUND + 1))
  fi
done

if [ $INTEGRATED_FOUND -gt 0 ]; then
  echo "✓ Found in $INTEGRATED_FOUND archived feedback items"
  echo "  (Run: grep -r '$SEARCH_TERM' feedback/integrated/ to see details)"
else
  echo "  (none found)"
fi

echo ""
echo "══════════════════════════════════════════════════════"
