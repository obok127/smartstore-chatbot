# 네이버 스마트스토어 FAQ RAG 챗봇 (스트리밍)

## 1) 문제 접근 방법
- 과제 요구사항을 기준으로 **로컬 벡터DB(Chroma) + OpenAI** 로 RAG 파이프라인을 설계했습니다.
- 한국어 검색의 **재현율 향상**을 위해 Dense 임베딩 검색에 **BM25 + Fuzzy 타이틀 부스팅**을 RRF로 융합했습니다.
- **대화 맥락**(최근 12개)은 SQLite에 저장하여, 후속 질문에 맥락을 반영합니다.
- **도메인 가드**: 스마트스토어와 무관 질문은 키워드+스코어 휴리스틱으로 차단하고 정중히 안내합니다.
- **스트리밍**: OpenAI Chat Completions 스트리밍을 받아 SSE로 그대로 전달합니다.

## 2) 코드 결과물 (Github 링크)
- (여기에 레포 링크 삽입)

## 3) 코드 실행 방법
```bash
# 0) 환경 변수 설정
cp .env.example .env
# OPENAI_API_KEY 채우기

# 1) 의존성 설치
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 2) 서버 실행
uvicorn app.main:app --reload

# 3) 인덱싱
curl -X POST http://127.0.0.1:8000/index -H "Content-Type: application/json" -d '{
  "pkl_path":"PATH/TO/final_result.pkl",
  "reset": true
}'

# 4) 대화 스트리밍
curl -N -X POST http://127.0.0.1:8000/chat/stream -H "Content-Type: application/json" -d '{
  "conversation_id": "demo-1",
  "message": "미성년자도 판매 회원 등록이 가능한가요?"
}'
```

## 4) 구조 및 설계
- `app/retriever.py`: Chroma Dense 검색 + BM25 + fuzzy 타이틀 부스팅 → RRF 융합
- `app/llm.py`: 시스템 프롬프트(도메인 제한) + 스트리밍 처리
- `app/memory.py`: SQLite 대화 기록
- `app/guard.py`: 도메인 필터 (키워드 + 스코어 임계값)
- `app/config.py`: `.env` 기반 설정
- `app/main.py`: FastAPI 엔드포인트 (인덱스/채팅/히스토리)

## 5) 데모 (2가지 이상)
### A. 입점/등록
유저: *미성년자도 판매 회원 등록이 가능한가요?*  
챗봇: *(FAQ 근거로 불가/가능 조건 안내)*  
챗봇:  
- 등록에 필요한 서류 안내해드릴까요?  
- 등록 절차 소요 기간이 궁금하신가요?  
- 개인/법인 사업자 조건 차이를 알려드릴까요?  

### B. 환불/교환/배송
유저: *구매자가 단순 변심으로 환불을 요청하면 누가 배송비를 부담하나요?*  
챗봇: *(FAQ 근거로 원칙/예외 안내 + 출처)*  
챗봇:  
- 교환 시 배송비는 어떻게 되나요?  
- 판매자 귀책 사유 환불 기준이 궁금하신가요?  
- 네이버페이 결제 취소 시 정산 영향이 있을까요?  

(원하면 스크린샷/텍스트 로그를 첨부)

## 6) 성능 최적화 포인트
- 임베딩 모델: 비용/품질에 따라 `text-embedding-3-small` ↔ `-3-large` 선택
- 재순위화: `cross-encoder/ms-marco-MiniLM-L-6-v2` (HF)로 상위 20개 재정렬 (옵션)
- 쿼리 재작성: LLM으로 한국어 동의어/오타 정규화
- 캐시/압축: 검색결과 캐시, 컨텍스트 압축으로 토큰 절약

## 7) 한계 및 확장
- 데이터 업데이트 자동화: 크롤러로 최신 FAQ 동기화 → 색인 리빌드
- 멀티모달: 이미지 가이드/스크린샷 인식
- 관리 콘솔: 질의 로그/피드백/가드레일 조정 UI

## 8) 사용 패키지
- FastAPI, Uvicorn, OpenAI, ChromaDB, pandas, rank-bm25, rapidfuzz, pydantic, pydantic-settings, python-dotenv, tiktoken

