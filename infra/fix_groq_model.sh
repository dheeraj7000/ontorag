#!/bin/bash
cd /home/ubuntu/ontorag
sed -i 's/"model": "mixtral-8x7b-32768"/"model": "llama-3.1-8b-instant"/' backend/app/core/llm_router.py
sudo systemctl restart ontorag-api
sleep 2
echo "=== Groq model fixed to llama-3.1-8b-instant ==="
curl -s http://localhost:8000/health
