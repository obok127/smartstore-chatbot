import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=os.getenv("ENV_FILE", os.path.join(os.getcwd(), ".env")),
        env_file_encoding="utf-8",
        extra="ignore",
    )
    
    # Keys & models
    openai_api_key: str = Field(default="", alias="OPENAI_API_KEY")
    openai_chat_model: str = Field(default="gpt-4o-mini", alias="OPENAI_CHAT_MODEL")
    gemini_api_key: str = Field(default="", alias="GEMINI_API_KEY")
    llm_provider: str = Field(default="gemini", alias="LLM_PROVIDER")  # "openai" or "gemini"

    # Local embeddings (BAAI/bge-m3)
    local_embed_model: str = Field(default="BAAI/bge-m3", alias="LOCAL_EMBED_MODEL")
    local_embed_device: str = Field(default="cpu", alias="LOCAL_EMBED_DEVICE")

    # Storage
    chroma_path: str = Field(default="data/chroma", alias="CHROMA_PATH")
    sqlite_path: str = Field(default="data/memory.db", alias="SQLITE_PATH")

    # Retrieval
    top_k: int = Field(default=6, alias="TOP_K")
    rerank_top_k: int = Field(default=20, alias="RERANK_TOP_K")
    score_threshold: float = Field(default=0.18, alias="SCORE_THRESHOLD")
    enable_reranker: bool = Field(default=True, alias="ENABLE_RERANKER")  # default True
    reranker_model: str = Field(default="BAAI/bge-reranker-v2-m3", alias="RERANKER_MODEL")

    # Hybrid fuse weight (dense score contribution multiplier)
    hybrid_dense_weight: float = Field(default=0.2, alias="HYBRID_DENSE_WEIGHT")
    
    # 차원 불일치 방지
    expected_embed_dim_env: str | None = os.getenv("EXPECTED_EMBED_DIM", "").strip() or None
    
    @property
    def expected_embed_dim(self) -> int | None:
        try:
            return int(self.expected_embed_dim_env) if self.expected_embed_dim_env else None
        except Exception:
            return None

settings = Settings()
