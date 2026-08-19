#!/bin/bash
cd /home/ubuntu/ontorag

# Try gemma-4-31b instead
sed -i 's/"model": "gpt-oss-120b"/"model": "gemma-4-31b"/' backend/app/core/llm_router.py

sudo systemctl restart ontorag-api
sleep 2

# Quick test - just one API call
curl -s -X POST http://localhost:8000/api/v1/hallucination/check \
  -H "Content-Type: application/json" \
  -d '{"answer": "FastAPI is a web framework."}'
