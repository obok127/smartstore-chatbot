from __future__ import annotations
from typing import List, Dict, Any, Iterable, Optional
import google.generativeai as genai
import time
import random
from .config import settings
from .utils.help_links import build_help_search_url

# === 1) 함수 선언 ===
open_help_decl = {
    "name": "open_help_search",
    "description": "스마트스토어 도움말(FAQ)에서 keyword로 검색하는 링크를 생성합니다.",
    "parameters": {
        "type": "object",
        "properties": {
            "keyword": {"type": "string", "description": "검색 키워드 (예: '상품등록')"},
            "categoryNo": {"type": "integer", "description": "도움말 카테고리 번호 (모르면 0)"},
        },
        "required": ["keyword"],
    },
}

TOOLS = [{"function_declarations": [open_help_decl]}]

def handle_tool_call(name: str, args: dict) -> Optional[dict]:
    """툴 호출을 처리하고 결과를 반환합니다."""
    if name == "open_help_search":
        keyword = str(args.get("keyword") or "스마트스토어")
        category_no = int(args.get("categoryNo") or 0)
        url = build_help_search_url(keyword, category_no)
        return {
            "tool": "open_help_search", 
            "url": url, 
            "keyword": keyword, 
            "categoryNo": category_no
        }
    return None

class GeminiLLM:
    def __init__(self):
        genai.configure(api_key=settings.gemini_api_key)
        self.model = genai.GenerativeModel(
            'gemini-1.5-flash',
            tools=TOOLS,
            tool_config={"function_calling_config": {"mode": "AUTO"}}
        )
        self.max_retries = 3
        self.timeout = 30
        
    def stream_answer(self, messages: List[Dict[str,str]]) -> Iterable[str]:
        """Gemini API를 사용해서 스트리밍 응답을 생성합니다."""
        for attempt in range(self.max_retries):
            try:
                # Gemini는 system message를 지원하지 않으므로 user message에 포함
                if messages[0]["role"] == "system":
                    system_content = messages[0]["content"]
                    user_content = messages[1]["content"]
                    combined_content = f"{system_content}\n\n{user_content}"
                    messages = [{"role": "user", "content": combined_content}]
                
                # Gemini API 호출
                response = self.model.generate_content(
                    messages[0]["content"],
                    stream=True,
                    generation_config=genai.types.GenerationConfig(
                        temperature=0.3,
                        top_p=0.9,
                        max_output_tokens=700,
                    )
                )
                
                # 스트리밍 응답
                for chunk in response:
                    if chunk.text:
                        yield chunk.text
                return  # 성공시 반복 종료
                    
            except Exception as e:
                if attempt == self.max_retries - 1:
                    # 최종 실패시 표준화된 에러 메시지
                    yield "죄송합니다. 일시적인 서비스 오류가 발생했습니다. 잠시 후 다시 시도해주세요."
                    return

                # 지수 백오프로 재시도
                wait_time = (2 ** attempt) + random.uniform(0, 1)
                time.sleep(wait_time)
