"""
스마트스토어 FAQ 챗봇 프롬프트 정의
"""

# 메인 시스템 프롬프트
SYSTEM_PROMPT = (
"""당신은 네이버 스마트스토어 전문 상담사입니다. 친근하고 실용적인 도움을 제공하세요.

답변 원칙:
1) 검색된 정보가 질문과 직접적으로 관련 있을 때만 사용하세요
2) 관련 정보가 없으면 솔직히 "관련 정보를 찾지 못했습니다"라고 말하고 일반적인 안내를 제공하세요
3) 자연스럽고 친근한 톤으로 단계별 안내를 해주세요
4) 형식적인 [결론], [근거 인용] 같은 표현은 사용하지 마세요
5) 구체적이고 실행 가능한 정보를 우선적으로 제공하세요

답변 스타일:
- 명확하고 직접적인 답변
- 단계별 안내 (필요시)
- 추가 도움을 받을 수 있는 방법
- 2-3개의 관련 후속 질문 제안

반드시 답변 끝에 <followups> … </followups> 블록을 넣어 2~3개의 후속질문을 제안하고, 
인용이 가능하면 <citations> … </citations> 블록에 (제목) (URL) 형태로 최대 3개 넣습니다.
"""
)

# 출력 형식 예시
OUTPUT_FORMAT_EXAMPLE = """
네, 만 14세 이상이면 스마트스토어를 개설할 수 있습니다!

**연령별 조건:**
- 만 14세~19세: 법정대리인 동의 + 서류 제출 필요
- 만 19세 이상: 일반 개설 가능

**필요 서류:**
1. 법정대리인 인감증명서 (최근 3개월 이내)
2. 가족관계증명서

더 궁금한 점이 있으시면 언제든 물어보세요!

<followups>
- 개인사업자 등록 방법이 궁금하신가요?
- 입점 심사 기간이 얼마나 걸리나요?
- 필요한 서류가 더 있나요?
</followups>

<citations>
- (스마트스토어 가입 절차) (https://help.sell.smartstore.naver.com)
</citations>
"""

# 폴백 프롬프트 (LLM 오류 시 사용)
FALLBACK_PROMPTS = {
    "conclusion": "[결론]: 아래 안내는 제공된 FAQ의 요약입니다.",
    "condition": "[조건/예외]: 상품/카테고리에 따라 세부 요건이 다를 수 있습니다.",
    "action": "[다음 액션]: 더 구체적인 상황을 알려주시면 단계별 체크리스트를 드리겠습니다.",
    "followups": [
        "관련된 다른 정책이 궁금하신가요?",
        "수수료/정산 주기에 대해 더 안내해드릴까요?",
        "상품 등록 절차를 도와드릴까요?"
    ]
}

# 사용자 메시지 프롬프트 템플릿
USER_PROMPT_TEMPLATE = """다음은 사용자 질문과 관련하여 검색된 스마트스토어 FAQ 내용입니다.

검색된 내용:
{context}

사용자 질문: {question}

위의 검색 내용이 사용자 질문과 관련이 있다면 이를 바탕으로 친근하고 실용적인 답변을 해주세요.
만약 검색 내용이 질문과 관련이 없다면, 솔직히 "관련 정보를 찾지 못했습니다"라고 말하고 일반적인 도움말을 제공해주세요.

답변에는 다음을 포함하세요:
- 명확하고 직접적인 답변
- 단계별 안내 (필요시)
- 추가 도움을 받을 수 있는 방법
- 2-3개의 관련 후속 질문 제안

[출력 형식 예시]
{output_format}
"""

def build_user_prompt(context: str, history: str, question: str) -> str:
    """사용자 메시지 프롬프트를 생성합니다."""
    return USER_PROMPT_TEMPLATE.format(
        context=context,
        question=question,
        output_format=OUTPUT_FORMAT_EXAMPLE
    )

def build_fallback_response(faq_text: str, citations: list) -> str:
    """폴백 응답을 생성합니다."""
    parts = []
    
    # 친근한 폴백 응답
    parts.append("죄송합니다. 해당 질문에 대한 구체적인 정보를 찾지 못했습니다.")
    parts.append("")
    parts.append("스마트스토어 관련 문의는 다음 방법으로 해결하실 수 있습니다:")
    parts.append("- 스마트스토어 고객센터: 1588-3819")
    parts.append("- 스마트스토어 센터 도움말 섹션")
    parts.append("- 네이버 비즈니스 스쿨 교육 자료")
    parts.append("")
    
    # 인용 추가
    if citations:
        parts.append("<citations>")
        for title, url in citations:
            parts.append(f"- ({title}) ({url})")
        parts.append("</citations>")
    
    # 후속 질문 추가
    parts.append("<followups>")
    parts.append("- 상품 등록 및 관리 방법이 궁금하신가요?")
    parts.append("- 수수료 및 정산 관련 정보를 알고 싶으신가요?")
    parts.append("- 스마트스토어 개설 절차가 궁금하신가요?")
    parts.append("</followups>")
    
    return "\n".join(parts)
