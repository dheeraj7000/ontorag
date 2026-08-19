#!/bin/bash
echo "=== Service Status ==="
sudo systemctl is-active ontorag-api
echo ""

echo "=== Docker Containers ==="
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
echo ""

echo "=== .env ==="
cat ~/ontorag/.env
echo ""

echo "=== Disk ==="
df -h / | tail -1
echo ""

echo "=== Memory ==="
free -m
echo ""

echo "=== Swap ==="
swapon --show
echo ""

echo "=== API Test ==="
curl -s http://localhost:8000/health
echo ""

echo "=== Neo4j Test ==="
curl -s -o /dev/null -w "%{http_code}" http://localhost:7474
echo ""

echo "=== Uploads Dir ==="
ls -la ~/ontorag/uploads/ 2>/dev/null | head -5
echo ""

echo "=== Endpoints Test ==="
curl -s http://localhost:8000/api/v1/graph/stats
echo ""
