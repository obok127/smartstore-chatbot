from typing import List, Dict, Any

SMART_KEYWORDS = [
    # 기본 키워드
    "스마트스토어","스마트 스토어","네이버페이","판매자센터","입점","수수료","정산","환불","교환","배송","노출","상품등록","카테고리","광고","리뷰","페널티",
    "사업자","통합매니저","주매니저","스토어","정책","인증","카테고리 변경","반품","원부","원산지","재고","딜","쿠폰","포인트","사입","세금계산서",
    
    # 회원 관리
    "회원가입","신규 회원가입","초대","아이디","비밀번호","탈퇴","재가입","2단계 인증",
    
    # 상품 관리
    "상품관리","상품 조회","상품 수정","상품 등록","상품 일괄등록","카달로그","가격관리","연관상품","사진 보관함","배송정보","템플릿","공지사항","검색품질","SEO","구독 관리","상품진단","상품명 마스터",
    
    # 쇼핑윈도
    "쇼핑윈도","쇼핑윈도 상품","쇼핑윈도 소식","쇼핑윈도 스토어",
    
    # 판매 관리
    "판매관리","주문통합검색","선물 수락","미결제확인","발주","주문확인","발송관리","배송현황","구매확정","취소 관리","반품 관리","교환 관리","판매방해",
    
    # 고객 관리
    "고객관리","반품안심케어","고객문의","리뷰 관리","리뷰이벤트","그룹상품","상품상세","블로그글","톡톡","쇼핑챗봇","AI FAQ",
    
    # 정산 관리
    "정산관리","정산 내역","일별","건별","항목별 정산","부가세신고","세금계산서","비즈월렛","통합 정산","중소상공인수수료","빠른정산","초보판매자","우대수수료","환급내역","수수료개편",
    
    # 스토어 관리
    "스토어관리","카테고리 관리","쇼핑스토리","쇼핑라이브","숏클립","CLOVA MD","상품추천","기본정보","API 관리","SNS 설정","쇼핑윈도 노출","네이버 서비스","가격비교",
    
    # 혜택/마케팅
    "혜택","마케팅","혜택 등록","혜택 조회","혜택 리포트","포인트","고객등급","마케팅 보내기","마케팅 이력","마케팅 통계","AI 마케팅","효과분석","마케팅 링크","브랜드 혜택","고객군","타겟팅","성과분석",
    
    # 라운지
    "라운지","라운지 노출","라운지 가입","라운지 멤버","라운지 스토리","라운지 통계",
    
    # 커머스솔루션
    "커머스솔루션","솔루션 목록","결제내역","소비자조사","Quick 모니터링","쇼핑 커넥트",
    
    # 데이터 분석
    "데이터 분석","스토어분석","요약","판매분석","마케팅분석","쇼핑행동분석","시장벤치마크","판매성과예측","고객현황","재구매","통계",
    
    # 광고 관리
    "광고관리","쇼핑버티컬광고","CRM 마케팅","타겟 광고","프로모션","기획전","참여형 프로모션","원쁠딜","원쁠템","미스터 N",
    
    # 배송 관리
    "배송 관리","N배송","N배송 프로그램","풀필먼트","풀필먼트 신청","풀필먼트 주문","N판매자배송","판매자 창고","N판매자배송 운영","N배송 재고",
    
    # 판매자 정보
    "판매자 정보","내정보","매니저 관리","판매자 등급","정보 변경","양도양수","사업자 전환","상품판매권한","고객확인제도","심사내역","판매자 지원","성장 마일리지",
    
    # 공지사항
    "공지사항","공통","기타","기본 이용방법","알림","쇼핑라이브","사장님 보험","사업자 대출","대출안심케어","정책지원금","스마트플레이스","커머스API센터","마이비즈","보증서 대출","API데이터솔루션","안전거래"
]

GREETING_WORDS = ["안녕", "안녕하세요", "하이", "hello", "hi", "헬로", "반가워"]
THANKS_WORDS = ["고마워", "고맙", "감사", "감사합니다", "thanks", "thx", "thank you"]
HELP_WORDS = ["사용법", "어떻게", "도와줘", "도움", "예시", "가이드", "방법", "설명", "무엇을", "뭐부터", "어디서"]

def is_on_topic(query: str, retrieved: List[Dict[str, Any]], score_threshold: float) -> bool:
    # 1) keyword heuristic
    if any(kw in query for kw in SMART_KEYWORDS):
        return True
    # 2) retrieval confidence (최고 점수가 컷오프 미만이면 off-topic으로 간주)
    if retrieved:
        max_soft = max([d.get("score", 0.0) for d in retrieved])
        return max_soft >= score_threshold
    return False

def detect_intent(query: str, retrieved: List[Dict[str, Any]], score_threshold: float) -> str:
    q = query.strip().lower()
    # Greetings first (very short chat too)
    if any(word in q for word in GREETING_WORDS) or len(q) <= 2:
        return "greeting"
    if any(word in q for word in THANKS_WORDS):
        return "thanks"
    if any(word in q for word in HELP_WORDS):
        # If also on-topic, still SMART. Otherwise treat as help.
        return "smart" if is_on_topic(query, retrieved, score_threshold) else "help"
    # Domain on-topic?
    if is_on_topic(query, retrieved, score_threshold):
        return "smart"
    return "offtopic"
