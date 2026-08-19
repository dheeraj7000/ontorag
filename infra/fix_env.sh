#!/bin/bash
cd /home/ubuntu/ontorag
sed -i 's|UPLOAD_DIR=/app/uploads|UPLOAD_DIR=/home/ubuntu/ontorag/uploads|' .env
sed -i 's|NEO4J_URI=bolt://neo4j:7687|NEO4J_URI=bolt://localhost:7687|' .env
mkdir -p uploads
sudo systemctl restart ontorag-api
sleep 2
curl -s http://localhost:8000/health
