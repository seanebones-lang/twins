#!/bin/bash
# Quick API server test script
# Assumes server is running on localhost:8000

API_URL="http://localhost:8000"

echo "🧪 Testing Digital Twin API"
echo "=========================="
echo ""

# Test 1: Health Check
echo "Test 1: Health Check"
echo "-------------------"
response=$(curl -s "$API_URL/health")
if echo "$response" | grep -q "healthy"; then
    echo "✅ Health check passed"
    echo "$response" | python3 -m json.tool
else
    echo "❌ Health check failed"
    echo "$response"
fi
echo ""

# Test 2: Generate (without RAG)
echo "Test 2: Generate Reply (no RAG)"
echo "-------------------------------"
response=$(curl -s -X POST "$API_URL/generate" \
    -H "Content-Type: application/json" \
    -d '{
        "context": "Hey, can we reschedule the meeting?",
        "use_rag": false,
        "max_length": 100
    }')

if echo "$response" | grep -q "reply"; then
    echo "✅ Generate endpoint working"
    echo "$response" | python3 -m json.tool
else
    echo "❌ Generate endpoint failed"
    echo "$response"
fi
echo ""

# Test 3: Generate (with RAG, if available)
echo "Test 3: Generate Reply (with RAG)"
echo "--------------------------------"
response=$(curl -s -X POST "$API_URL/generate" \
    -H "Content-Type: application/json" \
    -d '{
        "context": "Hey, can we reschedule the meeting?",
        "use_rag": true,
        "max_length": 100
    }')

if echo "$response" | grep -q "reply"; then
    echo "✅ Generate with RAG working"
    echo "$response" | python3 -m json.tool
else
    echo "⚠️  RAG may not be initialized (this is OK if not indexed)"
    echo "$response"
fi
echo ""

# Test 4: Retrieve (if RAG available)
echo "Test 4: Retrieve Similar"
echo "----------------------"
response=$(curl -s "$API_URL/retrieve?query=meeting&k=3")

if echo "$response" | grep -q "results"; then
    echo "✅ Retrieve endpoint working"
    echo "$response" | python3 -m json.tool | head -30
else
    echo "⚠️  RAG may not be initialized (this is OK if not indexed)"
    echo "$response"
fi
echo ""

echo "=========================="
echo "✅ API testing complete!"