# OntoRAG — Ontology-Grounded RAG with GNN Trust Scoring

A production-ready Retrieval-Augmented Generation system that grounds retrieval in a domain ontology, scores fact trustworthiness using Graph Neural Networks, detects hallucinations by cross-checking against the knowledge graph, and explains every answer via provenance visualization.

**Live:** http://32.195.248.147 | **Cost:** $0/month (free tier stack)

---

## Architecture

```
┌────────────────────────────────────────────────────────────────────┐
│  React 18 + Vite + Cytoscape.js (Frontend)                         │
├────────────────────────────────────────────────────────────────────┤
│  FastAPI Backend                                                    │
│  ├─ Two-Tier LLM Router:                                           │
│  │   ├─ Fast (Llama 3.1 8B) → extraction, JSON tasks              │
│  │   ├─ Smart (GPT-OSS 20B) → reasoning, answers, hallucination   │
│  │   └─ Fallback (Ollama) → offline, unlimited                     │
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
├────────────────────────────────────────────────────────────────────┤
│  AWS EC2 t2.micro (Free Tier) + Terraform IaC                      │
│  ├─ Docker (Neo4j), Nginx (reverse proxy), systemd (API)          │
│  ├─ Ollama (local LLM fallback on EC2)                             │
│  └─ S3 bucket (document storage)                                   │
└────────────────────────────────────────────────────────────────────┘
```

## Key Features

- **Ontology-Grounded KG Construction** — Schema-validated entity/relation extraction with 8 entity types and 10 relation types
- **GNN Trust Scoring** — 2-layer GAT propagates confidence through the graph via message passing
- **Hallucination Detection** — Extracts atomic claims from answers and cross-references against the KG
- **Explainable Answers** — Every fact includes provenance (source document, chunk, confidence)
- **Two-Tier LLM Router** — Llama 3.1 8B for cheap extraction, GPT-OSS 20B for reasoning, Ollama fallback
- **Zero-Cost Deployment** — Terraform IaC deploys to AWS EC2 free tier with one command
- **Evaluation Framework** — Built-in benchmark with faithfulness, relevance, precision, and recall metrics

---

## Setup Guide

### Prerequisites

| Requirement | Version | Notes |
|-------------|---------|-------|
| Python | 3.11+ | Core backend language |
| Docker & Docker Compose | Latest | For Neo4j |
| Node.js | 18+ | Frontend build |
| Terraform | 1.5+ | AWS deployment (optional) |
| AWS CLI | 2.x | AWS deployment (optional) |

