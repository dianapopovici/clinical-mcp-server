"""Application configuration, read from environment / .env (12-factor)."""

from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Semantic search is delegated to the Clinical RAG Engine over HTTP.
    rag_api_url: str = "http://localhost:8000"

    # Structured tools read a local, read-only data view.
    data_path: str = "data/synthetic/clinical_records.json"

    # Append-only audit trail of every tool call.
    audit_log_path: str = "audit.log"

    # Transport defaults for the HTTP server.
    mcp_host: str = "127.0.0.1"
    mcp_port: int = 9000


settings = Settings()
