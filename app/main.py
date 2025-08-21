from __future__ import annotations
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse, FileResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Dict, Any
import json, uuid, os
import re
import pandas as pd
from urllib.parse import quote_plus
from .schemas import ChatRequest, ChatChunk, ChatResponse, IndexRequest, ConversationHistory, Message
from .retriever import Retriever
from .memory import ConversationMemory
from .llm import LLM, build_prompt
from .config import settings
from .guard import is_on_topic, detect_intent
from .prompts import build_fallback_response

# 배포 환경에서 데이터 다운로드
def ensure_data_exists():
    """배포 환경에서 필요한 데이터 파일이 존재하는지 확인하고 다운로드합니다."""
    data_path = "data/final_result.pkl"
    
    if not os.path.exists(data_path):
        print("📥 배포 환경에서 데이터 파일이 없습니다. 다운로드를 시도합니다...")
        try:
            # 데이터 다운로드 스크립트 실행
            import subprocess
            result = subprocess.run(["python", "scripts/download_data.py"], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                print("✅ 데이터 다운로드 완료")
            else:
                print(f"❌ 데이터 다운로드 실패: {result.stderr}")
        except Exception as e:
            print(f"❌ 데이터 다운로드 스크립트 실행 실패: {e}")
            print("⚠️  수동으로 data/final_result.pkl 파일을 추가해주세요.")

app = FastAPI(title="SmartStore FAQ RAG (no-langchain)",
              description="Streaming RAG chatbot for Naver SmartStore FAQ",
              version="1.3.0")

# Enable CORS for local development and file/other origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

retriever = Retriever()
memory = ConversationMemory()
llm = LLM()


def make_help_links(q: str):
    base = "https://help.sell.smartstore.naver.com/index.help"
    search = f"https://help.sell.smartstore.naver.com/faq/search.help?categoryNo=0&searchKeyword={quote_plus(q)}"
    return base, search


@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/")
def serve_frontend_root():
    import os
    root = os.path.dirname(os.path.dirname(__file__))
    html_path = os.path.join(root, "smart_store_faq_chat_frontend_index.html")
    if os.path.exists(html_path):
        return FileResponse(html_path, media_type="text/html; charset=utf-8")
    return HTMLResponse("<h1>Frontend file not found</h1>", status_code=404)


@app.post("/index")
def index(req: IndexRequest):
    path = req.pkl_path
    if not os.path.exists(path):
        raise HTTPException(status_code=400, detail=f"File not found: {path}")

    if req.reset:
        retriever.reset()

    # Load .pkl (supports DataFrame, list[dict], list[(q,a)], dict[q->str|dict])
    try:
        obj = pd.read_pickle(path)
        if isinstance(obj, pd.DataFrame):
            df = obj
        elif isinstance(obj, list):
            if len(obj) > 0 and isinstance(obj[0], dict):
                df = pd.DataFrame(obj)
            elif len(obj) > 0 and isinstance(obj[0], (list, tuple)) and len(obj[0]) >= 2:
                # Assume (question, answer, ...)
                df = pd.DataFrame(obj, columns=["question", "answer"])  # extra cols ignored
            else:
                raise ValueError("Unsupported list format in pkl. Expect list of dicts or list of (q,a)")
        elif isinstance(obj, dict):
            rows = []
            for k, v in obj.items():
                if isinstance(v, str):
                    rows.append({"question": str(k), "answer": v})
                elif isinstance(v, dict):
                    q = v.get("question") or v.get("질문") or str(k)
                    a = v.get("answer") or v.get("답변") or v.get("내용") or ""
                    url = v.get("url") or v.get("링크") or ""
                    title = v.get("title") or v.get("제목") or str(k)
                    cat = v.get("category") or v.get("카테고리") or ""
                    rows.append({
                        "question": str(q),
                        "answer": str(a),
                        "url": str(url),
                        "title": str(title),
                        "category": str(cat),
                    })
                else:
                    rows.append({"question": str(k), "answer": str(v)})
            df = pd.DataFrame(rows)
        else:
            raise ValueError(f"Unsupported object type: {type(obj)}")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to load pkl: {e}")

    # Try to normalize column names
    rename_map = {
        "질문": "question",
        "문의": "question",
        "Q": "question",
        "답변": "answer",
        "A": "answer",
        "링크": "url",
        "제목": "title",
        "카테고리": "category",
    }
    for k, v in rename_map.items():
        if k in df.columns and v not in df.columns:
            df[v] = df[k]

    for col in ["question", "answer", "url", "title", "category"]:
        if col not in df.columns:
            df[col] = ""

    docs = []
    for i, row in df.iterrows():
        _id = str(row.get("id") or row.get("url") or f"doc-{i}")
        q = str(row.get("question","")).strip()
        a = str(row.get("answer","")).strip()
        title = str(row.get("title","")).strip() or q[:40]
        url = str(row.get("url","")).strip()
        cat = str(row.get("category","")).strip()
        # 하나의 FAQ(질문+답변)를 한 청크로 저장
        text = (q + "\n" + a).strip()
        if not text:
            continue
        docs.append({"id": _id, "text": text, "title": title, "url": url, "category": cat})

    if not docs:
        raise HTTPException(status_code=400, detail="No valid docs in the provided pkl.")

    result = retriever.upsert(docs)
    # 통계 정보 추가하여 반환
    try:
        chroma_count = retriever.collection.count()
    except Exception:
        chroma_count = 0
    bm25_loaded = bool(retriever._bm25)
    doc_map_size = len(getattr(retriever, "_doc_map", {}) or {})
    samples = []
    try:
        # 제목 샘플 최대 5개
        for i, d in enumerate(list((getattr(retriever, "_doc_map", {}) or {}).values())[:5]):
            samples.append(d.get("title", ""))
    except Exception:
        samples = []

    out = {
        **result,
        "chroma_count": chroma_count,
        "bm25_loaded": bm25_loaded,
        "doc_map_size": doc_map_size,
        "samples": samples,
    }
    return out

@app.post("/chat/stream")
def chat_stream(req: ChatRequest):
    conv_id = req.conversation_id or str(uuid.uuid4())
    user_msg = req.message.strip()
    top_k = req.top_k or settings.top_k

    if not user_msg:
        raise HTTPException(status_code=400, detail="Empty message.")

    memory.add(conv_id, "user", user_msg)
    history_text = memory.format_as_chat(conv_id, limit=12)
    ctx = retriever.retrieve(user_msg, k=top_k)

    # -------- Intent routing --------
    intent = detect_intent(user_msg, ctx, settings.score_threshold)

    def simple_stream(text: str):
        def gen():
            chunk_size = 90
            for i in range(0, len(text), chunk_size):
                yield f"data: {json.dumps({'type':'token','content': text[i:i+chunk_size]})}\n\n"
            yield "event: done\n"
            yield "data: {}\n\n"
        return StreamingResponse(gen(), media_type="text/event-stream")

    if intent == "greeting":
        msg = (
            "안녕하세요! 스마트스토어 FAQ 전용 챗봇입니다.\n"
            "바로 이렇게 물어보세요:\n"
            "- 미성년자도 스마트스토어를 개설할 수 있나요?\n"
            "- 상품 등록은 어떤 순서로 하나요?\n"
            "- 정산 주기/수수료는 어떻게 되나요?\n"
        )
        return simple_stream(msg)

    if intent == "thanks":
        msg = "도움이 되었다니 다행이에요! 스마트스토어에 대해 더 궁금한 점이 있으면 편하게 물어보세요."
        return simple_stream(msg)

    if intent == "help":
        msg = (
            "사용법 안내 드릴게요. 이 챗봇은 **스마트스토어 공식 FAQ**만을 근거로 짧게 답합니다.\n"
            "예시:\n"
            "- \"미성년자도 개설 가능?\"\n"
            "- \"국내 통신판매업 신고가 필수인가요?\"\n"
            "- \"상품 일괄등록 방법 알려줘\"\n"
            "구체적으로 물어볼수록 더 정확히 안내드려요."
        )
        return simple_stream(msg)

    if intent == "offtopic":
        msg = (
            "저는 스마트스토어 FAQ를 위한 챗봇입니다. 스마트스토어 관련 질문을 부탁드려요.\n\n"
            "예시: 상품 등록 절차, 수수료/정산, 정책/인증, 배송/교환/환불 등"
        )
        return simple_stream(msg)

    # -------- SMART intent: go through LLM (with fallback) --------
    messages = build_prompt(ctx, history_text, user_msg)

    def sse_gen():
        buffer = []
        try:
            for delta in llm.stream_answer(messages):
                buffer.append(delta)
                yield f"data: {json.dumps({'type':'token','content': delta})}\n\n"
            final = "".join(buffer)
            
            # 후처리 훅 적용
            final = _strip_persona(final)
            final = _dedup_followups(final)
            # citations 주입/치환
            cits = _build_citations(ctx)
            final = re.sub(r"<citations>.*?</citations>", cits, final, flags=re.S) if "<citations>" in final else (final + "\n\n" + cits)
            
            if final.strip():
                memory.add(conv_id, "assistant", final[:1500])
            yield "event: done\n"
            yield "data: {}\n\n"
        except Exception as e:
            # LLM 에러 로깅 추가
            import logging
            logging.exception("LLM error", exc_info=True)
            # Fallback: 컨텍스트 기반 간단 답변 (SMART 의도에서만 사용)
            try:
                parts = []
                if ctx:
                    best = ctx[0]
                    full = (best.get('text', '') or '').replace('passage: ', '')
                    if '\n' in full:
                        _, ans = full.split('\n', 1)
                    else:
                        ans = full
                    ans = ans.strip()
                    # Citations
                    cits = []
                    for d in ctx[:3]:
                        t = d.get('title', '') or 'FAQ'
                        u = d.get('url', '') or ''
                        if u:
                            cits.append((t, u))
                    
                    # 새로운 폴백 응답 빌더 사용
                    text = build_fallback_response(ans, cits)
                else:
                    text = "현재 참고할 컨텍스트가 없습니다. 나중에 다시 시도해주세요."
                chunk_size = 90
                for i in range(0, len(text), chunk_size):
                    yield f"data: {json.dumps({'type':'token','content': text[i:i+chunk_size]})}\n\n"
                memory.add(conv_id, "assistant", text[:1500])
            except Exception as _:
                err = f"[server error] {e}"
                yield f"data: {json.dumps({'type':'token','content': err})}\n\n"
            finally:
                yield "event: done\n"
                yield "data: {}\n\n"

    return StreamingResponse(sse_gen(), media_type="text/event-stream")

# 후처리 함수들
def _strip_persona(text: str) -> str:
    """페르소나 제거 (상담사입니다... 안녕하세요... 도입부 컷)"""
    lines = text.splitlines()
    out, started = [], False
    persona = re.compile(r"(상담사입니다|전문가입니다|도와드리겠습니다)", re.I)
    for ln in lines:
        if not started and (ln.strip().startswith("안녕하세요") or persona.search(ln)):
            continue
        started = True
        out.append(ln)
    return "\n".join(out).strip()

def _build_citations(ctx):
    """실제 인용 강제: 리트리버 상위 문서의 (title, url)로 citations 채움"""
    items, seen = [], set()
    for d in ctx[:3]:
        t, u = (d.get("title") or "").strip(), (d.get("url") or "").strip()
        if u and (t,u) not in seen:
            items.append(f"- ({t}) ({u})")
            seen.add((t,u))
    return "<citations>\n" + "\n".join(items) + "\n</citations>" if items else "<citations>\n</citations>"

def parse_answer_v3(text: str):
    """새로운 형식 파서: 라벨 없는 불릿 + 참고 링크"""
    pattern = re.compile(r"""
    ^(?P<summary>[^\n]+)\n+                             # 1) 첫 줄 요약
    (?P<tips>(?:-\s.*\n?)+)?                            # 2) 라벨 없는 불릿 0~N
    \n?\*\*(?:참고|근거)\*\*\s*\n                       # 3) 참고/근거 라벨(고정)
    (?P<refs>(?:-\s.*\n?)+)?                            # 4) 참고 링크 불릿 0~N
    \n?<followups>\s*\n                                 # 5) followups 시작
    (?P<fups>(?:-\s.*\n?)+)                             # 6) 후속질문 1~N
    \s*</followups>\s*$                                 # 7) 종료
    """, re.DOTALL | re.MULTILINE | re.UNICODE | re.VERBOSE)
    
    m = pattern.search(text.strip())
    if not m:
        return None
    
    tips = [l[2:].strip() for l in (m.group("tips") or "").splitlines() if l.strip().startswith("-")][:3]
    refs = [l[2:].strip() for l in (m.group("refs") or "").splitlines() if l.strip().startswith("-")][:2]
    fups = [l[2:].strip() for l in (m.group("fups") or "").splitlines() if l.strip().startswith("-")][:2]
    
    return {
        "summary": m.group("summary").strip(),
        "tips": tips,
        "refs": refs,
        "followups": fups,
    }

def _dedup_followups(text: str) -> str:
    """followups 2개로 정리·중복 제거"""
    m = re.search(r"<followups>(.*?)</followups>", text, flags=re.S)
    if not m:
        return text
    uniq, out = set(), []
    for ln in m.group(1).splitlines():
        ln = ln.strip()
        if ln.startswith("-"):
            key = ln[1:].strip().lower()
            if key and key not in uniq:
                uniq.add(key)
                out.append(ln)
        if len(out) >= 2:
            break
    newblk = "<followups>\n" + ("\n".join(out) if out else "- 다른 점도 도와드릴까요?") + "\n</followups>"
    return text[:m.start()] + newblk + text[m.end():]

@app.get("/debug/llm_status")
def debug_llm_status():
    """LLM 설정과 간단한 테스트를 수행합니다."""
    try:
        # LLM 설정 확인
        model_info = {
            "provider": settings.llm_provider,
            "model": settings.openai_chat_model if settings.llm_provider == "openai" else "gemini-1.5-flash",
            "api_key_set": bool(settings.openai_api_key if settings.llm_provider == "openai" else settings.gemini_api_key),
            "api_key_prefix": (settings.openai_api_key[:10] + "..." if settings.openai_api_key else "NOT SET") if settings.llm_provider == "openai" else (settings.gemini_api_key[:10] + "..." if settings.gemini_api_key else "NOT SET")
        }
        
        # 간단한 LLM 테스트
        test_messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Say 'OK' only."}
        ]
        
        response = ""
        for delta in llm.stream_answer(test_messages):
            response += delta
            if len(response) > 10:  # 너무 길면 중단
                break
        
        return {
            "status": "OK",
            "model_info": model_info,
            "test_response": response.strip(),
            "test_success": "OK" in response
        }
    except Exception as e:
        return {
            "status": "ERROR",
            "error": str(e),
            "model_info": {
                "provider": settings.llm_provider,
                "model": settings.openai_chat_model if settings.llm_provider == "openai" else "gemini-1.5-flash",
                "api_key_set": bool(settings.openai_api_key if settings.llm_provider == "openai" else settings.gemini_api_key),
                "api_key_prefix": (settings.openai_api_key[:10] + "..." if settings.openai_api_key else "NOT SET") if settings.llm_provider == "openai" else (settings.gemini_api_key[:10] + "..." if settings.gemini_api_key else "NOT SET")
            }
        }

