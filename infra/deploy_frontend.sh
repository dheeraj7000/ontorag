#!/bin/bash
# Build the frontend locally and deploy it to the EC2 instance.
# Run this from the repo root on your machine (needs the SSH key + Node).
set -e

HOST="ubuntu@${ONTORAG_HOST:-52.43.91.28}"
KEY="${ONTORAG_SSH_KEY:-$HOME/.ssh/ontorag-key-west.pem}"

cd "$(dirname "$0")/../frontend"
npm run build

ssh -o StrictHostKeyChecking=accept-new -i "$KEY" "$HOST" "rm -rf /tmp/ontorag_dist_new && mkdir -p /tmp/ontorag_dist_new"
scp -o StrictHostKeyChecking=accept-new -i "$KEY" -r dist/* "$HOST:/tmp/ontorag_dist_new/"
ssh -o StrictHostKeyChecking=accept-new -i "$KEY" "$HOST" '
  sudo cp -r /tmp/ontorag_dist_new /var/www/ontorag_new &&
  sudo chown -R www-data:www-data /var/www/ontorag_new &&
  sudo rm -rf /var/www/ontorag_old &&
  sudo mv /var/www/ontorag /var/www/ontorag_old &&
  sudo mv /var/www/ontorag_new /var/www/ontorag
'
echo "=== Deployed. Verifying ==="
curl -s -o /dev/null -w "HTTP:%{http_code}\n" "https://${ONTORAG_HOST:-ontorag.duckdns.org}/"
