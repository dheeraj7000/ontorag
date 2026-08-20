"""Application configuration loaded from environment variables."""

from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings with environment variable support."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Application
    app_name: str = "OntoRAG"
    app_env: str = "development"
    log_level: str = "INFO"
    debug: bool = False

    # LLM API Keys
    cerebras_api_key: Optional[str] = None
    groq_api_key: Optional[str] = None
    together_api_key: Optional[str] = None

    # Ollama (local fallback)
    ollama_url: str = "http://localhost:11434"
    ollama_model: str = "qwen2:0.5b"

    # Neo4j
    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_user: str = "neo4j"
    neo4j_password: str = "password"

    # AWS (optional)
    aws_access_key_id: Optional[str] = None
    aws_secret_access_key: Optional[str] = None
    aws_region: str = "us-east-1"
    s3_bucket: Optional[str] = None

    # File storage
    upload_dir: str = "./uploads"

    # Abuse/cost guardrails — this is a public, unauthenticated demo on a
    # single small instance, so these bound worst-case cost and load rather
    # than doing real per-user enforcement.
    max_upload_bytes: int = 3 * 1024 * 1024  # 3MB
    max_chunks_per_document: int = 20
    rate_limit_per_minute: int = 20

    # Demo mode: reset the knowledge graph on every page load so visitors
    # never see a previous visitor's data (no auth/multi-tenancy yet).
    demo_reset_enabled: bool = True


settings = Settings()
