#!/bin/bash
echo "=== Installing Ollama ==="
curl -fsSL https://ollama.com/install.sh | sh

echo "=== Pulling Llama 3.1 8B (this takes ~5 min on t2.micro) ==="
ollama pull llama3.1:8b

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
echo "=== DONE. Ollama is the fallback LLM. ==="