You need **at least one** LLM provider:
- A free Groq API key ([signup](https://console.groq.com/)) — recommended
- Ollama installed locally ([install](https://ollama.com/)) — offline fallback

### Step 1: Clone the Repository

```bash
git clone https://github.com/dheeraj7000/ontorag.git
cd ontorag
```

### Step 2: Get Groq API Key (Free)

1. Go to https://console.groq.com/keys
2. Create a new API key
3. You get access to Llama 3.1 8B (fast) + GPT-OSS 20B (smart) for free

### Step 3: Configure Environment

```bash
cp .env.example .env
```

Edit `.env`:
```bash
GROQ_API_KEY=gsk_your_key_here
CEREBRAS_API_KEY=          # Optional (if you have one)
TOGETHER_API_KEY=          # Optional

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
source venv/bin/activate

# Install dependencies
pip install -r backend/requirements.txt
pip install -r backend/requirements-dev.txt

# Optional: GNN trust scoring
pip install torch torch-geometric

# Optional: Embedding-based entity linking
pip install sentence-transformers
```

### Step 5: Start Neo4j

```bash
docker compose up -d neo4j
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

### Step 7: Frontend

```bash
cd frontend
npm install
npm run dev
# Dashboard at http://localhost:3000
```

### Step 8: Run Tests

```bash
pytest backend/tests/ -v
# 31 tests pass without Neo4j or LLM APIs
```

---

## Two-Tier LLM Routing

The router automatically selects the right model based on task complexity:

| Tier | Model | Tasks | Cost | Speed |
|------|-------|-------|------|-------|
| **Fast** | Llama 3.1 8B (Groq) | Entity extraction, JSON parsing | ~$0.05/1M tokens | ~0.5s |
| **Smart** | GPT-OSS 20B (Groq) | Answer generation, reasoning, hallucination detection | ~$0.20/1M tokens | ~2s |
| **Fallback** | Ollama (local) | All tasks when APIs unavailable | $0 | ~30s |

**Token usage per document ingestion:** ~10,000 tokens (5-10 chunks × ~1,300 input + ~500 output each)
**Token usage per query:** ~750 tokens (context assembly + answer generation)
**Daily budget on Groq free tier:** ~100 document ingestions or ~1,300 queries

---

## Usage

### Ingest a Document

```bash
curl -X POST http://localhost:8000/api/v1/ingest/ \
  -F "file=@your_document.md"
```

### Query the Knowledge Graph

```bash
curl -X POST http://localhost:8000/api/v1/query/ \
  -H "Content-Type: application/json" \
  -d '{"question": "What technologies does OntoRAG use?", "min_trust": 0.5}'
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

## Production Deployment (Terraform)

One-command deployment to AWS EC2 free tier:

```bash
cd infra

# Configure
cp terraform.tfvars.example terraform.tfvars
# Edit terraform.tfvars with your values

# Deploy
terraform init
terraform apply
```

This creates:
- EC2 t2.micro (free tier, 12 months)
- VPC + Security Group (SSH, HTTP, HTTPS restricted)
- Elastic IP (stable address)
- S3 bucket (document storage)
- Auto-installs Docker, Neo4j, Ollama, Nginx, and the app

**Tear down:** `terraform destroy`

### Post-Deploy Setup

```bash
# SSH in
ssh -i ~/.ssh/ontorag-key.pem ubuntu@<PUBLIC_IP>

# Set your Groq key
echo "GROQ_API_KEY=gsk_your_key" >> ~/ontorag/.env
sudo systemctl restart ontorag-api
```

### Memory (t2.micro = 1GB RAM)

The instance includes 2GB swap. Services are tuned for low memory:
- Neo4j: 400MB limit
- FastAPI: ~100MB
- Ollama: uses qwen2:0.5b (352MB) as fallback
- Nginx: ~10MB

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

Interactive API docs: http://32.195.248.147/docs

---

## Project Structure

```
ontorag/
├── backend/
│   ├── app/
│   │   ├── api/v1/endpoints/       # Route handlers
│   │   ├── core/                   # Config, LLM router, ontology, Neo4j
│   │   ├── evaluation/             # Benchmark runner, dataset, metrics
│   │   └── services/               # Business logic
│   │       ├── answer_generator.py # Trust-filtered answers (smart tier)
│   │       ├── chunker.py          # 500 tokens, 50 overlap
│   │       ├── document_parser.py  # PDF/MD/HTML/TXT
│   │       ├── extractor.py        # Schema-guided extraction (fast tier)
│   │       ├── gnn_trust.py        # GAT model + scoring pipeline
│   │       ├── hallucination_detector.py  # Claim extraction (smart tier)
│   │       ├── ingestion_pipeline.py      # Document-to-KG orchestration
│   │       ├── kg_builder.py       # Neo4j MERGE + provenance
│   │       └── retriever.py        # Entity linking + traversal
│   ├── tests/                      # 31 tests (pytest)
│   └── requirements.txt
├── frontend/
│   ├── src/pages/                  # Query, Ingest, Graph, Trust pages
│   ├── src/api.ts                  # Typed API client
│   └── vite.config.ts
├── infra/
│   ├── main.tf                     # Terraform (VPC, EC2, S3, EIP)
│   ├── variables.tf                # Configurable parameters
│   ├── outputs.tf                  # Public IP, SSH command, URLs
│   └── user_data.sh               # EC2 bootstrap script
├── docs/
│   └── OntoRAG-Technical-Scope-FreeTier.md
├── docker-compose.yml              # Local dev
├── docker-compose.prod.yml         # Production
├── nginx.conf                      # Reverse proxy
└── Makefile                        # Dev shortcuts
```

---

## Tech Stack

| Component | Technology |
|-----------|-----------|
| Backend | FastAPI, Python 3.11+ |
| Graph Database | Neo4j Community 5.x (Docker) |
| GNN | PyTorch Geometric (2-layer GAT, CPU) |
| Embeddings | sentence-transformers (all-MiniLM-L6-v2) |
| LLM (Fast) | Llama 3.1 8B via Groq |
| LLM (Smart) | GPT-OSS 20B via Groq |
| LLM (Fallback) | Ollama (qwen2:0.5b on EC2) |
| Frontend | React 18, Vite, Cytoscape.js |
| Infrastructure | Terraform, AWS EC2 t2.micro |
| Reverse Proxy | Nginx |
| SSL | Cloudflare (free) |

---

## Documentation

Full technical specification:
**[docs/OntoRAG-Technical-Scope-FreeTier.md](docs/OntoRAG-Technical-Scope-FreeTier.md)**

---

## License

MIT
