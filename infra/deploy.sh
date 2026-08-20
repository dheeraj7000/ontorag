#!/bin/bash
# Redeploy the backend: pull latest main, reinstall deps, restart the API,
# and run a quick smoke test. Run this ON the EC2 instance.
set -e
cd /home/ubuntu/ontorag

git pull --ff-only origin main
source venv/bin/activate
pip install -q -r backend/requirements.txt

sudo systemctl restart ontorag-api
sleep 3

echo "=== Health ==="
curl -s http://localhost:8000/health
echo ""

echo "=== Smoke test: ingest ==="
RESULT=$(curl -s -X POST http://localhost:8000/api/v1/ingest/ -F "file=@/home/ubuntu/ontorag/docs/OntoRAG-Technical-Scope-FreeTier.md")
echo "$RESULT"
