#!/usr/bin/env python3
"""
임베딩 인덱스와 원본 데이터를 함께 압축하여 배포용 패키지를 생성합니다.
"""

import os
import zipfile
import shutil
from pathlib import Path
from datetime import datetime

def package_index_with_data():
    """인덱스와 원본 데이터를 함께 압축합니다."""
    
    # 소스 디렉토리들
    chroma_dir = Path("data/chroma")
    pkl_file = Path("data/final_result.pkl")
    
    if not chroma_dir.exists():
        print("❌ data/chroma 디렉토리가 존재하지 않습니다.")
        return
    
    if not pkl_file.exists():
        print("❌ data/final_result.pkl 파일이 존재하지 않습니다.")
        return
    
    # 타임스탬프
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # 압축 파일명
    zip_filename = f"smartstore_faq_complete_{timestamp}.zip"
    
    print(f"📦 완전한 패키지 생성 시작: {zip_filename}")
    
    try:
        with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
            # 1. ChromaDB 인덱스 압축
            print("📄 ChromaDB 인덱스 압축 중...")
            for root, dirs, files in os.walk(chroma_dir):
                for file in files:
                    file_path = Path(root) / file
                    arc_name = file_path.relative_to(Path("data"))
                    zipf.write(file_path, arc_name)
                    print(f"  📄 {arc_name}")
            
            # 2. 원본 데이터 압축
            print("📄 원본 데이터 압축 중...")
            arc_name = pkl_file.relative_to(Path("data"))
            zipf.write(pkl_file, arc_name)
            print(f"  📄 {arc_name}")
        
        # 파일 크기 확인
        zip_size = Path(zip_filename).stat().st_size / (1024 * 1024)  # MB
        print(f"✅ 완전한 패키지 생성 완료: {zip_filename} ({zip_size:.1f}MB)")
        
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
        print(f"2. 환경 변수에 COMPLETE_ZIP_URL 설정")
        print(f"3. 애플리케이션 시작 시 자동 압축 해제")
        print(f"4. 인덱스 구축 없이 바로 사용 가능")
        
    except Exception as e:
        print(f"❌ 패키징 실패: {e}")

if __name__ == "__main__":
    package_index_with_data()