@app.get("/debug/embedding_status")
def debug_embedding_status():
    """임베딩 모델 상태 확인"""
    try:
        from .embeddings import LocalEmbedder
        embedder = LocalEmbedder()
        test_embedding = embedder.embed_one("test")
        
        return {
            "embed_model": embedder.model_name,
            "embed_dim": len(test_embedding),
            "index_dim": 1024,  # ChromaDB 컬렉션에서 확인한 차원
            "dimension_match": len(test_embedding) == 1024,
            "config_model": settings.local_embed_model,
            "config_device": settings.local_embed_device
        }
    except Exception as e:
        return {"error": str(e)}

@app.get("/debug/env")
def debug_env():
    """환경 변수 및 작업 경로 확인"""
    import os
    keys = ["USE_LOCAL_EMBEDDINGS","LOCAL_EMBED_MODEL","LOCAL_EMBED_DEVICE",
            "EXPECTED_EMBED_DIM","CHROMA_PATH","SQLITE_PATH","ENV_FILE"]
    return {
        "cwd": os.getcwd(),
        "env": {k: os.getenv(k) for k in keys}
    }

@app.get("/debug/parse_test")
def debug_parse_test():
    """새로운 파서 테스트"""
    test_text = """만 14세 이상이면 스마트스토어를 개설할 수 있어요.

- 만 14세~19세는 법정대리인 동의와 서류 제출이 필요해요
- 만 19세 이상은 일반 개설이 가능해요
- 개인사업자 등록이 필요할 수 있어요

**참고**
- (스마트스토어 가입 절차) (https://help.sell.smartstore.naver.com)
- (개인사업자 등록 안내) (https://help.sell.smartstore.naver.com)

<followups>
- 개인사업자 등록 방법이 궁금해요
- 입점 심사 기간이 얼마나 걸리나요?
</followups>"""
    
    parsed = parse_answer_v3(test_text)
    return {
        "original": test_text,
        "parsed": parsed,
        "success": parsed is not None
    }

