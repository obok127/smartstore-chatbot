import argparse, csv, json, re, time
from pathlib import Path
import requests

HEADERS = {"Content-Type": "application/json"}

PATTERNS = {
    "has_headings": re.compile(r"(요점|근거|다음으로)"),
    "has_citations": re.compile(r"<citations>.*?\(http", re.S),
    "persona_violation": re.compile(r"(상담사입니다|전문가입니다|안녕하세요)"),
    "offtopic_msg": re.compile(r"스마트스토어.*질문을 부탁|제공된 FAQ에서 확인되지 않았습니다"),
}

def sse_post(url, payload, timeout=60):
    """Stream SSE text from /chat/stream and return the concatenated final text."""
    with requests.post(url, json=payload, headers=HEADERS, stream=True, timeout=timeout) as r:
        r.raise_for_status()
        chunks = []
        for line in r.iter_lines(decode_unicode=True):
            if not line:
                continue
            if line.startswith("data:"):
                data = line[5:].strip()
                if data == "[DONE]":
                    break
                try:
                    obj = json.loads(data)
                except Exception:
                    continue
                if obj.get("type") == "chunk":
                    chunks.append(obj.get("text", ""))
        return "".join(chunks)

def get_index_status(base_url, q, k=3):
    try:
        resp = requests.get(f"{base_url}/debug/index_status", params={"q": q, "k": k}, timeout=30)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        return {"error": str(e)}

def score_answer(text, idx_status):
    s = {
        "len": len(text),
        "has_headings": bool(PATTERNS["has_headings"].search(text)),
        "has_citations": bool(PATTERNS["has_citations"].search(text)),
        "persona_violation": bool(PATTERNS["persona_violation"].search(text)),
        "offtopic_flag": bool(PATTERNS["offtopic_msg"].search(text)),
        "chroma_count": idx_status.get("chroma_count"),
        "top_titles": ", ".join([d.get("title","") for d in idx_status.get("top_docs",[])]) if isinstance(idx_status.get("top_docs"), list) else "",
    }
    # Simple quality heuristic: headings + citations present, no persona
    s["quality_ok"] = int(s["has_headings"] and s["has_citations"] and not s["persona_violation"])
    return s

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default="http://127.0.0.1:8000", help="Backend base URL")
    ap.add_argument("--conv", default="eval", help="Conversation ID")
    ap.add_argument("--infile", default="eval_queries_ko.txt")
    ap.add_argument("--out", default="eval_results.csv")
    args = ap.parse_args()

    queries = Path(args.infile).read_text(encoding="utf-8").strip().splitlines()
    rows = []
    for q in queries:
        t0 = time.time()
        text = sse_post(f"{args.base}/chat/stream", {"conversation_id": args.conv, "message": q})
        t1 = time.time()
        idx = get_index_status(args.base, q, k=3)
        s = score_answer(text, idx)
        s["query"] = q
        s["latency_ms"] = int((t1 - t0) * 1000)
        s["answer_preview"] = (text[:160] + "…") if len(text) > 180 else text
        rows.append(s)

    fieldnames = [
        "query","quality_ok","has_headings","has_citations","persona_violation",
        "offtopic_flag","len","latency_ms","chroma_count","top_titles","answer_preview"
    ]
    with open(args.out, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(rows)

    total = len(rows)
    ok = sum(r["quality_ok"] for r in rows)
    avg_lat = sum(r["latency_ms"] for r in rows) // max(1, total)
    print(f"Quality OK: {ok}/{total} ({ok/total*100:.1f}%)")
    print(f"Avg latency: {avg_lat} ms")
    print(f"Results saved to {args.out}")

if __name__ == "__main__":
    main()
