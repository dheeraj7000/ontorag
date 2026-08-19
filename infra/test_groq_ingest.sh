#!/bin/bash
echo "=== Ingesting with Groq ==="
RESULT=$(curl -s -X POST http://localhost:8000/api/v1/ingest/ -F "file=@/home/ubuntu/ontorag/docs/OntoRAG-Technical-Scope-FreeTier.md")
echo "$RESULT"
FILE_ID=$(echo "$RESULT" | python3 -c "import sys,json; print(json.load(sys.stdin)['file_id'])")

echo "Waiting 60s for extraction..."
sleep 60

echo "=== Status ==="
curl -s "http://localhost:8000/api/v1/ingest/status/$FILE_ID"
echo ""
echo ""
echo "=== Graph ==="
curl -s http://localhost:8000/api/v1/graph/stats
echo ""
echo ""
echo "=== Logs ==="
sudo journalctl -u ontorag-api --no-pager -n 10 | grep -iE "chunk|extract|groq|entities"
