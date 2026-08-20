#!/bin/bash
echo "=== Query Test ==="
curl -s -X POST http://localhost:8000/api/v1/query/ \
  -H "Content-Type: application/json" \
  -d '{"question": "What is OntoRAG?"}'

echo ""
echo ""
echo "=== Hallucination Test ==="
curl -s -X POST http://localhost:8000/api/v1/hallucination/check \
  -H "Content-Type: application/json" \
  -d '{"answer": "OntoRAG uses Django for its backend."}'

echo ""
echo ""
echo "=== Graph Stats ==="
curl -s http://localhost:8000/api/v1/graph/stats
