#!/usr/bin/env python3
"""
임베딩 인덱스를 압축하여 배포용 패키지를 생성합니다.
"""

import os
import zipfile
import shutil
from pathlib import Path
from datetime import datetime

def package_index():
    """인덱스를 압축하여 배포용 패키지를 생성합니다."""
    
    # 소스 디렉토리
    chroma_dir = Path("data/chroma")
    
    if not chroma_dir.exists():
        print("❌ data/chroma 디렉토리가 존재하지 않습니다.")
        print("먼저 인덱스를 구축해주세요:")
        print("curl -X POST 'http://localhost:8000/index' -H 'Content-Type: application/json' -d '{\"pkl_path\":\"data/final_result.pkl\",\"reset\":true}'")
        return
    
    # 타임스탬프
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # 압축 파일명
    zip_filename = f"smartstore_faq_index_{timestamp}.zip"
    
    print(f"📦 인덱스 패키징 시작: {zip_filename}")
    
    try:
        with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
            # ChromaDB 디렉토리 전체 압축
            for root, dirs, files in os.walk(chroma_dir):
                for file in files:
                    file_path = Path(root) / file
                    arc_name = file_path.relative_to(Path("data"))
                    zipf.write(file_path, arc_name)
                    print(f"  📄 {arc_name}")
        
        # 파일 크기 확인
        zip_size = Path(zip_filename).stat().st_size / (1024 * 1024)  # MB
        print(f"✅ 인덱스 패키징 완료: {zip_filename} ({zip_size:.1f}MB)")
        
        # 압축 해제 테스트
        print("🧪 압축 해제 테스트 중...")
        test_dir = Path(f"test_extract_{timestamp}")
        test_dir.mkdir(exist_ok=True)
        
        with zipfile.ZipFile(zip_filename, 'r') as zipf:
            zipf.extractall(test_dir)
        
        # 테스트 디렉토리 정리
        shutil.rmtree(test_dir)
        print("✅ 압축 해제 테스트 성공")
        
        print(f"\n📋 배포 방법:")
        print(f"1. {zip_filename} 파일을 Railway에 업로드")
        print(f"2. 환경 변수에 INDEX_ZIP_URL 설정")
        print(f"3. 애플리케이션 시작 시 자동 압축 해제")
        
    except Exception as e:
        print(f"❌ 패키징 실패: {e}")

if __name__ == "__main__":
    package_index()
