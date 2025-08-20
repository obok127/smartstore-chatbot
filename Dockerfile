FROM python:3.11-slim

WORKDIR /app

# 시스템 의존성 설치
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Python 의존성 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 애플리케이션 코드 복사
COPY . .

# data 디렉토리 생성
RUN mkdir -p data

# 포트 노출 (Railway는 $PORT 환경변수 사용)
EXPOSE 8000

# 시작 스크립트 생성
RUN echo '#!/bin/bash\n\
# 환경 변수에서 데이터 다운로드\n\
if [ ! -z "$COMPLETE_ZIP_URL" ]; then\n\
    echo "📥 데이터 다운로드 중..."\n\
    curl -L "$COMPLETE_ZIP_URL" -o data.zip\n\
    unzip -o data.zip -d data/\n\
    rm data.zip\n\
    echo "✅ 데이터 준비 완료"\n\
fi\n\
\n\
# 애플리케이션 실행\n\
exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}\n\
' > /app/start.sh && chmod +x /app/start.sh

# 시작 스크립트 실행
CMD ["/app/start.sh"]
