#!/bin/bash

# Answer Sheet Marker API - Live Demonstration
# API Running on: http://localhost:8001

BASE_URL="http://localhost:8001"

echo "=========================================="
echo "ANSWER SHEET MARKER API - LIVE DEMO"
echo "=========================================="
echo ""

# Step 1: Health Check
echo "STEP 1: Health Check"
echo "--------------------"
echo "GET $BASE_URL/health"
echo ""
curl -s $BASE_URL/health | python -m json.tool
echo ""
echo ""

# Step 2: Upload Marking Guide
echo "STEP 2: Upload Marking Guide (Questions + Rubric)"
echo "---------------------------------------------------"
echo "POST $BASE_URL/api/v1/marking-guides/upload"
echo "Uploading: example/Assessment.pdf"
echo ""
echo "This will:"
echo "  - Extract all questions from the PDF"
echo "  - Analyze marking criteria with AI"
echo "  - Create evaluation rubrics for each question"
echo ""
echo "Processing... (takes ~10-30 seconds)"
echo ""

curl -s -X POST "$BASE_URL/api/v1/marking-guides/upload" \
  -F "file=@example/Assessment.pdf" \
  | python -m json.tool > /tmp/guide_response.json

cat /tmp/guide_response.json
GUIDE_ID=$(python -c "import json; print(json.load(open('/tmp/guide_response.json'))['guide_id'])")

echo ""
echo "✓ Marking Guide Uploaded Successfully!"
echo "  Guide ID: $GUIDE_ID"
echo "  (Save this ID for marking answer sheets)"
echo ""
echo ""

# Step 3: List All Marking Guides
echo "STEP 3: List All Marking Guides"
echo "--------------------------------"
echo "GET $BASE_URL/api/v1/marking-guides"
echo ""
curl -s $BASE_URL/api/v1/marking-guides | python -m json.tool
echo ""
echo ""

# Step 4: Mark an Answer Sheet
echo "STEP 4: Mark Student Answer Sheet"
echo "-----------------------------------"
echo "POST $BASE_URL/api/v1/answer-sheets/mark"
echo "Marking: example/Student Answer Sheet 1.pdf"
echo "Student ID: student_001"
echo "Guide ID: $GUIDE_ID"
echo ""
echo "This will:"
echo "  - Extract student answers from PDF"
echo "  - Evaluate each answer against marking guide with AI"
echo "  - Calculate scores and generate feedback"
echo ""
echo "Processing... (takes ~30-60 seconds)"
echo ""

curl -s -X POST "$BASE_URL/api/v1/answer-sheets/mark" \
  -F "marking_guide_id=$GUIDE_ID" \
  -F "student_id=student_001" \
  -F "file=@example/Student Answer Sheet 1.pdf" \
  | python -m json.tool > /tmp/report_response.json

cat /tmp/report_response.json
REPORT_ID=$(python -c "import json; data=json.load(open('/tmp/report_response.json')); print(data['report_id'])")

echo ""
echo "✓ Answer Sheet Marked Successfully!"
echo "  Report ID: $REPORT_ID"
echo ""
echo ""

# Step 5: Get Report Details
echo "STEP 5: Get Marking Report"
echo "---------------------------"
echo "GET $BASE_URL/api/v1/reports/$REPORT_ID"
echo ""
curl -s "$BASE_URL/api/v1/reports/$REPORT_ID" | python -m json.tool
echo ""
echo ""

# Summary
echo "=========================================="
echo "DEMONSTRATION COMPLETE!"
echo "=========================================="
echo ""
echo "API Endpoints Available:"
echo "  - GET  /health"
echo "  - GET  /"
echo "  - POST /api/v1/marking-guides/upload"
echo "  - GET  /api/v1/marking-guides"
echo "  - GET  /api/v1/marking-guides/{id}"
echo "  - POST /api/v1/answer-sheets/mark"
echo "  - GET  /api/v1/reports"
echo "  - GET  /api/v1/reports/{id}"
echo ""
echo "Interactive Documentation:"
echo "  http://localhost:8001/docs"
echo ""
echo "For frontend/mobile development, use these same endpoints!"
echo ""
