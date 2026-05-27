from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str = "Auto Manual RAG Assistant"
    DATA_DIR: str = "data"
    RAW_DATA_DIR: str = "data/raw"
    PROCESSED_DATA_DIR: str = "data/processed"
    CHROMA_DIR: str = "data/chroma"
    OLLAMA_BASE_URL: str = "http://127.0.0.1:11434"
    OLLAMA_MODEL: str = "qwen2.5:7b"
    EMBEDDING_MODEL_NAME: str = "BAAI/bge-small-zh-v1.5"
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str | None = None
    ENABLE_METADATA_CONTEXT_SELECTION: bool = True
    CONTEXT_SELECTION_CANDIDATE_K: int = 10
    ENABLE_NEIGHBOR_CONTEXT_EXPANSION: bool = False
    MAX_CONTEXT_CHARS: int = 6000
    NEIGHBOR_EXPANSION_MAX_PER_CHUNK: int = 1
    RETRIEVAL_MODE: str = "hybrid"
    BM25_INDEX_PATH: str = "data/processed/bm25_index.pkl"
    DENSE_CANDIDATE_K: int = 10
    SPARSE_CANDIDATE_K: int = 10
    HYBRID_FUSION_TOP_K: int = 10
    RRF_K: int = 60
    BM25_CORE_TERM_PENALTY_FACTOR: float = 0.35

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
