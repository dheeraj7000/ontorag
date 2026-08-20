# Infra scripts

Terraform (`main.tf`, `variables.tf`, `outputs.tf`) provisions the EC2 instance,
security group, and S3 bucket. `user_data.sh` runs automatically on first boot
(installs Docker). Everything else here is run manually over SSH.

| Script | Purpose |
|---|---|
| `setup.sh` | One-shot fresh-instance setup: Node/frontend build, Python venv, `.env` template, Neo4j (docker), nginx, `ontorag-api` systemd service, Ollama fallback. Run once after `terraform apply`. |
| `deploy.sh` | Redeploy the backend after a code change: `git pull`, reinstall deps, restart the API, smoke-test ingest. Run on the instance. |
| `deploy_frontend.sh` | Build the frontend locally and push it to the server (atomic swap into `/var/www/ontorag`). Run from your machine. |
| `install_ollama.sh` | Installs Ollama + pulls the fallback model (`qwen2:0.5b` — the only size that fits a t2.micro's 1GB RAM). Already folded into `setup.sh`; kept standalone for re-running in isolation. |
| `check_status.sh` | Snapshot of service/container status, disk, memory, and a few endpoint checks. `.env` secrets are redacted. |
| `check_logs.sh [n]` | Tail the last `n` (default 80) `ontorag-api` log lines, filtered to the signal that usually matters. |
| `test_ingest.sh` | Smoke test: upload a doc, poll ingestion status, print graph stats. |
| `test_query.sh` | Smoke test: query + hallucination-check endpoints. |
| `list_groq_models.sh` | Lists models available to your Groq API key — useful when a model gets deprecated and `llm_router.py` needs updating. |

## HTTPS (DuckDNS + certbot)

The live instance has no Elastic IP, so it uses a free DuckDNS hostname instead
of a raw IP, kept in sync by a cron job on the box:

```bash
# one-time: point the DuckDNS record at this instance and keep it fresh
echo '*/5 * * * * curl -s "https://www.duckdns.org/update?domains=<subdomain>&token=<token>&ip="' | crontab -
```

Then issue a free cert and enable HTTPS:

```bash
sudo apt-get install -y certbot python3-certbot-nginx
sudo sed -i 's/server_name _;/server_name <subdomain>.duckdns.org;/' /etc/nginx/sites-available/ontorag
sudo nginx -t && sudo systemctl reload nginx
sudo certbot --nginx -d <subdomain>.duckdns.org --non-interactive --agree-tos -m <your-email> --redirect
```

Certbot installs its own renewal timer (`certbot.timer`) — no extra cron needed.
