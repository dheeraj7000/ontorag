#!/bin/bash
# One-time setup: install Ollama as the offline LLM fallback.
# Model choice must match backend/app/core/config.py's `ollama_model` default —
# a t2.micro (1GB RAM + swap) cannot run llama3.1:8b, so we use a small model.
set -e

echo "=== Installing Ollama ==="
curl -fsSL https://ollama.com/install.sh | sh

echo "=== Pulling qwen2:0.5b (352MB — fits a t2.micro) ==="
ollama pull qwen2:0.5b

echo "=== Starting Ollama service ==="
sudo systemctl enable ollama
sudo systemctl start ollama
sleep 3

echo "=== Verify Ollama ==="
curl -s http://localhost:11434/api/tags | head -c 200
echo ""

echo "=== Restart API ==="
sudo systemctl restart ontorag-api
sleep 2
curl -s http://localhost:8000/health
echo ""
echo "=== DONE. Ollama (qwen2:0.5b) is the offline fallback LLM. ==="
