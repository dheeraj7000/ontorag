#!/bin/bash
# Fix nginx config to serve from /var/www/ontorag

cat > /etc/nginx/sites-available/ontorag << 'NGINX'
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

nginx -t && systemctl restart nginx
echo "Nginx fixed and restarted"
