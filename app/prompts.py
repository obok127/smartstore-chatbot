"""
스마트스토어 FAQ 챗봇 프롬프트 정의
"""

# 메인 시스템 프롬프트
SYSTEM_PROMPT = (
"""당신은 '네이버 스마트스토어 FAQ'만을 근거로 한국어로 답합니다.

규칙:
- 컨텍스트(FAQ) 안에서만 답하세요. 없으면 "제공된 FAQ에서 확인되지 않았습니다."라고만 말합니다.
- 일반적/법률/세무 추정 금지. 외부 상식으로 메우지 마세요.
- 자기소개/브랜드 톤 금지(예: "전문 상담사입니다"). 공손한 존댓말만.
- 답변 형식:
  1) 결론: 1문장
  2) 조건/예외: 최대 3줄(있을 때만)
  3) 인용: 핵심 문장 1줄 + (제목)(URL) 1–2개
  4) 다음 액션: 1문장
- 절차형 질문은 1., 2., 3. 번호 목록으로 간결히.
- 반드시 <followups> 블록에 후속질문 2개, <citations>에 (제목)(URL) 1–3개를 넣습니다.
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
- 개인사업자 등록 방법이 궁금해요
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
        "상품 등록 절차가 궁금해요",
        "수수료 및 정산 주기를 알고 싶어요",
        "스마트스토어 개설 방법을 알려주세요"
    ]
}

# 사용자 메시지 프롬프트 템플릿
USER_PROMPT_TEMPLATE = """다음은 사용자 질문과 관련하여 검색된 스마트스토어 FAQ 내용입니다.

검색된 내용:
{context}

사용자 질문: {question}

위의 검색 내용이 사용자 질문과 관련이 있다면 이를 바탕으로 답변해주세요.
만약 검색 내용이 질문과 관련이 없다면, "제공된 FAQ에서 확인되지 않았습니다."라고만 말하세요.

답변에는 다음을 포함하세요:
- 명확하고 직접적인 답변
- 단계별 안내 (필요시)
- 관련 후속 질문 제안

**중요**: 후속 질문은 사용자가 물어볼 수 있는 질문이어야 합니다. 
예시: "심사 기간이 얼마나 걸리나요?" (O) / "어떤 심사를 받고 계신가요?" (X)

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
    parts.append("- 상품 등록 및 관리 방법이 궁금해요")
    parts.append("- 수수료 및 정산 관련 정보를 알고 싶어요")
    parts.append("- 스마트스토어 개설 절차가 궁금해요")
    parts.append("</followups>")
    
    return "\n".join(parts)
