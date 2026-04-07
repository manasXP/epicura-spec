#!/bin/bash
#
# MISRA C:2012 compliance checker using cppcheck
# Requires: cppcheck with MISRA addon
#

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Default values
SOURCE_DIRS="Core/Src App/Src"
INCLUDE_DIRS="Core/Inc App/Inc Drivers/CMSIS/Include Drivers/STM32F4xx_HAL_Driver/Inc"
MISRA_RULES="misra.json"
SUPPRESS_FILE=""
VERBOSE=0

# Usage
usage() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  -s, --source DIR     Source directories (default: Core/Src App/Src)"
    echo "  -i, --include DIR    Include directories (default: Core/Inc App/Inc ...)"
    echo "  -r, --rules FILE     MISRA rules file (default: misra.json)"
    echo "  -x, --suppress FILE  Suppressions file"
    echo "  -v, --verbose        Verbose output"
    echo "  -h, --help          Show this help"
    echo ""
    echo "Example:"
    echo "  $0 -s \"Core/Src App/Src\" -i \"Core/Inc App/Inc\""
    exit 1
}

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -s|--source)
            SOURCE_DIRS="$2"
            shift 2
            ;;
        -i|--include)
            INCLUDE_DIRS="$2"
            shift 2
            ;;
        -r|--rules)
            MISRA_RULES="$2"
            shift 2
            ;;
        -x|--suppress)
            SUPPRESS_FILE="$2"
            shift 2
            ;;
        -v|--verbose)
            VERBOSE=1
            shift
            ;;
        -h|--help)
            usage
            ;;
        *)
            echo "Unknown option: $1"
            usage
            ;;
    esac
done

# Check if cppcheck is installed
if ! command -v cppcheck &> /dev/null; then
    echo -e "${RED}Error: cppcheck is not installed${NC}"
    echo "Install with: sudo apt-get install cppcheck"
    exit 1
fi

# Check cppcheck version
CPPCHECK_VERSION=$(cppcheck --version | grep -oP '\d+\.\d+')
echo "Using cppcheck version: $CPPCHECK_VERSION"

# Create default MISRA rules file if it doesn't exist
if [ ! -f "$MISRA_RULES" ]; then
    echo "Creating default MISRA rules file: $MISRA_RULES"
    cat > "$MISRA_RULES" << 'EOF'
{
    "script": "misra",
    "args": ["--rule-texts=misra.txt"]
}
EOF
fi

# Build include path arguments
INCLUDE_ARGS=""
for dir in $INCLUDE_DIRS; do
    if [ -d "$dir" ]; then
        INCLUDE_ARGS="$INCLUDE_ARGS -I$dir"
    fi
done

# Build source file list
SOURCE_FILES=""
for dir in $SOURCE_DIRS; do
    if [ -d "$dir" ]; then
        SOURCE_FILES="$SOURCE_FILES $(find $dir -name '*.c')"
    fi
done

if [ -z "$SOURCE_FILES" ]; then
    echo -e "${RED}Error: No source files found in: $SOURCE_DIRS${NC}"
    exit 1
fi

FILE_COUNT=$(echo $SOURCE_FILES | wc -w)
echo -e "${GREEN}Found $FILE_COUNT source files${NC}"
echo ""

# Build cppcheck command
CPPCHECK_CMD="cppcheck \
    --enable=all \
    --addon=$MISRA_RULES \
    --suppress=missingIncludeSystem \
    --suppress=unmatchedSuppression \
    --inline-suppr \
    --std=c11 \
    --platform=unix32 \
    -D__GNUC__ \
    -DSTM32F4 \
    $INCLUDE_ARGS"

# Add suppressions file if provided
if [ -n "$SUPPRESS_FILE" ] && [ -f "$SUPPRESS_FILE" ]; then
    CPPCHECK_CMD="$CPPCHECK_CMD --suppressions-list=$SUPPRESS_FILE"
fi

# Add verbose flag
if [ $VERBOSE -eq 1 ]; then
    CPPCHECK_CMD="$CPPCHECK_CMD --verbose"
fi

# Run cppcheck
echo -e "${YELLOW}Running MISRA C:2012 compliance check...${NC}"
echo ""

OUTPUT_FILE="misra_report.txt"
ERROR_COUNT=0

# Execute and capture output
$CPPCHECK_CMD $SOURCE_FILES 2>&1 | tee "$OUTPUT_FILE"

# Count violations
ERROR_COUNT=$(grep -c "misra" "$OUTPUT_FILE" 2>/dev/null || echo "0")

echo ""
echo "=========================================="

if [ $ERROR_COUNT -eq 0 ]; then
    echo -e "${GREEN}✓ MISRA compliance check passed!${NC}"
    echo -e "${GREEN}  No violations found${NC}"
else
    echo -e "${RED}✗ MISRA compliance check failed${NC}"
    echo -e "${RED}  Found $ERROR_COUNT violations${NC}"
    
    echo ""
    echo "Top violations:"
    grep "misra" "$OUTPUT_FILE" | cut -d: -f3- | sort | uniq -c | sort -rn | head -10
fi

echo "=========================================="
echo ""
echo "Full report saved to: $OUTPUT_FILE"

# Generate summary by rule
echo ""
echo "Generating violation summary..."
grep "misra" "$OUTPUT_FILE" | \
    grep -oP "misra-c2012-\d+\.\d+" | \
    sort | uniq -c | sort -rn > "misra_summary.txt"

if [ -s "misra_summary.txt" ]; then
    echo ""
    echo "Violations by rule (top 20):"
    echo "----------------------------"
    head -20 "misra_summary.txt"
    echo ""
    echo "Full summary saved to: misra_summary.txt"
fi

# Exit with error if violations found
if [ $ERROR_COUNT -gt 0 ]; then
    exit 1
fi

exit 0
