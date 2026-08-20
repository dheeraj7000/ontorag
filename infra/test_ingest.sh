#!/bin/bash
echo "=== Uploading document ==="
RESULT=$(curl -s -X POST http://localhost:8000/api/v1/ingest/ -F "file=@/home/ubuntu/ontorag/docs/OntoRAG-Technical-Scope-FreeTier.md")
echo "$RESULT"

FILE_ID=$(echo "$RESULT" | python3 -c "import sys,json; print(json.load(sys.stdin)['file_id'])")
echo ""
echo "File ID: $FILE_ID"
echo "Waiting 90 seconds for extraction (5 req/min rate limit)..."
sleep 90

echo ""
echo "=== Ingestion Status ==="
curl -s "http://localhost:8000/api/v1/ingest/status/$FILE_ID"
echo ""

echo ""
echo "=== Graph Stats ==="
curl -s http://localhost:8000/api/v1/graph/stats
