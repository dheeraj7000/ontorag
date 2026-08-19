# OntoRAG: Technical Scope & Execution Plan (FREE TIER EDITION)
## Ontology-Grounded RAG with GNN Trust Scoring — Zero-Cost Deployment

**Version:** 2.1 (Deployed & Live)  
**Author:** Dheeraj Kumar  
**Target:** AI/ML Engineer (LLM/Agentic Focus) Portfolio Project  
**Live URL:** http://32.195.248.147  
**GitHub:** `github.com/dheeraj7000/ontorag`

---

## 1. PROJECT OVERVIEW

### 1.1 Problem Statement
Current RAG systems retrieve text chunks or graph entities without:
- Schema validation (entities may conflict, types may be inconsistent)
- Trust scoring (some facts are more reliable than others)
- Hallucination detection at the answer level
- Explainability (users can't see WHY an answer was given)

### 1.2 Solution
OntoRAG is a production-ready RAG system that:
1. **Grounds retrieval in a domain ontology** (schema-validated KG construction)
2. **Scores fact trustworthiness using GNNs** (message-passing confidence propagation)
3. **Detects hallucinations** by cross-checking LLM outputs against the KG
4. **Explains every answer** via provenance visualization

### 1.3 Key Differentiators
- Extends Microsoft Research's OG-RAG with GNN-based trust scoring
- Informed by published survey: "Ontology Engineering for Trustworthy AI"
- Combines PyTorch Geometric + Neo4j + FastAPI + **100% Free Tier Stack**
- Demonstrates production-grounded KG methodology at zero cost

---

## 2. FREE TIER STACK (Updated)

| Layer | Technology | Purpose | Cost |
|-------|-----------|---------|------|
| **Backend** | FastAPI (Python 3.11+) | API server | FREE (self-hosted) |
| **LLM (Fast)** | **Groq (Llama 3.1 8B)** | Entity extraction, JSON tasks | **FREE** |
| **LLM (Smart)** | **Groq (GPT-OSS 20B)** | Answer generation, reasoning, hallucination | **FREE** |
| **Embeddings** | sentence-transformers (`all-MiniLM-L6-v2`) | Local embeddings, no API cost | FREE (CPU) |
| **Fallback LLM** | Ollama (qwen2:0.5b) | Local LLM when APIs rate-limited | FREE (EC2) |
| **Graph DB** | Neo4j Community Edition (local/Docker) | Knowledge graph storage | FREE |
| **GNN** | PyTorch Geometric 2.5+ | Trust scoring model | FREE (CPU) |
| **Vector DB** | ChromaDB (local) OR Neo4j GDS | Semantic search fallback | FREE |
| **Frontend** | React 18 + Vite + Cytoscape.js | Dashboard | FREE |
| **Deployment** | **AWS EC2 t2.micro** (Terraform) + Nginx + systemd | Production hosting | **FREE** |
| **File Storage** | Local filesystem (EC2 EBS 30GB) + AWS S3 (5GB free) | Document storage | FREE |
| **IaC** | Terraform | One-command deploy/destroy | FREE |
| **Monitoring** | systemd journald + Docker logs | Logs/metrics | FREE |
| **Monitoring** | Docker logs + Prometheus (free) OR CloudWatch (basic) | Logs/metrics | FREE |
| **Domain** | Namecheap / Cloudflare | Custom domain | ~$12/year |

**TOTAL ESTIMATED COST: $0/month + $12/year for domain**

---

## 3. TWO-TIER LLM ROUTING STRATEGY

### 3.1 Design Principle

Instead of sending all tasks to one expensive model, OntoRAG routes by task complexity:

| Tier | Model | Use Case | Why |
|------|-------|----------|-----|
| **Fast** | Llama 3.1 8B (Groq) | Entity extraction, JSON parsing | High volume, structured output, doesn't need deep reasoning |
| **Smart** | GPT-OSS 20B (Groq) | Answer generation, hallucination detection | Needs reasoning, synthesis, and nuanced understanding |
| **Fallback** | qwen2:0.5b (Ollama on EC2) | All tasks when APIs unavailable | Unlimited, no internet needed, fits in 1GB RAM |

### 3.2 Token Economics

| Operation | Input Tokens | Output Tokens | Tier | Cost per Op |
|-----------|-------------|---------------|------|-------------|
| Extract entities from 1 chunk | ~1,300 | ~500 | Fast | ~$0.0001 |
| Ingest 1 document (6 chunks) | ~7,800 | ~3,000 | Fast | ~$0.0005 |
| Generate answer | ~550 | ~200 | Smart | ~$0.0002 |
| Check hallucination | ~500 | ~300 | Smart | ~$0.0002 |

**Daily capacity on Groq free tier:** ~100 document ingestions or ~1,300 queries

### 3.3 Implementation

See `backend/app/core/llm_router.py` — the `tier` parameter controls routing:
- `tier="fast"` → extraction pipeline
- `tier="smart"` → answer generation, hallucination detection

### 3.1 Recommended Free Tier APIs (Ranked)

| Provider | Free Tier | Rate Limits | Best For | Signup |
|----------|-----------|-------------|----------|--------|
| **Cerebras** | Unlimited API calls | 30 requests/min | Fast inference, good quality | Free API key at cerebras.ai |
| **Groq** | $5/month credits | 20 requests/min, 1M tokens/day | Very fast, Mixtral/Llama | Free tier available |
| **Together AI** | $5 sign-up credit | Varies by model | Model variety | Free tier available |
| **SambaNova** | Free tier | 30 requests/min | Llama 3.1 8B/70B | Free API key |
| **Fireworks AI** | Trial credits | Varies | Good for production testing | Trial signup |
| **Ollama (Local)** | Truly unlimited | Limited by your GPU/CPU | Fallback, no internet needed | Local install |

### 3.2 Recommended Setup

**Primary: Cerebras (Llama 3.1 70B)**
- Fastest free tier (unlimited calls, 30 req/min)
- Good quality for extraction and answering
- Sign up at: https://inference.cerebras.ai/

**Secondary: Groq (Mixtral 8x7B)**
- Backup when Cerebras is rate-limited
- Very fast token generation
- Sign up at: https://groq.com/

**Fallback: Ollama (Llama 3.1 8B locally)**
- Zero API dependency
- Good for development and testing
- Install: `curl -fsSL https://ollama.com/install.sh | sh`

### 3.3 LLM Router Implementation

See `backend/app/core/llm_router.py` for the full implementation.

### 3.4 Environment Variables (`.env.example`)

```bash
# LLM API Keys (at least one required)
CEREBRAS_API_KEY=your_cerebras_key_here
GROQ_API_KEY=your_groq_key_here
TOGETHER_API_KEY=your_together_key_here

# Neo4j
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=password

# AWS (for S3 and EC2 deployment — optional, free tier)
AWS_ACCESS_KEY_ID=your_aws_key
AWS_SECRET_ACCESS_KEY=your_aws_secret
AWS_REGION=us-east-1
S3_BUCKET=ontorag-documents

# Application
APP_ENV=development
LOG_LEVEL=INFO
```

---

## 4. UPDATED SYSTEM ARCHITECTURE (Free Tier)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         USER INTERFACE (Free)                                │
│  React 18 + Vite + Cytoscape.js → Served from EC2 Nginx OR Vercel (free)   │
├─────────────────────────────────────────────────────────────────────────────┤
│                         BACKEND (Free Tier)                                  │
│  FastAPI → Docker → AWS EC2 t2.micro (750 hrs/mo free)                    │
│  ├─ LLM Router: Cerebras → Groq → Together → Ollama (fallback)            │
│  ├─ sentence-transformers (local embeddings, CPU)                         │
│  ├─ Neo4j Community (Docker on same EC2)                                    │
│  ├─ ChromaDB (local, in-memory or persisted)                                │
│  └─ File storage: EC2 EBS (30GB free) OR S3 (5GB free)                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                         KNOWLEDGE GRAPH (Free)                             │
│  Neo4j Community Edition (Docker)                                         │
│  ├─ Entities: (:System), (:Component), (:API), etc.                        │
│  ├─ Relations: [:DEPENDS_ON], [:HAS_API], etc.                             │
│  ├─ Provenance: source_document, chunk_index, extraction_confidence       │
│  └─ Trust scores: Computed by GNN, stored as node/edge properties          │
├─────────────────────────────────────────────────────────────────────────────┤
│                         GNN TRUST MODEL (Free)                              │
│  PyTorch Geometric (CPU)                                                   │
│  ├─ 2-layer GAT on Neo4j subgraph                                          │
│  ├─ Trained on pseudo-labels (heuristic-based)                             │
│  └─ Updates trust_score on all nodes/edges in Neo4j                        │
├─────────────────────────────────────────────────────────────────────────────┤
│                         CI/CD (Free)                                         │
│  GitHub Actions (2,000 min/mo) → SSH into EC2 → Docker Compose pull       │
└────────────────────────────────────────────────────────────────────────────┘
```

---

## 5. EXECUTION PHASES

### PHASE 0: PROJECT SCAFFOLDING & FREE INFRASTRUCTURE ✅
- Project structure, Docker Compose, LLM Router, config, health endpoint

### PHASE 1: ONTOLOGY & KNOWLEDGE GRAPH CONSTRUCTION ✅
- Document parser, text chunker, schema-guided extractor, KG builder, ingestion pipeline

### PHASE 2: GNN TRUST SCORING MODEL ✅
- Feature engineering, GAT model, pseudo-label training, trust score pipeline

### PHASE 3: ONTOLOGY-GUIDED RETRIEVAL & ANSWERING ✅
- Entity linking, subgraph traversal, trust-filtered answer generation

### PHASE 4: HALLUCINATION DETECTION ✅
- Claim extraction, KG cross-check, hallucination scoring

### PHASE 5: FRONTEND DASHBOARD ✅
- React + Vite, Query/Ingest/Graph/Trust pages, Cytoscape.js ready

### PHASE 6: EVALUATION & BENCHMARKING ✅
- TechDoc-QA dataset (30 questions), metrics (faithfulness, relevance, precision, recall), benchmark runner

### PHASE 7: DEPLOYMENT & CI/CD ✅
- docker-compose.prod.yml, Nginx config, GitHub Actions workflow

---

## 6. FREE TIER LIMITS & MITIGATION

| Service | Free Tier Limit | Our Usage | Risk | Mitigation |
|---------|----------------|-----------|------|------------|
| **AWS EC2 t2.micro** | 750 hrs/mo (12 months) | ~720 hrs/mo (always-on) | LOW | Use spot instances if exceeding |
| **AWS S3** | 5 GB storage | ~500 MB (documents) | NONE | Use EC2 EBS instead |
| **AWS EBS** | 30 GB | ~10 GB (OS + Docker + data) | LOW | Monitor with `df -h` |
| **Cerebras API** | 30 req/min, unlimited | ~10 req/min avg | LOW | Add rate limiter + Ollama fallback |
| **Groq API** | 20 req/min, 1M tokens/day | Backup only | NONE | Only use if Cerebras fails |
| **GitHub Actions** | 2,000 min/mo | ~200 min/mo (10 deploys) | NONE | N/A |
| **Docker Hub** | 1 private repo | 1 repo (backend image) | NONE | Use public repo (free unlimited) |
| **Cloudflare** | Unlimited bandwidth | ~1 GB/mo | NONE | N/A |

**Memory Management on t2.micro (1 GB RAM):**
- Neo4j: 400MB limit
- FastAPI backend: 400MB limit
- Nginx: 50MB
- OS overhead: ~150MB

If memory is tight:
- Use swap file: `sudo dd if=/dev/zero of=/swapfile bs=1M count=2048 && sudo mkswap /swapfile && sudo swapon /swapfile`
- Reduce Neo4j heap: `NEO4J_server_memory_heap_max__size=300M`

---

## 7. AWS EC2 DEPLOYMENT

```bash
# SSH into EC2
ssh -i your-key.pem ec2-user@your-ec2-ip

# Install Docker
sudo yum install docker -y
sudo service docker start
sudo usermod -a -G docker ec2-user

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Clone and deploy
git clone https://github.com/dheeraj7000/ontorag.git
cd ontorag
cp .env.example .env
# Edit .env with your API keys

docker-compose -f docker-compose.prod.yml up -d
```

---

## 8. SUCCESS CRITERIA

- [x] Live URL serves dashboard over HTTPS (Cloudflare)
- [x] Can upload a document and see KG build with provenance
- [x] Can query and get answers with trust-filtered facts
- [x] Hallucination detection correctly flags unsupported claims
- [x] Evaluation report shows >20% faithfulness improvement over naive RAG
- [x] GitHub repo has README with architecture diagram, setup instructions
- [x] CI/CD auto-deploys on every push to main
- [x] **Total monthly cost = $0 (domain excluded)**
