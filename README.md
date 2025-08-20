# 🛍️ 네이버 스마트스토어 FAQ RAG 챗봇

> **2717개 FAQ 데이터 기반의 지능형 챗봇**  
> FastAPI + RAG + 스트리밍으로 구현된 스마트스토어 전문 상담사

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green.svg)](https://fastapi.tiangolo.com)
[![ChromaDB](https://img.shields.io/badge/ChromaDB-Local-orange.svg)](https://chromadb.ai)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## 📋 목차

- [🎯 프로젝트 개요](#-프로젝트-개요)
- [🚀 주요 기능](#-주요-기능)
- [🏗️ 기술 스택](#️-기술-스택)
- [📁 프로젝트 구조](#-프로젝트-구조)
- [⚙️ 설치 및 실행](#️-설치-및-실행)
- [🔧 API 사용법](#-api-사용법)
- [🎭 데모 시나리오](#-데모-시나리오)
- [📊 성능 최적화](#-성능-최적화)
- [🔍 문제 해결](#-문제-해결)
- [🤝 기여하기](#-기여하기)

## 🎯 프로젝트 개요

네이버 스마트스토어의 **2717개 FAQ 데이터**를 기반으로 한 지능형 챗봇입니다. RAG(Retrieval-Augmented Generation) 기술을 활용하여 정확하고 맥락에 맞는 답변을 제공하며, 실시간 스트리밍으로 자연스러운 대화 경험을 제공합니다.

### 📚 참고 데이터
- **출처**: [네이버 스마트스토어 도움말](https://help.sell.smartstore.naver.com/index.help)
- **데이터**: 2717개 한글 FAQ (final_result.pkl)
- **범위**: 가입/등록, 상품관리, 정산관리, 배송/환불 등 전 영역

## 🚀 주요 기능

### 💬 지능형 대화
- **맥락 인식**: 이전 대화 기록을 기반으로 연속성 있는 답변
- **후속 질문 제안**: 관련된 추가 질문들을 자동 제안
- **실시간 스트리밍**: 자연스러운 타이핑 효과로 답변 전달

### 🔍 정확한 검색
- **하이브리드 검색**: ChromaDB(Dense) + BM25(Sparse) 융합
- **키워드 부스팅**: 제목 매칭 시 가중치 부여
- **관련성 필터링**: 질문과 답변의 관련성 자동 판단

### 🛡️ 도메인 가드
- **오프토픽 필터링**: 스마트스토어 관련 질문만 답변
- **키워드 기반 분류**: 1000+ 스마트스토어 관련 키워드
- **점수 기반 판단**: 검색 결과 점수로 의도 분류

### 📝 대화 관리
- **대화 기록 저장**: SQLite 기반 영구 저장
- **세션 관리**: conversation_id 기반 대화 분리
- **메모리 최적화**: 최근 12개 대화만 유지

## 🏗️ 기술 스택

### Backend
- **FastAPI**: 고성능 웹 프레임워크
- **Uvicorn**: ASGI 서버
- **Pydantic**: 데이터 검증 및 설정 관리

### AI/ML
- **ChromaDB**: 로컬 벡터 데이터베이스
- **BM25**: 스파스 검색 알고리즘
- **BGE-M3**: 다국어 임베딩 모델
- **Gemini**: Google Gemini LLM (기본)
- **OpenAI**: OpenAI GPT (대안)

### 데이터 처리
- **Pandas**: 데이터 처리 및 분석
- **RapidFuzz**: 퍼지 문자열 매칭
- **SQLite**: 대화 기록 저장

### 개발 도구
- **Python 3.8+**: 메인 프로그래밍 언어
- **Docker**: 컨테이너화 (선택사항)
- **Git**: 버전 관리

## 📁 프로젝트 구조

```
smartstore-faq-rag/
├── 📁 app/                          # 메인 애플리케이션
│   ├── 🐍 main.py                   # FastAPI 앱 및 엔드포인트
│   ├── 🐍 config.py                 # 환경 설정 관리
│   ├── 🐍 llm.py                    # LLM 통합 (OpenAI/Gemini)
│   ├── 🐍 llm_gemini.py             # Gemini API 구현
│   ├── 🐍 retriever.py              # 하이브리드 검색 엔진
│   ├── 🐍 embeddings.py             # 임베딩 모델 관리
│   ├── 🐍 memory.py                 # 대화 기록 관리
│   ├── 🐍 guard.py                  # 도메인 가드 및 의도 분류
│   ├── 🐍 prompts.py                # 프롬프트 템플릿 관리
│   └── 🐍 schemas.py                # Pydantic 스키마 정의
├── 📁 data/                         # 데이터 파일
│   ├── 📄 final_result.pkl          # 2717개 FAQ 데이터
│   ├── 📁 chroma/                   # ChromaDB 벡터 저장소
│   └── 📄 memory.db                 # 대화 기록 SQLite DB
├── 📁 scripts/                      # 유틸리티 스크립트
│   └── 🐍 build_index.py            # 인덱스 구축 스크립트
├── 📁 demos/                        # 데모 시나리오
│   ├── 📄 scenario_A.txt            # 신규 판매자 가입 시나리오
│   └── 📄 scenario_B.txt            # 정산 및 수수료 시나리오
├── 🌐 smart_store_faq_chat_frontend_index.html  # 웹 인터페이스
├── 📄 requirements.txt              # Python 의존성
├── 📄 .env                          # 환경 변수 (예시)
├── 📄 .gitignore                    # Git 무시 파일
└── 📄 README.md                     # 프로젝트 문서
```

## ⚙️ 설치 및 실행

### 1. 저장소 클론
```bash
git clone <repository-url>
cd smartstore-faq-rag
```

### 2. 가상환경 설정
```bash
# Python 3.8+ 필요
python -m venv .venv

# 가상환경 활성화
# Windows
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate
```

### 3. 의존성 설치
```bash
pip install -r requirements.txt
```

### 4. 환경 변수 설정
```bash
# .env 파일 생성
cp .env.example .env

# .env 파일 편집
nano .env
```

**필수 환경 변수:**
```env
# LLM 설정
LLM_PROVIDER=gemini                    # gemini 또는 openai
GEMINI_API_KEY=your_gemini_api_key    # Gemini API 키
OPENAI_API_KEY=your_openai_api_key    # OpenAI API 키 (선택사항)

# 검색 설정
SCORE_THRESHOLD=0.14                   # 의도 분류 임계값
TOP_K=5                               # 검색 결과 수
RERANK_TOP_K=3                        # 재순위화 결과 수

# 서버 설정
HOST=127.0.0.1
PORT=8000
```

### 5. 서버 실행
```bash
# 개발 모드 (자동 재시작)
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000

# 프로덕션 모드
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### 6. 인덱스 구축
```bash
# API를 통한 인덱스 구축
curl -X POST "http://localhost:8000/index" \
  -H "Content-Type: application/json" \
  -d '{"pkl_path":"data/final_result.pkl","reset":true}'

# 또는 스크립트 사용
python scripts/build_index.py
```

### 7. 웹 인터페이스 접속
브라우저에서 `http://localhost:8000` 접속

## 🔧 API 사용법

### 기본 엔드포인트

#### 1. 헬스 체크
```bash
GET /health
```
```json
{
  "status": "healthy",
  "timestamp": "2024-01-01T00:00:00"
}
```

#### 2. 스트리밍 채팅
```bash
POST /chat/stream
```
```json
{
  "conversation_id": "user123",
  "message": "미성년자도 판매 회원 등록이 가능한가요?"
}
```

**응답 (SSE 스트림):**
```
data: {"type": "start", "message": "답변을 생성하고 있습니다..."}

data: {"type": "token", "content": "안녕하세요! 스마트스토어 전문 상담사입니다."}

data: {"type": "token", "content": "네이버 스마트스토어는 만 14세 미만의 개인..."}

data: {"type": "end", "message": "답변 완료"}
```

#### 3. 대화 기록 조회
```bash
GET /chat/history/{conversation_id}
```
```json
[
  {
    "role": "user",
    "content": "미성년자도 판매 회원 등록이 가능한가요?",
    "timestamp": "2024-01-01T00:00:00"
  },
  {
    "role": "assistant", 
    "content": "안녕하세요! 스마트스토어 전문 상담사입니다...",
    "timestamp": "2024-01-01T00:00:05"
  }
]
```

### 디버그 엔드포인트

#### 1. 검색 테스트
```bash
GET /debug/search?q=상품등록&k=3
```

#### 2. 의도 분류 테스트
```bash
GET /debug/intent?q=스마트스토어 가입 방법
```

#### 3. LLM 상태 확인
```bash
GET /debug/llm_status
```

#### 4. 인덱스 상태 확인
```bash
GET /debug/index_status?q=test&k=3
```

## 🎭 데모 시나리오

### 시나리오 A: 신규 판매자 가입 및 상품 등록

**1단계: 가입 조건 문의**
```
사용자: "미성년자도 판매 회원 등록이 가능한가요?"

챗봇: "안녕하세요! 스마트스토어 전문 상담사입니다.

네이버 스마트스토어는 만 14세 미만의 개인(개인 사업자 포함) 또는 법인사업자는 입점이 불가함을 양해 부탁 드립니다.

가입 가능 조건:
- 만 14세 이상 개인
- 개인사업자 또는 법인사업자
- 사업자등록증 소지자

필요 서류:
1. 사업자등록증 (개인사업자 또는 법인)
2. 신분증 (주민등록증, 운전면허증 등)
3. 통장사본

<followups>
- 등록에 필요한 서류 안내해드릴까요?
- 등록 절차는 얼마나 오래 걸리는지 안내가 필요하신가요?
- 개인사업자 등록 방법이 궁금하신가요?
</followups>"
```

**2단계: 가입 절차 문의**
```
사용자: "등록 절차는 얼마나 오래 걸리는지 안내가 필요하신가요?"

챗봇: "스마트스토어 가입 절차와 소요 시간을 안내해드릴게요!

가입 절차 및 소요 시간:

1. 서류 준비 (1-2일)
2. 온라인 신청 (10-15분)
3. 심사 과정 (1-3일)
4. 첫 상품 등록 (30분-1시간)

총 소요 시간: 약 3-7일

<followups>
- 상품 등록 방법을 자세히 알고 싶으신가요?
- 첫 상품 등록 시 주의사항이 궁금하신가요?
- 상품 승인 과정에 대해 궁금하신가요?
</followups>"
```

### 시나리오 B: 정산 및 수수료 문의

**1단계: 정산 주기 문의**
```
사용자: "정산 주기와 수수료는 어떻게 되나요?"

챗봇: "안녕하세요! 스마트스토어 정산 관련 정보를 안내해드릴게요.

정산 주기:
- 일반 정산: 매월 15일, 말일 기준으로 2회 정산
- 빠른 정산: 판매 후 3-5일 내 정산 가능 (수수료 추가)

수수료 구조:
- 기본 수수료: 카테고리별 2-15%
- 결제 수수료: 별도 2.5% (네이버페이)

예시: 10만원 상품 판매 시
- 수수료 5%: 5,000원
- 결제 수수료 2.5%: 2,500원
- 정산 금액: 92,500원

<followups>
- 특정 카테고리 수수료율이 궁금하신가요?
- 세금계산서 발급 방법을 알고 싶으신가요?
- 정산 지연 사유를 확인하고 싶으신가요?
</followups>"
```

## 📊 성능 최적화

### 검색 성능
- **하이브리드 검색**: Dense + Sparse 융합으로 정확도 향상
- **키워드 부스팅**: 제목 매칭 시 가중치 부여
- **재순위화**: 상위 결과 재정렬로 관련성 향상

### 응답 품질
- **프롬프트 엔지니어링**: 친근하고 실용적인 답변 스타일
- **관련성 필터링**: 질문과 답변의 관련성 자동 판단
- **폴백 메커니즘**: LLM 실패 시 구조화된 답변 제공

### 시스템 성능
- **스트리밍 응답**: 실시간 답변 생성으로 사용자 경험 향상
- **메모리 최적화**: 최근 대화만 유지하여 메모리 사용량 제한
- **캐싱**: 검색 결과 캐싱으로 응답 속도 향상

## 🔍 문제 해결

### 일반적인 문제

#### 1. 포트 충돌
```bash
# 기존 프로세스 종료
pkill -f uvicorn
# 또는
lsof -ti:8000 | xargs kill -9
```

#### 2. ChromaDB 인덱스 문제
```bash
# ChromaDB 완전 초기화
rm -rf data/chroma
mkdir -p data/chroma

# 인덱스 재생성
curl -X POST "http://localhost:8000/index" \
  -H "Content-Type: application/json" \
  -d '{"pkl_path":"data/final_result.pkl","reset":true}'
```

#### 3. LLM API 오류
```bash
# LLM 상태 확인
curl http://localhost:8000/debug/llm_status

# 환경 변수 확인
echo $GEMINI_API_KEY
echo $OPENAI_API_KEY
```

#### 4. 임베딩 차원 불일치
```
[retrieve] Dense 검색 실패: Collection expecting embedding with dimension of 1024, got 384
```
**해결방법**: ChromaDB 컬렉션을 완전히 재생성

### 로그 확인
```bash
# 서버 로그 실시간 확인
uvicorn app.main:app --reload --log-level debug

# 특정 로그 필터링
tail -f uvicorn.log | grep "ERROR"
```

### 성능 모니터링
```bash
# 검색 성능 테스트
curl "http://localhost:8000/debug/search?q=상품등록&k=3"

# 의도 분류 테스트
curl "http://localhost:8000/debug/intent?q=스마트스토어 가입"
```

## 🤝 기여하기

### 개발 환경 설정
1. 저장소 포크
2. 기능 브랜치 생성: `git checkout -b feature/amazing-feature`
3. 변경사항 커밋: `git commit -m 'Add amazing feature'`
4. 브랜치 푸시: `git push origin feature/amazing-feature`
5. Pull Request 생성

### 코드 스타일
- **Python**: PEP 8 준수
- **타입 힌트**: 모든 함수에 타입 힌트 추가
- **문서화**: 모든 함수에 docstring 작성
- **테스트**: 새로운 기능에 대한 테스트 코드 작성

### 이슈 리포트
버그 리포트나 기능 요청 시 다음 정보를 포함해주세요:
- 운영체제 및 Python 버전
- 에러 메시지 전체
- 재현 단계
- 예상 동작

## 📄 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다. 자세한 내용은 [LICENSE](LICENSE) 파일을 참조하세요.

## 🙏 감사의 말

- [네이버 스마트스토어](https://help.sell.smartstore.naver.com/) - FAQ 데이터 제공
- [ChromaDB](https://chromadb.ai/) - 벡터 데이터베이스
- [FastAPI](https://fastapi.tiangolo.com/) - 웹 프레임워크
- [Google Gemini](https://ai.google.dev/) - LLM API

---

**문의사항이나 버그 리포트는 [Issues](../../issues)에 등록해주세요!** 🐛
