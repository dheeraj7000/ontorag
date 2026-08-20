#!/bin/bash
set -e
cd /home/ubuntu/ontorag

# Python
sudo apt-get install -y python3.10-venv 2>&1 | tail -2
python3 -m venv venv
source venv/bin/activate
pip install -q -r backend/requirements.txt

# .env — fill in real API keys after this script runs (never commit real keys here)
cat > .env << 'EOF'
CEREBRAS_API_KEY=your_cerebras_key_here
GROQ_API_KEY=your_groq_key_here
TOGETHER_API_KEY=

NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=password

APP_ENV=production
LOG_LEVEL=INFO
UPLOAD_DIR=/home/ubuntu/ontorag/uploads
OLLAMA_URL=http://localhost:11434
EOF
chmod 600 .env
mkdir -p uploads

# Neo4j
docker compose up -d neo4j 2>&1 | tail -5
sleep 15

# Nginx
sudo apt-get install -y nginx 2>&1 | tail -2
cat > /tmp/ontorag-nginx << 'NGINX'
server {
    listen 80;
    server_name _;
    gzip on;
    gzip_types text/plain text/css application/json application/javascript text/javascript application/wasm;
    gzip_min_length 1024;

    location / { root /var/www/ontorag; try_files $uri $uri/ /index.html; }
    location /assets/ { root /var/www/ontorag; expires 1y; add_header Cache-Control "public, immutable"; }
    location /api/ { proxy_pass http://127.0.0.1:8000/api/; proxy_set_header Host $host; proxy_read_timeout 300s; }
    location /health { proxy_pass http://127.0.0.1:8000/health; }
    location /docs { proxy_pass http://127.0.0.1:8000/docs; }
    location /openapi.json { proxy_pass http://127.0.0.1:8000/openapi.json; }
}
NGINX
sudo cp /tmp/ontorag-nginx /etc/nginx/sites-available/ontorag
sudo ln -sf /etc/nginx/sites-available/ontorag /etc/nginx/sites-enabled/ontorag
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t && sudo systemctl restart nginx

# FastAPI
cat > /tmp/svc << 'SVC'
[Unit]
Description=OntoRAG
After=network.target
[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/ontorag
Environment=PATH=/home/ubuntu/ontorag/venv/bin:/usr/bin
ExecStart=/home/ubuntu/ontorag/venv/bin/uvicorn backend.app.main:app --host 0.0.0.0 --port 8000
Restart=always
[Install]
WantedBy=multi-user.target
SVC
sudo cp /tmp/svc /etc/systemd/system/ontorag-api.service
sudo systemctl daemon-reload
sudo systemctl enable ontorag-api
sudo systemctl start ontorag-api
sleep 3

# Ollama
curl -fsSL https://ollama.com/install.sh | sh 2>&1 | tail -2
ollama pull qwen2:0.5b 2>&1 | tail -2

echo "=== VERIFY ==="
curl -s http://localhost:8000/health
echo ""
curl -s -o /dev/null -w "Frontend: %{http_code}\n" http://localhost/