@app.get("/debug/model_info")
def debug_model_info():
    """실제 로드되는 모델 정보 확인"""
    try:
        from .embeddings import LocalEmbedder
        embedder = LocalEmbedder()
        test_embedding = embedder.embed_one("test")
        
        return {
            "model_name": embedder.model_name,
            "model_dim": embedder.dim,
            "test_embedding_shape": len(test_embedding),
            "config_model": settings.local_embed_model,
            "config_device": settings.local_embed_device,
            "model_loaded_successfully": True
        }
    except Exception as e:
        return {
            "error": str(e),
            "config_model": settings.local_embed_model,
            "config_device": settings.local_embed_device,
            "model_loaded_successfully": False
        }

@app.post("/debug/rebuild_dense")
def debug_rebuild_dense(batch_size: int = 256):
    try:
        out = retriever.rebuild_dense_from_docmap(batch_size=batch_size)
        return {"status": "ok", **out}
    except Exception as e:
        return {"status": "error", "error": str(e)}

@app.get("/debug/index_status")
def debug_index_status(q: str = "상품 등록 절차", k: int = 3):
    try:
        chroma_count = retriever.collection.count()
    except Exception:
        chroma_count = 0
    bm25_loaded = bool(retriever._bm25)
    doc_map_size = len(getattr(retriever, "_doc_map", {}) or {})
    dense_ok = bool(getattr(retriever, "dense_ok", False))

    preview = []
    try:
        hits = retriever.retrieve(q, k=k)
        for h in hits:
            preview.append({
                "id": h.get("id"),
                "title": h.get("title"),
                "score": round(float(h.get("score", 0.0)), 4),
                "has_url": bool(h.get("url")),
                "snippet": (h.get("text", "") or "")[:160]
            })
    except Exception:
        preview = []

    return {
        "chroma_path": settings.chroma_path,
        "chroma_count": chroma_count,
        "bm25_loaded": bm25_loaded,
        "doc_map_size": doc_map_size,
        "dense_ok": dense_ok,
        "sample_query": q,
        "preview": preview,
    }

@app.get("/conversations/{conversation_id}")
def get_history(conversation_id: str):
    rows = memory.fetch(conversation_id, limit=50)
    msgs = [Message(role=r, content=c) for r, c in rows]
    return ConversationHistory(conversation_id=conversation_id, messages=msgs)
