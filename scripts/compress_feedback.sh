#!/bin/bash

# compress_feedback.sh
# Helper script for command: compress-documentation workflow
# Supports the AI agent in tracking compression metadata and managing state

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
AGENT_DIR="$(dirname "$SCRIPT_DIR")"
METADATA_FILE="$AGENT_DIR/feedback/.compression_metadata.json"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_header() {
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}  Feedback Compression Helper${NC}"
    echo -e "${BLUE}========================================${NC}"
    echo
}

show_status() {
    print_header

    if [ -f "$METADATA_FILE" ]; then
        echo -e "${GREEN}✓ Compression metadata exists${NC}"
        echo
        cat "$METADATA_FILE" | jq '.' 2>/dev/null || cat "$METADATA_FILE"
        echo
    else
        echo -e "${YELLOW}⚠ No compression metadata found${NC}"
        echo "This appears to be the first compression."
        echo
    fi

    echo -e "${BLUE}Integrated feedback files:${NC}"
    INTEGRATED_COUNT=$(ls -1 "$AGENT_DIR/feedback/integrated/" 2>/dev/null | wc -l | tr -d ' ')
    echo "Total: $INTEGRATED_COUNT files"
    echo

    if [ -f "$METADATA_FILE" ]; then
        COMPRESSED_COUNT=$(cat "$METADATA_FILE" | jq '.compressed_feedback | length' 2>/dev/null || echo "0")
        UNCOMPRESSED_COUNT=$((INTEGRATED_COUNT - COMPRESSED_COUNT))
        echo -e "${GREEN}Already compressed: $COMPRESSED_COUNT${NC}"
        echo -e "${YELLOW}Not yet compressed: $UNCOMPRESSED_COUNT${NC}"
    else
        echo -e "${YELLOW}Not yet compressed: $INTEGRATED_COUNT${NC}"
    fi
    echo
}

list_uncompressed() {
    print_header
    echo -e "${BLUE}Uncompressed feedback files:${NC}"
    echo

    if [ ! -f "$METADATA_FILE" ]; then
        ls -lt "$AGENT_DIR/feedback/integrated/"
        return
    fi

    # Get list of already compressed files
    COMPRESSED=$(cat "$METADATA_FILE" | jq -r '.compressed_feedback[]' 2>/dev/null || echo "")

    # List all integrated files
    for file in "$AGENT_DIR/feedback/integrated"/*.md; do
        filename=$(basename "$file")

        # Check if already compressed
        if echo "$COMPRESSED" | grep -q "$filename"; then
            echo -e "${GREEN}✓ $filename (compressed)${NC}"
        else
            echo -e "${YELLOW}○ $filename (pending compression)${NC}"
        fi
    done
    echo
}

initialize_metadata() {
    print_header
    echo "Initializing compression metadata..."

    mkdir -p "$AGENT_DIR/feedback"

    cat > "$METADATA_FILE" <<EOF
{
  "last_compression_date": null,
  "compression_id": null,
  "compressed_feedback": [],
  "consolidations": [],
  "total_line_reduction": 0,
  "compression_count": 0,
  "history": []
}
EOF

    echo -e "${GREEN}✓ Metadata initialized${NC}"
    echo "Location: $METADATA_FILE"
    echo
}

record_compression() {
    print_header

    if [ ! -f "$METADATA_FILE" ]; then
        echo -e "${RED}Error: Metadata file not found${NC}"
        echo "Run: $0 init"
        exit 1
    fi

    echo "This function should be called by the AI agent after compression."
    echo "The agent will update the metadata with:"
    echo "  - Compression ID"
    echo "  - Compressed feedback files"
    echo "  - Consolidation details"
    echo "  - Line reduction metrics"
    echo
    echo "Use the template provided in command: compress-documentation."
    echo
}

create_backup() {
    print_header

    TIMESTAMP=$(date +%Y%m%d_%H%M%S)
    BACKUP_BRANCH="backup-pre-compression-$TIMESTAMP"

    echo "Creating backup branch: $BACKUP_BRANCH"

    cd "$AGENT_DIR"
    git checkout -b "$BACKUP_BRANCH"

    echo -e "${GREEN}✓ Backup branch created${NC}"
    echo
    echo "To restore if needed:"
    echo "  git checkout $BACKUP_BRANCH"
    echo
    echo "Switching back to previous branch..."
    git checkout -
    echo
}

show_help() {
    cat <<EOF
Feedback Compression Helper Script

USAGE:
  $0 [command]

COMMANDS:
  status      Show compression status and statistics
  list        List all integrated feedback (compressed vs. uncompressed)
  init        Initialize compression metadata file
  backup      Create git backup branch before compression
  record      Show template for recording compression (for AI use)
  help        Show this help message

EXAMPLES:
  # Check current compression status
  $0 status

  # See which feedback needs compression
  $0 list

  # Initialize for first time
  $0 init

  # Create backup before compression
  $0 backup

WORKFLOW:
  1. Run: $0 status          # Check current state
  2. Run: $0 list            # See uncompressed feedback
  3. Run: $0 backup          # Create safety backup
  4. Use: command: compress-documentation  # Let AI agent do compression
  5. AI agent updates metadata automatically

SEE ALSO:
  - agent/commands/compress-documentation.md (full workflow)
  - feedback/README.md (feedback system overview)

EOF
}

# Main script logic
case "${1:-status}" in
    status)
        show_status
        ;;
    list)
        list_uncompressed
        ;;
    init)
        initialize_metadata
        ;;
    backup)
        create_backup
        ;;
    record)
        record_compression
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        echo -e "${RED}Unknown command: $1${NC}"
        echo
        show_help
        exit 1
        ;;
esac
