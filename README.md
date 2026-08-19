# OntoRAG — Ontology-Grounded RAG with GNN Trust Scoring

A production-ready Retrieval-Augmented Generation system that grounds retrieval in a domain ontology, scores fact trustworthiness using Graph Neural Networks, detects hallucinations by cross-checking against the knowledge graph, and explains every answer via provenance visualization.

**Live:** `ontorag.yourdomain.com` | **Cost:** $0/month (free tier stack)

---

## Architecture

```
┌────────────────────────────────────────────────────────────────────┐
│  React 18 + Vite + Cytoscape.js (Frontend)                         │
├────────────────────────────────────────────────────────────────────┤
│  FastAPI Backend                                                    │
│  ├─ LLM Router: Cerebras → Groq → Together → Ollama (fallback)    │
│  ├─ Ingestion Pipeline: parse → chunk → extract → validate → KG   │
│  ├─ Retriever: entity linking → ontology traversal → trust filter  │
│  ├─ GNN Trust Scoring: 2-layer GAT (PyTorch Geometric, CPU)       │
│  ├─ Hallucination Detector: claim extraction + KG cross-check      │
│  └─ Evaluation Benchmark: TechDoc-QA (30 questions)                │
├────────────────────────────────────────────────────────────────────┤
│  Neo4j Community Edition (Knowledge Graph)                         │
│  ├─ Entities: System, Component, API, Concept, Technology, etc.    │
│  ├─ Relations: DEPENDS_ON, USES, HAS_API, IMPLEMENTS, etc.         │
│  └─ Provenance: source_document, chunk_index, trust_score          │
└────────────────────────────────────────────────────────────────────┘
```

## Key Features

- **Ontology-Grounded KG Construction** — Schema-validated entity/relation extraction with 8 entity types and 10 relation types
- **GNN Trust Scoring** — 2-layer GAT propagates confidence through the graph via message passing
- **Hallucination Detection** — Extracts atomic claims from answers and cross-references against the KG
- **Explainable Answers** — Every fact includes provenance (source document, chunk, confidence)
- **Multi-Provider LLM Router** — Automatic fallback across Cerebras, Groq, Together AI, and local Ollama
- **Zero-Cost Deployment** — Runs entirely on free tiers (AWS EC2 t2.micro + free LLM APIs)
- **Evaluation Framework** — Built-in benchmark with faithfulness, relevance, precision, and recall metrics

---

## Setup Guide

### Prerequisites

| Requirement | Version | Notes |
|-------------|---------|-------|
| Python | 3.11+ | Core backend language |
| Docker & Docker Compose | Latest | For Neo4j and production deploy |
| Node.js | 18+ | Frontend build |
| Git | Latest | Version control |

