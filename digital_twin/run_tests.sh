#!/bin/bash
# Comprehensive test runner for Digital Twin AI
# Run this after installing dependencies

set -e

echo "🧪 Digital Twin AI - Comprehensive Test Suite"
echo "=============================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Track results
PASSED=0
FAILED=0
SKIPPED=0

test_step() {
    local name=$1
    local command=$2
    local required=${3:-true}
    
    echo -n "Testing: $name... "
    
    if eval "$command" > /tmp/test_output.log 2>&1; then
        echo -e "${GREEN}✅ PASSED${NC}"
        ((PASSED++))
        return 0
    else
        if [ "$required" = "true" ]; then
            echo -e "${RED}❌ FAILED${NC}"
            echo "Error output:"
            cat /tmp/test_output.log | head -10
            ((FAILED++))
            return 1
        else
            echo -e "${YELLOW}⚠️  SKIPPED${NC}"
            ((SKIPPED++))
            return 0
        fi
    fi
}

# Phase 1: Code Validation
echo "Phase 1: Code Validation"
echo "----------------------"
test_step "Code Syntax" "python3 validate_code.py"
test_step "Setup Diagnostic" "python3 check_setup.py"
echo ""

# Phase 2: Import Tests
echo "Phase 2: Import Tests"
echo "----------------------"
test_step "Import data_prep" "python3 -c 'from src import data_prep'"
test_step "Import rag" "python3 -c 'from src import rag'"
test_step "Import server" "python3 -c 'from src import server'"
test_step "Import eval" "python3 -c 'from src import eval'"
test_step "Import security" "python3 -c 'from src import security'"
echo ""

# Phase 3: Unit Tests
echo "Phase 3: Unit Tests"
echo "----------------------"
if command -v pytest &> /dev/null; then
    test_step "Run pytest" "pytest tests/ -v --tb=short"
else
    echo -e "${YELLOW}⚠️  pytest not found, skipping unit tests${NC}"
    ((SKIPPED++))
fi
echo ""

# Phase 4: Data Prep (if sample data exists)
echo "Phase 4: Data Preparation"
echo "----------------------"
if [ -f "data/raw/sample_gmail.csv" ] || [ -f "data/raw/sample_texts.json" ]; then
    test_step "Data prep with samples" "python3 src/data_prep.py"
else
    echo -e "${YELLOW}⚠️  No sample data found, skipping${NC}"
    echo "   Create data/raw/sample_gmail.csv or data/raw/sample_texts.json to test"
    ((SKIPPED++))
fi
echo ""

# Phase 5: RAG System (if data processed)
echo "Phase 5: RAG System"
echo "----------------------"
if [ -f "data/processed/train.jsonl" ]; then
    test_step "RAG indexing" "python3 src/rag.py --dataset data/processed/train.jsonl"
    test_step "RAG retrieval test" "python3 src/rag.py --query 'test query'"
else
    echo -e "${YELLOW}⚠️  No processed data, skipping RAG tests${NC}"
    ((SKIPPED++))
fi
echo ""

# Phase 6: API Server (basic check)
echo "Phase 6: API Server"
echo "----------------------"
test_step "Server imports" "python3 -c 'from src.server import app; print(\"OK\")'"
echo ""

# Summary
echo "=============================================="
echo "Test Summary"
echo "=============================================="
echo -e "${GREEN}✅ Passed: $PASSED${NC}"
echo -e "${RED}❌ Failed: $FAILED${NC}"
echo -e "${YELLOW}⚠️  Skipped: $SKIPPED${NC}"
echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}🎉 All required tests passed!${NC}"
    exit 0
else
    echo -e "${RED}❌ Some tests failed. Check output above.${NC}"
    exit 1
fi