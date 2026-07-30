import os

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=("../../.env", ".env"), extra="ignore")

    google_api_key: str = ""
    # lite = generous free-tier daily quota; plain gemini-flash-latest is only
    # ~20 requests/day free (one research run makes ~6-10 LLM calls)
    gemini_model: str = "gemini-flash-lite-latest"
    service_api_key: str = "dev-secret-key"
    mcp_server_url: str = "http://localhost:8100/mcp"
    rag_service_url: str = "http://localhost:8001"
    rate_limit_per_minute: int = 10
    gcp_project_id: str = ""
    bq_dataset: str = "agent_analytics"
    bq_table: str = "requests"
    langsmith_tracing: str = "false"
    langsmith_api_key: str = ""
    langsmith_project: str = "agentic-research"


settings = Settings()

# LangSmith reads these from real environment variables, so export them
# (values from .env are only inside `settings` otherwise).
if settings.langsmith_tracing.lower() == "true" and settings.langsmith_api_key:
    os.environ.setdefault("LANGSMITH_TRACING", "true")
    os.environ.setdefault("LANGSMITH_API_KEY", settings.langsmith_api_key)
    os.environ.setdefault("LANGSMITH_PROJECT", settings.langsmith_project)
