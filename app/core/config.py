from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str = "Auto Manual RAG Assistant"
    DATA_DIR: str = "data"
    RAW_DATA_DIR: str = "data/raw"
    PROCESSED_DATA_DIR: str = "data/processed"
    CHROMA_DIR: str = "data/chroma"
    OLLAMA_BASE_URL: str = "http://127.0.0.1:11434"
    OLLAMA_MODEL: str = "qwen3.5:9b"
    OLLAMA_TEMPERATURE: float = 0.0
    OLLAMA_SEED: int = 42
    OLLAMA_THINK: bool | None = False
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
    ENABLE_RERANK: bool = False
    RERANK_MODEL_NAME: str = "BAAI/bge-reranker-base"
    RERANK_TOP_N: int = 10
    RERANK_OUTPUT_TOP_K: int = 5
    RERANK_DEVICE: str = "auto"
    RERANK_BATCH_SIZE: int = 8
    RERANK_MAX_LENGTH: int = 512

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
