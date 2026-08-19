#!/bin/bash
cd /home/ubuntu/ontorag
sed -i 's/"model": "gpt-oss-120b"/"model": "gemma-4-31b"/' backend/app/core/llm_router.py
grep "model" backend/app/core/llm_router.py | head -3
sudo systemctl restart ontorag-api
sleep 2
echo "=== Quick test ==="
curl -s -X POST http://localhost:8000/api/v1/hallucination/check \
  -H "Content-Type: application/json" \
  -d '{"answer": "FastAPI is a Python web framework."}'
