from __future__ import annotations
from typing import List, Dict, Any, Iterable
import json
import re
from openai import OpenAI
from .config import settings
from .prompts import SYSTEM_PROMPT, build_user_prompt
from .llm_gemini import GeminiLLM

def _strip_passage_prefix(text: str) -> str:
    if text.startswith("passage: "):
        return text[len("passage: "):]
    return text

def _clean_ctx(text: str) -> str:
    """UI 찌꺼기 제거 + 스니펫 정리"""
    trash = [
        r"위 도움말이 도움이 되었나요\??", r"별점\d점", r"보내기", r"도움말 닫기",
        r"관련된 다른 정책이 궁금하신가요\?", r"수수료/정산 주기에 대해 더 안내해드릴까요\?",
        r"상품 등록 절차를 도와드릴까요\?"
    ]
    out = text
    for pattern in trash:
        out = re.sub(pattern, " ", out)
    return re.sub(r"\s{2,}", " ", out).strip()

def build_prompt(context: List[Dict[str, Any]], history_text: str, user_msg: str) -> List[Dict[str,str]]:
    # Build a compact context block (제목/URL/본문요약)
    ctx_items = []
    for i, d in enumerate(context, start=1):
        raw = d.get("text","") or ""
        snippet = _clean_ctx(_strip_passage_prefix(raw))[:900]  # 길이 축소
        ctx_items.append({
            "index": i,
            "title": d.get("title",""),
            "url": d.get("url",""),
            "snippet": snippet,
        })
    ctx_json = json.dumps(ctx_items, ensure_ascii=False, indent=2)

    # 새로운 프롬프트 빌더 사용
    user_content = build_user_prompt(ctx_json, history_text, user_msg)

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_content}
    ]
    return messages

class LLM:
    def __init__(self):
        self.provider = settings.llm_provider
        if self.provider == "openai":
            self.client = OpenAI(api_key=settings.openai_api_key)
            self.model = settings.openai_chat_model
        elif self.provider == "gemini":
            self.gemini = GeminiLLM()
        else:
            raise ValueError(f"Unsupported LLM provider: {self.provider}")

    def stream_answer(self, messages: List[Dict[str,str]]) -> Iterable[str]:
        if self.provider == "openai":
            # OpenAI 스트리밍
            with self.client.chat.completions.stream(
                model=self.model,
                messages=messages,
                temperature=0.2,
                top_p=0.9,
                max_tokens=700
            ) as stream:
                for event in stream:
                    if event.type == "content.delta":
                        delta = event.delta
                        if delta:
                            yield delta
        elif self.provider == "gemini":
            # Gemini 스트리밍
            yield from self.gemini.stream_answer(messages)
