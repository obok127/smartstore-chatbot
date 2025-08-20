from __future__ import annotations
from typing import List, Dict, Any, Iterable
import google.generativeai as genai
from .config import settings

class GeminiLLM:
    def __init__(self):
        genai.configure(api_key=settings.gemini_api_key)
        self.model = genai.GenerativeModel('gemini-1.5-flash')
        
    def stream_answer(self, messages: List[Dict[str,str]]) -> Iterable[str]:
        """Gemini API를 사용해서 스트리밍 응답을 생성합니다."""
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
                    
        except Exception as e:
            # 에러 발생 시 간단한 폴백 메시지
            yield f"[Gemini API 오류: {str(e)}]"
            yield " 제공된 FAQ 정보를 기반으로 답변을 생성할 수 없습니다."
