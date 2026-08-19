"""OntoRAG — Ontology-Grounded RAG with GNN Trust Scoring."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.api.v1.router import api_router
from backend.app.core.config import settings

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper()),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown lifecycle events."""
    logger.info(f"Starting OntoRAG ({settings.app_env})")
    logger.info(f"Neo4j: {settings.neo4j_uri}")

    # Log available LLM providers
    providers = []
    if settings.cerebras_api_key:
        providers.append("Cerebras")
    if settings.groq_api_key:
        providers.append("Groq")
    if settings.together_api_key:
        providers.append("Together")
    providers.append("Ollama (fallback)")
    logger.info(f"LLM providers: {', '.join(providers)}")

    yield

    logger.info("Shutting down OntoRAG")


app = FastAPI(
    title="OntoRAG API",
    description="Ontology-Grounded RAG with GNN Trust Scoring",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.app_env == "development" else [
        "https://ontorag.yourdomain.com"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API routes
app.include_router(api_router, prefix="/api/v1")


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "ok",
        "service": "ontorag",
        "version": "0.1.0",
        "environment": settings.app_env,
    }
