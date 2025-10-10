#!/usr/bin/env bash

# promote.sh - Move work items between project management directories
# Usage: ./promote.sh <filename> <target-directory>
# Example: ./promote.sh STORY-123.md in-progress

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Project management base directory
PM_BASE="project-management"

# Valid target directories
VALID_DIRS=("backlog" "in-progress" "ready-for-review" "done" "blocked")

# Function to print error and exit
error_exit() {
    echo -e "${RED}ERROR: $1${NC}" >&2
    exit 1
}

# Function to print success
success() {
    echo -e "${GREEN}$1${NC}"
}

# Function to print warning
warning() {
    echo -e "${YELLOW}$1${NC}"
}

# Check arguments
if [ $# -ne 2 ]; then
    error_exit "Usage: $0 <filename> <target-directory>\nValid directories: ${VALID_DIRS[*]}"
fi

FILENAME="$1"
TARGET_DIR="$2"

# Validate target directory
if [[ ! " ${VALID_DIRS[@]} " =~ " ${TARGET_DIR} " ]]; then
    error_exit "Invalid target directory: $TARGET_DIR\nValid directories: ${VALID_DIRS[*]}"
fi

# Find the file in any subdirectory
FOUND_FILE=""
CURRENT_DIR=""

for dir in "${VALID_DIRS[@]}"; do
    if [ -f "$PM_BASE/$dir/$FILENAME" ]; then
        FOUND_FILE="$PM_BASE/$dir/$FILENAME"
        CURRENT_DIR="$dir"
        break
    fi
done

if [ -z "$FOUND_FILE" ]; then
    error_exit "File '$FILENAME' not found in any project management directory"
fi

# Check if already in target directory
if [ "$CURRENT_DIR" = "$TARGET_DIR" ]; then
    warning "File is already in $TARGET_DIR/"
    exit 0
fi

TARGET_PATH="$PM_BASE/$TARGET_DIR/$FILENAME"

# Get current timestamp in ISO 8601 format
TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

# Check if file has YAML frontmatter
if ! head -n 1 "$FOUND_FILE" | grep -q '^---$'; then
    warning "File does not have YAML frontmatter. Adding basic frontmatter..."

    # Create temp file with frontmatter
    TEMP_FILE=$(mktemp)
    cat > "$TEMP_FILE" << EOF
---
status: $TARGET_DIR
created_date: $TIMESTAMP
updated_date: $TIMESTAMP
history:
  - status: $TARGET_DIR
    timestamp: $TIMESTAMP
---

EOF
    cat "$FOUND_FILE" >> "$TEMP_FILE"
    mv "$TEMP_FILE" "$FOUND_FILE"
else
    # Update existing frontmatter
    # This is a simple approach - extract frontmatter, update it, rebuild file

    # Extract frontmatter (between first two --- lines)
    TEMP_FRONT=$(mktemp)
    TEMP_BODY=$(mktemp)

    awk '/^---$/{if(++count==2) exit; next} count==1' "$FOUND_FILE" > "$TEMP_FRONT"
    awk '/^---$/{count++; next} count>=2' "$FOUND_FILE" > "$TEMP_BODY"

    # Update status and updated_date in frontmatter
    sed -i.bak "s/^status: .*/status: $TARGET_DIR/" "$TEMP_FRONT"
    sed -i.bak "s/^updated_date: .*/updated_date: $TIMESTAMP/" "$TEMP_FRONT"
    rm -f "$TEMP_FRONT.bak"

    # Append to history
    echo "  - status: $TARGET_DIR" >> "$TEMP_FRONT"
    echo "    timestamp: $TIMESTAMP" >> "$TEMP_FRONT"

    # Rebuild file
    TEMP_REBUILT=$(mktemp)
    echo "---" > "$TEMP_REBUILT"
    cat "$TEMP_FRONT" >> "$TEMP_REBUILT"
    echo "---" >> "$TEMP_REBUILT"
    cat "$TEMP_BODY" >> "$TEMP_REBUILT"

    mv "$TEMP_REBUILT" "$FOUND_FILE"
    rm -f "$TEMP_FRONT" "$TEMP_BODY"
fi

# Move the file
mv "$FOUND_FILE" "$TARGET_PATH"

success "✓ Moved $FILENAME from $CURRENT_DIR/ to $TARGET_DIR/"
echo "  Status updated: $TARGET_DIR"
echo "  Timestamp: $TIMESTAMP"
