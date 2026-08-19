#!/bin/bash
# Fix: Use the correct Cerebras model name that the account has access to
cd /home/ubuntu/ontorag

# Update the LLM router to use gpt-oss-120b (available on this account)
sed -i 's/"model": "llama3.1-70b"/"model": "gpt-oss-120b"/' backend/app/core/llm_router.py

# Also reduce min_interval since we confirmed 5 req/min
grep "gpt-oss" backend/app/core/llm_router.py

sudo systemctl restart ontorag-api
sleep 2
echo "API restarted with correct model"
curl -s http://localhost:8000/health
