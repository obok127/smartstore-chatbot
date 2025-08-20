import argparse, os, requests
from pathlib import Path
import pandas as pd

"""
오프라인 전처리 인덱서
- 입력 pkl에서 문서 로드
- (옵션) 로컬 임베딩(bge-m3 등)으로 임베딩 생성
- Chroma에 업서트 또는 파일로 임베딩 저장
"""

def normalize_to_docs(obj):
    if isinstance(obj, pd.DataFrame):
        df = obj
    elif isinstance(obj, list):
        if obj and isinstance(obj[0], dict):
            df = pd.DataFrame(obj)
        elif obj and isinstance(obj[0], (list, tuple)) and len(obj[0]) >= 2:
            df = pd.DataFrame(obj, columns=["question","answer"])  # naive
        else:
            raise ValueError("Unsupported list format")
    elif isinstance(obj, dict):
        rows = []
        for k,v in obj.items():
            if isinstance(v, str):
                rows.append({"question": str(k), "answer": v})
            elif isinstance(v, dict):
                q = v.get("question") or v.get("질문") or str(k)
                a = v.get("answer") or v.get("답변") or v.get("내용") or ""
                url = v.get("url") or v.get("링크") or ""
                title = v.get("title") or v.get("제목") or str(k)
                cat = v.get("category") or v.get("카테고리") or ""
                rows.append({"question":q,"answer":a,"url":url,"title":title,"category":cat})
            else:
                rows.append({"question": str(k), "answer": str(v)})
        df = pd.DataFrame(rows)
    else:
        raise ValueError(f"Unsupported object: {type(obj)}")

    for col in ["question","answer","url","title","category"]:
        if col not in df.columns: df[col] = ""

    docs = []
    for i, row in df.iterrows():
        _id = str(row.get("id") or row.get("url") or f"doc-{i}")
        q = str(row.get("question",""))
        a = str(row.get("answer",""))
        title = str(row.get("title","")) or q[:40]
        url = str(row.get("url",""))
        cat = str(row.get("category",""))
        text = (q+"\n"+a).strip()
        if text:
            docs.append({"id":_id,"text":text,"title":title,"url":url,"category":cat})
    return docs

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pkl", required=True, help="Path or URL to final_result.pkl")
    ap.add_argument("--out_chroma", default="data/chroma", help="Chroma path to persist")
    ap.add_argument("--use_local", action="store_true", help="Use local embeddings (sentence-transformers)")
    ap.add_argument("--model", default="BAAI/bge-m3", help="Local embedding model name")
    ap.add_argument("--device", default="cpu", help="Embedding device: cpu|mps|cuda")
    ap.add_argument("--batch", type=int, default=16, help="Embedding batch size")
    args = ap.parse_args()

    path = args.pkl
    if path.startswith("http"):
        print(f"Downloading {path} ...")
        r = requests.get(path, timeout=60)
        r.raise_for_status()
        Path("final_result.pkl").write_bytes(r.content)
        path = "final_result.pkl"

    obj = pd.read_pickle(path)
    docs = normalize_to_docs(obj)
    print(f"Docs: {len(docs)}")

    # Build embeddings
    vectors = None
    if args.use_local:
        from sentence_transformers import SentenceTransformer
        import numpy as np
        m = SentenceTransformer(args.model, device=args.device)
        texts = [d["text"] for d in docs]
        vecs = m.encode(
            texts,
            batch_size=max(1, args.batch),
            show_progress_bar=True,
            normalize_embeddings=True,
        )
        vectors = [v.tolist() for v in vecs]

    # Upsert to Chroma
    import chromadb
    from chromadb.config import Settings as ChromaSettings
    client = chromadb.PersistentClient(path=args.out_chroma, settings=ChromaSettings(allow_reset=False))
    col = client.get_or_create_collection(name="smartstore_faq", metadata={"hnsw:space":"cosine"})
    ids = [d["id"] for d in docs]
    metadatas = [{"title":d.get("title",""),"url":d.get("url",""),"category":d.get("category","")} for d in docs]
    texts = [d["text"] for d in docs]
    col.upsert(ids=ids, metadatas=metadatas, documents=texts, embeddings=vectors)
    print("Chroma upsert done.")

if __name__ == "__main__":
    main()
