from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=("../../.env", ".env"), extra="ignore")

    google_api_key: str = ""
    embedding_model: str = "models/gemini-embedding-001"
    chroma_dir: str = "chroma_db"
    gcs_bucket: str = ""
    gcp_project_id: str = ""
    use_vertex_ai: bool = False
    gcp_location: str = "global"
    chunk_size: int = 1000
    chunk_overlap: int = 150


settings = Settings()
