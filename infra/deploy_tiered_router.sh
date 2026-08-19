#!/bin/bash
cd /home/ubuntu/ontorag
git pull origin main
sudo systemctl restart ontorag-api
sleep 3
echo "=== Deployed ==="
curl -s http://localhost:8000/health
echo ""

# Test ingestion (fast tier)
echo "=== Test Ingest ==="
RESULT=$(curl -s -X POST http://localhost:8000/api/v1/ingest/ -F "file=@/home/ubuntu/ontorag/docs/OntoRAG-Technical-Scope-FreeTier.md")
echo "$RESULT"