You also need **at least one** of:
- A free Cerebras API key ([signup](https://inference.cerebras.ai/))
- A free Groq API key ([signup](https://console.groq.com/))
- Ollama installed locally ([install](https://ollama.com/))

### Step 1: Clone the Repository

```bash
git clone https://github.com/dheeraj7000/ontorag.git
cd ontorag
```

### Step 2: Get Free LLM API Keys

| Provider | Signup URL | What You Get |
|----------|-----------|--------------|
| **Cerebras** (recommended) | https://inference.cerebras.ai/ | Unlimited calls, 30 req/min, Llama 3.1 70B |
| **Groq** (backup) | https://console.groq.com/ | $5/mo credits, 20 req/min, Mixtral 8x7B |
| **Together AI** (optional) | https://api.together.xyz/ | $5 signup credit |
| **Ollama** (local fallback) | https://ollama.com/ | Truly unlimited, runs offline |

For Ollama (no internet required):
```bash
curl -fsSL https://ollama.com/install.sh | sh
ollama pull llama3.1:8b
ollama serve  # Runs on localhost:11434
```

### Step 3: Configure Environment

```bash
cp .env.example .env
```

Edit `.env` with your API keys:
```bash
CEREBRAS_API_KEY=csk-xxxxxxxxxxxxxxxx
GROQ_API_KEY=gsk_xxxxxxxxxxxxxxxx
# TOGETHER_API_KEY=         # Optional

NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=password

APP_ENV=development
LOG_LEVEL=INFO
```

### Step 4: Backend Setup

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

# Install dependencies
pip install -r backend/requirements.txt
pip install -r backend/requirements-dev.txt

# For GNN trust scoring (optional, heavier install):
pip install torch torch-geometric

# For embedding-based entity linking (optional):
pip install sentence-transformers
```

### Step 5: Start Neo4j

```bash
docker-compose up -d neo4j
```

Wait ~15 seconds for Neo4j to become healthy, then verify:
```bash
# Neo4j Browser available at http://localhost:7474
# Default credentials: neo4j / password
```

### Step 6: Run the Backend

```bash
uvicorn backend.app.main:app --reload --port 8000
```

Verify:
```bash
curl http://localhost:8000/health
# {"status":"ok","service":"ontorag","version":"0.1.0","environment":"development"}
```

### Step 7: Frontend Setup

```bash
cd frontend
npm install
npm run dev
# Dashboard available at http://localhost:3000
```

To build for production:
```bash
npm run build
# Static files output to frontend/dist/
```

### Step 8: Run Tests

```bash
# From project root
pytest backend/tests/ -v
```

All 31 tests should pass without Neo4j or LLM APIs running (they're mocked/gracefully handled in tests).

---

## Usage

### Ingest a Document

```bash
curl -X POST http://localhost:8000/api/v1/ingest/ \
  -F "file=@your_document.md"
```

Or use the dashboard at `http://localhost:3000/ingest`.

### Query the Knowledge Graph

```bash
curl -X POST http://localhost:8000/api/v1/query/ \
  -H "Content-Type: application/json" \
  -d '{"question": "What web framework does OntoRAG use?", "min_trust": 0.5}'
```

### Check for Hallucinations

```bash
curl -X POST http://localhost:8000/api/v1/hallucination/check \
  -H "Content-Type: application/json" \
  -d '{"answer": "OntoRAG uses Django as its backend framework."}'
```

### Compute GNN Trust Scores

```bash
curl -X POST http://localhost:8000/api/v1/trust/compute
```

### Run Evaluation Benchmark

```bash
curl -X POST "http://localhost:8000/api/v1/eval/run?approach=both"
```

---

## Production Deployment (AWS EC2 Free Tier)

### 1. Launch EC2 Instance

- AMI: Amazon Linux 2023 or Ubuntu 22.04
- Instance type: t2.micro (1 vCPU, 1 GB RAM — free tier)
- Storage: 30 GB EBS (free tier)
- Security group: open ports 22, 80, 443, 7687, 8000

### 2. Install Docker on EC2

```bash
ssh -i your-key.pem ec2-user@your-ec2-ip

# Amazon Linux
sudo yum update -y
sudo yum install docker -y
sudo service docker start
sudo usermod -a -G docker ec2-user

# Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" \
  -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

### 3. Deploy

```bash
git clone https://github.com/dheeraj7000/ontorag.git
cd ontorag
cp .env.example .env
# Edit .env with production API keys

# Build frontend
cd frontend && npm install && npm run build && cd ..

# Start all services
docker-compose -f docker-compose.prod.yml up -d
```

### 4. Set Up Domain & SSL (Free via Cloudflare)

1. Buy domain on Namecheap (~$12/year)
2. Point nameservers to Cloudflare (free plan)
3. Add DNS A record: `ontorag` → your EC2 public IP
4. Enable SSL/TLS mode: Flexible (free SSL termination)
5. Turn on "Always Use HTTPS"

### 5. Memory Optimization (t2.micro)

If running tight on 1 GB RAM, add swap:
```bash
sudo dd if=/dev/zero of=/swapfile bs=1M count=2048
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
echo '/swapfile swap swap defaults 0 0' | sudo tee -a /etc/fstab
```

---

## CI/CD (GitHub Actions)

Configured in `.github/workflows/deploy.yml`. On push to `main`:
1. Runs linter (ruff)
2. Runs tests (pytest)
3. Builds and pushes Docker image to Docker Hub
4. SSHs into EC2 and pulls the latest image

Required GitHub Secrets:
- `DOCKER_USERNAME` / `DOCKER_PASSWORD`
- `EC2_PRIVATE_KEY` / `EC2_HOST` / `EC2_USER`

---

## API Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Service health check |
| POST | `/api/v1/ingest/` | Upload document for KG extraction |
| GET | `/api/v1/ingest/status/{file_id}` | Check ingestion progress |
| POST | `/api/v1/query/` | Query KG with ontology-guided retrieval |
| POST | `/api/v1/hallucination/check` | Verify answer against KG |
| GET | `/api/v1/graph/stats` | Knowledge graph statistics |
| GET | `/api/v1/graph/entities` | List entities with filters |
| GET | `/api/v1/graph/subgraph/{name}` | Get subgraph for visualization |
| POST | `/api/v1/trust/compute` | Trigger GNN trust scoring |
| GET | `/api/v1/trust/status` | GNN model info |
| POST | `/api/v1/eval/run` | Run evaluation benchmark |
| GET | `/api/v1/eval/dataset` | Benchmark dataset info |

Interactive API docs: `http://localhost:8000/docs`

---

## Project Structure

```
ontorag/
├── backend/
│   ├── app/
│   │   ├── api/v1/endpoints/       # Route handlers (ingest, query, graph, trust, hallucination, eval)
│   │   ├── core/                   # Config, LLM router, ontology schema, Neo4j connection
│   │   ├── evaluation/             # Benchmark runner, dataset, metrics
│   │   ├── models/                 # Pydantic schemas
│   │   └── services/               # Business logic
│   │       ├── answer_generator.py # Trust-filtered answer generation
│   │       ├── chunker.py          # Text chunking (500 tokens, 50 overlap)
│   │       ├── document_parser.py  # PDF/MD/HTML/TXT parsing
│   │       ├── extractor.py        # Schema-guided entity/relation extraction
│   │       ├── gnn_trust.py        # GAT model + trust scoring pipeline
│   │       ├── hallucination_detector.py  # Claim extraction + KG cross-check
│   │       ├── ingestion_pipeline.py      # Full document-to-KG orchestration
│   │       ├── kg_builder.py       # Neo4j MERGE + provenance tracking
│   │       └── retriever.py        # Entity linking + ontology-guided traversal
│   ├── tests/                      # 31 tests (pytest)
│   ├── Dockerfile
│   ├── requirements.txt
│   └── requirements-dev.txt
├── frontend/
│   ├── src/
│   │   ├── pages/                  # Query, Ingest, Graph, Trust pages
│   │   ├── api.ts                  # Typed API client
│   │   ├── App.tsx                 # Router + layout
│   │   └── index.css               # Dark theme styles
│   ├── package.json
│   └── vite.config.ts
├── docs/
│   └── OntoRAG-Technical-Scope-FreeTier.md  # Full technical spec
├── models/                         # Saved GNN weights (.pt files)
├── docker-compose.yml              # Local development (backend + Neo4j + ChromaDB)
├── docker-compose.prod.yml         # Production (EC2 with memory limits)
├── nginx.conf                      # Reverse proxy for frontend + API
├── Makefile                        # Dev shortcuts (make dev, make test, etc.)
├── .github/workflows/deploy.yml    # CI/CD pipeline
└── .env.example                    # Environment variable template
```

---

## LLM Providers

The LLM Router (`backend/app/core/llm_router.py`) tries providers in priority order with automatic failover:

| Priority | Provider | Model | Rate Limit | Cost |
|----------|----------|-------|------------|------|
| 1 | Cerebras | Llama 3.1 70B | 30 req/min | Free |
| 2 | Groq | Mixtral 8x7B | 20 req/min | Free ($5/mo credits) |
| 3 | Together AI | Llama 3.1 70B | 10 req/min | Free ($5 signup) |
| 4 | Ollama | Llama 3.1 8B | Unlimited | Free (local) |

---

## Tech Stack

| Component | Technology |
|-----------|-----------|
| Backend | FastAPI, Python 3.11+ |
| Graph Database | Neo4j Community Edition 5.x |
| GNN Framework | PyTorch Geometric (GAT) |
| Embeddings | sentence-transformers (all-MiniLM-L6-v2) |
| Frontend | React 18, Vite, Cytoscape.js |
| Deployment | AWS EC2 t2.micro, Docker Compose, Nginx |
| CI/CD | GitHub Actions |
| SSL | Cloudflare (free) |

---

## Documentation

Full technical specification with execution phases, architecture diagrams, and deployment details:

**[docs/OntoRAG-Technical-Scope-FreeTier.md](docs/OntoRAG-Technical-Scope-FreeTier.md)**

---

## License

MIT
