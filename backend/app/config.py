"""Application configuration from environment variables."""

from pydantic_settings import BaseSettings
from pathlib import Path


class Settings(BaseSettings):
    # App
    app_name: str = "DOCS.ai"
    debug: bool = True

    # Database
    database_url: str = "postgresql+asyncpg://docsai:docsai@localhost:5432/docsai"
    database_url_sync: str = "postgresql://docsai:docsai@localhost:5432/docsai"

    # Ollama
    ollama_base_url: str = "http://localhost:11434"
    ollama_vision_model: str = "llava-phi3:3.8b-mini-q4_0"
    ollama_embed_model: str = "nomic-embed-text"
    ollama_chat_model: str = "llava-phi3:3.8b-mini-q4_0"
    ollama_temperature: float = 0.1

    # Storage
    storage_path: Path = Path("./storage")
    pdf_storage_path: Path = Path("./storage/pdfs")
    render_storage_path: Path = Path("./storage/renders")

    # Embedding
    embedding_dim: int = 768

    # Chunking
    chunk_size: int = 500  # tokens
    chunk_overlap: int = 50

    # Retrieval
    retrieval_top_k: int = 10
    max_tool_calls: int = 5
    max_retrieved_chunks: int = 20

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()

# Ensure storage directories exist
settings.pdf_storage_path.mkdir(parents=True, exist_ok=True)
settings.render_storage_path.mkdir(parents=True, exist_ok=True)
