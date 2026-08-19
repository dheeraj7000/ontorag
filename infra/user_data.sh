#!/bin/bash
set -e

# ==========================================================================
# OntoRAG EC2 User Data Script
# Runs on first boot to set up Docker + deploy the application
# ==========================================================================

exec > /var/log/ontorag-setup.log 2>&1
echo "=== OntoRAG Setup Started: $(date) ==="

# --------------------------------------------------------------------------
# 1. System Updates
# --------------------------------------------------------------------------
apt-get update -y
apt-get upgrade -y

# --------------------------------------------------------------------------
# 2. Install Docker
# --------------------------------------------------------------------------
apt-get install -y ca-certificates curl gnupg lsb-release

mkdir -p /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg

echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null

apt-get update -y
apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

# Enable Docker on boot
systemctl enable docker
systemctl start docker

# Add ubuntu user to docker group
usermod -aG docker ubuntu

# --------------------------------------------------------------------------
# 3. Install Git and clone repo
# --------------------------------------------------------------------------
apt-get install -y git

su - ubuntu -c "git clone https://github.com/dheeraj7000/ontorag.git /home/ubuntu/ontorag"

# --------------------------------------------------------------------------
# 4. Create .env file
# --------------------------------------------------------------------------
cat > /home/ubuntu/ontorag/.env << 'ENVEOF'
CEREBRAS_API_KEY=${cerebras_api_key}
GROQ_API_KEY=
TOGETHER_API_KEY=

NEO4J_URI=bolt://neo4j:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=${neo4j_password}

APP_ENV=production
LOG_LEVEL=INFO
UPLOAD_DIR=/app/uploads
ENVEOF

chown ubuntu:ubuntu /home/ubuntu/ontorag/.env
chmod 600 /home/ubuntu/ontorag/.env

# --------------------------------------------------------------------------
# 5. Create swap file (t2.micro has only 1GB RAM)
# --------------------------------------------------------------------------
dd if=/dev/zero of=/swapfile bs=1M count=2048
chmod 600 /swapfile
mkswap /swapfile
swapon /swapfile
echo '/swapfile swap swap defaults 0 0' >> /etc/fstab

# --------------------------------------------------------------------------
# 6. Build frontend
# --------------------------------------------------------------------------
apt-get install -y nodejs npm
su - ubuntu -c "cd /home/ubuntu/ontorag/frontend && npm install && npm run build"

# --------------------------------------------------------------------------
# 7. Start services with Docker Compose
# --------------------------------------------------------------------------
su - ubuntu -c "cd /home/ubuntu/ontorag && docker compose -f docker-compose.prod.yml up -d"

# --------------------------------------------------------------------------
# 8. Set up auto-restart on reboot
# --------------------------------------------------------------------------
cat > /etc/systemd/system/ontorag.service << 'SVCEOF'
[Unit]
Description=OntoRAG Docker Compose
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/home/ubuntu/ontorag
ExecStart=/usr/bin/docker compose -f docker-compose.prod.yml up -d
ExecStop=/usr/bin/docker compose -f docker-compose.prod.yml down
User=ubuntu

[Install]
WantedBy=multi-user.target
SVCEOF

systemctl enable ontorag.service

echo "=== OntoRAG Setup Complete: $(date) ==="
