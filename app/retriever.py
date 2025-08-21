# app/retriever.py
from __future__ import annotations
from typing import List, Dict, Any, Tuple, Optional
import chromadb
from chromadb.config import Settings as ChromaSettings
from rank_bm25 import BM25Okapi
from rapidfuzz import process, fuzz
import pickle, json
from pathlib import Path
from .embeddings import LocalEmbedder
from .config import settings
from tqdm import tqdm
import logging

log = logging.getLogger(__name__)

# Optional reranker (FlagEmbedding)
try:
    from FlagEmbedding import FlagReranker  # pip install FlagEmbedding
except Exception:
    FlagReranker = None  # optional dependency

BM25_PKL = "bm25.pkl"
DOCS_PKL = "bm25_docs.pkl"

class Retriever:
    def __init__(self, chroma_path: Optional[str] = None):
        self.chroma_path = chroma_path or settings.chroma_path
        Path(self.chroma_path).mkdir(parents=True, exist_ok=True)

        self.client = chromadb.PersistentClient(
            path=self.chroma_path,
            settings=ChromaSettings(allow_reset=False)
        )
        
        # 로컬 임베딩만 사용
        self.embedder = LocalEmbedder(model_name=settings.local_embed_model, device=settings.local_embed_device)
        
        # ChromaDB 임베딩 함수 정의
        class ChromaEmbeddingFunction:
            def __init__(self, embedder):
                self.embedder = embedder
            
            def __call__(self, input):
                return self.embedder.embed(input)
            
            def name(self):
                return "custom_embedding_function"
        
        self.collection = self.client.get_or_create_collection(
            name="smartstore_faq",
            embedding_function=ChromaEmbeddingFunction(self.embedder),
            metadata={"hnsw:space": "cosine"}
        )
        self.embed_dim = self.embedder.dim
        
        # 차원 불일치 Fail Fast 가드
        try:
            self.index_dim = self._detect_index_dim()  # 컬렉션에서 1개 꺼내 길이 확인
            expected = settings.expected_embed_dim or self.embed_dim
            
            log.info(f"[INDEX] index_dim={self.index_dim}, embed_dim={self.embed_dim}, expected_dim={expected}")
            
            if self.index_dim and expected and self.index_dim != expected:
                raise ValueError(f"[DIM MISMATCH] index:{self.index_dim} != expected:{expected} — reindex or fix embedder")
            
            self.dense_ok = True
        except Exception as e:
            log.error(f"[INDEX] 차원 검증 실패: {e}")
            self.dense_ok = False

        # Optional reranker
        self.reranker = None
        if settings.enable_reranker and FlagReranker is not None:
            try:
                self.reranker = FlagReranker(settings.reranker_model, use_fp16=True)
            except Exception:
                self.reranker = None

        self._bm25, self._bm25_lookup = self._load_bm25()
        self._doc_map = self._load_docs()

    # ---------------- Ingestion ----------------
    def reset(self):
        try:
            self.client.delete_collection("smartstore_faq")
        except Exception:
            pass
        
        # ChromaDB 임베딩 함수 정의
        class ChromaEmbeddingFunction:
            def __init__(self, embedder):
                self.embedder = embedder
            
            def __call__(self, input):
                return self.embedder.embed(input)
            
            def name(self):
                return "custom_embedding_function"
        
        self.collection = self.client.get_or_create_collection(
            name="smartstore_faq", 
            embedding_function=ChromaEmbeddingFunction(self.embedder),
            metadata={"hnsw:space":"cosine"}
        )
        # 로컬 인덱스 리셋
        for p in [Path(self.chroma_path)/BM25_PKL, Path(self.chroma_path)/DOCS_PKL]:
            if p.exists():
                p.unlink()
        self._bm25, self._bm25_lookup = None, None
        self._doc_map = {}

    def upsert(self, docs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        docs: [{id, text, title, url, category}]
        로컬 임베딩으로 Chroma 업서트 + BM25 구축
        """
        ids = [d["id"] for d in docs]
        # BGE 권장: passage 접두어
        texts = [("passage: " + d["text"]) for d in docs]
        metadatas = [
            {"title": d.get("title",""), "url": d.get("url",""), "category": d.get("category","")}
            for d in docs
        ]

        # 1) 로컬 임베딩
        embeddings = None
        try:
            print(f"[index] 임베딩 시작: {len(texts)}개 문서")
            embeddings = self.embedder.embed(texts)
            print(f"[index] 임베딩 완료: {len(embeddings)}개 벡터")
        except Exception as e:
            print(f"[index] 임베딩 실패: {e}")
            raise e

        # 2) Chroma 업서트
        print("[index] Chroma 업서트 시작...")
        self.collection.upsert(ids=ids, metadatas=metadatas, documents=texts, embeddings=embeddings)
        print("[index] Chroma 업서트 완료")

        # 3) BM25 인덱스 & 로컬 문서맵 저장
        print("[index] BM25 토크나이즈...")
        tokenized = [self._tokenize(d["text"]) for d in tqdm(docs, desc="BM25 토크나이즈", unit="doc")]
        bm25 = BM25Okapi(tokenized)
        lookup = {i: ids[i] for i in range(len(ids))}
        with open(Path(self.chroma_path) / BM25_PKL, "wb") as f:
            pickle.dump({"bm25": bm25, "lookup": lookup}, f)
        self._bm25, self._bm25_lookup = bm25, lookup

        print("[index] 문서 맵 저장...")
        doc_map = {
            d["id"]: {
                "id": d["id"], "text": d["text"],
                "title": d.get("title",""), "url": d.get("url",""), "category": d.get("category","")
            } for d in docs
        }
        with open(Path(self.chroma_path) / DOCS_PKL, "wb") as f:
            pickle.dump(doc_map, f)
        self._doc_map = doc_map

        print("[index] 인덱싱 완료")
        return {"ingested": len(docs), "mode": "dense+bm25", "embedding_ok": True}

    def _load_bm25(self):
        path = Path(self.chroma_path) / BM25_PKL
        if path.exists():
            with open(path, "rb") as f:
                d = pickle.load(f)
                return d["bm25"], d["lookup"]
        return None, None

    def _detect_index_dim(self) -> int | None:
        """인덱스 차원 감지 - 실제 저장된 벡터에서 읽기"""
        try:
            if self.collection.count() > 0:
                g = self.collection.get(limit=1, include=["embeddings"])
                if g and g.get("embeddings") and g["embeddings"][0] is not None:
                    return len(g["embeddings"][0])
        except Exception as e:
            log.warning(f"[INDEX] 차원 감지 실패: {e}")
        return None

    def _load_docs(self) -> Dict[str, Any]:
        path = Path(self.chroma_path) / DOCS_PKL
        if path.exists():
            with open(path, "rb") as f:
                return pickle.load(f)
        return {}

    # ---------------- Retrieval ----------------
    def retrieve(self, query: str, k: Optional[int] = None) -> List[Dict[str, Any]]:
        k = k or settings.top_k
        candidate_k = max(k, settings.rerank_top_k)

        fused: Dict[str, float] = {}

        # 1) Dense retrieval (Chroma)
        if self.dense_ok:
            try:
                # BGE 권장: query 접두어 + 직접 임베딩 사용
                qvec = self.embedder.embed_one("query: " + query)
                dense_results = self.collection.query(
                    query_embeddings=[qvec],
                    n_results=candidate_k,
                    include=["metadatas", "documents", "distances"]
                )
                if dense_results["ids"] and dense_results["ids"][0]:
                    for i, doc_id in enumerate(dense_results["ids"][0]):
                        # Chroma는 거리 반환 → 유사도로 변환 (1 - 거리)
                        distance = dense_results["distances"][0][i]
                        score = 1.0 - distance
                        fused[doc_id] = fused.get(doc_id, 0.0) + (score * settings.hybrid_dense_weight)
            except Exception as e:
                print(f"[retrieve] Dense 검색 실패: {e}")

        # 2) Sparse retrieval (BM25)
        if self._bm25:
            try:
                tokenized_query = self._tokenize(query)
                bm25_scores = self._bm25.get_scores(tokenized_query)
                # Top-k BM25 결과
                top_indices = sorted(range(len(bm25_scores)), key=lambda i: bm25_scores[i], reverse=True)[:candidate_k]
                for idx in top_indices:
                    if bm25_scores[idx] > 0:
                        doc_id = self._bm25_lookup[idx]
                        # BM25 점수 정규화 (0~1 범위로)
                        normalized_score = min(bm25_scores[idx] / 10.0, 1.0)
                        fused[doc_id] = fused.get(doc_id, 0.0) + (normalized_score * (1.0 - settings.hybrid_dense_weight))
            except Exception as e:
                print(f"[retrieve] BM25 검색 실패: {e}")

        # 3) Fuzzy search (fallback)
        if not fused and self._doc_map:
            try:
                # 제목 기반 fuzzy search
                titles = [(doc_id, doc["title"]) for doc_id, doc in self._doc_map.items()]
                matches = process.extract(query, [t[1] for t in titles], limit=candidate_k, scorer=fuzz.partial_ratio)
                for choice, score, idx in matches:  # ✅ 올바른 언패킹
                    if score > 50:  # 50% 이상 매치
                        doc_id = titles[idx][0]
                        fused[doc_id] = max(fused.get(doc_id, 0.0), score / 100.0)
            except Exception as e:
                print(f"[retrieve] Fuzzy 검색 실패: {e}")

        # 4) Reranking (optional)
        if self.reranker and fused:
            try:
                # 상위 후보들만 rerank
                top_candidates = sorted(fused.items(), key=lambda x: x[1], reverse=True)[:settings.rerank_top_k]
                if len(top_candidates) > 1:
                    pairs = [(query, self._doc_map[doc_id]["text"]) for doc_id, _ in top_candidates]
                    rerank_scores = self.reranker.compute_score(pairs)
                    # Rerank 점수로 업데이트
                    for i, (doc_id, _) in enumerate(top_candidates):
                        if i < len(rerank_scores):
                            fused[doc_id] = rerank_scores[i]
            except Exception as e:
                print(f"[retrieve] Reranking 실패: {e}")

        # 5) 결과 정렬 및 반환
        sorted_results = sorted(fused.items(), key=lambda x: x[1], reverse=True)[:k]
        results = []
        for doc_id, score in sorted_results:
            if doc_id in self._doc_map:
                doc = self._doc_map[doc_id]
                results.append({
                    "id": doc_id,
                    "title": doc["title"],
                    "text": doc["text"],
                    "url": doc.get("url", ""),
                    "category": doc.get("category", ""),
                    "score": score
                })

        return results

    def rebuild_dense_from_docmap(self, batch_size: int = 256) -> Dict[str, Any]:
        if not self._doc_map:
            raise ValueError("doc_map 비어 있음: BM25/문서맵이 존재하는지 확인하세요.")

        # 이미 인덱싱된 문서 ID 확인
        existing_ids = set()
        try:
            if self.collection.count() > 0:
                existing = self.collection.get(limit=10000, include=[])
                if existing and existing.get("ids"):
                    existing_ids = set(existing["ids"])
        except Exception as e:
            print(f"[dense-rebuild] 기존 ID 확인 실패: {e}")

        ids, texts, metas = [], [], []
        total, done = len(self._doc_map), len(existing_ids)
        remaining = total - done

        print(f"[dense-rebuild] 기존: {done}개, 남은: {remaining}개")

        def flush():
            nonlocal ids, texts, metas, done
            if not ids:
                return
            embs = self.embedder.embed(texts)  # 1024차원 보장
            self.collection.upsert(ids=ids, documents=texts, metadatas=metas, embeddings=embs)
            done += len(ids)
            print(f"[dense-rebuild] upsert {done}/{total} (추가: {len(ids)}개)")
            ids, texts, metas = [], [], []

        for doc_id, d in self._doc_map.items():
            if doc_id in existing_ids:
                continue  # 이미 인덱싱된 문서는 건너뛰기
            
            ids.append(doc_id)
            texts.append("passage: " + (d.get("text") or ""))
            metas.append({"title": d.get("title",""), "url": d.get("url",""), "category": d.get("category","")})
            if len(ids) >= batch_size:
                flush()
        flush()

        return {
            "chroma_count": self.collection.count(),
            "doc_map_size": len(self._doc_map),
            "existing_count": len(existing_ids),
            "newly_added": self.collection.count() - len(existing_ids)
        }

    @staticmethod
    def _tokenize(text: str) -> List[str]:
        # Korean-friendly simple character bi/tri-gram tokenizer
        s = "".join(str(text).split())
        if not s:
            return []
        grams = []
        grams += [s[i:i+2] for i in range(len(s)-1)]  # bi-gram
        grams += [s[i:i+3] for i in range(len(s)-2)]  # tri-gram
        return grams
