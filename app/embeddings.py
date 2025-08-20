from typing import List, Optional
from .config import settings
from tqdm import tqdm

try:
    from sentence_transformers import SentenceTransformer
except Exception:
    SentenceTransformer = None  # optional dependency

class LocalEmbedder:
    """
    로컬 임베딩: BAAI/bge-m3 권장
    - 문서(패시지) 인덱싱 시: 'passage: ...' 접두어 포함한 텍스트를 encode
    - 쿼리 검색 시: 'query: ...' 접두어 포함한 텍스트를 encode
    접두어는 Retriever에서 붙여줍니다.
    """
    def __init__(self, model_name: Optional[str] = None, device: Optional[str] = None):
        if SentenceTransformer is None:
            raise RuntimeError("sentence-transformers가 설치되어 있지 않습니다. requirements에 추가하세요.")
        self.model_name = model_name or settings.local_embed_model
        self.device = device or settings.local_embed_device
        self.model = SentenceTransformer(self.model_name, device=self.device)

    def embed(self, texts: List[str]) -> List[List[float]]:
        vecs = self.model.encode(texts, batch_size=64, show_progress_bar=True, normalize_embeddings=True)
        return [v.tolist() for v in vecs]

    def embed_one(self, text: str) -> List[float]:
        return self.embed([text])[0]
