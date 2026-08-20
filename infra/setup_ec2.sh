#!/bin/bash
set -e
echo "=== OntoRAG EC2 Setup ==="

# 1. Fix Node.js (need v18+)
echo "--- Installing Node 18 ---"
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo dpkg --force-all --remove libnode72 2>/dev/null || true
sudo dpkg --force-all --remove libnode-dev 2>/dev/null || true
sudo apt-get install -y -f
sudo apt-get install -y nodejs
echo "Node: $(node --version)"

# 2. Build frontend
echo "--- Building frontend ---"
cd /home/ubuntu/ontorag/frontend
npm install
npm run build
sudo rm -rf /var/www/ontorag
sudo cp -r dist /var/www/ontorag
sudo chown -R www-data:www-data /var/www/ontorag

# 3. Setup Python venv
echo "--- Setting up Python ---"
cd /home/ubuntu/ontorag
sudo apt-get install -y python3.10-venv python3-pip
python3 -m venv venv
source venv/bin/activate
pip install -q -r backend/requirements.txt

# 4. Write .env — fill in real API keys after this script runs (never commit real keys here)
echo "--- Configuring .env ---"
cat > /home/ubuntu/ontorag/.env << 'EOF'
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
chmod 600 /home/ubuntu/ontorag/.env
mkdir -p /home/ubuntu/ontorag/uploads

# 5. Start Neo4j
echo "--- Starting Neo4j ---"
cd /home/ubuntu/ontorag
docker compose up -d neo4j
sleep 15

# 6. Setup Nginx
echo "--- Configuring Nginx ---"
sudo apt-get install -y nginx
cat > /tmp/ontorag-nginx << 'NGINX'
server {
    listen 80;
    server_name _;
    location / {
        root /var/www/ontorag;
        try_files $uri $uri/ /index.html;
    }
    location /api/ {
        proxy_pass http://127.0.0.1:8000/api/;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
    location /health {
        proxy_pass http://127.0.0.1:8000/health;
    }
    location /docs {
        proxy_pass http://127.0.0.1:8000/docs;
    }
    location /openapi.json {
        proxy_pass http://127.0.0.1:8000/openapi.json;
    }
}
NGINX
sudo cp /tmp/ontorag-nginx /etc/nginx/sites-available/ontorag
sudo ln -sf /etc/nginx/sites-available/ontorag /etc/nginx/sites-enabled/ontorag
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t && sudo systemctl restart nginx

# 7. Setup FastAPI systemd service
echo "--- Setting up FastAPI service ---"
cat > /tmp/ontorag-api.service << 'SVC'
[Unit]
Description=OntoRAG FastAPI Backend
After=network.target docker.service

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/ontorag
Environment=PATH=/home/ubuntu/ontorag/venv/bin:/usr/bin
ExecStart=/home/ubuntu/ontorag/venv/bin/uvicorn backend.app.main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
SVC
sudo cp /tmp/ontorag-api.service /etc/systemd/system/ontorag-api.service
sudo systemctl daemon-reload
sudo systemctl enable ontorag-api
sudo systemctl start ontorag-api
sleep 3

# 8. Install Ollama (small model)
echo "--- Installing Ollama ---"
curl -fsSL https://ollama.com/install.sh | sh
ollama pull qwen2:0.5b
sudo systemctl enable ollama

# 9. Verify
echo ""
echo "=== VERIFICATION ==="
curl -s http://localhost:8000/health
echo ""
curl -s -o /dev/null -w "Frontend: HTTP %{http_code}\n" http://localhost:80/
echo "=== DONE ==="
