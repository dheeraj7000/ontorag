#!/bin/bash
# Fix: The docker-compose.yml uses NEO4J_AUTH=neo4j/password
# but .env has NEO4J_PASSWORD=ontorag-neo4j-2024
# Solution: update .env to match what Neo4j was initialized with

cd /home/ubuntu/ontorag
sed -i 's|NEO4J_PASSWORD=ontorag-neo4j-2024|NEO4J_PASSWORD=password|' .env

sudo systemctl restart ontorag-api
sleep 2

echo "=== Graph Stats ==="
curl -s http://localhost:8000/api/v1/graph/stats
