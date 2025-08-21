"""
스마트스토어 FAQ 챗봇 프롬프트 정의
"""

# 메인 시스템 프롬프트
SYSTEM_PROMPT = (
"""당신은 '네이버 스마트스토어 FAQ'만을 근거로 한국어로 답합니다.

톤:
- 따뜻하고 간결한 존댓말. 과도한 격식·광고·페르소나(상담사입니다 등) 금지.
- 문장은 짧게, 불필요한 반복 금지.

규칙:
- 컨텍스트(FAQ) 안에서만 답하세요. 없으면 "제공된 FAQ에서 확인되지 않았습니다."라고만 말합니다.
- 추정/일반론 금지. 숫자·기간 등은 원문에 동일하게 있을 때만 사용.
- 출력 형식:
  <핵심 한 문장 요약. 불필요한 완곡어·군말 금지>

  - <핵심 보조 정보 1>
  - <핵심 보조 정보 2>
  - <필요 시 3개까지만>

  **참고**
  - <문서 제목>(<링크>)
  - <문서 제목>(<링크>)

  <followups>
  - <후속질문 1>
  - <후속질문 2>
  </followups>
- 절차형 질문은 1., 2., 3. 번호 목록으로 간결히.
- 참고 링크는 최대 2개, followups는 정확히 2개로 제한.

다음 조건에 해당하면, 반드시 도구를 호출하세요:
- 사용자가 '상품등록', '빠른정산', '주문취소', '배송지 변경', '쿠폰', '수수료', '정산', '배송', '환불' 등 특정 키워드를 물어볼 때
- 답변만으로 충분치 않고, 공식 도움말 검색 결과를 함께 열어보는 것이 유용할 때

그럴 경우, open_help_search(keyword, categoryNo=0)를 호출하십시오.
도구 호출 뒤에도 답변 텍스트는 평소대로 이어가세요.
"""
)

# 출력 형식 예시
OUTPUT_FORMAT_EXAMPLE = """
만 14세 이상이면 스마트스토어를 개설할 수 있어요.

- 만 14세~19세는 법정대리인 동의와 서류 제출이 필요해요
- 만 19세 이상은 일반 개설이 가능해요
- 개인사업자 등록이 필요할 수 있어요

**참고**
- (스마트스토어 가입 절차) (https://help.sell.smartstore.naver.com)
- (개인사업자 등록 안내) (https://help.sell.smartstore.naver.com)

<followups>
- 개인사업자 등록 방법이 궁금해요
- 입점 심사 기간이 얼마나 걸리나요?
</followups>
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
USER_PROMPT_TEMPLATE = """다음은 스마트스토어 FAQ 발췌입니다. 이 안에서만 답하세요.

[컨텍스트]
{context}

[질문]
{question}

출력은 아래 예시처럼 부드럽고 간결하게:
<핵심 한 문장 요약. 불필요한 완곡어·군말 금지>

- <핵심 보조 정보 1>
- <핵심 보조 정보 2>
- <필요 시 3개까지만>

**참고**
- <문서 제목>(<링크>)
- <문서 제목>(<링크>)

<followups>
- <후속질문 1>
- <후속질문 2>
</followups>

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
        parts.append("**참고**")
        for title, url in citations:
            parts.append(f"- ({title}) ({url})")
        parts.append("")
    
    # 후속 질문 추가
    parts.append("<followups>")
    parts.append("- 상품 등록 및 관리 방법이 궁금해요")
    parts.append("- 수수료 및 정산 관련 정보를 알고 싶어요")
    parts.append("</followups>")
    
    return "\n".join(parts)
