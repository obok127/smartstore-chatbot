import logging
from typing import List, Optional
from .config import settings
from tqdm import tqdm

log = logging.getLogger(__name__)

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
        
        log.info(f"[EMBED] 모델 로드 시작: {self.model_name} (device: {self.device})")
        try:
            self.model = SentenceTransformer(self.model_name, device=self.device)
            # 차원 프로브
            try:
                self._dim = int(self.model.get_sentence_embedding_dimension())
            except Exception:
                vec = self.model.encode(["probe"], normalize_embeddings=True)
                self._dim = int(getattr(vec, "shape", [None, len(vec[0])])[1])
            
            log.info(f"[EMBED] 모델 로드 성공: {self.model_name} (차원: {self._dim})")
            
            # 예상 차원과 일치하는지 확인
            if self.model_name == "BAAI/bge-m3" and self._dim != 1024:
                raise ValueError(f"BAAI/bge-m3 모델이 예상과 다른 차원({self._dim})을 반환합니다. 모델을 재다운로드하세요.")
        except Exception as e:
            log.exception(f"[EMBED] 모델 로드 실패: {self.model_name} on {self.device}")
            # 폴백 금지: 조용히 다른 모델 로드하지 말고 바로 실패
            raise RuntimeError(f"임베딩 모델 로드 실패: {self.model_name}. 폴백 모델을 사용하지 않습니다. {e}")
    
    @property
    def dim(self) -> int:
        return self._dim

    def embed(self, texts: List[str]) -> List[List[float]]:
        vecs = self.model.encode(texts, batch_size=64, show_progress_bar=True, normalize_embeddings=True)
        return [v.tolist() for v in vecs]

    def embed_one(self, text: str) -> List[float]:
        return self.embed([text])[0]
