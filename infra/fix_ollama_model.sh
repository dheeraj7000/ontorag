#!/bin/bash
# llama3.1:8b is too big for t2.micro (1GB RAM + 2GB swap)
# Use tinyllama (637MB) or qwen2:0.5b (352MB) instead

echo "=== Pulling small model (qwen2:0.5b - 352MB) ==="
ollama pull qwen2:0.5b

echo "=== Update config to use small model ==="
cd /home/ubuntu/ontorag
sed -i 's/ollama_model: str = "llama3.1:8b"/ollama_model: str = "qwen2:0.5b"/' backend/app/core/config.py

echo "=== Restart API ==="
sudo systemctl restart ontorag-api
sleep 3

echo "=== Test ==="
curl -s -X POST http://localhost:8000/api/v1/hallucination/check \
  -H "Content-Type: application/json" \
  -d '{"answer": "FastAPI is a Python web framework."}'
echo ""
echo ""
sudo journalctl -u ontorag-api --no-pager -n 5
